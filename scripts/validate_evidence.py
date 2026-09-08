"""Independently reconcile published metrics, artifacts and the benchmark contract."""
import hashlib
import json
import math
import statistics
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    base=json.loads((ROOT/'evidence/baseline-holdout.json').read_text(encoding='utf-8'))
    g1=json.loads((ROOT/'evidence/g1-holdout.json').read_text(encoding='utf-8'))
    paired=json.loads((ROOT/'evidence/paired-comparison.json').read_text(encoding='utf-8'))
    bench=json.loads((ROOT/'evidence/continuation-benchmark.json').read_text(encoding='utf-8'))
    meta=json.loads((ROOT/'metadata.json').read_text(encoding='utf-8'))
    index=json.loads((ROOT/'modelmaster.json').read_text(encoding='utf-8'))
    assert base['samples']==g1['samples']==paired['samples']==44450
    for report in (base,g1):
        groups=[report['segments'][key] for key in ('ordinaryRecipes','expertStrict','cosmicEstimated')]
        assert sum(g['samples'] for g in groups)==report['samples']
        for metric in ('top1','top3'):
            weighted=sum(g['samples']*g[metric] for g in groups)/report['samples']
            assert math.isclose(weighted,report['segments']['all'][metric],abs_tol=1e-9)
            for group in groups:
                assert abs(group[metric]*group['samples']-round(group[metric]*group['samples']))<1e-5
    assert paired['optimizedAccuracy']==g1['segments']['all']['top1']
    assert paired['baselineAccuracy']==base['segments']['all']['top1']
    assert meta['onnxSha256']==bench['modelSha256']==index['models'][0]['files']['onnx']['sha256']
    assert meta['featureEncoder']['dimension']==106 and len(meta['actionVocab']['actions'])==36
    assert meta['architecture']['expertFeatureIndex']==20
    assert meta['featureEncoder']['featureNames'][20]=='craftState.isExpert'
    assert bench['budgetMsPerSearch']==1000 and bench['caseCount']==24 and bench['seedsPerCase']==2
    assert len(bench['sameStateDecisionTimings'])==24
    assert len({r['caseId'] for r in bench['sameStateDecisionTimings']})==24
    rows=bench['trajectories']
    keys={(r['caseId'],r['seed'],r['method']) for r in rows}
    assert len(keys)==len(rows)==96
    for method in ('model','nativeSearch'):
        for segment in ('all','ordinary','expertStrict','cosmicEstimated'):
            selected=[r for r in rows if r['method']==method and (segment=='all' or r['segment']==segment)]
            expected=bench['summary'][method][segment]
            successes=sum(r['completed'] and r['finalQuality']>=r['requiredQuality'] for r in selected)
            assert len(selected)==expected['trajectories']
            assert successes==expected['goalMet']
            assert math.isclose(successes/len(selected),expected['goalMetRate'])
            assert sum(r['completed'] for r in selected)==expected['completed']
            assert all(len(r['actions'])==r['skillCalls'] for r in selected)
            assert math.isclose(sum(sum(r['decisionMs']) for r in selected),expected['decisionComputeMs'],abs_tol=1e-6)
    lookup={(r['caseId'],r['seed'],r['method']):r for r in rows}
    common=[]
    for row in rows:
        if row['method']=='model':
            native=lookup[row['caseId'],row['seed'],'nativeSearch']
            if row['goalMet'] and native['goalMet']:
                common.append((row['skillCalls'],native['skillCalls']))
    assert len(common)==bench['summary']['jointSuccess']['trajectories']==30
    assert statistics.median(x[0] for x in common)==4
    assert statistics.median(x[1] for x in common)==3
    local_artifacts=ROOT/'artifacts'
    artifact_checks=[]
    if local_artifacts.exists():
        for line in (local_artifacts/'SHA256SUMS').read_text().splitlines():
            expected,name=line.split('  ',1)
            assert hashlib.sha256((local_artifacts/name).read_bytes()).hexdigest()==expected,name
            artifact_checks.append(name)
        assert (ROOT/'metadata.json').read_bytes()==(local_artifacts/'metadata.json').read_bytes()
    model_ms=statistics.median(r['modelDecisionMedianMs'] for r in bench['sameStateDecisionTimings'])
    search_ms=statistics.median(r['nativeSearchMs'] for r in bench['sameStateDecisionTimings'])
    report=dict(verifiedUtc=datetime.now(timezone.utc).isoformat(),assessment='Share with caveats',
        metricReconciliationPassed=True,benchmarkDenominatorsVerified=True,commonSuccessPairsVerified=True,
        artifactHashesVerified=artifact_checks,modelId='RURI-Craft-G1',version='1.0.0-beta.1',
        sameStateDecisionMedianMs={'g1':model_ms,'nativeSearch':search_ms},
        ratioOfResponseMedians=search_ms/model_ms,frameworkCommit=index['models'][0]['framework']['commit'],
        newTrainingStarted=False,newTeacherBatchMerged=False,
        caveats=['Historical holdout reused; no new independent blind test.',
                 '24 saved states / 2 seeds are a small stratified continuation sample.',
                 'Response cost excludes loading, IPC, simulator and game action execution.',
                 'Native bounded search is not upstream Raphael; no optimality, energy or end-to-end speedup claim.',
                 'G1 did not reduce skill calls on the jointly successful trajectories.'],
        sourceHashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'evidence').glob('*.json')
                      if p.name!='release-validation.json' and not p.name.endswith('.partial.json')})
    (ROOT/'evidence/release-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
