from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

O=Path(__file__).resolve().parents[2] / 'figures' / 'corrected_figure2'
S=O/'source/Figure2_candidate_statistics.csv'
df=pd.read_csv(S)
order=['IL7R','SQSTM1','EGR1','IGF1','ESR1','A2M','FOXO1','EIF5A2','EGFR','MYC','MAPK8','IRS2']
df=df.set_index('gene').loc[order].reset_index()
assert len(df)==12 and df.gene.is_unique
assert (df.ci_low<=df.beta_age_z).all() and (df.beta_age_z<=df.ci_high).all()
assert (df.fdr_adjusted<.05).all()
assert df.loc[df.gene.eq('IL7R'),'beta_age_z'].iloc[0]<0
assert df.loc[df.gene.eq('ESR1'),'beta_age_z'].iloc[0]>0
assert (df[df['class'].eq('Class A')]['fdr_geo_directional']<.05).all()
assert (df[df['class'].eq('Class B')]['fdr_geo_directional']<.05).all()
assert (df[df['class'].eq('Class C')]['fdr_geo_directional']>=.05).all()
C={'Class A':'#168A8B','Class B':'#D09746','Class C':'#816BAD'}
ink='#1F3345';muted='#52667A';grid='#E5EAEE'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':ink,'text.color':ink,'xtick.color':ink,'ytick.color':ink,'figure.facecolor':'white'})
N=len(df);y=np.arange(N)

def base(title,sub,xlim,xlab,figsize=(10.8,7.1)):
 fig,ax=plt.subplots(figsize=figsize)
 fig.subplots_adjust(left=.16,right=.86,top=.80,bottom=.20)
 ax.set_yticks(y,df.gene,fontstyle='italic',fontsize=11);ax.invert_yaxis()
 ax.set_xlim(*xlim);ax.set_xlabel(xlab,fontsize=11,labelpad=10)
 ax.grid(axis='x',color=grid,lw=.8);ax.set_axisbelow(True)
 for z in (3.5,7.5):ax.axhline(z,color='#CBD3DB',lw=1.3)
 ax.tick_params(axis='y',length=0,pad=9)
 fig.text(.075,.945,title,fontsize=17.5,fontweight='bold',color=ink)
 fig.text(.075,.892,sub,fontsize=10,color=muted)
 return fig,ax

def save(fig,name):
 for ext in ['png','svg','pdf']:
  fig.savefig(O/(name+'.'+ext),dpi=380 if ext=='png' else None,bbox_inches='tight',pad_inches=.22)
 plt.close(fig)

# Panel A
fig,ax=base('A  |  Covariate-adjusted age associations','TCGA-BRCA · HC3-robust model · 12 prespecified display genes',(-.35,.56),'Adjusted age coefficient β per SD (95% CI)')
for i,r in df.iterrows():
 c=C[r['class']]
 ax.plot([r.ci_low,r.ci_high],[i,i],color=c,lw=2.6,solid_capstyle='round')
 ax.plot([r.ci_low,r.ci_low],[i-.11,i+.11],color=c,lw=1.5)
 ax.plot([r.ci_high,r.ci_high],[i-.11,i+.11],color=c,lw=1.5)
 ax.scatter(r.beta_age_z,i,s=105,c=c,marker='o' if r['class']=='Class A' else 'D' if r['class']=='Class B' else 's',edgecolors='white',linewidths=1,zorder=4)
ax.axvline(0,c='#607281',ls='--',lw=1.2)
for i,r in df.iterrows():ax.text(1.025,i,f'{r.fdr_adjusted:.2g}',transform=ax.get_yaxis_transform(),va='center',fontsize=9,color=ink)
ax.text(1.025,-.72,'BH-FDR q',transform=ax.get_yaxis_transform(),fontsize=9,fontweight='bold',color=ink)
handles=[Line2D([0],[0],marker=m,markersize=9,markerfacecolor=C[k],markeredgecolor='white',color='none',label=k) for k,m in [('Class A','o'),('Class B','D'),('Class C','s')]]
ax.legend(handles=handles,loc='upper left',bbox_to_anchor=(0,-.22),frameon=False,ncol=3,fontsize=9)
save(fig,'Figure2_A_Corrected')

# Panel B: signed external correlation
fig,ax=base('B  |  Independent directional replication','GSE42568 · Spearman correlation with age · sign preserved from source table',(-.50,.40),'External Spearman correlation ρ with age')
for i,r in df.iterrows():
 sig=r.fdr_geo_directional<.05
 c=C[r['class']] if sig else '#A8B2BC'
 ax.plot([0,r.rho_geo],[i,i],c=c,lw=3,alpha=.7)
 ax.scatter(r.rho_geo,i,s=108,c=c,marker='D' if sig else 'o',edgecolors='white',linewidths=.9,zorder=4)
 ax.text(1.025,i,f'{r.fdr_geo_directional:.2g}',transform=ax.get_yaxis_transform(),va='center',fontsize=9,color=ink)
ax.axvline(0,c='#607281',ls='--',lw=1.2)
ax.text(1.025,-.72,'Directional q',transform=ax.get_yaxis_transform(),fontsize=9,fontweight='bold',color=ink)
# marker meaning is explained in caption
save(fig,'Figure2_B_Corrected')

# Panel C: ER stratified
fig,ax=base('C  |  Estrogen-receptor-stratified age associations','TCGA-BRCA · ER+ n = 795  · ER− n = 235',(-.38,.52),'Within-stratum Spearman ρ with age')
for i,r in df.iterrows():
 ax.plot([r.rho_er_pos,r.rho_er_neg],[i,i],color='#BDC8D1',lw=2.5,zorder=2)
 ax.scatter(r.rho_er_pos,i,s=100,c='#148F97',marker='o',edgecolors='white',linewidths=.9,zorder=3)
 ax.scatter(r.rho_er_neg,i,s=100,c='#D17771',marker='s',edgecolors='white',linewidths=.9,zorder=3)
 ax.text(1.02,i,'*' if r.fdr_er_heterogeneity<.05 else '—',transform=ax.get_yaxis_transform(),va='center',fontsize=15 if r.fdr_er_heterogeneity<.05 else 10,color='#B54D41' if r.fdr_er_heterogeneity<.05 else '#95A3AE')
ax.axvline(0,c='#607281',ls='--',lw=1.2)
ax.text(1.02,-.72,'Heterogeneity',transform=ax.get_yaxis_transform(),fontsize=9,fontweight='bold',color=ink)
leg=[Line2D([0],[0],marker='o',color='none',markerfacecolor='#148F97',markersize=9,markeredgecolor='white',label='ER+'),Line2D([0],[0],marker='s',color='none',markerfacecolor='#D17771',markersize=9,markeredgecolor='white',label='ER−')]
ax.legend(handles=leg,loc='upper left',bbox_to_anchor=(0,-.22),frameon=False,ncol=2,fontsize=9)
# significance and stratification interpretation explained in caption
save(fig,'Figure2_C_Corrected')

# Panel D: quantitative matrix with actual q threshold; false separation avoided
fig,ax=plt.subplots(figsize=(11.6,7.5));fig.subplots_adjust(left=.15,right=.96,top=.76,bottom=.16)
cols=['Adjusted TCGA','GEO directional','ER heterogeneity','Evidence class']
ax.set_xlim(-.5,3.5);ax.set_ylim(N-.5,-.5)
for i,r in df.iterrows():
 cell=[('q < 0.05',r.fdr_adjusted<.05),('q < 0.05' if r.fdr_geo_directional<.05 else 'q ≥ 0.05',r.fdr_geo_directional<.05),('q < 0.05' if r.fdr_er_heterogeneity<.05 else 'q ≥ 0.05',r.fdr_er_heterogeneity<.05)]
 for j,(t,v) in enumerate(cell):
  fc='#BFE5DB' if v else '#E6E8EC'
  if j==2 and v:fc='#F4C5B5'
  ax.add_patch(Rectangle((j-.47,i-.43),.94,.86,facecolor=fc,edgecolor='white',linewidth=1.8))
  ax.text(j,i,t,va='center',ha='center',fontsize=10,color=ink)
 ax.add_patch(Rectangle((2.53,i-.43),.94,.86,facecolor={'Class A':'#C8E7E4','Class B':'#F2E0C0','Class C':'#E4DDF2'}[r['class']],edgecolor='white',linewidth=1.8))
 ax.text(3,i,r['class'],ha='center',va='center',fontsize=10,fontweight='bold',color=ink)
for z in [3.5,7.5]:ax.axhline(z,color='#BBC7D1',lw=1.6)
ax.set_yticks(y,df.gene,fontsize=10.8,fontstyle='italic');ax.set_xticks(range(4),cols,fontsize=10,fontweight='bold');ax.xaxis.tick_top();ax.tick_params(length=0,pad=6)
for sp in ax.spines.values():sp.set_visible(False)
fig.text(.075,.944,'D  |  Integrated evidence-classification matrix',fontsize=17.5,fontweight='bold',color=ink)
fig.text(.075,.892,'Exact significance status per gene; ER heterogeneity is distinct from ER-sensitive classification',fontsize=10,color=muted)
fig.text(.15,.072,'Class A: replicated, ER-robust  •  Class B: replicated, ER-sensitive  •  Class C: no significant directional replication',fontsize=9,color=muted)
fig.text(.15,.044,'A2M has directional instability without significant heterogeneity; EGFR has significant heterogeneity but no external replication.',fontsize=8.5,color=muted)
save(fig,'Figure2_D_Corrected')

# Raw corrected data and QA
cols=['gene','class','beta_age_z','ci_low','ci_high','fdr_adjusted','rho_geo','fdr_geo_directional','rho_er_pos','rho_er_neg','fdr_er_heterogeneity']
df[cols].to_csv(O/'Figure2_Validated_Source.csv',index=False)
checks=[]
for _,r in df.iterrows():
 checks.append({'gene':r.gene,'TCGA_direction':'positive' if r.beta_age_z>0 else 'negative','GEO_direction':'positive' if r.rho_geo>0 else 'negative','GEO_replication':bool(r.fdr_geo_directional<.05),'ER_heterogeneity_significant':bool(r.fdr_er_heterogeneity<.05),'evidence_class':r['class']})
pd.DataFrame(checks).to_csv(O/'Figure2_QA_Checks.csv',index=False)
(O/'Figure2_Caption_and_Integrity.txt').write_text('''Figure 2. Age-associated breast-cancer candidate evidence from adjusted discovery, external replication and receptor-stratified sensitivity. (A) HC3-robust adjusted age coefficients and 95% confidence intervals for 12 selected genes in TCGA-BRCA, with BH-adjusted q-values. (B) Signed Spearman correlations with age in the independent GSE42568 cohort; colored diamonds indicate significant directional replication (BH-FDR < 0.05), and grey circles indicate nonsignificant directional replication. (C) ER-positive and ER-negative subgroup age correlations in TCGA-BRCA; asterisks indicate significant ER-heterogeneity after FDR correction. (D) Per-gene matrix of adjusted discovery significance, directional external replication, ER heterogeneity, and reported study evidence classes. The displayed genes are a selected subset of the discovery results. A2M is Class B because of directional instability, despite nonsignificant ER heterogeneity. EGFR shows significant ER heterogeneity but does not meet the external-replication criterion. None of these associations establishes prognostic, therapeutic or clinical biomarker validity.\n\nDATA PROVENANCE: ageaware-breast-cancer-final.zip / data/source_tables/Figure2_candidate_statistics.csv. The code in regenerate_figure2.py regenerates every submitted panel and checks key class- and sign-related conditions. No patient-level rerun or reanalysis was performed. External GSE42568 results are unadjusted Spearman correlations and therefore not estimand-equivalent to adjusted TCGA-BRCA coefficients.\n''')
# PPTX with panel images kept separately moveable (do not distort aspect ratio)
prs=Presentation();prs.slide_width=Inches(16);prs.slide_height=Inches(10.2);blank=prs.slide_layouts[6]
sl=prs.slides.add_slide(blank)
for i,letter in enumerate('ABCD'):
 name=f'Figure2_{letter}_Corrected.png'
 x=.26+(i%2)*7.87;y=.28+(i//2)*4.94
 # picture sizes aspect-preserving
 im=Image.open(O/name);w,h=im.size
 maxw,maxh=7.5,4.6;scale=min(maxw/w,maxh/h)
 ww,hh=w*scale,h*scale
 sl.shapes.add_picture(str(O/name),Inches(x+(maxw-ww)/2),Inches(y+(maxh-hh)/2),width=Inches(ww),height=Inches(hh))
for letter in 'ABCD':
 slide=prs.slides.add_slide(blank)
 path=O/f'Figure2_{letter}_Corrected.png';im=Image.open(path);w,h=im.size;sc=min(15/w,9.4/h)
 slide.shapes.add_picture(str(path),Inches((16-w*sc)/2),Inches((10.2-h*sc)/2),width=Inches(w*sc),height=Inches(h*sc))
prs.save(O/'Figure2_Corrected_Assembly.pptx')
# Preview create consistent non-stretched panel placement
canvas=Image.new('RGB',(2900,2030),'white')
for i,letter in enumerate('ABCD'):
 im=Image.open(O/f'Figure2_{letter}_Corrected.png').convert('RGB')
 im.thumbnail((1415,968),Image.Resampling.LANCZOS)
 left=20+(i%2)*1450+(1415-im.width)//2;top=20+(i//2)*995+(968-im.height)//2
 canvas.paste(im,(left,top))
canvas.save(O/'Figure2_Corrected_Combined_Preview.png')
print('Panels generated, automated integrity checks passed.')
