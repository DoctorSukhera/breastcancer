from pathlib import Path
import hashlib
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'frozen'


def digest_tree():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DATA.iterdir()) if p.is_file()}

# Normal release workflow must not invoke the builder.
run_all = (ROOT / 'run_all.py').read_text()
assert 'build_frozen_inputs.py' not in run_all
assert run_all.count("benchmark/validate_package.py") >= 2

# Builder must refuse to mutate frozen inputs without explicit confirmation.
before = digest_tree()
proc = subprocess.run(
    [sys.executable, str(ROOT / 'benchmark' / 'build_frozen_inputs.py')],
    cwd=ROOT,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)
assert proc.returncode != 0
assert '--confirm-rebuild' in proc.stderr
assert digest_tree() == before

# Builder source must expose an explicit confirmation gate before DATA writes.
builder = (ROOT / 'benchmark' / 'build_frozen_inputs.py').read_text()
assert '--confirm-rebuild' in builder
assert 'Refusing to rewrite shipped frozen benchmark inputs' in builder

print('Issue 13 frozen-input immutability tests: PASS')
