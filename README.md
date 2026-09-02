# Evolution Grammar — Live Track

**本仓库是一个时间戳存证（timestamp registry）**

我们公开注册一组对未来的预测，用 GitHub 的提交时间作为不可篡改的时间证明，
然后在预测期结束后用公开数据对账。仓库中**不包含任何源代码**，只有预测结果。

## 注册内容（v1，冻结于 2026-08-31）

- **数据截止**：2026-08-01（Nextstrain ncov open 全球元数据快照）
- **预测窗口**：2026-09-01 至 2027-02-28
- **任务**：预测窗口内将**首次出现**的 SARS-CoV-2 RBD（刺突蛋白受体结合域，331-531 位点）单突变
- **候选池**：3,678 个截止前尚未出现的单突变
- **系统**：v3_linear（语法特征线性提案器）与 v3_lm（+ 因子化事件流语言模型）
- **主指标**：hit@10、hit@50、auc、auc_strict（流行度 ≥5 过滤）

## 文件（v1）

| 文件 | 内容 |
| --- | --- |
| `eval_protocol_v1.json` | 评分协议（口径、指标、对账规则、数据来源） |
| `predictions_v1_v3_linear.csv` | 全部 3,678 个候选的线性系统评分（含排名标记） |
| `predictions_v1_v3_lm.csv` | 神经增强系统的全量评分 |
| `predictions_v1_summary.json` | 两个系统的 top-10 / top-50 提名清单 |

## 注册内容（v2 追加，冻结于 2026-09-02）

按 v1 协议"更正只以追加版本发布"，在**同一数据截止、同一候选池、同一预测窗口**上追加注册收编前沿方法后的系统。v1 注册于方法收编之前，v2 收编之后——2027-03 对账时 v1 与 v2 在同一窗口上构成受控对比。

- **主系统 `bloom_esc`**：语法三特征 + z(bloom mut-fitness) + z(evescape) 线性融合（回测 auc_strict 0.939，历史最优）
- **`bloom_full`**：bloom_esc + 自有因子化事件流语言模型（evoLM-v2）
- **`v3_lm` / `v3_linear`**：v1 系统同种子复现（top50 与 v1 重合 50/50，注册可复现性验证）
- **`bloom_zeroshot`**：文献口径零样本排序（参考）

| 文件 | 内容 |
| --- | --- |
| `eval_protocol_v2.json` | v2 评分协议（系统定义、与 v1 的关系、对账规则） |
| `predictions_v2_bloom_esc.csv` | 主系统全量评分（3,678 候选） |
| `predictions_v2_bloom_full.csv` / `predictions_v2_v3_lm.csv` / `predictions_v2_v3_linear.csv` | 其余系统全量评分 |
| `predictions_v2_bloom_zeroshot.csv` | 零样本参考排序 |
| `predictions_v2_summary.json` | 各系统 top-10 / top-50 提名清单 |

## 规则

2027-03-01 起，用同期 Nextstrain ncov open 新快照重算"窗口内首次出现"的突变集合，
对照本仓库的 `in_top10` / `in_top50` 标记公布命中结果。第三方可用全量评分文件独立复算。
注册后本仓库内容不再修改；任何更正只以追加版本（v3, v4…）的方式发布。

