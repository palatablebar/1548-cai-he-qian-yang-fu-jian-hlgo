from proofswatch.pipeline import preview
from proofswatch.swatch_rescan.service import operating_ledger


def note(key, measures, *, zone='甲区', state='已分派', estimate=0, hits=(), missing=()):
    return {'key':key,'zone':zone,'state':state,'estimate':estimate,'hits':hits,
            'unmeasured':missing,'measurements':dict(zip(('cyan_shift', 'magenta_shift', 'register_um', 'moisture', 'ink_c', 'image_blocks'),measures,strict=True))}


def test_field_plan_is_visible_and_references_real_tickets():
    desk = preview()
    plan = desk['sections'][6]
    assert plan['operating_title'] == '色块复检安排'
    assert plan['operating_rows']
    scoped = {item['关联单据'] for item in plan['operating_rows'] if '关联单据' in item}
    assert scoped and scoped <= {row['key'] for row in desk['rows']}
    assert all(item['业务安排'] for item in plan['operating_rows'])


def test_register_violation_changes_the_patch_used_for_review():
    swatch = note('PS-1',(29,30,111,63,27,20),estimate=.85,state='暂停')
    action, stock = operating_ledger([swatch])
    assert action['复检色块']=='十字套准规'
    assert action['参考张数']==0 and stock['需确认基准']
