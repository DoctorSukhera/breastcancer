# Restricted LLM comparator protocol

The revised manuscript does **not** report quantitative performance for an external LLM agent, because no external model was executed and archived under the identical frozen 760-scenario inference environment.

`llm/restricted_llm_protocol.py` exposes the same registered action vocabulary and controller-visible scenario fields to an optional Hugging Face model. The script is dry-run/inspection oriented by default; model execution requires `--execute` and the optional dependencies in `requirements-llm.txt`.

This protocol is included for transparency and future sensitivity testing. It must not be interpreted as evidence that the bounded deterministic controller outperforms contemporary LLM-based biomedical agents.
