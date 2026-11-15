#!/usr/bin/env python3
"""Write or validate the deterministic repository SHA-256 manifest."""
from __future__ import annotations
from pathlib import Path
import argparse, csv, hashlib, sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "SHA256_MANIFEST.csv"
EXCLUDED_PARTS = {"__pycache__", ".git", ".venv", ".pytest_cache", ".mypy_cache"}
EXCLUDED_NAMES = {"SHA256_MANIFEST.csv", ".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp"}


def included_files():
    files=[]
    for p in ROOT.rglob('*'):
        if not p.is_file():
            continue
        rel=p.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        if p.name in EXCLUDED_NAMES or p.suffix in EXCLUDED_SUFFIXES:
            continue
        files.append(p)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def rows_now():
    return [
        (p.relative_to(ROOT).as_posix(), p.stat().st_size, sha256(p))
        for p in included_files()
    ]


def write_manifest():
    rows=rows_now()
    with MANIFEST.open('w', newline='', encoding='utf-8') as f:
        w=csv.writer(f, lineterminator='\n')
        w.writerow(['path','size_bytes','sha256'])
        w.writerows(rows)
    print(f"Wrote {MANIFEST.name}: {len(rows)} files")


def read_manifest():
    if not MANIFEST.exists():
        raise FileNotFoundError(MANIFEST)
    with MANIFEST.open(newline='', encoding='utf-8') as f:
        return {r['path']:(int(r['size_bytes']),r['sha256']) for r in csv.DictReader(f)}


def validate_manifest():
    expected=read_manifest()
    current={path:(size,digest) for path,size,digest in rows_now()}
    missing=sorted(set(expected)-set(current))
    extra=sorted(set(current)-set(expected))
    changed=sorted(path for path in set(expected)&set(current) if expected[path] != current[path])
    if missing or extra or changed:
        print('REPOSITORY SHA256 MANIFEST: FAIL', file=sys.stderr)
        if missing: print('Missing:', *missing, sep='\n  ', file=sys.stderr)
        if extra: print('Extra:', *extra, sep='\n  ', file=sys.stderr)
        if changed: print('Changed:', *changed, sep='\n  ', file=sys.stderr)
        return 1
    print(f"REPOSITORY SHA256 MANIFEST: PASS ({len(expected)} files)")
    return 0


def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--write', action='store_true', help='Rewrite SHA256_MANIFEST.csv from the current release tree.')
    g.add_argument('--validate', action='store_true', help='Validate the current release tree against SHA256_MANIFEST.csv.')
    args=ap.parse_args()
    if args.write:
        write_manifest(); return 0
    return validate_manifest()

if __name__ == '__main__':
    raise SystemExit(main())
