from math import exp, log, fsum, sqrt
from statistics import median, mean, quantiles

from .bayes_model import score_kernel



def explain_proof_bayes(fit, calibration, replay, live):
    populations = fit.parameters
    rows = []
    for press in live:
        posterior, terms = score_kernel(populations,press)
        strongest = max(range(len(terms)),key=lambda k:abs(terms[k]))
        raw = press.input_values
        polarity = '偏深' if raw[0]+raw[1]>=0 else '偏浅'
        likelihood = ('双色偏移','套准','水分','热墨','版间差')[strongest]
        rows.append({'签样号':press.key,'压力组':press.cohort,'合成偏色':polarity,
                     '类条件主因':likelihood,'对数贡献':round(terms[strongest],3),'后验':round(posterior,4)})
    return sorted(rows,key=lambda item:(-item['后验'],item['签样号']))[:12]
