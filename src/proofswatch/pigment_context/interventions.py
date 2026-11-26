from dataclasses import replace
from statistics import median

from .contracts import PigmentContext, Proposal


def measure_pigment_context(values) -> PigmentContext:
    cyan_shift, magenta_shift, register_um, moisture, ink_c, image_blocks = values
    return PigmentContext(
        cyan_abs=abs(cyan_shift),
        magenta_abs=abs(magenta_shift),
        coincident_cast=min(abs(cyan_shift),abs(magenta_shift))*(1 if cyan_shift*magenta_shift>=0 else 0),
        register_stack=register_um*image_blocks/16,
        paper_delta=abs(moisture-62)/10,
        warm_ink=max(0,ink_c-28),
        registration_margin=105-register_um,
        load_impact=(abs(cyan_shift)+abs(magenta_shift))*image_blocks/32,
    )


def propose_swatch_rescan(values, missing=()):
    cyan_shift, magenta_shift, register_um, moisture, ink_c, image_blocks = values
    if 'register_um' not in missing and (register_um>=23):
        yield Proposal('重新套准十五微米', 'register_um', register_um, max(8,register_um-15), 2)
    if 'cyan_shift' not in missing and (abs(cyan_shift)>=6):
        yield Proposal('压低青版偏差', 'cyan_shift', cyan_shift, round(cyan_shift*.65), 1)
    if 'moisture' not in missing and (abs(moisture-62)>=12):
        yield Proposal('纸样调湿后复扫', 'moisture', moisture, 62, 3)
    if 'ink_c' not in missing and (ink_c>=26):
        yield Proposal('下一张降低墨温', 'ink_c', ink_c, max(16,ink_c-5), 2)
