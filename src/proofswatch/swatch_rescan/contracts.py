from dataclasses import dataclass, replace

RISK_CUTOFF = 0.51


@dataclass(frozen=True, slots=True)
class Policy:
    capacity: int
    group_quota: int
    trigger: float

    @classmethod
    def select(cls, capacity, mode):
        if type(capacity) is not int or not 1 <= capacity <= 60:
            raise ValueError('本班额度须在 1 至 60 之间')
        if mode == 'balanced':
            per_group = max(3, (capacity*3 + 4)//5)
            return cls(capacity, per_group, RISK_CUTOFF)
        if mode == 'focus':
            return cls(capacity, capacity, RISK_CUTOFF * .92)
        raise ValueError('未知复核策略')


@dataclass(frozen=True, slots=True)
class RuleNotice:
    rule_id: str
    meaning: str
    hard: bool = False


@dataclass(frozen=True, slots=True)
class CyanSpan:
    """Endpoint recomputations for a ticket whose only gap is cyan density."""

    cohort: str
    sample_count: int
    value_low: float | None
    value_high: float | None
    estimate_at_low: float | None
    estimate_at_high: float | None
    estimate_floor: float | None
    estimate_ceiling: float | None

    @property
    def available(self):
        return None not in (self.estimate_floor, self.estimate_ceiling)

    @property
    def has_measurement_band(self):
        return None not in (self.value_low, self.value_high)

    def basis(self, cutoff):
        if not self.available:
            return {'作业区': self.cohort, '同区拟合实测单数': self.sample_count,
                    '青版密度范围': '无实测'}
        result = {
            '作业区': self.cohort,
            '同区拟合实测单数': self.sample_count,
        }
        if self.has_measurement_band:
            result.update({
                '青版实测下限': self.value_low,
                '青版实测上限': self.value_high,
                '下限取值复算预测': self.estimate_at_low,
                '上限取值复算预测': self.estimate_at_high,
            })
        result.update({
            '复算预测下界': self.estimate_floor,
            '复算预测上界': self.estimate_ceiling,
            '复检线': cutoff,
        })
        return result


CyanProbe = CyanSpan
CyanBand = CyanSpan
CyanRange = CyanSpan


@dataclass(frozen=True, slots=True)
class Job:
    key: str
    cohort: str
    estimate: float
    lower: float | None
    upper: float | None
    cost: int
    state: str
    reason: str
    summary: str
    priority: float
    rule_hits: tuple[str, ...]

    def change(self, state, reason, summary):
        return replace(self, state=state, reason=reason, summary=summary)


@dataclass(frozen=True, slots=True)
class Plan:
    jobs: tuple[Job, ...]
    capacity: int
    balance: int
    used_by_group: tuple[tuple[str, int], ...]
