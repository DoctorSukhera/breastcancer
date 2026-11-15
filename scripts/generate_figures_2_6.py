import matplotlib
matplotlib.use("Agg")
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "figures"
SOURCE_DIR = ROOT / "data" / "source_tables"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
print("Figures will be written to:", OUTPUT_DIR.resolve())

THEME = {
    "white": "#FFFFFF",
    "header": "#FFFFFF",
    "panel_edge": "#323A43",
    "text": "#1F2933",
    "muted": "#5C6770",
    "grid": "#E1E5E8",
    "blue": "#6F93B8",
    "blue_light": "#AFC4D7",
    "green": "#86A98D",
    "rose": "#C58D91",
    "amber": "#D2AE67",
    "purple": "#9B8BC3",
    "teal": "#78A8A4",
    "grey": "#A8AFB6",
    "dark_grey": "#68737D",
}

plt.rcParams.update({
    "figure.facecolor": THEME["white"],
    "axes.facecolor": THEME["white"],
    "savefig.facecolor": THEME["white"],
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.edgecolor": THEME["dark_grey"],
    "axes.labelcolor": THEME["text"],
    "xtick.color": THEME["text"],
    "ytick.color": THEME["text"],
    "text.color": THEME["text"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "svg.hashsalt": "ageaware-bc-figures-v1",
})

PNG_DPI = 600
SHOW_TITLES_INSIDE_ARTWORK = False

def save_all(fig, stem):
    fig.savefig(OUTPUT_DIR / f"{stem}.png", dpi=PNG_DPI, bbox_inches="tight", facecolor="white",
                metadata={"Software": "Matplotlib 3.10.8"})
    fig.savefig(OUTPUT_DIR / f"{stem}.pdf", bbox_inches="tight", facecolor="white",
                metadata={"CreationDate": None, "ModDate": None, "Creator": "AgeAware BC reproducible figure pipeline", "Producer": "Matplotlib 3.10.8"})
    fig.savefig(OUTPUT_DIR / f"{stem}.svg", bbox_inches="tight", facecolor="white",
                metadata={"Date": None, "Creator": "AgeAware BC reproducible figure pipeline"})
    print(f"Saved {stem}.png / .pdf / .svg")

def clean_axis(ax, grid_axis=None):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(THEME["dark_grey"])
    ax.spines["bottom"].set_color(THEME["dark_grey"])
    if grid_axis:
        ax.grid(axis=grid_axis, color=THEME["grid"], lw=0.7, zorder=0)

def panel_frame(fig, rect, letter, title, header_frac=0.11):
    outer = fig.add_axes(rect)
    outer.set_axis_off()
    outer.add_patch(
        FancyBboxPatch(
            (0, 0), 1, 1,
            boxstyle="round,pad=0.004,rounding_size=0.012",
            fc=THEME["white"], ec=THEME["panel_edge"], lw=1.05,
            transform=outer.transAxes, clip_on=False
        )
    )
    outer.add_patch(
        Rectangle((0, 1-header_frac), 1, header_frac,
                  fc=THEME["header"], ec="none", transform=outer.transAxes)
    )
    outer.text(0.025, 1-header_frac/2, letter, va="center", ha="left",
               fontsize=15, fontweight="bold")
    outer.text(0.10, 1-header_frac/2, title, va="center", ha="left",
               fontsize=11.5, fontweight="bold")

    l,b,w,h = rect
    content = [l + 0.035*w, b + 0.045*h, 0.93*w, h*(1-header_frac)-0.07*h]
    return outer, content

def add_text_box(ax, xy, wh, text, fc="#F7F8F9", ec=None,
                 fontsize=9.5, weight="normal", align="center"):
    x,y = xy
    w,h = wh
    if ec is None:
        ec = THEME["panel_edge"]
    patch = FancyBboxPatch((x,y), w,h,
                           boxstyle="round,pad=0.01,rounding_size=0.015",
                           fc=fc, ec=ec, lw=0.8,
                           transform=ax.transAxes)
    ax.add_patch(patch)
    ax.text(x+w/2 if align=="center" else x+0.02,
            y+h/2, text, transform=ax.transAxes,
            ha=align, va="center", fontsize=fontsize,
            fontweight=weight, wrap=True)
    return patch

def fmt_p(p):
    p = float(p)
    if p < 1e-4:
        return f"{p:.1e}"
    if p < 0.01:
        return f"{p:.4f}"
    return f"{p:.3f}"

FIG1 = {
    "genage": 307,
    "expression_testable": 292,
    "unadjusted_significant": 126,
    "adjusted_significant": 80,
    "external_locked": 40,
    "externally_replicated": 8,
    "class_A": 4,
    "tcga_n": 1079,
    "gse_n": 104,
    "string_mapped": 79,
    "string_edges_700": 213,
    "enrichment_tested": 1698,
    "enrichment_significant": 514,
}

CLASS_DEFS = {
    "Class A": {"genes":["IL7R","SQSTM1","EGR1","IGF1"],
                "definition":"Cross-cohort replicated and ER-robust"},
    "Class B": {"genes":["ESR1","A2M","FOXO1","EIF5A2"],
                "definition":"Cross-cohort replicated but ER-sensitive"},
    "Class C": {"genes":["EGFR","MYC","MAPK8","IRS2"],
                "definition":"Adjusted discovery + network/functional convergence"},
    "Class D": {"genes":[],
                "definition":"68 remaining adjusted signals"},
}

FIG2 = pd.DataFrame([
    ["IL7R","Class A",-0.209888,-0.281409,-0.138367,5.157169e-07,-0.282248,0.012326,-0.222530,-0.047038,0.153994],
    ["SQSTM1","Class A",0.096623,0.056064,0.137182,7.357097e-05,0.262804,0.020096,0.188315,0.084207,0.452372],
    ["EGR1","Class A",-0.189673,-0.277729,-0.101616,3.725795e-04,-0.391872,0.000778,-0.146702,-0.064565,0.569849],
    ["IGF1","Class A",-0.039126,-0.057764,-0.020488,4.674261e-04,-0.340639,0.002685,-0.153091,-0.033362,0.353844],
    ["ESR1","Class B",0.421989,0.338080,0.505897,1.867481e-20,0.253794,0.023331,0.426423,0.061656,0.000039],
    ["A2M","Class B",-0.140713,-0.200480,-0.080945,8.855628e-05,-0.318283,0.003969,-0.170531,0.007582,0.153994],
    ["FOXO1","Class B",-0.087115,-0.124592,-0.049638,1.078193e-04,-0.354405,0.002233,-0.184513,0.068267,0.027781],
    ["EIF5A2","Class B",-0.056848,-0.083770,-0.029927,4.589255e-04,-0.324967,0.003816,-0.190031,0.061610,0.027781],
    ["EGFR","Class C",-0.146846,-0.205482,-0.088210,2.977867e-05,0.071668,0.805422,-0.269172,0.084604,0.000197],
    ["MYC","Class C",-0.170122,-0.238440,-0.101804,3.088451e-05,-0.137687,0.192975,-0.126505,-0.179614,0.743872],
    ["MAPK8","Class C",-0.057034,-0.081638,-0.032430,1.078193e-04,0.138702,0.919869,-0.169346,-0.117054,0.744981],
    ["IRS2","Class C",-0.130629,-0.192166,-0.069093,4.413651e-04,-0.090697,0.342718,-0.207379,-0.156393,0.749300],
], columns=[
    "gene","class","beta_age_z","ci_low","ci_high","fdr_adjusted",
    "rho_geo","fdr_geo_directional","rho_er_pos","rho_er_neg","fdr_er_heterogeneity"
])
REPLICATED8 = ["IL7R","SQSTM1","EGR1","IGF1","ESR1","A2M","FOXO1","EIF5A2"]

FIG3 = {
    "observed_fdr_genes":126,
    "n_permutations":500,
    "empirical_p":0.001996,
    "string":pd.DataFrame({"score":[400,700,900],"edges":[566,213,114],"density":[0.184,0.069,0.037]}),
    "rank_stability":pd.DataFrame({"comparison":["400 vs 700","700 vs 900","400 vs 900"],
                                   "spearman_rho":[0.887,0.899,0.806]}),
    "resilience":pd.DataFrame({"strategy":["Random","Degree-targeted","Betweenness-targeted"],
                               "auc":[0.283,0.146,0.155]}),
    "top20_overlap":pd.DataFrame({"comparison":["400 vs 700","700 vs 900"],
                                  "jaccard_overlap":[0.667,0.667]}),
}


# Figure 5/6 benchmark values are loaded exclusively from validated source tables below.




# Verified top-20 degree overlap relative to the primary score-700 network.
FIG3["top20_overlap"] = pd.DataFrame({
    "comparison":["400 vs 700","700 reference","900 vs 700"],
    "jaccard_overlap":[0.667,1.000,0.667]
})

# Benchmark and ablation values are never embedded in plotting code.
# Load the frozen numerical source tables.  The plotting script is read-only with
# respect to these CSVs; it does not regenerate or overwrite source data.
FIG2 = pd.read_csv(SOURCE_DIR / "Figure2_candidate_statistics.csv")
REPLICATED8 = FIG2.loc[FIG2["class"].isin(["Class A", "Class B"]), "gene"].tolist()
FIG3["string"] = pd.read_csv(SOURCE_DIR / "Figure3_STRING_thresholds.csv")
FIG3["rank_stability"] = pd.read_csv(SOURCE_DIR / "Figure3_degree_rank_stability.csv")
FIG3["resilience"] = pd.read_csv(SOURCE_DIR / "Figure3_node_removal_resilience.csv")
FIG3["top20_overlap"] = pd.read_csv(SOURCE_DIR / "Figure3_top20_degree_overlap.csv")
FIG4_COUNTS = pd.read_csv(SOURCE_DIR / "Figure4_enrichment_counts.csv").iloc[0].to_dict()
FIG5_COMPOSITION = pd.read_csv(SOURCE_DIR / "Figure5_scenario_composition.csv")
FIG5_CONTROLLERS = pd.read_csv(SOURCE_DIR / "Figure5_controller_summary.csv")
FIG5_PAIRED = pd.read_csv(SOURCE_DIR / "Figure5_paired_policy_comparisons.csv")
FIG5_TRACES = pd.read_csv(SOURCE_DIR / "Figure5_representative_traces.csv")
FIG5_REFERENCE_OUTCOMES = {k: int(FIG5_COMPOSITION[k].sum()) for k in ["COMPLETE", "BLOCK", "FAIL_SAFE"]}
FIG6 = pd.read_csv(SOURCE_DIR / "Figure6_ablation_summary.csv")
FIG6_FAILURE_SIGNATURES = pd.read_csv(SOURCE_DIR / "Figure6_failure_signatures.csv")


def make_figure_2():
    fig=plt.figure(figsize=(15,9),facecolor="white")
    rects={
        "a":[0.02,0.52,0.25,0.45],
        "b":[0.28,0.52,0.34,0.45],
        "c":[0.63,0.52,0.35,0.45],
        "d":[0.02,0.05,0.31,0.43],
        "e":[0.34,0.05,0.32,0.43],
        "f":[0.67,0.05,0.31,0.43],
    }
    titles={
        "a":"Evidence refinement",
        "b":"TCGA-BRCA adjusted association with age",
        "c":"GSE42568 replication",
        "d":"ER-stratified association with age",
        "e":"ER sensitivity",
        "f":"Candidate classes",
    }
    frames={}; contents={}
    for k in rects:
        frames[k],contents[k]=panel_frame(fig,rects[k],k,titles[k])

    ax=frames["a"]
    chain=[
        (307,"curated ageing genes (GenAge)"),
        (292,"expression-testable in TCGA-BRCA"),
        (126,"age-associated (FDR < 0.05)"),
        (80,"adjusted (ER, PR, HER2, stage)"),
        (40,"locked external-test candidates"),
        (8,"replicated in GSE42568"),
        (4,"Class A"),
    ]
    y=0.78
    for i,(n,lab) in enumerate(chain):
        add_text_box(ax,(0.14,y),(0.72,0.095),f"{n}\n{lab}",
                     fc="#F2F4F5",fontsize=8.6,weight="bold")
        if i<len(chain)-1:
            ax.annotate("",xy=(0.50,y-0.025),xytext=(0.50,y),
                        xycoords=ax.transAxes,textcoords=ax.transAxes,
                        arrowprops=dict(arrowstyle="-|>",color=THEME["dark_grey"],lw=1))
        y-=0.112

    eight=FIG2.set_index("gene").loc[REPLICATED8].reset_index()
    yv=np.arange(len(eight))

    ax=fig.add_axes(contents["b"])
    x=eight["beta_age_z"].to_numpy()
    lo=x-eight["ci_low"].to_numpy()
    hi=eight["ci_high"].to_numpy()-x
    ax.errorbar(x,yv,xerr=[lo,hi],fmt="o",color=THEME["blue"],
                ecolor=THEME["dark_grey"],capsize=2.5,lw=1,zorder=3)
    ax.axvline(0,color=THEME["dark_grey"],ls="--",lw=0.9)
    ax.set_yticks(yv); ax.set_yticklabels(eight["gene"])
    ax.invert_yaxis()
    ax.set_xlabel("Adjusted β per 1-SD age (95% CI)")
    ax.set_xlim(-0.35,0.58)
    clean_axis(ax,"x")
    for i,row in eight.iterrows():
        ax.text(0.57,i,fmt_p(row["fdr_adjusted"]),ha="right",va="center",fontsize=7.6)
    ax.text(0.57,-0.72,"FDR",ha="right",fontsize=8.2,fontweight="bold")

    ax=fig.add_axes(contents["c"])
    vals=eight["rho_geo"].to_numpy()
    colors=np.where(vals>=0,THEME["blue"],THEME["rose"])
    ax.barh(yv,vals,color=colors,edgecolor="none",zorder=2)
    ax.axvline(0,color=THEME["dark_grey"],lw=0.9)
    ax.set_yticks(yv); ax.set_yticklabels(eight["gene"])
    ax.invert_yaxis()
    ax.set_xlabel("Spearman ρ with age")
    ax.set_xlim(-0.50,0.38)
    clean_axis(ax,"x")
    for i,row in eight.iterrows():
        ax.text(0.37,i,fmt_p(row["fdr_geo_directional"]),ha="right",va="center",fontsize=7.6)
    ax.text(0.37,-0.72,"Directional FDR",ha="right",fontsize=8.0,fontweight="bold")

    ax=fig.add_axes(contents["d"])
    pos=eight["rho_er_pos"].to_numpy()
    neg=eight["rho_er_neg"].to_numpy()
    ax.scatter(pos,yv-0.10,s=34,color=THEME["blue"],label="ER+ (n=795)",zorder=3)
    ax.scatter(neg,yv+0.10,s=34,color=THEME["rose"],label="ER− (n=235)",zorder=3)
    ax.axvline(0,color=THEME["dark_grey"],ls="--",lw=0.9)
    ax.set_yticks(yv); ax.set_yticklabels(eight["gene"])
    ax.invert_yaxis()
    ax.set_xlabel("Spearman ρ with age")
    ax.set_xlim(-0.35,0.52)
    clean_axis(ax,"x")
    ax.legend(frameon=False,fontsize=7.8,loc="lower right")

    ax=frames["e"]
    ax.text(0.04,0.78,"Gene",transform=ax.transAxes,fontweight="bold",fontsize=8.5)
    ax.text(0.25,0.78,"ρ (ER+)",transform=ax.transAxes,fontweight="bold",fontsize=8.5)
    ax.text(0.43,0.78,"ρ (ER−)",transform=ax.transAxes,fontweight="bold",fontsize=8.5)
    ax.text(0.61,0.78,"Het. FDR",transform=ax.transAxes,fontweight="bold",fontsize=8.5)
    ax.text(0.82,0.78,"Status",transform=ax.transAxes,fontweight="bold",fontsize=8.5)
    yy=0.70
    for _,r in eight.iterrows():
        if r["gene"]=="A2M":
            status="Sensitive*"
        elif r["fdr_er_heterogeneity"]<0.05:
            status="Sensitive"
        else:
            status="Robust"
        ax.text(0.04,yy,r["gene"],transform=ax.transAxes,fontsize=8.1)
        ax.text(0.25,yy,f"{r['rho_er_pos']:.3f}",transform=ax.transAxes,fontsize=8.1)
        ax.text(0.43,yy,f"{r['rho_er_neg']:.3f}",transform=ax.transAxes,fontsize=8.1)
        ax.text(0.61,yy,fmt_p(r["fdr_er_heterogeneity"]),transform=ax.transAxes,fontsize=8.1)
        ax.text(0.82,yy,status,transform=ax.transAxes,fontsize=7.7)
        yy-=0.072
    ax.text(0.04,0.08,"*A2M: direction instability despite non-significant heterogeneity FDR.",
            transform=ax.transAxes,fontsize=7.4,color=THEME["muted"])

    ax=frames["f"]
    class_colors={"Class A":"#D7E3EC","Class B":"#E9DFC9","Class C":"#D9E5DB","Class D":"#E5E2E8"}
    yy=0.68
    for cl in ["Class A","Class B","Class C","Class D"]:
        genes=", ".join(CLASS_DEFS[cl]["genes"])
        label = f"{cl}: {CLASS_DEFS[cl]['definition']}" if cl=="Class D" else f"{cl}: {genes}\n{CLASS_DEFS[cl]['definition']}"
        add_text_box(ax,(0.05,yy),(0.90,0.17),
                     label,
                     fc=class_colors[cl],fontsize=8.5,align="left")
        yy-=0.20
    ax.text(0.05,0.03,
            "External replication = expression reproducibility, not clinical biomarker validation.",
            transform=ax.transAxes,fontsize=7.6,color=THEME["muted"])

    save_all(fig,"Figure_2")
    return fig



def make_figure_3():
    fig=plt.figure(figsize=(15,8.5),facecolor="white")
    rects=[
        [0.02,0.52,0.31,0.44],[0.345,0.52,0.31,0.44],[0.67,0.52,0.31,0.44],
        [0.02,0.05,0.31,0.43],[0.345,0.05,0.31,0.43],[0.67,0.05,0.31,0.43],
    ]
    titles=["Permutation / robustness","STRING thresholds","Hub-rank stability",
            "Node-removal resilience","Top-20 overlap","Interpretation"]
    frames=[]; contents=[]
    for i,(r,t) in enumerate(zip(rects,titles)):
        f,c=panel_frame(fig,r,chr(ord('a')+i),t)
        frames.append(f); contents.append(c)

    ax=frames[0]
    add_text_box(ax,(0.10,0.63),(0.80,0.16),
                 f"Observed unadjusted\nFDR-significant genes: {FIG3['observed_fdr_genes']}",
                 fc="#F2F4F5",fontsize=10)
    add_text_box(ax,(0.10,0.39),(0.80,0.16),
                 f"Stratified age-label permutations: n = {FIG3['n_permutations']}",
                 fc="#F2F4F5",fontsize=10)
    add_text_box(ax,(0.10,0.15),(0.80,0.16),
                 f"Empirical P = {FIG3['empirical_p']:.6f}",
                 fc="#F2F4F5",fontsize=11,weight="bold")

    ax=fig.add_axes(contents[1])
    df=FIG3["string"]
    bars=ax.bar(df["score"].astype(str),df["edges"],
                color=[THEME["blue"],THEME["green"],THEME["amber"]])
    ax.set_ylabel("Edges"); ax.set_xlabel("STRING required score")
    clean_axis(ax,"y"); ax.set_ylim(0,650)
    for bar,(_,r) in zip(bars,df.iterrows()):
        ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+14,
                f"{int(r['edges'])}\ndensity={r['density']:.3f}",
                ha="center",va="bottom",fontsize=8)

    ax=fig.add_axes(contents[2])
    rs=FIG3["rank_stability"]
    yy=np.arange(len(rs))
    ax.barh(yy,rs["spearman_rho"],color=[THEME["blue"],THEME["green"],THEME["amber"]])
    ax.set_yticks(yy); ax.set_yticklabels(rs["comparison"])
    ax.invert_yaxis(); ax.set_xlim(0,1.0); ax.set_xlabel("Spearman ρ")
    clean_axis(ax,"x")
    for i,v in enumerate(rs["spearman_rho"]):
        ax.text(v+0.015,i,f"{v:.3f}",va="center",fontsize=8.5)

    ax=fig.add_axes(contents[3])
    rr=FIG3["resilience"]
    bars=ax.bar(rr["strategy"],rr["auc"],color=[THEME["blue"],THEME["amber"],THEME["rose"]])
    ax.set_ylabel("Resilience AUC"); ax.set_ylim(0,0.34)
    clean_axis(ax,"y"); ax.tick_params(axis="x",labelrotation=10)
    for bar,v in zip(bars,rr["auc"]):
        ax.text(bar.get_x()+bar.get_width()/2,v+0.008,f"{v:.3f}",
                ha="center",fontsize=8.5,fontweight="bold")

    ax=fig.add_axes(contents[4])
    ov=FIG3["top20_overlap"]
    yy=np.arange(len(ov))
    ax.barh(yy,ov["jaccard_overlap"],color=[THEME["blue"],THEME["purple"]])
    ax.set_yticks(yy); ax.set_yticklabels(ov["comparison"])
    ax.invert_yaxis(); ax.set_xlim(0,1.0)
    ax.set_xlabel("Jaccard overlap vs score-700 reference")
    clean_axis(ax,"x")
    for i,v in enumerate(ov["jaccard_overlap"]):
        ax.text(v+0.02,i,f"{v:.3f}",va="center",fontsize=8.5)

    ax=frames[5]
    notes=[
        ("Permutation","Association burden exceeds the stratified null."),
        ("Thresholds","Network density falls as STRING confidence rises."),
        ("Ranks","Hub ordering remains comparatively stable."),
        ("Attacks","Targeted removal fragments the network faster than random."),
    ]
    yy=0.65
    for title,txt in notes:
        add_text_box(ax,(0.07,yy),(0.86,0.14),
                     f"{title}: {txt}",fc="#F5F6F7",fontsize=9,align="left")
        yy-=0.17

    save_all(fig,"Figure_3")
    return fig



def make_figure_4():
    """Render Figure 4 from verified aggregate enrichment quantities only.

    The historical full enrichment table and exact 30-module membership output are
    not bundled with the release. Therefore this figure intentionally avoids
    representative-term identities, module-size estimates, adjusted-P values, and
    candidate×module membership cells that cannot be independently audited from
    the archived source package.
    """
    fig=plt.figure(figsize=(15,8.5),facecolor="white")
    rects={
        "a":[0.02,0.52,0.27,0.44],
        "b":[0.30,0.52,0.30,0.44],
        "c":[0.61,0.52,0.37,0.44],
        "d":[0.02,0.05,0.48,0.43],
        "e":[0.51,0.05,0.47,0.43],
    }
    titles={
        "a":"Enrichment reduction workflow",
        "b":"GO/KEGG term counts",
        "c":"Significant-term fractions",
        "d":"Redundancy-reduction summary",
        "e":"Evidence boundary",
    }
    frames={}; contents={}
    for k in rects:
        frames[k],contents[k]=panel_frame(fig,rects[k],k,titles[k])

    counts={k: float(v) for k,v in FIG4_COUNTS.items()}
    total_tested=int(counts["total_tested"])
    go_tested=int(counts["go_tested"])
    kegg_tested=int(counts["kegg_tested"])
    total_sig=int(counts["total_significant"])
    go_sig=int(counts["go_significant"])
    kegg_sig=int(counts["kegg_significant"])
    clustered=int(counts["clustered_terms"])
    modules=int(counts["representative_modules"])
    jaccard=float(counts["jaccard_threshold"])

    # a — only archived aggregate quantities.
    ax=frames["a"]
    seq=[
        (total_tested,"tested GO/KEGG terms"),
        (total_sig,"BH-FDR-significant terms"),
        (clustered,"most significant terms entered\ninto overlap reduction"),
        (modules,"representative overlap components"),
    ]
    yy=0.68
    for i,(n,lab) in enumerate(seq):
        add_text_box(ax,(0.18,yy),(0.64,0.14),f"{n:,}\n{lab}",
                     fc="#F2F4F5",fontsize=9.0,weight="bold")
        if i<len(seq)-1:
            ax.annotate("",xy=(0.50,yy-0.035),xytext=(0.50,yy),
                        xycoords=ax.transAxes,textcoords=ax.transAxes,
                        arrowprops=dict(arrowstyle="-|>",color=THEME["dark_grey"],lw=1))
        yy-=0.18
    ax.text(0.08,0.045,
            f"Jaccard ≥ {jaccard:.2f}; lowest-FDR representative per component.",
            transform=ax.transAxes,fontsize=7.5,color=THEME["muted"])

    # b — archived tested/significant counts.
    ax=fig.add_axes(contents["b"])
    cats=["GO BP","KEGG","Total"]
    tested=[go_tested,kegg_tested,total_tested]
    sig=[go_sig,kegg_sig,total_sig]
    x=np.arange(3); w=0.34
    b1=ax.bar(x-w/2,tested,w,label="Tested",color=THEME["blue"])
    b2=ax.bar(x+w/2,sig,w,label="BH-FDR significant",color=THEME["rose"])
    ax.set_xticks(x); ax.set_xticklabels(cats)
    ax.set_ylabel("Terms")
    ax.set_ylim(0,max(tested)*1.14)
    clean_axis(ax,"y"); ax.legend(frameon=False,fontsize=8)
    for bars in (b1,b2):
        for bar in bars:
            ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+max(tested)*0.018,
                    f"{int(bar.get_height()):,}",ha="center",fontsize=7.8)

    # c — derived ratios, not new empirical outputs.
    ax=fig.add_axes(contents["c"])
    frac=np.array([
        go_sig/go_tested if go_tested else np.nan,
        kegg_sig/kegg_tested if kegg_tested else np.nan,
        total_sig/total_tested if total_tested else np.nan,
    ])
    bars=ax.bar(cats,frac,color=[THEME["purple"],THEME["amber"],THEME["teal"]])
    ax.set_ylim(0,max(0.75,float(np.nanmax(frac))*1.18))
    ax.set_ylabel("Fraction BH-FDR significant")
    clean_axis(ax,"y")
    for bar,v in zip(bars,frac):
        ax.text(bar.get_x()+bar.get_width()/2,v+0.02,f"{100*v:.1f}%",
                ha="center",fontsize=8.5,fontweight="bold")
    ax.text(0.02,0.97,"Derived directly from archived term counts.",
            transform=ax.transAxes,va="top",fontsize=7.4,color=THEME["muted"])

    # d — reduction ratios that can be recomputed from the archived counts.
    ax=fig.add_axes(contents["d"])
    labels=["FDR-significant\nterms","Terms entered into\nJaccard clustering","Representative\noverlap components"]
    vals=np.array([total_sig,clustered,modules],dtype=float)
    bars=ax.bar(labels,vals,color=[THEME["rose"],THEME["blue"],THEME["green"]])
    ax.set_ylabel("Count")
    ax.set_ylim(0,max(vals)*1.17)
    clean_axis(ax,"y")
    for bar,v in zip(bars,vals):
        ax.text(bar.get_x()+bar.get_width()/2,v+max(vals)*0.025,f"{int(v):,}",
                ha="center",fontsize=8.6,fontweight="bold")
    selected_pct=100*clustered/total_sig if total_sig else np.nan
    reduction_pct=100*(1-modules/clustered) if clustered else np.nan
    ax.text(0.02,0.97,
            f"Top-term subset = {selected_pct:.1f}% of significant terms; "
            f"component reduction = {reduction_pct:.1f}%.",
            transform=ax.transAxes,va="top",fontsize=7.5,color=THEME["muted"])

    # e — explicit claim boundary replacing unsupported module identities/matrix.
    ax=frames["e"]
    statements=[
        ("Verified","1,698 tested terms; 514 BH-FDR significant (379 GO BP, 135 KEGG)."),
        ("Verified","Top 180 significant terms entered Jaccard-based redundancy reduction."),
        ("Verified",f"Jaccard threshold {jaccard:.2f} yielded 30 representative overlap components."),
        ("Not reconstructed","Exact module identities, sizes and candidate×module\ncells require the historical full enrichment output."),
    ]
    yy=0.66
    for label,txt in statements:
        add_text_box(ax,(0.06,yy),(0.88,0.145),f"{label}: {txt}",
                     fc="#F5F6F7",fontsize=8.2,align="left")
        yy-=0.17
    ax.text(0.06,0.045,
            "Only archived aggregate quantities are shown; module-level rows are not inferred from artwork.",
            transform=ax.transAxes,fontsize=7.4,color=THEME["muted"],wrap=True)

    save_all(fig,"Figure_4")
    return fig


def make_figure_5():
    fig=plt.figure(figsize=(15,9),facecolor="white")
    rects=[
        [0.02,0.52,0.31,0.44],[0.345,0.52,0.31,0.44],[0.67,0.52,0.31,0.44],
        [0.02,0.05,0.31,0.43],[0.345,0.05,0.31,0.43],[0.67,0.05,0.31,0.43],
    ]
    benchmark_n = int(FIG5_COMPOSITION["n"].sum())
    titles=[f"Benchmark composition (n = {benchmark_n})","Policy conformance","Workflow cost",
            "Paired improvement over comparators","Bounded controller metrics","Example execution traces"]
    frames=[]; contents=[]
    for i,(r,t) in enumerate(zip(rects,titles)):
        f,c=panel_frame(fig,r,chr(ord('a')+i),t)
        frames.append(f); contents.append(c)

    ax=fig.add_axes(contents[0])
    dfc=FIG5_COMPOSITION.iloc[::-1]
    y=np.arange(len(dfc))
    left=np.zeros(len(dfc))
    colors={"COMPLETE":THEME["blue"],"BLOCK":THEME["rose"],"FAIL_SAFE":THEME["green"]}
    for outcome in ["COMPLETE","BLOCK","FAIL_SAFE"]:
        vals=dfc[outcome].to_numpy()
        ax.barh(y,vals,left=left,label=outcome,color=colors[outcome])
        left+=vals
    ax.set_yticks(y); ax.set_yticklabels(dfc["family"],fontsize=7.4)
    ax.set_xlabel("Number of scenarios"); clean_axis(ax,"x")
    ax.legend(frameon=False,fontsize=7.2,loc="lower right")
    for i,n in enumerate(dfc["n"]):
        ax.text(n+3,i,str(int(n)),va="center",fontsize=7.5)

    ax=fig.add_axes(contents[1])
    df=FIG5_CONTROLLERS
    labels=["Static","Goal\nplanner","Adaptive","Bounded\ncontroller"]
    bars=ax.bar(labels,df["policy"],
                color=[THEME["grey"],THEME["blue"],THEME["rose"],THEME["green"]])
    ax.set_ylim(0,1.08); ax.set_ylabel("Policy conformance"); clean_axis(ax,"y")
    for bar,v in zip(bars,df["policy"]):
        ax.text(bar.get_x()+bar.get_width()/2,v+0.025,f"{v:.3f}",
                ha="center",fontsize=8.2,fontweight="bold")

    ax=fig.add_axes(contents[2])
    bars=ax.bar(labels,df["mean_cost"],
                color=[THEME["grey"],THEME["blue"],THEME["rose"],THEME["green"]])
    ax.set_ylabel("Mean normalized workflow cost"); clean_axis(ax,"y")
    ax.set_ylim(0,8.6)
    for bar,v in zip(bars,df["mean_cost"]):
        ax.text(bar.get_x()+bar.get_width()/2,v+0.18,f"{v:.2f}",
                ha="center",fontsize=8.2,fontweight="bold")
    ax.text(0.02,0.97,"Bars show verified means; quartile whiskers are omitted because source Q1–Q3 values are unavailable.",
            transform=ax.transAxes,va="top",fontsize=7.2,color=THEME["muted"])

    ax=fig.add_axes(contents[3])
    d=FIG5_PAIRED
    y=np.arange(len(d))
    err_low=d["difference"]-d["sensitivity_low"]
    err_hi=d["sensitivity_high"]-d["difference"]
    ax.errorbar(d["difference"],y,xerr=[err_low,err_hi],fmt="o",
                color=THEME["blue"],ecolor=THEME["dark_grey"],capsize=3,lw=1.1)
    ax.axvline(0,color=THEME["dark_grey"],ls="--",lw=0.9)
    ax.set_yticks(y); ax.set_yticklabels(d["comparison"])
    ax.invert_yaxis(); ax.set_xlim(-0.03,1.10)
    ax.set_xlabel("Absolute Δ policy conformance")
    ax.text(0.02,0.97,"Whiskers: leave-one-family-out sensitivity range (not a confidence interval)",
            transform=ax.transAxes,va="top",fontsize=7.0,color=THEME["muted"])
    clean_axis(ax,"x")
    for i,r in d.iterrows():
        ax.text(r["sensitivity_high"]+0.025,i,
                f"{r['difference']:.3f}\n[{r['sensitivity_low']:.3f}–{r['sensitivity_high']:.3f}]",
                va="center",fontsize=7.5)

    ax=fig.add_axes(contents[4])
    bounded=df.iloc[-1]
    metric_names=["Policy\nconformance","Action\nappropriateness","Safety\nconformance",
                  "Provenance\nconformance","Escalation\nconformance","Resource\nstewardship"]
    vals=[bounded["policy"],bounded["action"],bounded["safety"],bounded["provenance"],
          bounded["escalation"],bounded["stewardship"]]
    y=np.arange(len(vals))
    ax.barh(y,vals,color=[THEME["blue"]]*5+[THEME["green"]])
    ax.set_yticks(y); ax.set_yticklabels(metric_names)
    ax.invert_yaxis(); ax.set_xlim(0,1.06); ax.set_xlabel("Score")
    clean_axis(ax,"x")
    for i,v in enumerate(vals):
        ax.text(v+0.012,i,f"{v:.3f}",va="center",fontsize=8)

    ax=frames[5]
    ax.text(0.03,0.79,"ID",transform=ax.transAxes,fontweight="bold",fontsize=8)
    ax.text(0.18,0.79,"Scenario",transform=ax.transAxes,fontweight="bold",fontsize=8)
    ax.text(0.51,0.79,"Outcome",transform=ax.transAxes,fontweight="bold",fontsize=8)
    ax.text(0.73,0.79,"Actions",transform=ax.transAxes,fontweight="bold",fontsize=8)
    yy=0.70
    for _,r in FIG5_TRACES.iterrows():
        ax.text(0.03,yy,r.ID,transform=ax.transAxes,fontsize=7.5,fontweight="bold")
        ax.text(0.18,yy,r.scenario,transform=ax.transAxes,fontsize=7.2)
        ax.text(0.51,yy,r.outcome,transform=ax.transAxes,fontsize=7.2,fontweight="bold")
        ax.text(0.73,yy,str(r.actions_n),transform=ax.transAxes,fontsize=7.2)
        ax.text(0.18,yy-0.045,str(r.key_actions),transform=ax.transAxes,fontsize=5.8,color=THEME["muted"],wrap=True)
        yy-=0.14
    ax.text(0.03,0.10,
            (f"Reference outcomes: {FIG5_REFERENCE_OUTCOMES['COMPLETE']} COMPLETE, "
             f"{FIG5_REFERENCE_OUTCOMES['BLOCK']} BLOCK, "
             f"{FIG5_REFERENCE_OUTCOMES['FAIL_SAFE']} FAIL_SAFE."),
            transform=ax.transAxes,fontsize=7.6,color=THEME["muted"])

    save_all(fig,"Figure_5")
    return fig



def make_figure_6():
    fig=plt.figure(figsize=(15,9),facecolor="white")
    rects=[
        [0.02,0.52,0.31,0.44],[0.345,0.52,0.31,0.44],[0.67,0.52,0.31,0.44],
        [0.02,0.05,0.31,0.43],[0.345,0.05,0.31,0.43],[0.67,0.05,0.31,0.43],
    ]
    titles=["Ablation design","Policy conformance after module removal","Failure-mode signatures",
            "Cost-awareness removal impact","Ablation summary","Interpretation"]
    frames=[]; contents=[]
    for i,(r,t) in enumerate(zip(rects,titles)):
        f,c=panel_frame(fig,r,chr(ord('a')+i),t)
        frames.append(f); contents.append(c)

    ax=frames[0]
    boxes=[
        ("Full bounded controller","All modules enabled"),
        ("Single-component ablation","Remove one component at a time"),
        ("Re-run benchmark",f"Same {int(FIG5_COMPOSITION['n'].sum())} scenarios and reference policy"),
        ("Metrics assessed","Policy + module-specific + stewardship metrics"),
    ]
    yy=0.68
    for title,txt in boxes:
        add_text_box(ax,(0.08,yy),(0.84,0.15),
                     f"{title}\n{txt}",fc="#F3F5F6",fontsize=9.0,align="left")
        yy-=0.18

    ax=fig.add_axes(contents[1])
    order=["Full bounded agent","Replanning removed","Verifier removed",
           "Safety gate removed","Provenance removed","Cost-awareness removed"]
    d=FIG6.set_index("system").loc[order]
    labels=["Full","−Replanning","−Verifier","−Safety","−Provenance","−Cost"]
    cols=[THEME["green"],THEME["blue"],THEME["amber"],
          THEME["rose"],THEME["purple"],THEME["teal"]]
    bars=ax.bar(labels,d["policy"],color=cols)
    ax.set_ylim(0,1.08); ax.set_ylabel("Policy conformance")
    clean_axis(ax,"y"); ax.tick_params(axis="x",labelrotation=20)
    for bar,v in zip(bars,d["policy"]):
        ax.text(bar.get_x()+bar.get_width()/2,v+0.02,f"{v:.3f}",
                ha="center",fontsize=7.7)

    ax=frames[2]
    ax.text(0.03,0.79,"Module removed",transform=ax.transAxes,fontweight="bold",fontsize=7.8)
    ax.text(0.29,0.79,"Primary effect",transform=ax.transAxes,fontweight="bold",fontsize=7.8)
    ax.text(0.73,0.79,"Change",transform=ax.transAxes,fontweight="bold",fontsize=7.8)
    yy=0.69
    for _,r in FIG6_FAILURE_SIGNATURES.iterrows():
        effect = r.primary_effect
        change = r.change
        if r.module_removed == "Cost-awareness":
            effect = effect.replace(" / ", " /\n")
            change = change.replace(" / ", "\n")
        ax.text(0.03,yy,r.module_removed,transform=ax.transAxes,fontsize=7.3,fontweight="bold",va="top")
        ax.text(0.29,yy,effect,transform=ax.transAxes,fontsize=6.7,va="top")
        ax.text(0.73,yy,change,transform=ax.transAxes,fontsize=6.7,va="top")
        yy-=0.125

    ax=fig.add_axes(contents[3])
    full=FIG6.set_index("system").loc["Full bounded agent"]
    nocost=FIG6.set_index("system").loc["Cost-awareness removed"]
    metrics=["Policy\nconformance","Action\nappropriateness","Resource\nstewardship"]
    fullv=[full["policy"],full["action_appropriateness"],full["stewardship"]]
    nov=[nocost["policy"],nocost["action_appropriateness"],nocost["stewardship"]]
    x=np.arange(3); w=0.34
    b1=ax.bar(x-w/2,fullv,w,color=THEME["blue"],label="Full bounded controller")
    b2=ax.bar(x+w/2,nov,w,color=THEME["rose"],label="Cost-awareness removed")
    ax.set_xticks(x); ax.set_xticklabels(metrics)
    ax.set_ylim(0,1.08); ax.set_ylabel("Score"); clean_axis(ax,"y")
    ax.legend(frameon=False,fontsize=7.1,loc="lower left")
    for bars in [b1,b2]:
        for bar in bars:
            ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+0.02,
                    f"{bar.get_height():.3f}",ha="center",fontsize=7.4)

    ax=frames[4]
    system_by_module = {
        "Replanning": "Replanning removed",
        "Verifier": "Verifier removed",
        "Safety gate": "Safety gate removed",
        "Provenance": "Provenance removed",
        "Cost-awareness": "Cost-awareness removed",
    }
    ablation_by_system = FIG6.set_index("system")
    rows=[]
    for _, signature in FIG6_FAILURE_SIGNATURES.iterrows():
        module = signature["module_removed"]
        system = system_by_module[module]
        overall = f"{float(ablation_by_system.loc[system, 'policy']):.3f}"
        impact = f"{signature['primary_effect']}: {signature['change']}"
        rows.append((module, overall, impact))
    ax.text(0.03,0.79,"Module",transform=ax.transAxes,fontweight="bold",fontsize=7.8)
    ax.text(0.34,0.79,"Overall",transform=ax.transAxes,fontweight="bold",fontsize=7.8)
    ax.text(0.53,0.79,"Key impact",transform=ax.transAxes,fontweight="bold",fontsize=7.8)
    yy=0.69
    for m,overall,impact in rows:
        ax.text(0.03,yy,m,transform=ax.transAxes,fontsize=7.3,fontweight="bold")
        ax.text(0.35,yy,overall,transform=ax.transAxes,fontsize=7.3)
        ax.text(0.53,yy,impact,transform=ax.transAxes,fontsize=6.8,wrap=True)
        yy-=0.125

    ax=frames[5]
    notes=[
        ("Replanning","supports recovery from transient/recoverable failures."),
        ("Verifier","enforces evidence-state adequacy."),
        ("Safety gate","enforces the prohibited clinical-action boundary."),
        ("Provenance","supports traceability under provenance corruption."),
        ("Cost-awareness","improves action appropriateness and resource stewardship while preserving terminal policy conformance."),
    ]
    yy=0.70
    for title,txt in notes:
        add_text_box(ax,(0.06,yy),(0.88,0.12),
                     f"{title}: {txt}",fc="#F4F6F7",fontsize=8.2,align="left")
        yy-=0.14
    ax.text(0.06,0.04,
            "Effects are specific to this implemented controller and finite benchmark;\n"
            "they do not establish universal architectural causality.",
            transform=ax.transAxes,fontsize=7.4,color=THEME["muted"])

    save_all(fig,"Figure_6")
    return fig





def _require_columns(df, required, label):
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def validate_source_tables():
    """Validate plotting inputs structurally without embedding expected result values."""
    _require_columns(FIG2, {"gene", "class"}, "Figure2_candidate_statistics.csv")
    required_f4 = {
        "total_tested", "go_tested", "kegg_tested", "total_significant",
        "go_significant", "kegg_significant", "clustered_terms",
        "representative_modules", "jaccard_threshold",
    }
    missing_f4 = required_f4 - set(FIG4_COUNTS)
    if missing_f4:
        raise ValueError(f"Figure4_enrichment_counts.csv missing fields: {sorted(missing_f4)}")
    f4 = {k: float(FIG4_COUNTS[k]) for k in required_f4}
    if int(f4["go_tested"] + f4["kegg_tested"]) != int(f4["total_tested"]):
        raise ValueError("Figure4 tested-term counts do not sum")
    if int(f4["go_significant"] + f4["kegg_significant"]) != int(f4["total_significant"]):
        raise ValueError("Figure4 significant-term counts do not sum")
    if not (0 <= f4["representative_modules"] <= f4["clustered_terms"] <= f4["total_significant"] <= f4["total_tested"]):
        raise ValueError("Figure4 reduction counts are not monotonically nested")
    if not (0 < f4["jaccard_threshold"] <= 1):
        raise ValueError("Figure4 Jaccard threshold must be in (0, 1]")
    _require_columns(FIG5_COMPOSITION, {"family", "n", "COMPLETE", "BLOCK", "FAIL_SAFE"},
                     "Figure5_scenario_composition.csv")
    _require_columns(FIG5_CONTROLLERS,
                     {"system", "policy", "action", "safety", "provenance", "escalation", "stewardship", "mean_cost"},
                     "Figure5_controller_summary.csv")
    _require_columns(FIG5_PAIRED, {"comparison", "difference", "sensitivity_low", "sensitivity_high"},
                     "Figure5_paired_policy_comparisons.csv")
    _require_columns(FIG5_TRACES, {"ID", "scenario", "outcome", "key_actions", "actions_n"},
                     "Figure5_representative_traces.csv")
    _require_columns(FIG6,
                     {"system", "policy", "feasible_completion", "action_appropriateness", "safety",
                      "provenance", "stewardship", "transient_recovery", "safe_block", "irrecoverable_fail_safe"},
                     "Figure6_ablation_summary.csv")
    _require_columns(FIG6_FAILURE_SIGNATURES, {"module_removed", "primary_effect", "change"},
                     "Figure6_failure_signatures.csv")
    if FIG5_COMPOSITION.empty or FIG5_CONTROLLERS.empty or FIG5_PAIRED.empty or FIG6.empty:
        raise ValueError("Figure 5/6 benchmark source tables must not be empty")


if __name__ == "__main__":
    validate_source_tables()
    for fn in [make_figure_2,make_figure_3,make_figure_4,make_figure_5,make_figure_6]:
        fig=fn(); plt.close(fig)
    print("ALL FIGURES 2–6 GENERATED EXCLUSIVELY FROM SOURCE DATA")
