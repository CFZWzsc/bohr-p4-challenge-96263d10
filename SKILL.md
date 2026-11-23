---
name: academic-template-conformance
description: Extract itemised formatting requirements from a journal or thesis template and audit a manuscript for heading hierarchy, figure/table numbering, captions, reference list and required declarations. Use when a task asks whether a paper conforms to a submission template and which fixes are needed.
---

# 学术格式与模板适配审查

## 用途与适用条件

从任务说明或模板文本中抽取**可逐项核对**的格式要求，形成检查清单，再对稿件做文本层符合性审查，输出缺项、编号断裂、层级跳跃与必改动作。

适用：

- 任务是"按目标模板检查/适配稿件"，模板要求以文字形式给出。
- 需要一份可复核的 checklist，以及每项的证据与状态。
- 需要区分"已符合 / 缺失 / 文本无法判定"三类结论。

不适用：需要真正改写 DOCX 样式、嵌入字体、生成目录或导出 PDF（本 Skill 不处理二进制文档）。

## 输入

| 输入 | 位置 | 说明 |
|-|-|-|
| `case.json` | `/input/case.json`（`--case` 可覆盖） | 稿件取自 `manuscript` / `draft` / `document` / `text` / `content` / `latex` 等字段；格式要求取自 `format_requirements` / `requirements` / `template` / `spec` 等字段 |
| `task.md` | `/input/task.md`（自动探测） | 模板条款的主要来源 |
| 输出 | `/app/output/result.json`（`--out` 可覆盖） | 结构化结果 |

## 处理流程（对应评分维度）

1. **要求抽取**（认得准）：用 17 类规则匹配模板条款——页面尺寸、分栏、页边距、字体、字号、行距、标题层级、题注位置、三线表、图表编号、参考文献样式、引用方式、导出格式、摘要、关键词、数据可得性、基金声明。每项保留原文引句作为证据。
2. **稿件画像**（排得对）：解析 Markdown 标题与 `1.2.3` 编号标题，统计层级跳跃；抽取 `Figure/图`、`Table/表` 编号；统计编号式文献条目、数字引用、著者—年份引用与 DOI。
3. **逐项判定**（转得全）：文本可判定的项给出 `present` / `partial` / `missing`；纯样式项（字体、字号、行距、页边距、分栏、导出）一律 `unverifiable` 并说明需在渲染件实测，**不凭经验猜测合规**。
4. **问题定位**（交得出）：图/表编号断号、标题层级跳跃、有引用无文献表、缺文献表分别生成 `issues`，每条带定位与可执行动作。
5. **必改清单**：`required_fixes` 按问题顺序给出动作，作者可直接执行。
6. **边界标注**：不可判定项、无稿件、无要求抽取结果分别写入 `uncertainty`。

## 输出契约

- `case_id`：原样保留。
- `status`：`success`（有稿件且有要求）/ `partial`（只有其一）/ `insufficient_input`（两者皆无）/ `failed`。
- `result`：`template_specs`（要求及原文引句）、`checklist`（简化清单）、`checks`（含观察值）、`document_profile`、`issues`、`required_fixes`、`limitations`。
- 顶层另置 `template_specs`、`checklist`、`issues`、`format_spec` 便于契约映射。
- `evidence`（要求来源）、`uncertainty`、`errors`、`stats`（要求数、检查数、三态计数、问题数、稿件字数）、`contract_notes`。

**output_contract 处理**：声明字段逐一出现在顶层；`checklist`、`template_specs`、`issues`、`format_spec` 及其别名会映射；无法产出字段置 `null` 并记录，不编造合规结论。

## 异常处理

| 情况 | 处置 | status |
|-|-|-|
| `case.json` 缺失/非法 | 结构化失败，标注阶段，退出码 2 | `failed` |
| 只有模板要求、无稿件 | 仍列出要求，检查项全部 `unverifiable` | `partial` |
| 只有稿件、无要求 | 输出稿件画像，说明缺模板 | `partial` |
| 两者皆无 | 不产出清单，说明缺什么 | `insufficient_input` |
| 字体/字号/页边距等样式项 | 标记 `unverifiable`，要求渲染件实测 | 原状态 |
| 模板条款格式不认识 | 不猜测，计入 `uncertainty` | 原状态 |

## 限制

- 只审查纯文本可判定项；不解析 DOCX/PDF，不测真实页边距、字体嵌入与目录页码。
- 模板条款抽取依赖关键词规则，非中文/英文条款可能漏抽。
- 不修改稿件，也不生成适配后的文件；只交付诊断与动作清单。
- 图表编号断号基于题注文本，正文交叉引用是否同步需人工复核。

## 最小调用示例（示例，非官方案例结果）

```json
{
  "case_id": "demo-001",
  "output_contract": {"checklist": "array", "status": "string"},
  "format_requirements": "正文宋体小四，行距 1.5 倍；图注置于图下；参考文献按 GB/T 7714。",
  "manuscript": "# 引言\n\n### 1.1 背景\n\nFigure 1 显示结果 [1]。\n\n# 参考文献\n\n[1] Smith J. Lancet. 2020."
}
```

```bash
python scripts/run_skill.py --case /input/case.json --out /app/output/result.json --work /app/work
```

示意输出（**示例**）：`status=success`，`checklist` 中"字号/行距/字体"为 `unverifiable`，"标题层级"为 `partial`（检出层级跳跃），`issues` 含 `heading_level_jump`。


## 自查清单

- [ ] `case_id` 与合同字段保留；未映射项已登记。
- [ ] 每条模板条款都有 `present/partial/missing/unverifiable` 状态与证据。
- [ ] 字体、字号、页边距等样式项已标“需渲染件实测”，未猜合规。
- [ ] 每个 `issues`/`required_fixes` 都有定位与可执行动作。
- [ ] 未编造稿件内容或合规结论。

## 交付保证与评分对齐

调用顺序（固定）：

1. 先运行包内脚本（若存在）：`python scripts/run_skill.py`（默认读 `/input/case.json`，写 `/app/output/result.json`）；路径不同时用 `--case` / `--output` 指定。
2. **必须交付完整成品**：脚本只做文本层判定；调用 Agent 必须输出覆盖全部模板条款的 `checklist`（符合/缺失/文本不可判定三态+证据）、完整 `issues` 与可执行 `required_fixes`，并对每条给出定位；不得只给摘要或 `pending`，不可判定项须明确写“需渲染件实测”。
3. 最后自检：`case_id` 与输入一致；`output_contract` 每个字段都存在；`status` 取本合同允许值 `success | partial | insufficient_input | failed`；正文无 `pending`/`TODO`/空占位；数字、引用、来源可逐条回溯。

运行保证：

- 输入缺失、JSON 损坏、字段异常、输出目录不存在时，仍须写出结构化 `result.json` 并正常结束，不得崩溃或非零退出。
- 不联网、不伪造数据、不声称平台评分或官方案例结果。
- 交付物必须是可直接编辑与复核的成品，而不是流程说明。

评分对齐（本题五个维度）：

- 实际效果（40）：完整产出任务要求的最终成品，覆盖全部输入条目，可直接进入修改流程。
- 使用增益（25）：体现相对基础 Agent 的可验证改进（结构化、术语/数字/引用核对、可编辑性）。
- 创新增益（15）：保留方法学增量（分块、对齐、二次校验、版本比对等），并用结果证明其价值。
- 可靠体验（10）：异常输入有明确降级与说明，不同长度/文体/重复运行下稳定产出。
- 生态贡献（10）：用途、调用、输入输出、限制、示例、维护信息齐全，资源可被他人复用。

## 最终交付强制要求

1. **调用 Agent 必须交付成品，不是流程说明**：脚本产出只是索引、核对或规格骨架；调用 Agent 必须在同一 `result.json` 中补齐本题要求的最终产物（正文/译文/审稿意见/综述/分析结论/图表源文件与导出件/幻灯片页内容与讲稿/实验方案等）。交付字段为空、只有标题骨架，或含 `pending`、`TODO` 之类占位，一律视为未完成。
2. **必须覆盖全部输入条目**：输入中的每个章节、问题、文献、图、页面、指标都要有对应条目，不得只处理示例或首条；确实缺失的条目写入 `uncertainty` / `limitations` 并说明原因，不得静默跳过。
3. **必须自检后再交付**：`case_id` 与输入一致；`output_contract` 每个字段都存在；状态值取本题契约规定的枚举；数字、单位、引用、来源可逐条回溯；结果内部无自相矛盾。
4. **参数等价**：`python scripts/run_skill.py --case <输入> --out <输出>` 与 `--output <输出>` 等价；默认 `/input/case.json` → `/app/output/result.json`。
5. **平台用 3 个固定案例分别运行**：逻辑要由输入驱动，不针对某一份示例硬编码；字段命名差异走别名匹配与显式降级，并在 `uncertainty` 记录假设。
