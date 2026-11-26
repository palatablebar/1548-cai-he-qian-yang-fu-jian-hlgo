from .operating_ledger import operating_ledger
from collections import Counter, defaultdict
from math import exp, isfinite

from .contracts import RuleNotice, Job, Plan, Policy, RISK_CUTOFF, CyanProbe
from .constraints import WorkOrder, apply_swatch_rescan

CYAN_FIELD = 'cyan_shift'
CYAN_CROSSING_REASON = 'CYAN_RANGE_CROSSES_LINE'
CYAN_NO_REFERENCE_REASON = 'CYAN_COHORT_REFERENCE_MISSING'


def measures(raw):
    return tuple(raw)


def signals(data, estimate, missing=()):
    absent=frozenset(missing)
    cyan_shift, magenta_shift, register_um, moisture, ink_c, image_blocks = data
    hits = []
    if not absent.intersection(('register_um', 'image_blocks')) and (register_um >= 105 and image_blocks >= 17):
        hits.append(RuleNotice('REGISTRATION_HOLD', '先暂停签样并重新套准', hard=True))
    if not absent.intersection(('moisture', 'ink_c')) and (moisture >= 84 and ink_c >= 29):
        hits.append(RuleNotice('WET_STOCK', '湿纸热墨需复测', hard=False))
    if not absent.intersection(('cyan_shift', 'magenta_shift')) and (cyan_shift >= 26 and magenta_shift >= 28):
        hits.append(RuleNotice('DUAL_DRIFT', '双色同时正偏', hard=False))
    return tuple(hits)


def cyan_only_gap(raw):
    missing = frozenset(getattr(raw, 'missing', ()))
    return missing == {CYAN_FIELD}


def recorded_cyan_shift(record):
    if hasattr(record, CYAN_FIELD):
        return getattr(record, CYAN_FIELD)
    values = getattr(record, 'input_values', None)
    if values:
        missing = frozenset(getattr(record, 'missing', ()))
        return None if CYAN_FIELD in missing else values[0]
    return None


def cohort_cyan_limits(training):
    """Actual cyan extrema from mature fitting records, grouped by cohort."""
    values = {}
    for record in training:
        reading = recorded_cyan_shift(record)
        if reading is None:
            continue
        cohort = record.cohort
        if cohort in values:
            low, high = values[cohort]
            values[cohort] = (min(low, reading), max(high, reading))
        else:
            values[cohort] = (reading, reading)
    return {cohort: values[cohort] for cohort in sorted(values)}


cyan_limits = cohort_cyan_limits
cyan_bounds = cohort_cyan_limits
cohort_cyan_bounds = cohort_cyan_limits
cyan_reference_limits = cohort_cyan_limits
cyan_reference_bounds = cohort_cyan_limits
missing_cyan_limits = cohort_cyan_limits


def cyan_probe_for(assessment, cyan_probes=None):
    raw = assessment.raw
    if not cyan_only_gap(raw):
        return None
    if cyan_probes is not None:
        if hasattr(cyan_probes, 'estimate_floor') and hasattr(cyan_probes, 'available'):
            return cyan_probes
        if hasattr(cyan_probes, 'get'):
            if raw.key in cyan_probes:
                probe = cyan_probes[raw.key]
                if isinstance(probe, CyanProbe):
                    return probe
                if probe is None:
                    return CyanProbe(raw.cohort, 0, None, None, None, None, None, None)
        elif raw.key in getattr(cyan_probes, '__dict__', {}):
            probe = getattr(cyan_probes, raw.key)
            if isinstance(probe, CyanProbe):
                return probe
    if assessment.lower is None or assessment.upper is None:
        return CyanProbe(raw.cohort, 0, None, None, None, None, None, None)
    floor = min(assessment.lower, assessment.upper)
    ceiling = max(assessment.lower, assessment.upper)
    return CyanProbe(raw.cohort, 0, None, None, assessment.lower, assessment.upper,
                     floor, ceiling)


def cyan_decision(probe, cutoff):
    if not probe.available:
        return '无同区实测', CYAN_NO_REFERENCE_REASON, (
            '同区无实测：青版是唯一缺测项，但同区拟合期没有青版实测上下限，转人工，不占工位')
    floor, ceiling = probe.estimate_floor, probe.estimate_ceiling
    if probe.has_measurement_band:
        source = f'同区拟合实测上下限 {probe.value_low:g}–{probe.value_high:g}，'
    else:
        source = ''
    band = f'青版缺测按{source}本次特征、模型和校准复算，预测区间 {floor:.3f}–{ceiling:.3f}'
    if floor >= cutoff:
        return '始终达线', 'ABOVE_TRIGGER', band + f'，始终达线（≥{cutoff:.2f}），照常派单'
    if ceiling < cutoff:
        return '始终线下', 'BELOW_TRIGGER', band + f'，始终线下（<{cutoff:.2f}），留待观察'
    return '跨线', CYAN_CROSSING_REASON, band + f'，预测随缺项取值跨过复检线 {cutoff:.2f}，转人工，不占工位'


def expected_load(measurements):
    cyan_shift, magenta_shift, register_um, moisture, ink_c, image_blocks = measurements
    return 1 + int(image_blocks >= 14)


def dispatch_pressure(values, estimate):
    cyan_shift, magenta_shift, register_um, moisture, ink_c, image_blocks = values
    return register_um/110 + (abs(cyan_shift)+abs(magenta_shift))/65


def confidence_weight(estimate, cutoff):
    shifted = (estimate - cutoff) / max(.5, abs(cutoff) * .35)
    if shifted >= 0:
        return 1 / (1 + exp(-shifted))
    bounded = exp(shifted)
    return bounded / (1 + bounded)


PLURAL_PROBE_ALIASES = ('cyan_reviews', 'cyan_spans', 'cyan_bands', 'cyan_ranges', 'cyan_contexts')
SINGULAR_PROBE_ALIASES = ('cyan_review', 'cyan_span', 'cyan_band', 'cyan_range', 'cyan_context')


def resolve_probe_argument(raw, cyan_probes, options):
    if cyan_probes is not None:
        return cyan_probes
    for name in PLURAL_PROBE_ALIASES:
        if name in options:
            return options[name]
    for name in SINGULAR_PROBE_ALIASES:
        if name in options:
            return {raw.key: options[name]}
    return None


def recommend(assessment, attention, policy, cyan_probes=None, **options):
    raw = assessment.raw
    cyan_probes = resolve_probe_argument(raw, cyan_probes, options)
    data = measures(raw.input_values)
    estimate = assessment.estimate
    domain_codes = signals(data, estimate, raw.missing)
    level = confidence_weight(estimate, policy.trigger)
    cost = expected_load(data)
    if not isfinite(estimate) or not 1 <= cost <= 12:
        raise ValueError('处置量不在有效范围')
    cyan_probe = cyan_probe_for(assessment, cyan_probes)
    job_lower, job_upper = assessment.lower, assessment.upper
    if cyan_probe is not None and cyan_probe.available:
        job_lower, job_upper = cyan_probe.estimate_floor, cyan_probe.estimate_ceiling
    if domain_codes and domain_codes[0].hard:
        state = '暂停'
        reason = domain_codes[0].rule_id
        summary = domain_codes[0].meaning
    elif raw.key in attention or assessment.uncertain:
        state = '人工判读'
        reason = 'OUT_OF_REFERENCE' if raw.key in attention else 'INSUFFICIENT_CALIBRATION'
        summary = '分布偏移或校准量不足，需核对原始单据'
    elif domain_codes:
        # Measured rules take precedence over the missing-cyan sensitivity band.
        state = '候选'
        reason = domain_codes[0].rule_id
        summary = domain_codes[0].meaning
    elif cyan_probe is not None:
        _verdict, reason, summary = cyan_decision(cyan_probe, RISK_CUTOFF)
        if reason == CYAN_CROSSING_REASON or reason == CYAN_NO_REFERENCE_REASON:
            state = '人工判读'
        elif reason == 'ABOVE_TRIGGER':
            state = '候选'
        else:
            state = '观察'
    elif estimate >= policy.trigger:
        state = '候选'
        reason = 'ABOVE_TRIGGER'
        summary = '达到本班复核阈值'
    else:
        state = '观察'
        reason = 'BELOW_TRIGGER'
        summary = '保留记录并等待下一次巡查'
    return Job(raw.key, raw.cohort, round(estimate, 4), job_lower, job_upper, cost,
               state, reason, summary, round(level, 5), tuple(item.rule_id for item in domain_codes))


def allocate(assessments, attention, policy, cyan_probes=None, **options):
    work = [WorkOrder(recommend(assessment, attention, policy, cyan_probes, **options), assessment)
            for assessment in assessments]
    if len({item.job.key for item in work}) != len(work):
        raise ValueError('待处理单据编号重复')
    candidates = sorted((order for order in work if order.job.state == '候选'),
                        key=lambda order: (not bool(order.job.rule_hits), -dispatch_pressure(order.assessment.raw.input_values, order.job.estimate),
                                           -order.job.priority, order.job.cost, order.job.key))
    remaining = policy.capacity
    used = defaultdict(int)
    allocated = {}

    def wait(order, reason, evidence):
        allocated[order.job.key] = order.job.change('候补', reason, evidence)

    def admit(order):
        nonlocal remaining
        job = order.job
        if job.cost > remaining:
            wait(order,'CAPACITY_REACHED','剩余作业额度不足')
        elif used[job.cohort] + job.cost > policy.group_quota:
            wait(order,'GROUP_CAP_REACHED','已达分区额度上限')
        else:
            remaining -= job.cost
            used[job.cohort] += job.cost
            allocated[job.key] = job.change('已分派', job.reason, job.summary)
            return True
        return False

    apply_swatch_rescan(candidates, admit, wait)
    if set(allocated) != {item.job.key for item in candidates}:
        raise ArithmeticError('存在未经过工位规则的候选单据')
    resolved = sorted((allocated.get(item.job.key,item.job) for item in work),
                      key=lambda job: (job.state != '已分派', job.state == '观察', -job.priority, job.key))
    if sum(used.values()) + remaining != policy.capacity:
        raise ArithmeticError('派发余额核对失败')
    return Plan(tuple(resolved), policy.capacity, remaining, tuple(sorted(used.items())))


def plan_jobs(assessments, attention, capacity, mode='balanced', cyan_probes=None, **options):
    return allocate(assessments, frozenset(attention), Policy.select(capacity, mode),
                    cyan_probes, **options)


def action_evidence(plan):
    counts = Counter(job.state for job in plan.jobs)
    status = [{'处置': state, '单量': count} for state, count in sorted(counts.items())]
    status.extend({'处置': '分区 ' + group, '额度': cost} for group, cost in plan.used_by_group)
    status += [{'处置': '剩余额度', '额度': plan.balance}]
    return status


def swatch_mode(raw):
    register_um = raw[2]
    return int(register_um//25)


def operating_group(assessments, progression):
    source={line.raw.key:line.raw.input_values for line in assessments}
    cells=Counter()
    for work in progression.jobs:
        if work.state != '已分派':
            continue
        band=swatch_mode(source[work.key])
        cells[work.cohort,band] += work.cost
    return [{ '作业区': zone, '套版区': band, '班组用量': total } for (zone,band),total in sorted(cells.items())]
