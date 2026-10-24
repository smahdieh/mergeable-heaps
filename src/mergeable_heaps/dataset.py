"""Create, save and load the synthetic benchmark datasets.

Every stream is generated once at the largest size (10 million by default)
and the benchmarks use prefixes of it for smaller n, so all sizes come from
the same distribution and the same file.

Streams:
  keys              uniform random int32 keys in [0, 2^31)           (insert / heapsort)
  decrease_targets  uniform random uint32; map to a node with target_index(raw, n)
  decrease_amounts  how much to lower that node's key, in [1, 2^24]  (decrease-key)
  graph_<V>_*       random directed graph with V nodes and avg_degree * V edges
                    (src, dst, weight arrays)                         (Dijkstra)

Files are raw little-endian 4-byte integers (Python `array`), described by
manifest.json with the count and SHA-256 of each file.
"""

import hashlib
import json
import random
import sys
from array import array
from pathlib import Path
from typing import Optional

KEY_BITS = 31
MAX_DECREASE = 1 << 24
MANIFEST = "manifest.json"


def _int32_array(typecode: str, values=()) -> array:
    """Input: 'i' (signed) or 'I' (unsigned) and values. Output: a 4-byte-per-item array."""
    arr = array(typecode, values)
    if arr.itemsize != 4:
        raise RuntimeError(f"array('{typecode}') is {arr.itemsize} bytes on this platform, expected 4")
    return arr


def random_keys(count: int, seed: int) -> array:
    """Uniform random keys.

    Input: number of keys, seed. Output: array('i') of ints in [0, 2^31).
    """
    rng = random.Random(f"{seed}-keys")
    bits = rng.getrandbits
    return _int32_array("i", (bits(KEY_BITS) for _ in range(count)))


def decrease_ops(count: int, seed: int) -> tuple:
    """Random decrease-key operations, usable for any heap size n <= 2^32.

    Input: number of operations, seed.
    Output: (targets, amounts). targets is array('I') of raw 32-bit values
    (turn one into a node index with target_index), amounts is array('i')
    in [1, 2^24].
    """
    rng = random.Random(f"{seed}-decrease")
    bits, randint = rng.getrandbits, rng.randint
    targets = _int32_array("I", (bits(32) for _ in range(count)))
    amounts = _int32_array("i", (randint(1, MAX_DECREASE) for _ in range(count)))
    return targets, amounts


def target_index(raw: int, n: int) -> int:
    """Map a raw 32-bit target to a node index in [0, n) without modulo bias.

    Input: raw value from decrease_ops, heap size n. Output: index in [0, n).
    """
    return (raw * n) >> 32


def random_graph(num_nodes: int, avg_degree: int, seed: int, max_weight: int = 1000) -> tuple:
    """Random directed graph that is strongly connected.

    The first num_nodes edges form a cycle through a random permutation of the
    nodes, so every node is reachable from every other; the rest are uniform
    random edges. Weights are uniform in [1, max_weight].

    Input: node count V, average out-degree d, seed, max edge weight.
    Output: (src, dst, weight) arrays, each with V * d entries.
    """
    if num_nodes < 2 or avg_degree < 1:
        raise ValueError("need at least 2 nodes and avg_degree >= 1")
    rng = random.Random(f"{seed}-graph-{num_nodes}")
    num_edges = num_nodes * avg_degree
    order = list(range(num_nodes))
    rng.shuffle(order)

    src = _int32_array("i", order)
    dst = _int32_array("i", order[1:] + order[:1])
    rand_node, rand_weight = rng.randrange, rng.randint
    extra = num_edges - num_nodes
    src.extend(rand_node(num_nodes) for _ in range(extra))
    dst.extend(rand_node(num_nodes) for _ in range(extra))
    weight = _int32_array("i", (rand_weight(1, max_weight) for _ in range(num_edges)))
    return src, dst, weight


def save_array(arr: array, path: Path) -> None:
    """Write an array as raw little-endian bytes. Input: array, file path. Output: None."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if sys.byteorder != "little":
        arr = array(arr.typecode, arr)
        arr.byteswap()
    with path.open("wb") as f:
        arr.tofile(f)


def load_array(path: Path, typecode: str, limit: Optional[int] = None) -> array:
    """Read a file written by save_array.

    Input: file path, 'i' or 'I', optional number of items to read (a prefix).
    Output: the array.
    """
    arr = _int32_array(typecode)
    count = path.stat().st_size // arr.itemsize
    if limit is not None:
        count = min(count, limit)
    with path.open("rb") as f:
        arr.fromfile(f, count)
    if sys.byteorder != "little":
        arr.byteswap()
    return arr


def sha256(path: Path) -> str:
    """Input: file path. Output: hex SHA-256 of the file."""
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_manifest(out_dir: Path, params: dict, files: dict) -> None:
    """Write manifest.json listing every file with its type, count and checksum.

    Input: data folder, generation parameters, {file name: (typecode, description)}.
    Output: None.
    """
    entries = {}
    for name, (typecode, description) in files.items():
        path = out_dir / name
        entries[name] = {
            "typecode": typecode,
            "count": path.stat().st_size // 4,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "description": description,
        }
    manifest = {"format": "raw little-endian 4-byte integers", **params, "files": entries}
    (out_dir / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n")


def load_manifest(data_dir: Path) -> dict:
    """Input: data folder. Output: the parsed manifest.json."""
    return json.loads((data_dir / MANIFEST).read_text())


def verify_dataset(data_dir: Path) -> list:
    """Check every file in the manifest exists and matches its size and checksum.

    Input: data folder. Output: list of problems (empty if everything is fine).
    """
    problems = []
    for name, info in load_manifest(data_dir)["files"].items():
        path = data_dir / name
        if not path.exists():
            problems.append(f"{name}: missing")
        elif path.stat().st_size != info["bytes"]:
            problems.append(f"{name}: size {path.stat().st_size} != {info['bytes']}")
        elif sha256(path) != info["sha256"]:
            problems.append(f"{name}: checksum mismatch")
    return problems
