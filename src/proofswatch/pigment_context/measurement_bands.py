from dataclasses import replace
from statistics import mean, median
from collections import Counter
from math import fsum

from .contracts import FEATURE_NAMES, FEATURE_KEYS, RAW_KEYS


def current_cyan_abs(vector):
    cyan_shift = vector.input_values[0]
    return float(abs(cyan_shift))


def compare_cyan_abs(training, target):
    usual_cyan_abs = take_sample(training, current_cyan_abs)
    recent_cyan_abs = take_sample(target, current_cyan_abs)
    if len(usual_cyan_abs) < 4 or not recent_cyan_abs:
        return {'作业量': '青版绝对色偏', '有效读数': len(recent_cyan_abs), '判断': '参考不足'}
    anchor_cyan_abs = median(usual_cyan_abs)
    measured_cyan_abs = median(recent_cyan_abs)
    ordered_cyan_abs = sorted(usual_cyan_abs)
    low_cyan_abs, high_cyan_abs = ordered_cyan_abs[len(ordered_cyan_abs)//10], ordered_cyan_abs[(len(ordered_cyan_abs)*9)//10]
    change_cyan_abs = measured_cyan_abs-anchor_cyan_abs
    outside_cyan_abs = sum(value<low_cyan_abs or value>high_cyan_abs for value in recent_cyan_abs)
    return {'作业量': '青版绝对色偏', '训练参考': round(anchor_cyan_abs, 4), '现场中位': round(measured_cyan_abs, 4),
            '变动': round(change_cyan_abs, 4), '越界量': outside_cyan_abs, '有效读数': len(recent_cyan_abs)}


def current_magenta_abs(vector):
    magenta_shift = vector.input_values[1]
    return float(abs(magenta_shift))


def compare_magenta_abs(training, target):
    usual_magenta_abs = take_sample(training, current_magenta_abs)
    recent_magenta_abs = take_sample(target, current_magenta_abs)
    if len(usual_magenta_abs) < 4 or not recent_magenta_abs:
        return {'作业量': '品红绝对色偏', '有效读数': len(recent_magenta_abs), '判断': '参考不足'}
    anchor_magenta_abs = median(usual_magenta_abs)
    measured_magenta_abs = median(recent_magenta_abs)
    ordered_magenta_abs = sorted(usual_magenta_abs)
    low_magenta_abs, high_magenta_abs = ordered_magenta_abs[len(ordered_magenta_abs)//10], ordered_magenta_abs[(len(ordered_magenta_abs)*9)//10]
    change_magenta_abs = measured_magenta_abs-anchor_magenta_abs
    outside_magenta_abs = sum(value<low_magenta_abs or value>high_magenta_abs for value in recent_magenta_abs)
    return {'作业量': '品红绝对色偏', '训练参考': round(anchor_magenta_abs, 4), '现场中位': round(measured_magenta_abs, 4),
            '变动': round(change_magenta_abs, 4), '越界量': outside_magenta_abs, '有效读数': len(recent_magenta_abs)}


def current_coincident_cast(vector):
    cyan_shift = vector.input_values[0]
    magenta_shift = vector.input_values[1]
    return float(min(abs(cyan_shift),abs(magenta_shift))*(1 if cyan_shift*magenta_shift>=0 else 0))


def compare_coincident_cast(training, target):
    usual_coincident_cast = take_sample(training, current_coincident_cast)
    recent_coincident_cast = take_sample(target, current_coincident_cast)
    if len(usual_coincident_cast) < 4 or not recent_coincident_cast:
        return {'作业量': '双通道同向量', '有效读数': len(recent_coincident_cast), '判断': '参考不足'}
    anchor_coincident_cast = median(usual_coincident_cast)
    measured_coincident_cast = median(recent_coincident_cast)
    ordered_coincident_cast = sorted(usual_coincident_cast)
    low_coincident_cast, high_coincident_cast = ordered_coincident_cast[len(ordered_coincident_cast)//10], ordered_coincident_cast[(len(ordered_coincident_cast)*9)//10]
    change_coincident_cast = measured_coincident_cast-anchor_coincident_cast
    outside_coincident_cast = sum(value<low_coincident_cast or value>high_coincident_cast for value in recent_coincident_cast)
    return {'作业量': '双通道同向量', '训练参考': round(anchor_coincident_cast, 4), '现场中位': round(measured_coincident_cast, 4),
            '变动': round(change_coincident_cast, 4), '越界量': outside_coincident_cast, '有效读数': len(recent_coincident_cast)}


def current_register_stack(vector):
    register_um = vector.input_values[2]
    image_blocks = vector.input_values[5]
    return float(register_um*image_blocks/16)


def compare_register_stack(training, target):
    usual_register_stack = take_sample(training, current_register_stack)
    recent_register_stack = take_sample(target, current_register_stack)
    if len(usual_register_stack) < 4 or not recent_register_stack:
        return {'作业量': '版面累计错位', '有效读数': len(recent_register_stack), '判断': '参考不足'}
    anchor_register_stack = median(usual_register_stack)
    measured_register_stack = median(recent_register_stack)
    band_register_stack = max(1.0, abs(anchor_register_stack)*.2, median(abs(value-anchor_register_stack) for value in usual_register_stack))
    change_register_stack = (measured_register_stack-anchor_register_stack) / band_register_stack
    outside_register_stack = sum(abs(value-anchor_register_stack)>2.5*band_register_stack for value in recent_register_stack)
    return {'作业量': '版面累计错位', '训练参考': round(anchor_register_stack, 4), '现场中位': round(measured_register_stack, 4),
            '变动': round(change_register_stack, 4), '越界量': outside_register_stack, '有效读数': len(recent_register_stack)}


def current_paper_delta(vector):
    moisture = vector.input_values[3]
    return float(abs(moisture-62)/10)


def compare_paper_delta(training, target):
    usual_paper_delta = take_sample(training, current_paper_delta)
    recent_paper_delta = take_sample(target, current_paper_delta)
    if len(usual_paper_delta) < 4 or not recent_paper_delta:
        return {'作业量': '标准含水率偏差', '有效读数': len(recent_paper_delta), '判断': '参考不足'}
    anchor_paper_delta = median(usual_paper_delta)
    measured_paper_delta = median(recent_paper_delta)
    ordered_paper_delta = sorted(usual_paper_delta)
    low_paper_delta, high_paper_delta = ordered_paper_delta[len(ordered_paper_delta)//10], ordered_paper_delta[(len(ordered_paper_delta)*9)//10]
    change_paper_delta = measured_paper_delta-anchor_paper_delta
    outside_paper_delta = sum(value<low_paper_delta or value>high_paper_delta for value in recent_paper_delta)
    return {'作业量': '标准含水率偏差', '训练参考': round(anchor_paper_delta, 4), '现场中位': round(measured_paper_delta, 4),
            '变动': round(change_paper_delta, 4), '越界量': outside_paper_delta, '有效读数': len(recent_paper_delta)}


def current_warm_ink(vector):
    ink_c = vector.input_values[4]
    return float(max(0,ink_c-28))


def compare_warm_ink(training, target):
    usual_warm_ink = take_sample(training, current_warm_ink)
    recent_warm_ink = take_sample(target, current_warm_ink)
    if len(usual_warm_ink) < 4 or not recent_warm_ink:
        return {'作业量': '高黏偏差代理', '有效读数': len(recent_warm_ink), '判断': '参考不足'}
    anchor_warm_ink = median(usual_warm_ink)
    measured_warm_ink = median(recent_warm_ink)
    ordered_warm_ink = sorted(usual_warm_ink)
    low_warm_ink, high_warm_ink = ordered_warm_ink[len(ordered_warm_ink)//10], ordered_warm_ink[(len(ordered_warm_ink)*9)//10]
    change_warm_ink = measured_warm_ink-anchor_warm_ink
    outside_warm_ink = sum(value<low_warm_ink or value>high_warm_ink for value in recent_warm_ink)
    return {'作业量': '高黏偏差代理', '训练参考': round(anchor_warm_ink, 4), '现场中位': round(measured_warm_ink, 4),
            '变动': round(change_warm_ink, 4), '越界量': outside_warm_ink, '有效读数': len(recent_warm_ink)}


def current_registration_margin(vector):
    register_um = vector.input_values[2]
    return float(105-register_um)


def compare_registration_margin(training, target):
    usual_registration_margin = take_sample(training, current_registration_margin)
    recent_registration_margin = take_sample(target, current_registration_margin)
    if len(usual_registration_margin) < 4 or not recent_registration_margin:
        return {'作业量': '距套准工艺线', '有效读数': len(recent_registration_margin), '判断': '参考不足'}
    anchor_registration_margin = median(usual_registration_margin)
    measured_registration_margin = median(recent_registration_margin)
    ordered_registration_margin = sorted(usual_registration_margin)
    low_registration_margin, high_registration_margin = ordered_registration_margin[len(ordered_registration_margin)//10], ordered_registration_margin[(len(ordered_registration_margin)*9)//10]
    change_registration_margin = measured_registration_margin-anchor_registration_margin
    outside_registration_margin = sum(value<low_registration_margin or value>high_registration_margin for value in recent_registration_margin)
    return {'作业量': '距套准工艺线', '训练参考': round(anchor_registration_margin, 4), '现场中位': round(measured_registration_margin, 4),
            '变动': round(change_registration_margin, 4), '越界量': outside_registration_margin, '有效读数': len(recent_registration_margin)}


def current_load_impact(vector):
    cyan_shift = vector.input_values[0]
    magenta_shift = vector.input_values[1]
    image_blocks = vector.input_values[5]
    return float((abs(cyan_shift)+abs(magenta_shift))*image_blocks/32)


def compare_load_impact(training, target):
    usual_load_impact = take_sample(training, current_load_impact)
    recent_load_impact = take_sample(target, current_load_impact)
    if len(usual_load_impact) < 4 or not recent_load_impact:
        return {'作业量': '综合色偏密区负荷', '有效读数': len(recent_load_impact), '判断': '参考不足'}
    anchor_load_impact = median(usual_load_impact)
    measured_load_impact = median(recent_load_impact)
    band_load_impact = max(1.0, abs(anchor_load_impact)*.2, median(abs(value-anchor_load_impact) for value in usual_load_impact))
    change_load_impact = (measured_load_impact-anchor_load_impact) / band_load_impact
    outside_load_impact = sum(abs(value-anchor_load_impact)>2.5*band_load_impact for value in recent_load_impact)
    return {'作业量': '综合色偏密区负荷', '训练参考': round(anchor_load_impact, 4), '现场中位': round(measured_load_impact, 4),
            '变动': round(change_load_impact, 4), '越界量': outside_load_impact, '有效读数': len(recent_load_impact)}


def take_sample(vectors, measure):
    return tuple(measure(record) for record in vectors if not record.missing)


def measure_pigment_context_band(history, daybook):
    yield compare_cyan_abs(history, daybook)
    yield compare_magenta_abs(history, daybook)
    yield compare_coincident_cast(history, daybook)
    yield compare_register_stack(history, daybook)
    yield compare_paper_delta(history, daybook)
    yield compare_warm_ink(history, daybook)
    yield compare_registration_margin(history, daybook)
    yield compare_load_impact(history, daybook)


def evaluate_shift(training, current):
    return list(measure_pigment_context_band(training, current))
