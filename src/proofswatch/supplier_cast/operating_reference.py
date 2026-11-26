from dataclasses import dataclass
from math import sqrt, fsum
from statistics import median


@dataclass(frozen=True, slots=True)
class DomainStudy:
    counts: tuple[int, int, int]
    rate: float | None
    midpoint: float | None
    expected: float | None
    drift: float | None

def supplier_cast_domains(vectors):
    cyan_abs = []
    magenta_abs = []
    coincident_cast = []
    register_stack = []
    paper_delta = []
    warm_ink = []
    registration_margin = []
    load_impact = []
    for measurement in vectors:
        unobserved = frozenset(measurement.missing)
        cyan_shift, magenta_shift, register_um, moisture, ink_c, image_blocks = measurement.input_values
        if unobserved.isdisjoint(('cyan_shift', 'image_blocks')):
            cyan_abs.append((round(abs(cyan_shift), 4), image_blocks>=19))
        if unobserved.isdisjoint(('cyan_shift', 'magenta_shift')):
            magenta_abs.append((round(abs(magenta_shift), 4), abs(cyan_shift)+abs(magenta_shift)>=38))
        if unobserved.isdisjoint(('cyan_shift', 'magenta_shift', 'register_um')):
            coincident_cast.append((round(min(abs(cyan_shift),abs(magenta_shift))*(1 if cyan_shift*magenta_shift>=0 else 0), 4), register_um>=86))
        if unobserved.isdisjoint(('register_um', 'moisture', 'image_blocks')):
            register_stack.append((round(register_um*image_blocks/16, 4), moisture>=80))
        if unobserved.isdisjoint(('moisture', 'ink_c')):
            paper_delta.append((round(abs(moisture-62)/10, 4), ink_c>=33))
        if unobserved.isdisjoint(('ink_c', 'image_blocks')):
            warm_ink.append((round(max(0,ink_c-28), 4), image_blocks>=19))
        if unobserved.isdisjoint(('cyan_shift', 'magenta_shift', 'register_um')):
            registration_margin.append((round(105-register_um, 4), abs(cyan_shift)+abs(magenta_shift)>=38))
        if unobserved.isdisjoint(('cyan_shift', 'magenta_shift', 'register_um', 'image_blocks')):
            load_impact.append((round((abs(cyan_shift)+abs(magenta_shift))*image_blocks/32, 4), register_um>=86))
    return {
        '青版绝对色偏 · 版面块多': tuple(cyan_abs),
        '品红绝对色偏 · 密度偏色': tuple(magenta_abs),
        '双通道同向量 · 高位套准': tuple(coincident_cast),
        '版面累计错位 · 受潮基材': tuple(register_stack),
        '标准含水率偏差 · 墨路高温': tuple(paper_delta),
        '高黏偏差代理 · 版面块多': tuple(warm_ink),
        '距套准工艺线 · 密度偏色': tuple(registration_margin),
        '综合色偏密区负荷 · 高位套准': tuple(load_impact),
    }


def evaluate_domains(training, current):
    references = supplier_cast_domains(training)
    activity = supplier_cast_domains(current)
    diagnostics = []
    for domain, observed in activity.items():
        baseline = references.get(domain, ())
        study = characterize(baseline, observed)
        diagnostics.append({'观察维度': domain, '训练有效量': study.counts[0], '当班有效量': study.counts[1],
                            '越线量':study.counts[2], '越线比例':study.rate, '参考中位':study.midpoint,
                            '当班中位':study.expected, '相对训练变化':study.drift})
    return diagnostics


def characterize(before, after):
    history = tuple(value for value, _ in before)
    observed = tuple(value for value, _ in after)
    violating = sum(flag for _, flag in after)
    old = median(history) if history else None
    new = median(observed) if observed else None
    pct = round(violating / len(after), 4) if after else None
    movement = round(new - old, 4) if old is not None and new is not None else None
    return DomainStudy((len(before),len(after),violating),pct,old,new,movement)
