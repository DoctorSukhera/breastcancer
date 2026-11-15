from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch, Circle

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'figures'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'Liberation Sans','font.size':9,'axes.linewidth':0.8,'svg.hashsalt':'ageaware-bc-figures-v1'})

fig=plt.figure(figsize=(14,7),facecolor='white')
ax=fig.add_axes([0,0,1,1]); ax.set_axis_off(); ax.set_xlim(0,1); ax.set_ylim(0,1)

C={'border':'#263238','text':'#111827','blue':'#dceeff','blue2':'#5aa6e8','green':'#dff3e8','green2':'#5dbf8a',
   'yellow':'#fff2d7','orange':'#ffe7d8','pink':'#fde2eb','pink2':'#f7c7d5','purple':'#ece5ff','gray':'#f5f7f9','red':'#f24464'}

def panel(x,y,w,h,label,title):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.004,rounding_size=0.004',fc='white',ec=C['border'],lw=1.1))
    ax.text(x+0.012*w,y+h-0.035*h,label,ha='left',va='top',fontsize=14,fontweight='bold',color=C['text'])
    ax.text(x+0.095*w,y+h-0.035*h,title,ha='left',va='top',fontsize=12.2,fontweight='bold',color=C['text'])

def rbox(x,y,w,h,text,fc,ec='#7aa7c7',lw=0.8,fs=8.5,bold_first=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.003,rounding_size=0.004',fc=fc,ec=ec,lw=lw))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=fs,color=C['text'],fontweight='bold' if bold_first else 'normal',linespacing=1.15)

def arrow(x1,y1,x2,y2,rad=0):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=12,lw=1.0,color='#466b8f',connectionstyle=f'arc3,rad={rad}'))

# Layout
panel(0.008,0.315,0.33,0.675,'a','Objective and evidence inputs')
panel(0.008,0.010,0.33,0.295,'c','Evidence hierarchy')
panel(0.346,0.515,0.646,0.475,'b','Age-aware analysis workflow')
panel(0.346,0.010,0.35,0.495,'d','Bounded orchestration layer')
panel(0.704,0.010,0.288,0.495,'e','Governed outputs and claim boundary')

# Panel a
x0,y0,w,h=0.008,0.315,0.33,0.675
rbox(x0+0.012,y0+h-0.165,w-0.024,0.095,'Objective: age-aware molecular candidate\nprioritization in breast cancer using\nmulti-evidence integration',C['blue'],'#6ab0e8',fs=9.2)
items=[
('GenAge/HAGR','307 curated human ageing-related genes','gene'),
('TCGA-BRCA','1,079 primary tumors\nRNA-seq + clinical covariates','db'),
('GSE42568','104 breast tumors\nindependent microarray expression cohort','grid'),
('STRING','79 mapped genes\n213 edges at required score 700','net'),
('GO + KEGG','1,698 terms tested\n514 FDR-significant','doc')]
ys=[y0+h-0.245,y0+h-0.345,y0+h-0.445,y0+h-0.545,y0+h-0.645]
for (name,desc,typ),yy in zip(items,ys):
    ix=x0+0.02; cy=yy+0.02
    if typ=='gene':
        for dx,dy,r in [(0,0,0.011),(-0.014,0.015,0.007),(0.014,0.015,0.007)]: ax.add_patch(Circle((ix+0.018+dx,cy+dy),r,fc='#4aa3df',ec='white',lw=.5))
    elif typ=='db':
        for k in range(3): ax.add_patch(Rectangle((ix+0.003,cy-0.015+k*0.012),0.032,0.010,fc='#7469c5',ec='white',lw=.5))
    elif typ=='grid':
        for a in range(4):
            for b in range(4): ax.add_patch(Circle((ix+0.007+a*0.0085,cy-0.012+b*0.009),0.0032,fc=['#4aa3df','#e85f7a'][(a+b)%2],ec='none'))
    elif typ=='net':
        pts=[(ix+0.005,cy),(ix+0.018,cy+0.02),(ix+0.033,cy),(ix+0.015,cy-0.02),(ix+0.034,cy-0.018)]
        for a,b in [(0,1),(1,2),(0,3),(1,3),(2,4),(3,4)]: ax.plot([pts[a][0],pts[b][0]],[pts[a][1],pts[b][1]],color='#566573',lw=.7)
        for p in pts: ax.add_patch(Circle(p,0.005,fc='#63bf8a',ec=C['border'],lw=.5))
    else:
        ax.add_patch(Rectangle((ix+0.006,cy-0.023),0.028,0.042,fc='white',ec='#228ac5',lw=1.2)); ax.plot([ix+0.012,ix+0.028],[cy+0.006,cy+0.006],color='#228ac5',lw=1); ax.plot([ix+0.012,ix+0.028],[cy-0.004,cy-0.004],color='#228ac5',lw=1)
    ax.text(x0+0.07,yy+0.035,name,ha='left',va='center',fontsize=9.6,fontweight='bold',color=C['text'])
    ax.text(x0+0.07,yy-0.002,desc,ha='left',va='center',fontsize=8.6,color='#243b5a',linespacing=1.2)

# Panel b
bx,by,bw,bh=0.346,0.515,0.646,0.475
labels=['307\nGenAge','292\nexpression-\ntestable','126\nage-associated','80\nadjusted','40\nlocked\nexternal-test','8\nexternally\nreplicated','4\nClass A']
cols=[C['blue'],C['green'],C['yellow'],C['orange'],C['pink'],C['pink2'],'#f7c0cf']
left=bx+0.012; gap=0.010; boxw=(bw-0.024-gap*6)/7; topy=by+0.255
for i,(lab,fc) in enumerate(zip(labels,cols)):
    xx=left+i*(boxw+gap); rbox(xx,topy,boxw,0.12,lab,fc,'#7aa7c7',fs=8.7,bold_first=(i in [0,6]))
    if i<6: arrow(xx+boxw,topy+0.06,xx+boxw+gap,topy+0.06)
labels2=['Continuous-age\nassociation','Covariate\nadjustment','ER-stratified\nsensitivity','External\nreplication','STRING\nnetwork analysis','GO/KEGG +\nredundancy\nreduction','Hierarchical\nprioritization']
for i,(lab,fc) in enumerate(zip(labels2,cols)):
    xx=left+i*(boxw+gap); rbox(xx,by+0.155,boxw,0.075,lab,fc,'#7aa7c7',fs=7.5)
    if i<6: arrow(xx+boxw,by+0.1925,xx+boxw+gap,by+0.1925)
ax.text(bx+0.02,by+0.115,'Adjustment:',fontweight='bold',fontsize=8.5,color=C['text']); ax.text(bx+0.082,by+0.115,'ER, PR, HER2 and pathological stage; HC3 robust covariance',fontsize=8.3,color='#243b5a')
ax.text(bx+0.02,by+0.078,'External replication:',fontweight='bold',fontsize=8.5,color=C['text']); ax.text(bx+0.121,by+0.078,'same direction + one-sided BH-FDR < 0.05 in GSE42568',fontsize=8.3,color='#243b5a')
ax.text(bx+0.02,by+0.041,'Context:',fontweight='bold',fontsize=8.5,color=C['text']); ax.text(bx+0.065,by+0.041,'STRING network analysis + GO/KEGG enrichment and redundancy reduction',fontsize=8.3,color='#243b5a')

# Panel c
cx,cy,cw,ch=0.008,0.010,0.33,0.295
rows=[('Class A','Cross-cohort replicated + ER-robust','IL7R, SQSTM1, EGR1, IGF1','n = 4',C['pink']),('Class B','Cross-cohort replicated but ER-sensitive','ESR1, A2M, FOXO1, EIF5A2','n = 4',C['yellow']),('Class C','Adjusted discovery + network/functional\nconvergence','EGFR, MYC, MAPK8, IRS2','n = 4',C['green']),('Class D','Lower-priority adjusted signals','68 remaining adjusted signals','n = 68',C['purple'])]
ry=cy+0.19
for i,(cl,desc,genes,n,fc) in enumerate(rows):
    yy=ry-i*0.055
    ax.add_patch(FancyBboxPatch((cx+0.012,yy),0.058,0.043,boxstyle='round,pad=.002,rounding_size=.003',fc=fc,ec='#bd9eb2',lw=.7)); ax.text(cx+0.041,yy+.0215,cl,ha='center',va='center',fontweight='bold',fontsize=8.8)
    ax.add_patch(FancyBboxPatch((cx+0.073,yy),0.198,0.043,boxstyle='round,pad=.002,rounding_size=.003',fc=fc,ec='#bd9eb2',lw=.7)); ax.text(cx+0.079,yy+.029,desc,ha='left',va='center',fontsize=7.1,color='#243b5a',linespacing=1.0); ax.text(cx+0.079,yy+.010,genes,ha='left',va='center',fontsize=7.6,fontweight='bold',fontstyle='italic',color=['#d22b4c','#e87500','#16814a','#2a67c8'][i])
    ax.add_patch(FancyBboxPatch((cx+0.276,yy),0.046,0.043,boxstyle='round,pad=.002,rounding_size=.003',fc=fc,ec='#bd9eb2',lw=.7)); ax.text(cx+0.299,yy+.0215,n,ha='center',va='center',fontweight='bold',fontsize=8.5)

# Panel d
dx,dy,dw,dh=0.346,0.010,0.35,0.495
top_y=dy+0.30
names=['Goal\nspecification','Planning','Tool\nselection','Execution','Observation /\ndata capture']
xs=[dx+0.015,dx+0.080,dx+0.145,dx+0.210,dx+0.275]
ws=[0.058,0.058,0.058,0.058,0.058]
for i,n in enumerate(names):
    rbox(xs[i],top_y,ws[i],0.07,n,[C['blue'],C['green'],C['yellow'],C['orange'],C['pink']][i],'#7aa7c7',fs=7.8)
    if i<4: arrow(xs[i]+ws[i],top_y+0.035,xs[i+1],top_y+0.035)
# lower branch
rbox(dx+0.070,dy+0.20,0.080,0.065,'Replanning',C['purple'],'#9a80d5',fs=8.0)
rbox(dx+0.220,dy+0.20,0.095,0.065,'Verification /\ntermination',C['blue'],'#6da9e0',fs=7.7)
# observation down and branch
obsx=xs[4]+ws[4]/2
ax.plot([obsx,obsx],[top_y,dy+0.275],color='#466b8f',lw=1)
# recoverable-failure branch: observation -> replanning
ax.plot([obsx,dx+0.155],[dy+0.275,dy+0.275],color='#466b8f',lw=1)
arrow(dx+0.155,dy+0.275,dx+0.110,dy+0.265)
# terminal branch: observation -> verification/termination
arrow(obsx,dy+0.275,dx+0.267,dy+0.265)
# replanning -> planning
arrow(dx+0.110,dy+0.265,dx+0.109,top_y)
# oversight
ax.add_patch(FancyBboxPatch((dx+0.012,dy+0.035),dw-0.024,0.115,boxstyle='round,pad=.003,rounding_size=.004',fc='white',ec='#9ab6ce',lw=.9,linestyle=(0,(4,3))))
ax.text(dx+dw/2,dy+0.138,'Bounded oversight and control',ha='center',va='center',fontsize=8.5,fontweight='bold')
ctrls=['Provenance','Safety','Cost-awareness','Audit / logging','Human review']; cc=[C['blue'],C['green'],C['yellow'],C['pink'],C['purple']]
cx0=dx+0.02; cgap=0.006; cww=(dw-0.04-cgap*4)/5
for i,(n,fc) in enumerate(zip(ctrls,cc)): rbox(cx0+i*(cww+cgap),dy+0.055,cww,0.05,n,fc,'#8aa7c0',fs=6.9)

# Panel e
ex,ey,ew,eh=0.704,0.010,0.288,0.495
rbox(ex+0.014,ey+0.255,ew-0.028,0.145,'',C['blue'],'#78b9ec')
ax.text(ex+0.035,ey+0.382,'Research outputs',fontsize=9.8,fontweight='bold',ha='left',va='center')
for j,t in enumerate(['Prioritized molecular candidates','Network / functional context','Provenance trace','Scientific evidence report']): ax.text(ex+0.04,ey+0.35-j*0.027,'•  '+t,fontsize=8.2,ha='left',va='center',color='#193e6b')
ax.add_patch(FancyBboxPatch((ex+0.014,ey+0.035),ew-0.028,0.205,boxstyle='round,pad=.004,rounding_size=.004',fc='#fff0f3',ec='#ff6680',lw=.9))
ax.text(ex+0.035,ey+0.212,'Explicit claim boundary',fontsize=9.5,fontweight='bold',ha='left',va='center')
ax.text(ex+0.035,ey+0.174,'Not within scope',fontsize=9.1,fontweight='bold',color='#e51b3e',ha='left')
for j,t in enumerate(['diagnosis','prognosis','treatment recommendation','clinical biomarker declaration']): ax.text(ex+0.04,ey+0.145-j*0.022,'•  '+t,fontsize=8.1,ha='left',color='#22375f')
ax.plot([ex+0.035,ex+ew-0.035],[ey+0.062,ey+0.062],color='#9ab0c0',lw=.7)
ax.text(ex+0.035,ey+0.043,'Research prioritization support only.',fontsize=8.1,ha='left',color='#22375f')

for ext in ['png','pdf','svg']:
    path=OUT/f'Figure_1.{ext}'
    metadata = ({'Software':'Matplotlib 3.10.8'} if ext == 'png' else
                {'CreationDate':None,'ModDate':None,'Creator':'AgeAware BC reproducible figure pipeline','Producer':'Matplotlib 3.10.8'} if ext == 'pdf' else
                {'Date':None,'Creator':'AgeAware BC reproducible figure pipeline'})
    fig.savefig(path,dpi=600 if ext=='png' else None,bbox_inches='tight',facecolor='white',metadata=metadata)
print('saved Figure_1')
