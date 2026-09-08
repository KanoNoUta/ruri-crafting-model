"""Reproduce README figures from the published JSON evidence; no model training."""
from pathlib import Path
import json
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'evidence'
OUT = ROOT/'assets'
OUT.mkdir(exist_ok=True)
BLUE, GREY, INK, GRID = '#2563EB', '#64748B', '#182230', '#E2E8F0'
fonts = {f.name for f in font_manager.fontManager.ttflist}
font = next((name for name in ('Microsoft YaHei','Noto Sans CJK SC','SimHei','DejaVu Sans') if name in fonts),'DejaVu Sans')
plt.rcParams.update({'font.family':font,'font.size':11,'axes.unicode_minus':False,
    'text.color':INK,'axes.labelcolor':INK,'xtick.color':GREY,'ytick.color':INK,
    'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':GRID,
    'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})
baseline = json.loads((EVIDENCE/'baseline-holdout.json').read_text())
g1 = json.loads((EVIDENCE/'g1-holdout.json').read_text())
paired = json.loads((EVIDENCE/'paired-comparison.json').read_text())
bench = json.loads((EVIDENCE/'continuation-benchmark.json').read_text())


def title(fig, heading, subtitle, note):
    fig.text(.07,.955,heading,fontsize=20,weight='bold',va='top')
    fig.text(.07,.900,subtitle,fontsize=10.5,color=GREY,va='top')
    fig.text(.07,.035,note,fontsize=9,color=GREY,va='bottom',linespacing=1.6)


def export(fig,name):
    fig.savefig(OUT/name,dpi=150)
    plt.close(fig)


segments = [('all','整体'),('ordinaryRecipes','普通配方'),('expertStrict','严格专家标签'),('cosmicEstimated','宇宙概率标签')]
fig,ax = plt.subplots(figsize=(10,6.5))
fig.subplots_adjust(left=.22,right=.90,top=.77,bottom=.20)
y = np.arange(len(segments)); height=.30
for report,offset,label,color,hatch in ((baseline,-height/2,'旧神经网络基线',GREY,'//'),(g1,height/2,'RURI-Craft G1',BLUE,None)):
    values = [report['segments'][key]['top1']*100 for key,_ in segments]
    bars=ax.barh(y+offset,values,height,label=label,color='white' if hatch else color,edgecolor=color,hatch=hatch)
    for bar,value in zip(bars,values): ax.text(value+1,bar.get_y()+bar.get_height()/2,f'{value:.2f}%',va='center',fontsize=10)
ax.set_yticks(y,[f'{label}\nn = {g1["segments"][key]["samples"]:,}' for key,label in segments])
ax.invert_yaxis();ax.set_xlim(0,106);ax.set_xticks([0,20,40,60,80,100])
ax.set_xlabel('与教师下一技能一致率（%）');ax.xaxis.grid(True,color=GRID);ax.set_axisbelow(True)
ax.legend(loc='lower left',bbox_to_anchor=(-.02,1.02),frameon=False,ncol=2)
title(fig,'G1 的下一技能预测更接近教师','44,450 条历史留出状态 · 2026-09-08 · 对比对象是旧模型',
      '来源：evidence/g1-holdout.json、baseline-holdout.json\n历史留出集已重复使用；一致率不是制作成功率，也不是与传统搜索器的准确率对比。')
export(fig,'agreement.png')

timings=bench['sameStateDecisionTimings']
native=np.array([r['nativeSearchMs'] for r in timings]);model=np.array([r['modelDecisionMedianMs'] for r in timings])
order=np.argsort(native)
fig,ax=plt.subplots(figsize=(10,9))
fig.subplots_adjust(left=.22,right=.91,top=.80,bottom=.19)
for y,i in enumerate(order):
    ax.plot([model[i],native[i]],[y,y],color=GRID,lw=1)
ax.scatter(model[order],np.arange(len(order)),label='G1：编码 + 掩码 + ONNX + 选技能',color=BLUE,s=35,zorder=3)
ax.scatter(native[order],np.arange(len(order)),label='本地传统搜索：求解后取下一技能',facecolors='white',edgecolors=GREY,marker='s',s=35,zorder=3)
names={'ordinary':'普通','expertStrict':'严格专家','cosmicEstimated':'宇宙概率'}
ax.set_yticks(np.arange(len(order)),[f'{names[timings[i]["segment"]]} #{i+1:02}' for i in order],fontsize=9)
ax.set_xscale('log');ax.set_xlabel('单次响应计算耗时（毫秒，对数坐标；越低越好）')
ax.grid(axis='x',color=GRID);ax.set_axisbelow(True);ax.invert_yaxis()
ax.legend(loc='lower left',bbox_to_anchor=(-.02,1.02),frameon=False,fontsize=10)
title(fig,'同一状态下，G1 的候选动作响应更快',
      f'7800X3D · CPU 单线程 ONNX · 24 个相同起点 · 中位数 G1 {np.median(model):.3f} ms / 搜索 {np.median(native):.2f} ms',
      '来源：evidence/continuation-benchmark.json；模型每起点测 30 次，搜索每起点测 1 次。\n搜索每步预算 1 秒 / 60,000 节点；不含加载、IPC、模拟器。响应可能无解。\n比较的是本仓库 GlobalParetoSearch / BeamSearch，不是上游 Raphael，也不是完整制作加速倍数。')
export(fig,'decision-latency.png')

groups=[('all','整体'),('ordinary','普通'),('expertStrict','严格专家状态'),('cosmicEstimated','宇宙概率状态')]
fig,ax=plt.subplots(figsize=(10,6.5));fig.subplots_adjust(left=.10,right=.96,top=.76,bottom=.23)
x=np.arange(len(groups));width=.32
for method,offset,label,color,hatch in [('nativeSearch',-width/2,'本地传统搜索',GREY,'//'),('model',width/2,'RURI-Craft G1',BLUE,None)]:
    metrics=[bench['summary'][method][group] for group,_ in groups]
    bars=ax.bar(x+offset,[r['goalMetRate']*100 for r in metrics],width,label=label,color='white' if hatch else color,edgecolor=color,hatch=hatch)
    for bar,row in zip(bars,metrics):
        ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+2,f'{row["goalMet"]}/{row["trajectories"]}',ha='center',fontsize=11)
ax.set_xticks(x,[label for _,label in groups]);ax.set_ylim(0,112);ax.set_yticks([0,20,40,60,80,100]);ax.set_ylabel('完成进度且达到原品质目标（%）')
ax.yaxis.grid(True,color=GRID);ax.set_axisbelow(True);ax.legend(loc='lower left',bbox_to_anchor=(0,1.02),ncol=2,frameon=False)
title(fig,'低延迟不代表更高的制作达标率','24 个保存状态 × 2 个随机种子 / 方法 · 每类 8 个状态 · 同一规则模拟器',
      '来源：evidence/continuation-benchmark.json；每步都根据观察状态重新决策，不启用模型失败后的算法回退。\n小规模、等权分层、中间状态续作；不是游戏实测或全部配方成功率。每状态两条轨迹并非两个独立配方。')
export(fig,'continuation.png')

fig,axes=plt.subplots(1,3,figsize=(11,6));fig.subplots_adjust(left=.08,right=.97,top=.73,bottom=.27,wspace=.38)
values=[(baseline['segments']['all']['remainingStepsMae'],g1['segments']['all']['remainingStepsMae'],'剩余技能次数预测误差','MAE（次，越低越好）',3),
        (paired['cpuLatencyMs']['baseline']['median'],paired['cpuLatencyMs']['optimized']['median'],'历史 CPU 推理耗时','毫秒 / 状态（越低越好）',4),
        (paired['baselineBytes']/1e6,paired['optimizedBytes']/1e6,'ONNX 文件大小','MB（十进制）',3)]
for ax,(old,new,heading,unit,precision) in zip(axes,values):
    ax.bar([0],[old],color='white',edgecolor=GREY,hatch='//',width=.55)
    ax.bar([1],[new],color=BLUE,edgecolor=BLUE,width=.55)
    for i,value in enumerate([old,new]):ax.text(i,value+max(old,new)*.05,f'{value:.{precision}f}',ha='center',fontsize=11)
    ax.set_title(heading,fontsize=12,pad=13);ax.set_xticks([0,1],['旧模型','G1']);ax.set_ylim(0,max(old,new)*1.30)
    ax.set_ylabel(unit,fontsize=10);ax.yaxis.grid(True,color=GRID);ax.set_axisbelow(True)
title(fig,'精度改善伴随着额外计算与体积成本','与旧神经网络基线相比 · 2026-09-08 历史同机评估',
      '来源：holdout reports / paired-comparison.json。三面板单位不同，请分别读取。\n历史延迟是预编码输入的 ONNX 单线程测量，与本次 7800X3D 完整决策计时不同。\n剩余次数预测误差下降不等于实际技能次数减少；能耗和云费用未测量。')
export(fig,'tradeoffs.png')

print(json.dumps({'images':[p.name for p in OUT.glob('*.png')],
    'sameStateModelMedianMs':float(np.median(model)),'sameStateSearchMedianMs':float(np.median(native)),
    'sameStateResponseRatio':float(np.median(native)/np.median(model)),
    'holdoutTop1GainPercentagePoints':100*(g1['segments']['all']['top1']-baseline['segments']['all']['top1']),
    'remainingStepsMaeReductionPercent':100*(1-g1['segments']['all']['remainingStepsMae']/baseline['segments']['all']['remainingStepsMae'])}))
