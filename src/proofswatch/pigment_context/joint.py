from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JointAction:
    case: str
    work_units: int
    notes: str
    changes: dict[str, tuple[float, float]]

    def evidence(self, old_value, new_value, extrapolates):
        return {'联动推演':self.case, '用量':self.work_units, '先决条件':self.notes,
                '原预测':round(old_value,4), '替换预测':round(new_value,4),
                '变化':round(new_value-old_value,4), '超训练域':bool(extrapolates),
                '联动量测':{item:{'原值':before,'替换值':after} for item,(before,after) in self.changes.items()}}


def simulate_relevel_plates(readings, invalid):
    cyan_shift, magenta_shift = readings[0], readings[1]
    if invalid.intersection(('cyan_shift', 'magenta_shift')):
        return None
    if not (abs(cyan_shift)>=5 and abs(magenta_shift)>=5):
        return None
    cyan_shift_adjusted = round(cyan_shift*.5)
    magenta_shift_adjusted = round(magenta_shift*.6)
    inspected = {
        'cyan_shift': (cyan_shift, cyan_shift_adjusted),
        'magenta_shift': (magenta_shift, magenta_shift_adjusted),
    }
    if any(new != old for old,new in inspected.values()):
        return JointAction('青红成对修版', 2, '双版调整后保留首张样', inspected)
    return None


def simulate_equilibrate_stock(readings, invalid):
    moisture, ink_c = readings[3], readings[4]
    if invalid.intersection(('moisture', 'ink_c')):
        return None
    if not (abs(moisture-62)>=9 and ink_c>=25):
        return None
    moisture_adjusted = 62
    ink_c_adjusted = ink_c-5
    inspected = {
        'moisture': (moisture, moisture_adjusted),
        'ink_c': (ink_c, ink_c_adjusted),
    }
    if any(new != old for old,new in inspected.values()):
        return JointAction('纸样调湿与降墨温', 3, '再次过机之前按标准环境存放', inspected)
    return None


def simulate_compact_layout(readings, invalid):
    register_um, image_blocks = readings[2], readings[5]
    if invalid.intersection(('register_um', 'image_blocks')):
        return None
    if not (register_um>=28 and image_blocks>=7):
        return None
    register_um_adjusted = register_um-15
    image_blocks_adjusted = image_blocks-4
    inspected = {
        'register_um': (register_um, register_um_adjusted),
        'image_blocks': (image_blocks, image_blocks_adjusted),
    }
    if any(new != old for old,new in inspected.values()):
        return JointAction('校准小版打样', 2, '用低密度切边定位套准卡', inspected)
    return None


def simulate_reduce_heat_black(readings, invalid):
    ink_c, image_blocks = readings[4], readings[5]
    if invalid.intersection(('ink_c', 'image_blocks')):
        return None
    if not (ink_c>=26 and image_blocks>=13):
        return None
    ink_c_adjusted = ink_c-6
    image_blocks_adjusted = image_blocks-6
    inspected = {
        'ink_c': (ink_c, ink_c_adjusted),
        'image_blocks': (image_blocks, image_blocks_adjusted),
    }
    if any(new != old for old,new in inspected.values()):
        return JointAction('热墨加密集块分段', 2, '改用分次过机并测墨温', inspected)
    return None


def simulate_align_cyan(readings, invalid):
    cyan_shift, register_um = readings[0], readings[2]
    if invalid.intersection(('cyan_shift', 'register_um')):
        return None
    if not (abs(cyan_shift)>=8 and register_um>=26):
        return None
    cyan_shift_adjusted = round(cyan_shift*.6)
    register_um_adjusted = register_um-16
    inspected = {
        'cyan_shift': (cyan_shift, cyan_shift_adjusted),
        'register_um': (register_um, register_um_adjusted),
    }
    if any(new != old for old,new in inspected.values()):
        return JointAction('复调青版和套准', 2, '检测低温青版输出的套准差', inspected)
    return None


def options(values, missing):
    measurements=tuple(values)
    unobserved=frozenset(missing)
    cases=(
        simulate_relevel_plates(measurements, unobserved),
        simulate_equilibrate_stock(measurements, unobserved),
        simulate_compact_layout(measurements, unobserved),
        simulate_reduce_heat_black(measurements, unobserved),
        simulate_align_cyan(measurements, unobserved),
    )
    return tuple(action for action in cases if action is not None)
