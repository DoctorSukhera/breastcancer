from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from PIL import Image, ImageOps, ImageDraw

ROOT=Path(__file__).resolve().parents[2] / 'results' / 'generated'
OUT=Path(__file__).resolve().parents[2] / 'figures' / 'corrected_figure5';OUT.mkdir(parents=True, exist_ok=True)
base=pd.read_csv(ROOT/'benchmark_controller_summary.csv')
det=pd.read_csv(ROOT/'deterministic_error_handling_summary.csv')
df=pd.concat([base,det],ignore_index=True)
order=['Static workflow','Goal planner','Adaptive planner','Deterministic error-handling workflow','Bounded controller']
df=df.set_index('system').loc[order].reset_index()
short=['Static workflow','Goal planner','Adaptive planner','Error-handling workflow','Bounded controller']
metrics=['policy_conformance','action_appropriateness','safety_conformance','provenance_conformance','escalation_conformance','resource_stewardship']
labels=['Policy\nconformance','Action\nappropriateness','Safety','Provenance','Escalation','Resource\nstewardship']
assert len(df)==5 and np.allclose(df.loc[4,metrics],1)
assert df.loc[3,'policy_conformance']==1 and abs(df.loc[3,'action_appropriateness']-640/760)<1e-10
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10.5,'svg.fonttype':'none','pdf.fonttype':42,'savefig.facecolor':'white','figure.facecolor':'white'})
cmap=LinearSegmentedColormap.from_list('bluegreen',['#f2f3f5','#c9e5e5','#60aaa8','#1e767c'])
def export(fig,s):
 for ext in ('png','pdf','svg'):
  fig.savefig(OUT/(s+'.'+ext),bbox_inches='tight',pad_inches=.23,dpi=350 if ext=='png' else None)
 plt.close(fig)
# A summary heatmap
fig,ax=plt.subplots(figsize=(12.8,5.4));fig.subplots_adjust(left=.235,right=.96,top=.78,bottom=.15)
arr=df[metrics].to_numpy(dtype=float)
ax.imshow(arr,cmap=cmap,vmin=0,vmax=1,aspect='auto')
for i in range(5):
 for j in range(6):
  v=arr[i,j]
  ax.text(j,i,f'{v:.3f}',ha='center',va='center',fontsize=11.5,fontweight='bold' if i>=3 else 'normal',color='white' if v>.89 else '#23384a')
ax.set_yticks(range(5),short,fontsize=11.4)
ax.set_xticks(range(6),labels,fontsize=10.7);ax.xaxis.tick_top();ax.tick_params(length=0,pad=10)
for i in range(6):ax.axvline(i-.5,color='white',lw=3)
for i in range(5):ax.axhline(i-.5,color='white',lw=3)
for sp in ax.spines.values():sp.set_visible(False)
fig.text(.025,.94,'A',weight='bold',fontsize=23)
fig.text(.08,.94,'Five-controller governance benchmark',weight='bold',fontsize=17,color='#193449')
fig.text(.08,.87,'760 matched constructed scenarios per controller · values are observed proportions',fontsize=10.8,color='#627385')
export(fig,'Figure5_A_Five_Controller_Metrics')
# B paired differences from source
paired=pd.read_csv(ROOT/'primary_paired_policy_comparisons.csv')
pair_det=pd.read_csv(ROOT/'bounded_vs_deterministic_paired_comparison.csv')
comparators=['Static workflow','Goal planner','Adaptive planner','Error-handling workflow']
deltas=[float(df.loc[4,'policy_conformance']-df.loc[i,'policy_conformance'])*100 for i in range(4)]
actions=[float(df.loc[4,'action_appropriateness']-df.loc[i,'action_appropriateness'])*100 for i in range(4)]
assert np.allclose(deltas[:3],paired['difference']*100,atol=.00001)
assert abs(actions[3]-pair_det.loc[pair_det.metric=='Action appropriateness','difference'].iloc[0]*100)<1e-6
fig,axs=plt.subplots(1,2,figsize=(13,5),sharey=True,gridspec_kw={'width_ratios':[1.05,1]})
fig.subplots_adjust(left=.20,right=.95,top=.73,bottom=.19,wspace=.13)
for ax,values,color,title in zip(axs,[deltas,actions],['#318d95','#d38d4c'],['Policy conformance','Action appropriateness']):
 for i,v in enumerate(values):
  ax.plot([0,v],[i,i],lw=3,color=color,alpha=.55)
  ax.scatter(v,i,s=125,c=color,edgecolor='white',lw=1.3,zorder=4)
  ax.annotate(f'+{v:.1f} pp',(v,i),xytext=(7,0),textcoords='offset points',va='center',fontsize=10.5)
 ax.set_xlim(0,84 if title=='Policy conformance' else 86);ax.set_xticks([0,20,40,60,80]);ax.set_ylim(3.55,-.55)
 ax.axvline(0,ls='--',color='#607080',lw=1);ax.grid(axis='x',lw=.75,color='#e2e7ed');ax.set_axisbelow(True)
 ax.set_title(title,loc='left',fontweight='bold',fontsize=13,pad=16)
 ax.set_xlabel('Bounded − comparator (percentage points)',fontsize=9.5)
 for s in ['top','right','left']:ax.spines[s].set_visible(False)
 ax.spines['bottom'].set_color('#bbc6ce')
 ax.tick_params(axis='y',length=0)
axs[0].set_yticks(range(4),comparators,fontsize=10.5)
axs[1].tick_params(labelleft=False)
fig.text(.025,.94,'B',weight='bold',fontsize=23)
fig.text(.08,.94,'Paired benchmark advantage across four comparators',weight='bold',fontsize=16.5,color='#193449')
fig.text(.08,.86,'Same 760 scenarios · no policy advantage over the strong error-handling comparator',fontsize=10.6,color='#627385')
export(fig,'Figure5_B_Paired_Performance_Gains')
# C family heatmap
traj=pd.read_csv(ROOT/'benchmark_trajectory_level.csv')
dtraj=pd.read_csv(ROOT/'deterministic_error_handling_trajectory_level.csv')
alltraj=pd.concat([traj,dtraj],ignore_index=True)
families=['clean','known_source_outage','transient_failure','evidence_quality','irrecoverable_source_loss','provenance_attack','prohibited_clinical_request','resource_stress','unseen_composition']
fam_name=['Clean tasks','Known source outage','Transient failure','Evidence quality','Irrecoverable source loss','Provenance attack','Prohibited clinical request','Resource stress','Unseen composition']
counts=alltraj[alltraj.system=='Bounded controller'].groupby('family').size().reindex(families)
assert counts.sum()==760
fdata=alltraj.groupby(['family','system']).policy_conformance.mean().unstack().loc[families,order]
assert np.all(fdata.iloc[:,-2:].to_numpy()==1)
fig,ax=plt.subplots(figsize=(13.4,6.6));fig.subplots_adjust(left=.255,right=.96,top=.79,bottom=.13)
arr=fdata.to_numpy(float)
ax.imshow(arr,cmap=cmap,vmin=0,vmax=1,aspect='auto')
for i in range(9):
 for j in range(5):
  ax.text(j,i,f'{arr[i,j]*100:.0f}%',ha='center',va='center',fontsize=10.7,fontweight='bold' if j>=3 else 'normal',color='white' if arr[i,j]>=.88 else '#284052')
ax.set_yticks(range(9),[f'{n} (n={int(c)})' for n,c in zip(fam_name,counts)],fontsize=10.3)
ax.set_xticks(range(5),['Static','Goal','Adaptive','Error-handling','Bounded'],fontsize=10.5)
ax.xaxis.tick_top();ax.tick_params(length=0,pad=9)
for j in range(6):ax.axvline(j-.5,lw=3,color='white')
for i in range(10):ax.axhline(i-.5,lw=3,color='white')
for sp in ax.spines.values():sp.set_visible(False)
fig.text(.025,.95,'C',weight='bold',fontsize=23)
fig.text(.08,.95,'Policy conformance across nine scenario families',weight='bold',fontsize=17,color='#193449')
fig.text(.08,.885,'Family-specific proportions · 760 scenarios per controller · descriptive internal benchmark',fontsize=10.4,color='#627385')
export(fig,'Figure5_C_Family_Robustness')
# create source derived CSVs
z=df[['system']+metrics].copy();z.to_csv(OUT/'Figure5_A_Source.csv',index=False)
pd.DataFrame({'comparator':comparators,'policy_advantage_pp':deltas,'action_appropriateness_advantage_pp':actions}).to_csv(OUT/'Figure5_B_Source.csv',index=False)
fdata.reset_index().to_csv(OUT/'Figure5_C_Source.csv',index=False)
# figure5 assemblage using image tiles maintaining aspect, not distort
parts=[OUT/'Figure5_A_Five_Controller_Metrics.png',OUT/'Figure5_B_Paired_Performance_Gains.png',OUT/'Figure5_C_Family_Robustness.png']
canvas=Image.new('RGB',(2800,2000),'white')
boxes=[(65,80,1300,760),(1435,80,1300,760),(310,905,2180,990)]
for f,(x,y,w,h) in zip(parts,boxes):
 im=Image.open(f).convert('RGB');im.thumbnail((w,h),Image.Resampling.LANCZOS)
 canvas.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2))
canvas.save(OUT/'Figure5_Corrected_Combined_Preview.png')
prs=Presentation();prs.slide_width=Inches(16);prs.slide_height=Inches(11.3)
blank=prs.slide_layouts[6]
def text(sl,x,y,w,h,st,sz=19):
 sh=sl.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));p=sh.text_frame.paragraphs[0];p.text=st;p.font.size=Pt(sz);p.font.color.rgb=RGBColor(23,45,61)
sl=prs.slides.add_slide(blank)
text(sl,.45,.16,15,.5,'Figure 5 | Five-controller benchmark comparison',23)
for (f,(x,y,w,h)) in zip(parts,[(.5,.75,7.35,4.25),(8.1,.75,7.35,4.25),(1.5,5.1,13,5.8)]):
 
 from PIL import Image as _Im
 iw,ih=_Im.open(f).size
 sc=min(w/iw,h/ih);ww=iw*sc;hh=ih*sc
 sl.shapes.add_picture(str(f), Inches(x+(w-ww)/2),Inches(y+(h-hh)/2),width=Inches(ww),height=Inches(hh))
for i,f in enumerate(parts):
 sl=prs.slides.add_slide(blank);text(sl,.5,.2,15,.6,f'Figure 5 panel {chr(65+i)}',22)
 
 iw,ih=Image.open(f).size;sc=min(13.8/iw,8.9/ih);ww=iw*sc;hh=ih*sc
 sl.shapes.add_picture(str(f),Inches(1.1+(13.8-ww)/2),Inches(1.2+(8.9-hh)/2),width=Inches(ww),height=Inches(hh))
prs.save(OUT/'Figure5_Corrected_Assembly.pptx')
# Make clear caption text
(OUT/'Figure5_Corrected_Caption.txt').write_text('''Figure 5. Internal benchmark comparison of bounded workflow control with static, goal-based, adaptive, and deterministic error-handling strategies. (A) Governance scores across six predefined metrics in 760 matched constructed scenarios per controller. (B) Paired differences in policy conformance and action appropriateness between the bounded controller and each comparator. The deterministic error-handling workflow matched the bounded controller on policy conformance (both 1.000) but achieved lower action appropriateness (0.842 versus 1.000). (C) Policy-conformance rates stratified by nine predefined scenario families. Results are descriptive for the constructed internal benchmark; the scores are not evidence of external clinical effectiveness or generalization to independently designed workflows.\n\nSource: results/generated/benchmark_controller_summary.csv, deterministic_error_handling_summary.csv, benchmark_trajectory_level.csv, deterministic_error_handling_trajectory_level.csv and paired-comparison summaries. The source code script regenerate_step5_figures.py directly generates all three numerical panels and combined image.\n''')
(OUT/'Figure6_Corrected_Caption.txt').write_text('''Figure 6. Architectural ablation and its consequences for governance and execution in a constructed 760-scenario benchmark. (A) Policy conformance and action appropriateness for the intact bounded controller and five single-component ablations. (B) Percentage-point performance changes following each ablation across transient recovery, evidence-quality conformance, safe blocking, provenance-attack conformance, overall action appropriateness, and resource stewardship. (C) Number of scenarios with execution cost below or above the scenario-specific reference under each ablation. (D) Difference in mean number of executed actions per scenario relative to the intact controller. Panels C and D are distinct subplots of execution behavior and should both be included in the main-figure caption if the submitted four-panel composite is retained. All findings are specific to the prespecified, internally constructed benchmark and do not demonstrate external clinical effectiveness.\n\nSource: results/generated/ablation_summary_metrics.csv and ablation_trajectory_level.csv.\n''')
print('Validated 5-controller numbers:')
print(df[['system','policy_conformance','action_appropriateness']].to_string(index=False))
print('Outputs:',len(list(OUT.iterdir())))
