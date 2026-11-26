from collections import defaultdict
from math import fabs, fsum
from statistics import mean, median

from .bayes_model import score_kernel


def roller_limits(past):
    conditions = defaultdict(list)
    for proof in past:
        chroma = abs(proof.input_values[0]) + abs(proof.input_values[1])
        conditions[proof.cohort].append((chroma,proof.outcome))
    return conditions


def chroma_probability(model, proof):
    offset = abs(proof.input_values[0])+abs(proof.input_values[1])
    options = model.get(proof.cohort,())
    if not options:
        options = [entry for partition in model.values() for entry in partition]
    usable = sorted(options,key=lambda feat:(abs(feat[0]-offset),feat[0]))[:7]
    return (1 + sum(flag for _,flag in usable))/(2+len(usable))


def baseline_review(fit, training, replay):
    control = roller_limits(training)
    by_cohort = defaultdict(list)
    for result in replay:
        if result.observed and result.outcome in (0,1):
            forecast, _ = score_kernel(fit.parameters,result)
            local = chroma_probability(control, result)
            error_a, error_b = (forecast-result.outcome)**2, (local-result.outcome)**2
            by_cohort[result.cohort].append((error_a,error_b,int(result.outcome),forecast,local))
    report = []
    for location, comparisons in sorted(by_cohort.items()):
        samples = len(comparisons)
        expected = fsum(row[3] for row in comparisons)
        confirmed = sum(row[2] for row in comparisons)
        misses = sum(row[2] and row[3] < 0.51 for row in comparisons)
        base_misses = sum(row[2] and row[4] < 0.51 for row in comparisons)
        before = fsum(row[1] for row in comparisons) / samples
        after = fsum(row[0] for row in comparisons) / samples
        report.append({'回放组':location,'实绩数':samples,'估计代价':round(after,4),'业务基线代价':round(before,4),
                       '基线':'旧机台按偏色绝对值筛样','预测阳性总量':round(expected,3),'实绩阳性数':confirmed,
                       '模型漏判':misses,'基线漏判':base_misses,
                       '相对 Brier 改善':round(1-after/before,4) if before else None})
    return report
