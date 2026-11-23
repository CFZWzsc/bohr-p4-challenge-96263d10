---
name: academic-template-conformance
description: Extract itemised formatting requirements from a journal or thesis template, audit and text-level fix a manuscript (heading hierarchy, numbering, captions, reference entries) for conformance, inventory content units, and report per-item evidence with locators in /app/output/result.json. Use when a task asks whether and how a paper should be adapted to a submission template.
---

# 学术格式与模板适配审查

## 用途与适用条件

从任务说明或模板文本中抽取**可逐项核对**的格式要求，形成检查清单；对稿件逐项判定，并把文本层能改的项直接落到可编辑稿 `adapted_manuscript`。

适用：

- 任务是“按目标模板检查/适配稿件”，模板要求以文字形式给出。
- 需要一份可复核的 checklist，以及每项的证据、定位与状态。
- 需要区分“已符合 / 缺失 / 文本无法判定”三类结论，并交付可编辑改稿。

不适用：没有渲染件时改写 DOCX 二进制样式、嵌入字体或生成目录——这些项标 `unverifiable` 并给出实测命令，不凭经验猜测合规。

## 输入

| 输入 | 位置 | 说明 |
|-|-|-|
| `case.json` | `/input/case.json`（`--case` 可覆盖） | 稿件取自 `manuscript` / `draft` / `document` / `text` / `content` / `latex`；格式要求取自 `format_requirements` / `requirements` / `template` / `spec` |
| `task.md` | `/input/task.md`（自动探测） | 模板条款的主要来源 |
| 输出 | `/app/output/result.json`（`--out` 可覆盖） | 结构化结果 |

## 处理流程

1. **要求抽取**（认得准）：用 17 类规则匹配模板条款——页面尺寸、分栏、页边距、字体、字号、行距、标题层级、题注位置、三线表、图表编号、参考文献样式、引用方式、导出格式、摘要、关键词、数据可得性、基金声明。每项保留原文引句；相互冲突的规定写入 `template_conflicts`。
2. **稿件画像与内容单元**（转得全）：解析标题层级与 `1.2.3` 编号，统计层级跳跃；抽取图表编号、编号式文献、数字/著者—年份引用与 DOI；清点图、表、公式、脚注、批注、修订、域代码、目录等 `content_units` 及其保真状态。
3. **逐项判定**（排得对）：文本可判定的项给 `present` / `partial` / `missing` 并附 `locator`；字体、字号、行距、页边距、分栏、导出等纯样式项一律 `unverifiable`，说明需渲染件实测。
4. **文本层修复**（交得出）：标题层级、编号断号、题注位置、参考文献条目顺序等在 `adapted_manuscript` 中实际改好，未涉及段落保持原文；每处改动写入 `applied_changes`（`before`/`after`/`rule`/`locator`）。禁止只给建议而不落稿。
5. **问题与必改项**：`issues` 每条带 `locator`、`detail`、`action`、`priority`；`required_fixes` 按优先级给出可执行动作。
6. **边界标注**：不可判定项、模板冲突、无稿件、无要求分别写入 `uncertainty` 或 `needs_human_confirmation`。

## 输出契约

| 字段 | 类型 | 含义 | 示例（合成） |
|---|---|---|---|
| `case_id` | string | 原样保留 | `"case-x"` |
| `status` | enum | `success/partial/insufficient_input/failed` | `"partial"` |
| `result.template_specs` | array | 条款：`spec_id/label/value/source_quote/text_verifiable` | `{"spec_id":"font_size","value":"小四","source_quote":"正文宋体小四"}` |
| `result.template_conflicts` | array | 冲突或版本差异条款及处理 | `{"clause_a":"双栏","clause_b":"单栏","status":"unresolved"}` |
| `result.checklist` | array | 每项含 `item/expected/status/locator/observed/source_quote` | `{"item":"标题层级","status":"partial","locator":"manuscript L3-L18"}` |
| `result.checks` / `document_profile` | array/object | 判定明细与稿件统计 | `{"heading_level_jumps":2}` |
| `result.content_units` | array | 内容单元及保真状态 `preserved/altered/missing/not_present` | `{"unit":"Table 1","status":"preserved","locator":"L42-L47"}` |
| `result.adapted_manuscript` | string | 文本层改好的可编辑稿；未改段落逐字保留 | `"# 1 引言\n…"` |
| `result.applied_changes` | array | 每处改动的前后文与依据 | `{"locator":"L17","before":"### 1.1","after":"## 1.1","rule":"heading_levels"}` |
| `result.issues` | array | `issue/locator/detail/action/priority` | `{"issue":"figure_numbering_gap","locator":"L40","priority":"high"}` |
| `result.required_fixes` / `needs_human_confirmation` | array | 必改动作；需作者确认项 | `{"item":"字体无法从文本判定","reason":"需 DOCX/PDF 实测"}` |
| 顶层 `evidence` | array | 要求来源：`spec_id/source_quote` | `{"spec_id":"font_size","source_quote":"…"}` |
| `output_contract` 各字段 | 保留 | 每个字段名都存在；无法产出置 `null` 并记 `contract_notes` | — |

## 异常处理

| 情况 | 处置 | status |
|-|-|-|
| `case.json` 缺失/非法 | 结构化失败，标注阶段，退出码 2 | `failed` |
| 只有模板要求、无稿件 | 列出要求，检查项全部 `unverifiable` | `partial` |
| 只有稿件、无要求 | 输出稿件画像，说明缺模板 | `partial` |
| 两者皆无 | 不产出清单，说明缺什么 | `insufficient_input` |
| 字体/字号/页边距等样式项 | 标 `unverifiable`，要求渲染件实测 | 原状态 |
| 模板条款相互冲突 | 两条都保留，写入 `template_conflicts` | 原状态 |

## 限制

- 只对纯文本可判定项做出合规结论；不解析 DOCX/PDF，不测真实页边距、字体嵌入与目录页码。
- 条款抽取依赖关键词规则，非中文/英文条款可能漏抽。
- 编号重排只在 `adapted_manuscript` 内进行，并同步更新文内引用；原二进制文件不改写。
- 图表交叉引用是否随编号同步需在渲染件复核，未复核项标 `unverifiable`。

## 最小调用示例（示例，非官方结果）

```json
{"case_id":"demo-001","output_contract":{"checklist":"array","status":"string"},
 "format_requirements":"正文宋体小四，行距 1.5 倍；图注置于图下；参考文献按 GB/T 7714。",
 "manuscript":"# 引言\n\n### 1.1 背景\n\nFigure 1 显示结果 [1]。\n\n# 参考文献\n\n[1] Smith J. Lancet. 2020."}
```

```bash
python scripts/run_skill.py --case /input/case.json --out /app/output/result.json --work /app/work
```

示意：`status=success`；字号/行距/字体为 `unverifiable`，标题层级为 `partial`（检出跳跃），`issues` 含 `heading_level_jump`，`adapted_manuscript` 已把 `### 1.1` 改为 `## 1.1`。

## 交付与自检

1. 先执行 `python scripts/run_skill.py`（默认 `/input/case.json` → `/app/output/result.json`；`--case`、`--out`、`--output` 等价）。
2. 脚本产出 `template_specs/checklist/checks/document_profile/issues/required_fixes/evidence/stats`；调用 Agent 补齐 `template_conflicts`、`content_units`、`adapted_manuscript`、`applied_changes`、`needs_human_confirmation`。
3. 输入缺失、JSON 损坏、输出目录不存在时仍写出结构化 `result.json`；脚本正常结束时退出码为 0，失败类别以 `status` 为准。
4. 自检：`case_id` 一致；`output_contract` 每字段存在；每条判定有 `locator` 与证据；样式项未猜合规；`adapted_manuscript` 与 `applied_changes` 一一对应，无 `pending`/`TODO`。
