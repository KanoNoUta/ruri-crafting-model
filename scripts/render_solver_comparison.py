"""Render the README's local-search/model time and compute-cost overview.

Chart contract: compare two named methods using all 24 saved initial states
and the separate 48-trajectory runs in continuation-benchmark.json. Two
zero-based horizontal bar panels show response medians (ms) and each run's
cumulative decision time (s). The latter is descriptive, not equal-work
throughput. The existing decision-latency.png retains all 24 observations.
Use the repository's blue root plus neutral open/hatched search bars, direct
labels, and a white background. Deliver a PNG for GitHub Markdown at 800 px;
inspect that image and the rendered README before publication. No training.
"""

import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
BLUE, GREY, INK, GRID = '#2563EB', '#64748B', '#182230', '#E2E8F0'


def render():
    bench = json.loads((ROOT / 'evidence/continuation-benchmark.json').read_text(encoding='utf-8'))
    timings = bench['sameStateDecisionTimings']
    assert len(timings) == bench['caseCount'] == 24
    assert len({row['caseId'] for row in timings}) == len(timings)
    methods = ('nativeSearch', 'model')
    latency = [statistics.median(row[field] for row in timings)
               for field in ('nativeSearchMs', 'modelDecisionMedianMs')]
    # Recalculate accumulated time from trajectories, rather than charting
    # rounded README values or silently accepting stale summary totals.
    compute_seconds = []
    for method in methods:
        rows = [row for row in bench['trajectories'] if row['method'] == method]
        assert len(rows) == bench['summary'][method]['all']['trajectories'] == 48
        compute_seconds.append(sum(sum(row['decisionMs']) for row in rows) / 1000)
    assert min(latency + compute_seconds) > 0
    ratio = latency[0] / latency[1]

    fonts = {entry.name for entry in font_manager.fontManager.ttflist}
    font = next((name for name in ('Microsoft YaHei', 'Noto Sans CJK SC', 'SimHei')
                 if name in fonts), None)
    if font is None:
        raise RuntimeError('Install Microsoft YaHei or Noto Sans CJK SC to render Chinese labels.')
    plt.rcParams.update({
        'font.family': font, 'font.size': 11, 'axes.unicode_minus': False,
        'text.color': INK, 'axes.labelcolor': GREY, 'xtick.color': GREY,
        'ytick.color': INK, 'axes.spines.top': False, 'axes.spines.right': False,
        'axes.edgecolor': GRID, 'figure.facecolor': 'white',
        'axes.facecolor': 'white', 'savefig.facecolor': 'white',
    })
    fig, axes = plt.subplots(2, 1, figsize=(10.8, 8.2))
    fig.subplots_adjust(left=.23, right=.94, top=.80, bottom=.28, hspace=1.12)
    panels = [
        (latency, '单次决策时间', '24 个相同起点 · 响应中位数 · 毫秒（越低越好）',
         [f'{latency[0]:.3f} ms', f'{latency[1]:.4f} ms']),
        (compute_seconds, '续作累计计算开销', '每种方法各 48 条轨迹 · 秒（运行记录，工作量不同）',
         [f'{value:.3f} s' for value in compute_seconds]),
    ]
    for ax, (values, heading, unit, labels) in zip(axes, panels):
        ax.barh(0, values[0], height=.45, color='white', edgecolor=GREY, hatch='//', linewidth=1)
        ax.barh(1, values[1], height=.45, color=BLUE, edgecolor=BLUE, linewidth=1)
        for y, (value, label) in enumerate(zip(values, labels)):
            ax.text(value + max(values) * .025, y, label, va='center', fontsize=12,
                    weight='bold', color=INK if y == 0 else BLUE)
        ax.set_yticks([0, 1], ['传统本地搜索', 'RURI-Craft G1'])
        ax.set_ylim(1.6, -.6)
        ax.set_xlim(0, max(values) * 1.26)
        ax.xaxis.grid(True, color=GRID, linewidth=.8)
        ax.set_axisbelow(True)
        ax.tick_params(axis='y', length=0, pad=12)
        ax.set_title(heading, loc='left', pad=32, fontsize=14, weight='bold')
        ax.text(0, 1.10, unit, transform=ax.transAxes, color=GREY, fontsize=10)

    fig.text(.07, .955, '传统本地搜索 vs 模型：时间与计算开销',
             fontsize=20, weight='bold', va='top')
    fig.text(.07, .905, f'Ryzen 7 7800X3D · CPU 单线程 ONNX · {bench["createdUtc"][:10]}',
             fontsize=11, color=GREY, va='top')
    fig.text(.07, .195, f'同起点响应中位数之比 ≈ {ratio:,.0f} 倍', fontsize=15, weight='bold')
    fig.text(.07, .154, '该比值表示决策响应开销差异，不代表完整制作速度或实际技能次数的提升。',
             fontsize=10, color=GREY)
    fig.text(.07, .110, '续作访问的状态、停止位置与动作数不同；累计耗时不能换算同等工作量吞吐或费用。',
             fontsize=10, color=GREY)
    fig.text(.07, .070, '来源：evidence/continuation-benchmark.json；不含加载、IPC、模拟器与游戏技能执行。',
             fontsize=9.5, color=GREY)
    fig.text(.07, .035, '搜索器：GlobalParetoSearch / DeterministicBeamSearch；不是上游 Raphael。',
             fontsize=9.5, color=GREY)
    output = ROOT / 'assets/solver-comparison.png'
    output.parent.mkdir(exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)
    print(json.dumps({'image': str(output), 'sameStateMedianMs': dict(zip(methods, latency)),
                      'trajectoryDecisionSeconds': dict(zip(methods, compute_seconds)),
                      'ratioOfResponseMedians': ratio}))


if __name__ == '__main__':
    render()
