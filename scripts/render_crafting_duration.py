"""Estimate saved-state crafting duration, never present this as game telemetry.

Chart contract: GitHub README PNG, 800px display width; two zero-based horizontal
stacked bars compare mean skill-execution and measured decision seconds in the
same 30 successful pairs (15 ordinary, 15 expert; no successful cosmic pairs).
This is all available paired-success evidence, not a request for a time series.
Question: does faster inference shorten crafting once skill calls are included?
Takeaway: G1's additional skill calls outweigh its decision-time saving here.
Use blue #2563EB and neutral #64748B with open/hatched execution marks, direct
method labels and a shared legend for time components. Inspect the exported PNG.
"""
import argparse
import hashlib
import json
import math
import statistics as stats
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'evidence/continuation-benchmark.json'
REPORT = ROOT / 'evidence/crafting-duration-estimate.json'
METHODS = ('nativeSearch', 'model')


def calculate():
    bench = json.loads(SOURCE.read_text(encoding='utf-8'))
    rows = bench['trajectories']
    assert len(rows) == len({(r['caseId'], r['seed'], r['method']) for r in rows}) == 96
    groups = {m: {(r['caseId'], r['seed']): r for r in rows
                  if r['method'] == m and r['goalMet']} for m in METHODS}
    keys = sorted(groups[METHODS[0]].keys() & groups[METHODS[1]].keys())
    assert len(keys) == 30
    paired = []
    for key in keys:
        pair = {'caseId': key[0], 'seed': key[1], 'segment': groups['model'][key]['segment']}
        for method in METHODS:
            row = groups[method][key]
            assert row['completed'] and row['finalQuality'] >= row['requiredQuality']
            assert row['skillCalls'] == len(row['actions'])
            assert all(math.isfinite(x) and x >= 0 for x in row['decisionMs'])
            pair[method] = dict(skillCalls=row['skillCalls'], decisionSeconds=sum(row['decisionMs']) / 1000)
        paired.append(pair)
    scenarios = []
    for seconds in (2, 3):
        summary = {}
        for method in METHODS:
            values = [r[method] for r in paired]
            totals = [r['skillCalls'] * seconds + r['decisionSeconds'] for r in values]
            summary[method] = dict(
                meanSkillCalls=stats.mean(r['skillCalls'] for r in values),
                medianSkillCalls=stats.median(r['skillCalls'] for r in values),
                meanExecutionSeconds=stats.mean(r['skillCalls'] * seconds for r in values),
                meanDecisionSeconds=stats.mean(r['decisionSeconds'] for r in values),
                meanTotalSeconds=stats.mean(totals), medianTotalSeconds=stats.median(totals))
        scenarios.append(dict(secondsPerSkill=seconds, methods=summary,
                              meanModelMinusSearchSeconds=summary['model']['meanTotalSeconds']
                              - summary['nativeSearch']['meanTotalSeconds']))
    return dict(schemaVersion=1, estimateOnly=True, source=SOURCE.relative_to(ROOT).as_posix(),
                sourceSha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                pairedTrajectories=len(paired), independentStartingStates=len({k[0] for k in keys}),
                segments={s: sum(r['segment'] == s for r in paired) for s in sorted({r['segment'] for r in paired})},
                assumptions=['Uniform 2 or 3 seconds per skill; decisions executed serially between skills.',
                             'Remaining work from saved initial/intermediate states, not complete recipes from zero.',
                             'No loading, IPC, menus, network jitter, failed attempts, retries or hybrid verification/fallback.'],
                scenarios=scenarios, pairs=paired)


def render(report):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    fonts = {entry.name for entry in font_manager.fontManager.ttflist}
    font = next((f for f in ('Microsoft YaHei', 'Noto Sans CJK SC', 'SimHei') if f in fonts), None)
    if font is None:
        raise RuntimeError('Install Microsoft YaHei or Noto Sans CJK SC')
    grey, blue, ink, grid = '#64748B', '#2563EB', '#182230', '#E2E8F0'
    plt.rcParams.update({'font.family': font, 'font.size': 12, 'axes.unicode_minus': False,
                         'figure.facecolor': 'white', 'axes.facecolor': 'white', 'text.color': ink,
                         'axes.edgecolor': grid, 'axes.spines.top': False, 'axes.spines.right': False,
                         'xtick.color': grey, 'ytick.color': ink})
    fig, ax = plt.subplots(figsize=(10.8, 6.2))
    fig.subplots_adjust(left=.24, right=.93, top=.66, bottom=.40)
    values = report['scenarios'][1]['methods']
    for i, method in enumerate(METHODS):
        value = values[method]
        ax.barh(i, value['meanExecutionSeconds'], height=.42, color='white', edgecolor=grey,
                hatch='//', linewidth=1, label='技能执行（估算）' if i == 0 else None)
        ax.barh(i, value['meanDecisionSeconds'], left=value['meanExecutionSeconds'], height=.42,
                color=blue, edgecolor=blue, linewidth=1, label='决策计算（已测）' if i == 0 else None)
        ax.text(value['meanTotalSeconds'] + .35, i, f"{value['meanTotalSeconds']:.2f} 秒",
                va='center', fontsize=13, weight='bold')
    ax.set_xlim(0, 21)
    ax.set_ylim(1.55, -.55)
    ax.set_yticks([0, 1], ['传统本地搜索', 'RURI-Craft G1'])
    ax.tick_params(axis='y', length=0, pad=12)
    ax.set_xlabel('平均剩余制作时间 / 秒（越低越好）', color=grey, labelpad=12)
    ax.xaxis.grid(True, color=grid, linewidth=.8)
    ax.set_axisbelow(True)
    ax.legend(loc='lower left', bbox_to_anchor=(-.02, 1.08), frameon=False, ncol=2, fontsize=11)
    fig.text(.07, .94, '游戏内制作耗时估算：技能次数仍是关键', fontsize=19, weight='bold')
    fig.text(.07, .876, '同一批 30 对共同达标续作 · 普通 15 对 / 专家 15 对 · 假设每技能 3 秒', fontsize=11, color=grey)
    fig.text(.07, .812, '总时间 = 实际模拟技能次数 × 每技能耗时 + 该轨迹已测决策时间', fontsize=11, color=grey)
    fig.text(.07, .225, '搜索：4.67 次 × 3 秒 + 0.512 秒    |    G1：5.60 次 × 3 秒 + 0.00155 秒', fontsize=11)
    fig.text(.07, .178, '这批样本中，模型节省的决策时间未抵消额外技能的执行时间。', fontsize=12, weight='bold')
    fig.text(.07, .112, '保存状态后的剩余耗时估算；不是整件配方从零开始、游戏实测或混合回退性能。', fontsize=10, color=grey)
    fig.text(.07, .055, '来源：continuation-benchmark.json（2026-09-08）；不含失败重试、加载、菜单与网络等待。', fontsize=9.5, color=grey)
    fig.savefig(ROOT / 'assets/crafting-duration.png', dpi=160, facecolor='white')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Reconcile derived evidence using only the standard library')
    args = parser.parse_args()
    report = calculate()
    if args.check:
        assert json.loads(REPORT.read_text(encoding='utf-8')) == report
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        for method in METHODS:
            value = report['scenarios'][1]['methods'][method]
            assert f"{value['meanTotalSeconds']:.2f} 秒" in readme
        assert 'assets/crafting-duration.png' in readme
        assert (ROOT / 'assets/crafting-duration.png').is_file()
    else:
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        render(report)
    print(json.dumps({k: v for k, v in report.items() if k != 'pairs'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
