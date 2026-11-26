# 彩盒签样复检验证目录

AI/ML · 传统ML · 中型

修改业务链路时先检查受影响模块的测试，再运行整套 `pytest`。回归记录须能够定位到具体单据或计算值。

## 功能模块

| 编号 | 功能 | 核对内容 | 核心文件 | 独立测试 |
|---|---|---|---|---|
| M1 | 色样票 | 单据版次与隔离 | `src/proofswatch/print_tickets/service.py` | `tests/test_print_tickets.py` |
| M2 | 印刷班次 | 截止日和成熟标签 | `src/proofswatch/press_shifts/service.py` | `tests/test_press_shifts.py` |
| M3 | 颜料因素 | 原始数据到特征 | `src/proofswatch/pigment_context/service.py` | `tests/test_pigment_context.py` |
| M4 | 签样分类 | 训练及可重复推断 | `src/proofswatch/proof_bayes/service.py` | `tests/test_proof_bayes.py` |
| M5 | 色样核验 | 回放误差及可信区间 | `src/proofswatch/impression_reliability/service.py` | `tests/test_impression_reliability.py` |
| M6 | 基材变化 | 差异定位和外推审查 | `src/proofswatch/supplier_cast/service.py` | `tests/test_supplier_cast.py` |
| M7 | 复扫分派 | 硬规则与额度分配 | `src/proofswatch/swatch_rescan/service.py` | `tests/test_swatch_rescan.py` |
| M8 | 签样落款 | 单据及额度证据 | `src/proofswatch/signoff_slip/service.py` | `tests/test_signoff_slip.py` |

## 深度登记

| 编号 | 边界 | 判断 | 处理位置 | 测试定位 |
|---|---|---|---|---|
| TRAP-14 | 同版不同读数 | 两条都隔离，换序结论一致 | `src/proofswatch/print_tickets/service.py` | `tests/test_print_tickets.py::test_conflicting_same_version_is_order_independent` |
| TRAP-19 | 多个规则或外推标记重叠 | 硬约束优先，保留全部命中码 | `src/proofswatch/swatch_rescan/service.py` | `tests/test_swatch_rescan.py::test_hard_rule_precedes_outside_reference` |
| TRAP-23 | 标签落在窗口的终点 | 终点进入隔离段，窗口为半开区间 | `src/proofswatch/press_shifts/service.py` | `tests/test_press_shifts.py::test_half_open_days` |
| TRAP-32 | 大偏移细方差与常数列 | 中心化后累加，常数列尺度为一 | `src/proofswatch/pigment_context/service.py` | `tests/test_pigment_context.py::test_cancellation_safe_scaling` |
| TRAP-42 | 拟合窗口后才回传结果 | 依标签成熟时间屏蔽，未来数据不参与拟合 | `src/proofswatch/press_shifts/service.py` | `tests/test_press_shifts.py::test_mature_label_cannot_cross_partition` |
| TRAP-43 | 回放没有成熟记录 | 记录未定义状态，避免以零误差替代 | `src/proofswatch/impression_reliability/service.py` | `tests/test_impression_reliability.py::test_no_outcome_gets_undefined_metrics` |
| TRAP-44 | 校准样本不足 | 分派前转人工判读并保留原因 | `src/proofswatch/impression_reliability/service.py` | `tests/test_impression_reliability.py::test_empty_calibration_requires_review` |
| TRAP-53 | 单条推断与混批 | 复用冻结参数，各条估计完全一致 | `src/proofswatch/proof_bayes/service.py` | `tests/test_proof_bayes.py::test_input_batch_invariance` |
| TRAP-54 | 特征版本与模型不配对 | 拒绝继续推断并要求重拟合 | `src/proofswatch/proof_bayes/service.py` | `tests/test_proof_bayes.py::test_mismatched_model_input_version_fails` |
