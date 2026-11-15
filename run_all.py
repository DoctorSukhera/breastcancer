#!/usr/bin/env python3
"""Reproduce the released benchmark/figures and optionally rerun molecular analyses."""
from pathlib import Path
import argparse, subprocess, sys
ROOT=Path(__file__).resolve().parent

ap=argparse.ArgumentParser()
ap.add_argument('--molecular-config', help='Optional JSON config for a full external-data molecular rerun')
args=ap.parse_args()

steps=[
    [sys.executable,'scripts/repository_manifest.py','--validate'],
    [sys.executable,'benchmark/validate_package.py'],
]
if args.molecular_config:
    steps.append([sys.executable,'analysis/run_molecular_pipeline.py','--config',args.molecular_config,'--require-outside-repo'])
else:
    steps.append([sys.executable,'analysis/run_molecular_pipeline.py','--release-status'])
steps += [
    [sys.executable,'benchmark/run_benchmark.py'],
    [sys.executable,'benchmark/run_deterministic_baseline.py'],
    [sys.executable,'benchmark/run_ablation.py'],
    [sys.executable,'benchmark/analyze_results.py'],
    [sys.executable,'scripts/sync_figure5_controller_summary.py'],
    [sys.executable,'-m','unittest','discover','-s','tests','-v'],
    [sys.executable,'scripts/generate_figure1.py'],
    [sys.executable,'scripts/generate_figures_2_6.py'],
    [sys.executable,'benchmark/validate_package.py'],
    [sys.executable,'scripts/repository_manifest.py','--validate'],
]
for cmd in steps:
    print('\n>>>',' '.join(cmd),flush=True)
    subprocess.run(cmd,cwd=ROOT,check=True)
print('\nREPRODUCIBILITY WORKFLOW: PASS')
if not args.molecular_config:
    print('NOTE: Molecular analyses were not rerun because external source files were not supplied. Use --molecular-config for a full molecular rerun.')
