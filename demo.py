"""Proof that Rust and Python work together, two ways, with results cross-checked."""
import json
import os
import subprocess
import sys
import tempfile
import time

import hybrid_search  # <- compiled Rust, imported like any Python module

# Make a test corpus: 200 files x 5,000 lines.
tmp = tempfile.mkdtemp()
paths = []
for f in range(200):
    p = os.path.join(tmp, f"file_{f}.rs")
    with open(p, "w") as fh:
        for i in range(5000):
            fh.write(f"fn handler_{i}() {{ let x = {i}; }}\n" if i % 97 == 0 else f"// line {i} of file {f}\n")
    paths.append(p)
PATTERN = "fn handler_"


def pure_python(paths, pattern):
    hits = []
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as fh:
            for n, line in enumerate(fh, 1):
                line = line.rstrip("\n")
                if pattern in line:
                    hits.append((p, n, line))
    return hits


# Way 1: PyO3 module (Rust called directly from Python).
t = time.perf_counter(); rust_hits = hybrid_search.search(paths, PATTERN); t_rust = time.perf_counter() - t

# Way 2: separate Rust CLI, Python reads its JSON Lines output.
cli = os.path.join(os.path.dirname(os.path.abspath(__file__)), "target", "release",
                   "hsearch.exe" if os.name == "nt" else "hsearch")
t = time.perf_counter()
out = subprocess.run([cli, PATTERN, *paths], capture_output=True, text=True, check=True).stdout
cli_hits = [(d["path"], d["line"], d["text"]) for d in map(json.loads, out.splitlines())]
t_cli = time.perf_counter() - t

# Reference: pure Python.
t = time.perf_counter(); py_hits = pure_python(paths, PATTERN); t_py = time.perf_counter() - t

print(f"Python {sys.version.split()[0]}, module loaded from: {hybrid_search.__file__}")
print(f"Matches  PyO3 module: {len(rust_hits):,}   Rust CLI: {len(cli_hits):,}   pure Python: {len(py_hits):,}")
assert rust_hits == py_hits, "PyO3 results differ from pure Python"
assert cli_hits == py_hits, "CLI results differ from pure Python"
print("All three result sets are IDENTICAL (every path, line number and text).")
print(f"Time     PyO3 module: {t_rust*1000:.1f} ms   Rust CLI: {t_cli*1000:.1f} ms   pure Python: {t_py*1000:.1f} ms")
print("Sample:", rust_hits[0])
