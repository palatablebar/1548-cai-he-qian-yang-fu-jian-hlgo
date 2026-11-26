from dataclasses import dataclass
from math import isfinite
from ..print_tickets.contracts import ProofswatchRecord as RawObservation

RAW_KEYS = ('cyan_shift', 'magenta_shift', 'register_um', 'moisture', 'ink_c', 'image_blocks')
FEATURE_KEYS = ('color_radius', 'registration', 'paper_jump', 'ink_exposure', 'pigment_gap')
FEATURE_NAMES = ('双色偏差模长', '密版套准漂移', '纸张水分偏离', '油墨与版面交互', '通道相对色偏')


@dataclass(frozen=True, slots=True)
class FeatureState:
    fill: tuple[float, ...]
    offsets: tuple[float, ...]
    scales: tuple[float, ...]
    floor: tuple[float, ...]
    ceil: tuple[float, ...]
    fingerprint: str

    def __post_init__(self):
        if len(self.fill) != len(RAW_KEYS):
            raise ValueError('补值向量维数与字段表不匹配')
        if any(len(column) != len(FEATURE_KEYS) for column in (self.offsets, self.scales, self.floor, self.ceil)):
            raise ValueError('特征状态维数不匹配')
        if min(self.scales) <= 0:
            raise ValueError('特征尺度必须为正')


@dataclass(frozen=True, slots=True)
class FeatureVector:
    key: str
    cohort: str
    day: int
    values: tuple[float, ...]
    factors: tuple[float, ...]
    missing: tuple[str, ...]
    excursions: tuple[str, ...]
    outcome: float | None
    observed: bool
    input_values: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class PreparedRuns:
    train: tuple[FeatureVector, ...]
    calibration: tuple[FeatureVector, ...]
    replay: tuple[FeatureVector, ...]
    live: tuple[FeatureVector, ...]

    def segments(self):
        return tuple((name, getattr(self, name)) for name in ('train', 'calibration', 'replay', 'live'))


@dataclass(frozen=True, slots=True)
class Proposal:
    name: str
    field: str
    before: float
    after: float
    work: int

    def __post_init__(self):
        if self.before == self.after or not isfinite(self.after) or self.work < 0:
            raise ValueError('推演动作需要实质变动和有效额度')

    def evidence(self):
        return {'情形': self.name, '变更项': self.field, '原值': self.before,
                '置换值': self.after, '用量': self.work}

@dataclass(frozen=True, slots=True)
class PigmentContext:
    cyan_abs: float
    magenta_abs: float
    coincident_cast: float
    register_stack: float
    paper_delta: float
    warm_ink: float
    registration_margin: float
    load_impact: float

    def __post_init__(self):
        if not all(isfinite(amount) for amount in (self.cyan_abs, self.magenta_abs, self.coincident_cast, self.register_stack, self.paper_delta, self.warm_ink, self.registration_margin, self.load_impact)):
            raise ValueError('色样票存在无效的作业量测')

    def explain(self, labels=None):
        return (
            ('青版绝对色偏', round(self.cyan_abs, 4)),
            ('品红绝对色偏', round(self.magenta_abs, 4)),
            ('双通道同向量', round(self.coincident_cast, 4)),
            ('版面累计错位', round(self.register_stack, 4)),
            ('标准含水率偏差', round(self.paper_delta, 4)),
            ('高黏偏差代理', round(self.warm_ink, 4)),
            ('距套准工艺线', round(self.registration_margin, 4)),
            ('综合色偏密区负荷', round(self.load_impact, 4)),
        )
