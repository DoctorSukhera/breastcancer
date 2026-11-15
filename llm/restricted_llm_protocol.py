#!/usr/bin/env python3
"""Restricted LLM comparator protocol.

The manuscript does NOT report LLM performance values. This script exposes the
same frozen action registry and operational scenario fields to an optional local
Hugging Face model and requests a single registered action in JSON. By default
it runs in --dry-run mode so reviewers can inspect prompts without downloading
model weights.
"""
import argparse, csv, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'frozen'

def registry():
    with open(DATA/'action_registry.csv') as f:return [r['action_id'] for r in csv.DictReader(f) if r['category']!='controller']

def make_prompt(s):
    visible={k:s.get(k) for k in ['scenario_key','family','goal_name','unavailable_actions','transient_fail_action','transient_mode','mapping_loss','provenance_corrupted','fallback_available','resource_prefer_low_cost','prohibited_pattern']}
    return "You are a restricted molecular-workflow tool selector. Choose only one registered action or TERMINATE. Return strict JSON {\\\"action\\\":...}.\nRegistered actions: "+", ".join(registry())+"\nVisible state: "+json.dumps(visible,sort_keys=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scenario-id',type=int,default=34);ap.add_argument('--model',default='Qwen/Qwen3-4B-Instruct-2507');ap.add_argument('--dry-run',action='store_true',default=True);ap.add_argument('--execute',action='store_true');args=ap.parse_args()
    import pandas as pd
    s=pd.read_csv(DATA/'controller_input_manifest.csv').fillna('').query('scenario_id == @args.scenario_id').iloc[0].to_dict();prompt=make_prompt(s)
    if not args.execute:
        print(prompt);return
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    tok=AutoTokenizer.from_pretrained(args.model);model=AutoModelForCausalLM.from_pretrained(args.model,torch_dtype='auto',device_map='auto')
    x=tok(prompt,return_tensors='pt').to(model.device);y=model.generate(**x,max_new_tokens=80,do_sample=False);print(tok.decode(y[0][x['input_ids'].shape[1]:],skip_special_tokens=True))
if __name__=='__main__':main()
