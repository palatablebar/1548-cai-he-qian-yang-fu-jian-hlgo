from collections import Counter
from math import isfinite


def accountable_plan(rows, actual_balance, starting_capacity):
    seen = set()
    counts = Counter()
    total = 0
    for row in rows:
        if row['key'] in seen:
            raise ArithmeticError('复核凭证的关联单号不唯一')
        key = row['key']
        seen.add(key)
        state = row['state']
        counts[state] += 1
        if state == '已分派':
            total += row['cost']
        if not isfinite(row['estimate']):
            raise ArithmeticError('非有限估计不能签发')
    if total + actual_balance != starting_capacity:
        raise ArithmeticError('处置清册与工位余额不符')
    return counts, total


def register_signoff_slip(measurements, estimate):
    cyan_shift = measurements['cyan_shift']
    magenta_shift = measurements['magenta_shift']
    register_um = measurements['register_um']
    moisture = measurements['moisture']
    ink_c = measurements['ink_c']
    image_blocks = measurements['image_blocks']
    return {
        '青版绝对色偏': round(abs(cyan_shift), 3),
        '双通道同向量': round(min(abs(cyan_shift),abs(magenta_shift))*(1 if cyan_shift*magenta_shift>=0 else 0), 3),
        '距套准工艺线': round(105-register_um, 3),
        '综合色偏密区负荷': round((abs(cyan_shift)+abs(magenta_shift))*image_blocks/32, 3),
        '复核代价指标': round(register_um/110 + (abs(cyan_shift)+abs(magenta_shift))/65, 4),
    }


def document_control(rows):
    register = []
    for row in rows:
        if row['state'] not in {'已分派', '暂停', '人工判读'}:
            continue
        note = register_signoff_slip(row['measurements'], row['estimate'])
        register.append({'单号': row['key'], '区段': row['zone'], '处置': row['state'], **note})
    return register
