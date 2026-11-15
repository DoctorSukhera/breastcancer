# Corrected revised-submission plotting scripts

From repository root (after installing requirements):

```bash
python -m pip install pillow python-pptx
python scripts/final_figure_panels/regenerate_figure2.py
python scripts/final_figure_panels/regenerate_figure5.py
```

Both scripts use repository-relative paths and write into `figures/corrected_figure2/` and `figures/corrected_figure5/`. Figure 2 uses the archived selected-candidate summary CSV; Figure 5 uses the constructed benchmark's generated outputs. These scripts do **not** reproduce original TCGA/GEO molecular data processing. See `docs/FIGURE_REPRODUCIBILITY_STATUS.md`.
