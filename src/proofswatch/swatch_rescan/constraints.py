from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Callable

from .contracts import Job


@dataclass(frozen=True, slots=True)
class WorkOrder:
    job: Job
    assessment: Any

    def __post_init__(self):
        if self.job.key != self.assessment.raw.key:
            raise ValueError('处置工位与单据不匹配')


def apply_swatch_rescan(proofs, admit: Callable, wait: Callable):
    plate_batches = set()
    for proof in proofs:
        cyan, magenta, shift, moisture, ink, blocks = proof.assessment.raw.input_values
        color_side = (cyan >= 0, magenta >= 0)
        press = proof.job.cohort
        if moisture < 48 and ink >= 40:
            wait(proof, 'PAPER_ACCLIMATION', '纸张先适应车间温湿后再复扫')
            continue
        reference = (press, color_side, shift//32)
        if reference in plate_batches and blocks < 22:
            wait(proof, 'SWATCH_COMBINE', '与同版色样同台复核')
        elif admit(proof):
            plate_batches.add(reference)
