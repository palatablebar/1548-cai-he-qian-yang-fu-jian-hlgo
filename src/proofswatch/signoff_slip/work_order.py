def collect_press_alignment(measures, missing, estimate):
    register_um = measures['register_um']
    if not (register_um>=52):
        return None
    value=register_um
    return {'现场复核':'复查套准卡','可复查值':round(value,3),'单位':'μm','归档要求':'保留同张套准标附近图像',
            '需补测':not set(missing).isdisjoint(('register_um',))}


def collect_pigment_delta(measures, missing, estimate):
    cyan_shift = measures['cyan_shift']
    magenta_shift = measures['magenta_shift']
    if not (abs(cyan_shift)+abs(magenta_shift)>=37):
        return None
    value=abs(cyan_shift)+abs(magenta_shift)
    return {'现场复核':'青品红比色','可复查值':round(value,3),'单位':'0.01D','归档要求':'同色样卡分档追加实测',
            '需补测':not set(missing).isdisjoint(('cyan_shift', 'magenta_shift'))}


def collect_paper_hold(measures, missing, estimate):
    moisture = measures['moisture']
    ink_c = measures['ink_c']
    if not (moisture>=76 or ink_c>=36):
        return None
    value=moisture/10
    return {'现场复核':'纸张调湿','可复查值':round(value,3),'单位':'%','归档要求':'核对纸样放置和墨温时点',
            '需补测':not set(missing).isdisjoint(('moisture', 'ink_c'))}


def collect_block_scan(measures, missing, estimate):
    image_blocks = measures['image_blocks']
    if not (image_blocks>=17):
        return None
    value=image_blocks
    return {'现场复核':'密集块复扫','可复查值':round(value,3),'单位':'块','归档要求':'沿高密度区取两处签认点',
            '需补测':not set(missing).isdisjoint(('image_blocks',))}


def check_signoff_slip(records):
    guide = []
    for ticket in records:
        if ticket['state'] not in ('已分派','暂停','人工判读'):
            continue
        measures=ticket['measurements']
        absent=ticket['unmeasured']
        estimate=ticket['estimate']
        checks = (
            collect_press_alignment(measures,absent,estimate),
            collect_pigment_delta(measures,absent,estimate),
            collect_paper_hold(measures,absent,estimate),
            collect_block_scan(measures,absent,estimate),
        )
        required=tuple(check for check in checks if check is not None)
        if not required:
            continue
        review=ticket['key']
        for check in required:
            guide.append({'签收单':review,'作业区':ticket['zone'],'处置':ticket['state'],**check})
    return guide
