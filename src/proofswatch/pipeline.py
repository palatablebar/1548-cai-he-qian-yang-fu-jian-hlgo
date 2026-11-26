from dataclasses import replace
import json
from pathlib import Path

from .print_tickets import service as intake_service
from .press_shifts import service as cohort_service
from .pigment_context import service as feature_service
from .proof_bayes import service as model_service
from .impression_reliability import service as calibration_service
from .supplier_cast import service as monitor_service
from .swatch_rescan import service as dispatch_service
from .signoff_slip import service as audit_service
from .press_shifts import contracts as window_contract

PRESET = Path(__file__).resolve().parents[2] / 'sample_data' / 'print_tickets_sample.json'
MODULES = (('print_tickets', '色样票'),
 ('press_shifts', '印刷班次'),
 ('pigment_context', '颜料因素'),
 ('proof_bayes', '签样分类'),
 ('impression_reliability', '色样核验'),
 ('supplier_cast', '基材变化'),
 ('swatch_rescan', '复扫分派'),
 ('signoff_slip', '签样落款'))
DISPLAY = {'title': '彩盒签样复检',
 'object_name': '色样票',
 'unit': '概率',
 'role': '印刷质检领班',
 'endpoint': 'proofswatch',
 'identity': 'PROOF REGISTER',
 'location': '印务中心 · 彩盒签样室',
 'visual': '印刷分区色带',
 'queue': '彩盒验收登记',
 'resource': '签样台工位',
 'action': '派发签样复检',
 'lane': 'L8',
 'field_title': '色块复检安排'}


def open_fixture(path=PRESET):
    document = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(document, dict) or not isinstance(document.get('records'), list):
        raise ValueError('样例必须包含 records 数组')
    if len(document['records']) > 2500:
        raise ValueError('单次导入最多处理 2500 条单据')
    return document


def stage_at(index, details, records, issues=()):
    code, title = MODULES[index]
    return {'key': code, 'title': title, 'summary': details, 'records': list(records), 'errors': list(issues)}


def rows_for(plan, scored, vectors):
    by_key = {item.key: item for item in scored}
    factor_names = ('双色偏差模长', '密版套准漂移', '纸张水分偏离', '油墨与版面交互', '通道相对色偏')
    order = []
    for job in plan.jobs:
        point = by_key[job.key]
        if len(point.contributions) == len(factor_names):
            reasons = sorted(zip(factor_names, point.contributions, strict=True), key=lambda val: (-abs(val[1]), val[0]))
            driver = ' · '.join(f'{key} {amount:+.2f}' for key, amount in reasons[:2])
        else:
            driver = ' · '.join(f'{amount:+.2f}' for amount in point.contributions)
        interval = ('–' if job.lower is None else f'{job.lower:.2f}–{job.upper:.2f}')
        order.append({'key': job.key, 'zone': job.cohort, 'estimate': job.estimate, 'interval': interval,
                      'state': job.state, 'cost': job.cost, 'reason': job.reason, 'evidence': job.summary,
                      'drivers': driver, 'missing': len(point.missing), 'hits': list(job.rule_hits),
                      'measurements': dict(zip(('cyan_shift', 'magenta_shift', 'register_um', 'moisture', 'ink_c', 'image_blocks'), point.input_values, strict=True)),
                      'unmeasured': list(point.missing), 'operations': feature_service.business_factors(vectors[job.key])})
    return order


def comparison_rows(predictions):
    return [{'单号': point.key, '分组': point.cohort, '原始估计': round(point.score, 4),
             '补值字段': len(point.missing), '偏离特征': '、'.join(point.excursions) or '—'}
            for point in predictions[:14]]


def replay_metrics(report):
    result = [{'label': '回放实绩样本', 'value': report.count}, {'label': '回放绝对误差', 'value': report.mae}]
    return result


def worksheet(documents, as_of):
    if type(as_of)!=int or as_of < 91 or as_of > 3650:
        raise ValueError('工日参数必须为 91–3650')
    if not isinstance(documents, (tuple,list)) or len(documents)==0 or len(documents)>2500:
        raise ValueError('需要有效的单据列表，最多 2500 行')
    base = intake_service.load_samples(documents,as_of)
    rule = window_contract.WindowRule.standard(allow_censor=False)
    release = cohort_service.build_windows(base.entries,replace(rule,as_of=as_of))
    cohort_service.model_inputs(release)
    stat = feature_service.fit_features(release.train)
    return base,release,stat


def calibrate_cell(source, oversight):
    frame = oversight.fingerprint
    parameters = model_service.fit_model(source.train,frame)
    verified = calibration_service.prepare_verification(model_service.predict(parameters,source.calibration,frame))
    output = []
    for label, slice_ in (('replay',source.replay),('live',source.live)):
        forecasts = model_service.predict(parameters,slice_,frame)
        output.append((forecasts,calibration_service.validate_predictions(forecasts,verified)))
    return parameters,verified,output


def execute(documents, capacity=12, mode='balanced', *, as_of=96):
    intake, windows, state = worksheet(documents,as_of)
    features = feature_service.transform_windows(windows,state)
    kernel, fitted_calibration, (recent, shift) = calibrate_cell(features, state)
    evaluated = recent[1]
    scored, checked_live = shift
    previous=monitor_service.fit_baseline(features.train,state.fingerprint)
    drift=monitor_service.scan_current(previous,features.live,state.fingerprint)
    coverage=monitor_service.coverage_by_group(features.calibration,features.live)
    allocation=dispatch_service.plan_jobs(checked_live,drift.domain,capacity,mode)
    closed=audit_service.close_batch(documents,intake,windows,allocation,state.fingerprint,kernel.name,mode)
    performance=calibration_service.performance(evaluated)
    states = dict(closed.totals.states)
    overview = [
        {'label': '当班色样票', 'value': len(allocation.jobs)},
        {'label': '已分派', 'value': states.get('已分派', 0)},
        {'label': '候补', 'value': states.get('候补', 0)},
        {'label': '暂停及人工判读', 'value': states.get('暂停', 0) + states.get('人工判读', 0)},
        {'label': '额度结余', 'value': allocation.balance},
    ]
    vectors = {item.key: item for item in features.live}
    row_list = rows_for(allocation, scored, vectors)
    operating_rows = dispatch_service.operating_ledger(row_list)
    overtime = calibration_service.boundary_diagnostics(evaluated, 0.51)
    sector = calibration_service.sector_replay(evaluated, 0.51)
    operating_shift = monitor_service.shop_floor_shift(features.train, features.live)
    field_evidence = audit_service.sign_field_evidence(row_list, allocation)
    features_glance = feature_service.feature_evidence(state) + feature_service.measure_review(features)
    weight_rows = [{'量测': key, '取值': value} for key, value in kernel.evidence]
    ignored = [issue.evidence() for issue in intake.issues]
    details = [
        stage_at(0, f'接收 {intake.source_rows} 条，采用 {len(intake.entries)} 条', intake_service.preliminary_evidence(intake), ignored),
        stage_at(1, f'拟合 {len(windows.train)} 条，校准 {len(windows.calibration)} 条，回放 {len(windows.replay)} 条', cohort_service.window_evidence(windows) + cohort_service.readiness_evidence(windows, as_of)),
        stage_at(2, '特征转换版本 ' + state.fingerprint, features_glance),
        stage_at(3, kernel.name, weight_rows + model_service.inspection_rows(kernel, features) + comparison_rows(scored)),
        stage_at(4, f'{fitted_calibration.method} · {performance.status} · {performance.count} 条回放实绩', calibration_service.calibration_evidence(performance) + [overtime] + sector),
        stage_at(5, f'{drift.status} · {len(drift.domain)} 张单据需外推判读', monitor_service.shift_evidence(drift, coverage) + operating_shift),
        stage_at(6, f'本班占用 {allocation.capacity-allocation.balance} / {allocation.capacity} 个工位单位', dispatch_service.action_evidence(allocation) + dispatch_service.operating_group(checked_live, allocation)),
        stage_at(7, f'处置凭证 {closed.stamp} · 额度守恒', audit_service.reconciliation_evidence(closed) + field_evidence['执行业务单']),
    ]
    details[6]['operating_rows'] = operating_rows
    details[6]['operating_title'] = '色块复检安排'
    points = [{'label': row['key'], 'value': row['estimate'], 'state': row['state'], 'zone': row['zone'],
               'upper': row['interval'], 'cost': row['cost']} for row in sorted(row_list, key=lambda row: row['key'])]
    def estimate(vector):
        return calibration_service.check_point(model_service.predict_one(kernel, vector), fitted_calibration).estimate

    # Compare interventions against frozen features, model and calibration;
    # scenario estimates never overwrite the base ticket or its decision.
    for row in row_list:
        current = vectors[row['key']]
        row['alternatives'] = feature_service.render_interventions(current, state, estimate)
        row['joint_experiments'] = feature_service.render_joint_experiments(current,state,estimate)
    details[7]['records'].extend(audit_service.site_checklist(row_list))
    details[7]['records'].extend(audit_service.intervention_summary(row_list))
    overview_report = {'capacity' : capacity, 'mode': mode, 'as_of': as_of, 'sample_hash': closed.batch_hash,
              'policy_hash': closed.policy_hash, 'feature_stamp': state.fingerprint,
              'model': kernel.name, 'run_id': closed.stamp, 'object_name': DISPLAY['object_name'],
              'unit': DISPLAY['unit'], 'sections': details, 'flow_counts': list(states.items()),
              'measures': {'cyan_shift': ('青版密度偏差', '0.01D'),
 'magenta_shift': ('品红密度偏差', '0.01D'),
 'register_um': ('套准偏差', 'μm'),
 'moisture': ('纸张含水率', '0.1%'),
 'ink_c': ('油墨温度', '℃'),
 'image_blocks': ('版面高密度块', '块')}, 'metrics': overview, 'performance': replay_metrics(performance), 'rows': row_list, 'series': points}
    return overview_report


def preview(capacity=12, mode='balanced'):
    fixture = open_fixture()
    return execute(fixture['records'], capacity, mode, as_of=fixture['as_of'])
