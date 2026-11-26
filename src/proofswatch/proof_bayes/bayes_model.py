from math import exp, fsum, log, pi


def smooth_moments(points, prior_centre, prior_spread):
    count = len(points)
    centre = (fsum(points) + 2.5 * prior_centre) / (count + 2.5)
    dispersion = fsum((p - centre) ** 2 for p in points)
    return centre, max(.04, (dispersion + 2.5 * prior_spread) / (count + 2.5))


def fit_kernel(rows):
    yes = [record.values for record in rows if record.outcome >= .5]
    no = [record.values for record in rows if record.outcome < .5]
    parameters = []
    overall = list(zip(*(record.values for record in rows), strict=True))
    corpus = len(rows)
    for group in (no, yes):
        means = []
        for coordinate, total in enumerate(overall):
            origin = fsum(total) / len(total)
            variance = fsum((value-origin) ** 2 for value in total) / len(total)
            observed = [record[coordinate] for record in group]
            means.append(smooth_moments(observed, origin, variance))
        parameters.append((log((len(group) + 1) / (corpus + 2)), tuple(means)))
    return tuple(parameters), (('偏色票', len(yes)), ('合格票', len(no)), ('方差下限', .04))


def score_kernel(populations, sample):
    joint = []
    for prior, moments in populations:
        local = tuple(-.5 * (log(2*pi*variance) + (value - centre) ** 2 / variance)
                      for value, (centre, variance) in zip(sample.values, moments, strict=True))
        joint.append((prior + fsum(local), local))
    log0, left = joint[0]
    log1, right = joint[1]
    base = max(log0, log1)
    weights = [exp(log0-base), exp(log1-base)]
    return weights[1] / sum(weights), tuple(b - a for a, b in zip(left, right, strict=True))
