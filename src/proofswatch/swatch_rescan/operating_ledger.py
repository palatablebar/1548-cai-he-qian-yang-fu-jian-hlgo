from collections import defaultdict
from dataclasses import dataclass
from math import hypot
from statistics import median


@dataclass(frozen=True, slots=True)
class ProofVector:
    cyan: float
    magenta: float
    register: float
    stock_band: str
    crop: int


def isolate_color(sample):
    signals = sample['measurements']
    damp = signals['moisture'] - 60
    temp = signals['ink_c'] - 23
    cyan = (signals['cyan_shift'] - damp*.09 - temp*.13) / 100
    magenta = (signals['magenta_shift'] - damp*.12 - temp*.1) / 100
    bands = '湿纸' if signals['moisture'] >= 84 else '常用纸' if signals['moisture'] >= 55 else '干纸'
    return ProofVector(cyan,magenta,signals['register_um'],bands,int(signals['image_blocks']))


def choose_patch(vector, target, risk):
    if vector.register >= 105:
        return '十字套准规', '重贴定位胶片'
    change_c = vector.cyan-target[0]
    change_m = vector.magenta-target[1]
    length = hypot(change_c,change_m)
    if risk < .51 and length < .19:
        return '标准灰阶', '签样抽核'
    if change_c * change_m > .031 and min(abs(change_c),abs(change_m))>.14:
        return '叠印灰平衡块', '检查供墨与润版'
    if abs(change_c) > abs(change_m):
        return '青色实地块', '沿版向补测青组'
    return '品红中间调块', '补测品红网点扩张'


def operating_ledger(rows):
    proofs = defaultdict(list)
    findings = []
    for ticket in rows:
        if ticket['unmeasured']:
            findings.append({'业务安排': '补全光源条件或密度记录', '关联单据': ticket['key'], '暂缓授权': True})
            continue
        color = isolate_color(ticket)
        proofs[ticket['zone'], color.stock_band].append((color,ticket))
    for (press, paper), group in sorted(proofs.items()):
        references = [color for color,ticket in group if color.register <= 70 and ticket['state']=='观察']
        ready = len(references)>=3
        neutral = (median(color.cyan for color in references), median(color.magenta for color in references)) if ready else (0,0)
        checks = 0
        for color,ticket in sorted(group,key=lambda pair:(-pair[0].register,pair[1]['key'])):
            patch, step = choose_patch(color,neutral,ticket['estimate'])
            if ready and step=='签样抽核' and color.crop<24:
                continue
            checks += 1
            findings.append({'业务安排': step, '关联单据': ticket['key'], '机台': press, '同纸组': paper,
                             '复检色块': patch, '青密度差': round(color.cyan-neutral[0],3),
                             '品红密度差': round(color.magenta-neutral[1],3), '参考张数': len(references)})
        findings.append({'业务安排': '纸色基准账', '机台':press, '同纸组':paper,
                         '常态签样张数':len(references), '需复检张数':checks, '需确认基准':not ready})
    return findings
