from dataclasses import dataclass

FIELDS = {'cyan_shift': ('青版密度偏差', '0.01D', -24, 43),
 'magenta_shift': ('品红密度偏差', '0.01D', -30, 48),
 'register_um': ('套准偏差', 'μm', 8, 128),
 'moisture': ('纸张含水率', '0.1%', 40, 95),
 'ink_c': ('油墨温度', '℃', 16, 43),
 'image_blocks': ('版面高密度块', '块', 1, 32)}
LIMITS = {'result_max': 1}


class MeasureIssue(ValueError):
    def __init__(self, field: str, code: str):
        super().__init__(f'{field}:{code}')
        self.field = field
        self.code = code


@dataclass(frozen=True, slots=True)
class ProofswatchRecord:
    key: str
    cohort: str
    day: int
    received: int
    revision: int
    result_day: int | None
    outcome: float | None
    observed: bool
    cyan_shift: float | None
    magenta_shift: float | None
    register_um: float | None
    moisture: float | None
    ink_c: float | None
    image_blocks: float | None

    def signature(self):
        return (self.key, self.cohort, self.day, self.revision, self.result_day, self.outcome, self.observed,
                *(getattr(self, key) for key in FIELDS))


@dataclass(frozen=True, slots=True)
class Issue:
    source_row: int
    key: str
    field: str
    code: str

    def evidence(self):
        return {'行号': self.source_row, '单号': self.key, '字段': FIELDS.get(self.field, (self.field,))[0],
                '原因': self.code}


@dataclass(frozen=True, slots=True)
class DecodeResult:
    entries: tuple[ProofswatchRecord, ...]
    issues: tuple[Issue, ...]
    source_rows: int
