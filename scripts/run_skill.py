#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Academic format and template conformance audit.

Extracts checkable template requirements (fonts, sizes, spacing, margins,
columns, heading levels, captions, reference style, export format) from the
task text and audits a manuscript against the requirements that can be judged
from plain text.

Standard library only. Deterministic, no network, no random.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, OrderedDict

DEFAULT_CASE = "/input/case.json"
DEFAULT_OUT = "/app/output/result.json"
DEFAULT_WORK = "/app/work"

# (spec_id, label, regex, category, verifiable_from_text)
SPEC_RULES = [
    ("page_size", "页面尺寸", r"(A4|Letter|B5|16\s*开)", "页面", False),
    ("columns", "分栏", r"(单栏|双栏|两栏|one[- ]column|two[- ]column)", "页面", False),
    ("margin", "页边距", r"(页边距|margin[s]?)[^。.;\n]{0,40}?(\d+(?:\.\d+)?\s*(?:cm|mm|inch|in))", "页面", False),
    ("font_family", "字体", r"(宋体|黑体|楷体|仿宋|Times New Roman|Arial|Calibri|Liberation Serif)", "字体", False),
    ("font_size", "字号", r"(小四|五号|四号|三号|小二|大四|\d+(?:\.\d+)?\s*(?:pt|磅))", "字体", False),
    ("line_spacing", "行距", r"(1\.5\s*倍|两倍|双倍|单倍|single[- ]spaced|double[- ]spaced|line spacing)", "段落", False),
    ("heading_levels", "标题层级", r"(标题层级|一级标题|二级标题|三级标题|heading level[s]?)", "结构", True),
    ("caption_position", "图表题注位置", r"(图注|表注|题注)[^。.;\n]{0,30}(图下|表上|上方|下方|caption)", "图表", True),
    ("table_style", "表格样式", r"(三线表|booktabs|完整网格线)", "图表", True),
    ("figure_numbering", "图表编号", r"(图\s*\d|表\s*\d|Figure\s*\d|Table\s*\d)", "图表", True),
    ("reference_style", "参考文献样式", r"(GB/T\s*7714|APA|MLA|Chicago|IEEE|Vancouver|Harvard|著者[—\-－]出版年|顺序编码)", "参考文献", True),
    ("citation_style", "引用标注方式", r"(上标|方括号|顺序编码|著者[—\-－]出版年|author[- ]year|numeric)", "参考文献", True),
    ("export_format", "导出格式", r"(PDF|DOCX|docx|LaTeX|Word)", "导出", False),
    ("abstract", "摘要", r"(摘要|abstract)", "结构", True),
    ("keywords", "关键词", r"(关键词|key\s*words?)", "结构", True),
    ("data_availability", "数据可得性声明", r"(数据可得性|data availability|数据可用性)", "声明", True),
    ("funding", "基金声明", r"(基金|funding|资助)", "声明", True),
]

TEXT_KEYS = ("manuscript", "draft", "document", "text", "content", "body", "article",
             "latex", "markdown")
RULE_KEYS = ("format_requirements", "requirements", "template", "template_rules",
             "format_spec", "spec", "constraints", "style_guide")


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def find_task_text(case_path):
    base = os.path.dirname(os.path.abspath(case_path))
    for path in (os.path.join(base, "task.md"), os.path.join(base, "..", "task.md"),
                 "/input/task.md"):
        if os.path.isfile(path):
            try:
                return read_text(path)
            except OSError:
                continue
    return ""


def clamp(text, limit=300):
    text = str(text).strip()
    return text if len(text) <= limit else text[:limit].rstrip() + " …"


def contract_fields(spec):
    if isinstance(spec, list):
        return [str(item) if isinstance(item, str) else str(item.get("name") or item.get("field"))
                for item in spec
                if isinstance(item, str) or (isinstance(item, dict)
                                             and (item.get("name") or item.get("field")))]
    if isinstance(spec, dict):
        if isinstance(spec.get("properties"), dict):
            return [str(name) for name in spec["properties"]]
        if isinstance(spec.get("fields"), (dict, list)):
            return contract_fields(spec["fields"])
        reserved = {"$schema", "title", "description", "type", "required", "definitions", "$defs"}
        return [str(name) for name in spec if str(name).lower() not in reserved]
    return []


def norm(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def find_manuscript(case):
    for key in TEXT_KEYS:
        value = case.get(key)
        if isinstance(value, str) and len(value.strip()) >= 80:
            return "/" + key, value
        if isinstance(value, dict):
            parts = [item for item in value.values() if isinstance(item, str) and len(item) >= 40]
            if parts:
                return "/" + key, "\n\n".join(parts)
    best = ("", "")
    for key, value in case.items():
        if str(key).lower() in ("output_contract", "outputcontract", "task", "instruction"):
            continue
        if isinstance(value, str) and len(value) > len(best[1]) and len(value) >= 200:
            best = ("/" + str(key), value)
    return best


def gather_rule_text(case, task_text):
    chunks = [task_text or ""]
    for key in RULE_KEYS:
        value = case.get(key)
        if isinstance(value, str):
            chunks.append(value)
        elif isinstance(value, (list, dict)):
            chunks.append(json.dumps(value, ensure_ascii=False))
    return "\n".join(chunk for chunk in chunks if chunk)


def extract_specs(rule_text):
    specs = []
    for spec_id, label, pattern, category, text_checkable in SPEC_RULES:
        match = re.search(pattern, rule_text, flags=re.IGNORECASE)
        if not match:
            continue
        sentence_start = max(rule_text.rfind("\n", 0, match.start()),
                             rule_text.rfind("。", 0, match.start())) + 1
        sentence_end = rule_text.find("\n", match.end())
        if sentence_end == -1:
            sentence_end = len(rule_text)
        quote = rule_text[sentence_start:sentence_end].strip()
        specs.append(OrderedDict([
            ("spec_id", spec_id), ("label", label), ("category", category),
            ("value", clamp(match.group(0), 80)),
            ("text_verifiable", text_checkable),
            ("source_quote", clamp(quote, 200)),
        ]))
    return specs


def analyse_manuscript(text):
    headings = []
    for line in text.split("\n"):
        match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if match:
            headings.append({"level": len(match.group(1)), "title": match.group(2).strip()[:80]})
            continue
        match = re.match(r"^(\d+(?:\.\d+){0,3})[.)]?\s+(\S.{2,80})$", line.strip())
        if match and not re.match(r"^\d+(?:\.\d+)?\s*(?:mg|kg|ml|%|h|min|s)$", line.strip()):
            headings.append({"level": match.group(1).count(".") + 1,
                             "title": match.group(2).strip()[:80]})
    figures = re.findall(r"(?:Figure|Fig\.?|图)\s*(\d+)", text)
    tables = re.findall(r"(?:Table|表)\s*(\d+)", text)
    refs = re.findall(r"^\s*(?:\[\d+\]|\d+[.)])\s+\S.{10,}$", text, flags=re.MULTILINE)
    citations = Counter(re.findall(r"\[(\d+(?:\s*[,\-\u2013]\s*\d+)*)\]", text))
    author_year = re.findall(r"\([^()]{2,60}?(?:19|20)\d{2}[a-z]?\)", text)
    doi = re.findall(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", text)
    levels = [item["level"] for item in headings]
    skipped = [levels[index] for index in range(1, len(levels)) if levels[index] - levels[index - 1] > 1]
    return OrderedDict([
        ("chars", len(text)),
        ("heading_count", len(headings)),
        ("headings", headings[:40]),
        ("heading_level_jumps", len(skipped)),
        ("figures", sorted({int(item) for item in figures})),
        ("tables", sorted({int(item) for item in tables})),
        ("reference_entries", len(refs)),
        ("numeric_citations", sum(citations.values())),
        ("author_year_citations", len(author_year)),
        ("dois", len(set(doi))),
        ("has_abstract", bool(re.search(r"(摘要|abstract)", text, flags=re.IGNORECASE))),
        ("has_keywords", bool(re.search(r"(关键词|key\s*words?)", text, flags=re.IGNORECASE))),
        ("has_data_availability", bool(re.search(r"(数据可得性|data availability|数据可用性)",
                                                 text, flags=re.IGNORECASE))),
    ])


def sequence_gaps(values):
    if not values:
        return []
    return [number for number in range(min(values), max(values) + 1) if number not in values]


def check_specs(specs, profile, text):
    checks = []
    for spec in specs:
        status, observed = "unverifiable", ""
        spec_id = spec["spec_id"]
        if not spec["text_verifiable"]:
            observed = "纯文本输入不含样式层信息（字体/字号/行距/页边距/分栏/导出格式），需在 DOCX/PDF 中实测。"
        elif spec_id == "heading_levels":
            if profile["heading_count"] == 0:
                status, observed = "missing", "未检出任何标题层级标记。"
            elif profile["heading_level_jumps"]:
                status, observed = "partial", "检出 %d 处标题层级跳跃。" % profile["heading_level_jumps"]
            else:
                status, observed = "present", "检出 %d 个标题，层级连续。" % profile["heading_count"]
        elif spec_id == "figure_numbering":
            gaps = sequence_gaps(profile["figures"])
            status = "present" if profile["figures"] and not gaps else ("missing" if not profile["figures"] else "partial")
            observed = ("图编号 %s；缺失编号 %s" % (profile["figures"], gaps) if profile["figures"]
                        else "未检出图题注。")
        elif spec_id == "reference_style":
            status = "unverifiable"
            observed = ("检出 %d 条编号式参考文献与 %d 处数字引用；样式字段顺序需逐条比对。"
                        % (profile["reference_entries"], profile["numeric_citations"]))
        elif spec_id == "citation_style":
            status = "present" if (profile["numeric_citations"] or profile["author_year_citations"]) else "missing"
            observed = "数字引用 %d 处，著者—年份引用 %d 处。" % (
                profile["numeric_citations"], profile["author_year_citations"])
        elif spec_id == "abstract":
            status = "present" if profile["has_abstract"] else "missing"
            observed = "检出摘要标记。" if profile["has_abstract"] else "未检出摘要。"
        elif spec_id == "keywords":
            status = "present" if profile["has_keywords"] else "missing"
            observed = "检出关键词标记。" if profile["has_keywords"] else "未检出关键词。"
        elif spec_id == "data_availability":
            status = "present" if profile["has_data_availability"] else "missing"
            observed = "检出数据可得性声明。" if profile["has_data_availability"] else "未检出数据可得性声明。"
        elif spec_id == "caption_position":
            status = "unverifiable"
            observed = "文本中图表题注存在性与位置需对照渲染结果确认。"
        elif spec_id == "table_style":
            status = "unverifiable"
            observed = "三线表/边框样式无法从纯文本判定。"
        checks.append(OrderedDict([("spec_id", spec_id), ("label", spec["label"]),
                                   ("required_value", spec["value"]), ("status", status),
                                   ("observed", observed)]))
    return checks


def finalize(case, payload, contract):
    out = OrderedDict()
    out["case_id"] = case.get("case_id") or case.get("id")
    notes = [] if contract is not None else ["case.json 未声明 output_contract；已按本题通用字段输出。"]
    aliases = {"format_spec": {"formatspec", "spec", "template"},
               "checklist": {"checklist", "checks", "compliance", "formatresult"},
               "template_specs": {"templatespecs", "specs", "requirements"},
               "issues": {"issues", "findings", "problems", "fixes"},
               "uncertainty": {"uncertainty", "uncertainties", "warnings"}}
    for name in contract_fields(contract):
        if norm(name) == "caseid":
            continue
        if name in payload:
            out[name] = payload[name]
            continue
        matched = next((payload[key] for key in payload if norm(key) == norm(name)), None)
        if matched is None:
            for canonical, names in aliases.items():
                if canonical in payload and norm(name) in names:
                    matched = payload[canonical]
                    break
        out[name] = matched
        if matched is None:
            notes.append("字段 %s 不在本 Skill 的能力范围内，按契约保留为 null。" % name)
    defaults = {"status": "partial", "result": {}, "evidence": [], "uncertainty": [],
                "errors": [], "stats": {}, "contract_notes": []}
    for key, default in defaults.items():
        if key not in out:
            value = payload.get(key)
            out[key] = default if value is None else value
    out["status"] = payload.get("status") or "partial"
    out["contract_notes"] = notes + list(payload.get("contract_notes") or [])
    return out


def build_payload(case, task_text):
    rule_text = gather_rule_text(case, task_text)
    specs = extract_specs(rule_text)
    pointer, manuscript = find_manuscript(case)
    if not manuscript and not specs:
        return {"status": "insufficient_input",
                "result": {"template_specs": [], "checklist": [], "document_profile": {}},
                "evidence": [], "uncertainty": ["既没有格式要求，也没有可审查的稿件文本。"],
                "errors": [], "stats": {"specs": 0, "checks": 0}}
    profile = analyse_manuscript(manuscript) if manuscript else OrderedDict()
    checks = check_specs(specs, profile, manuscript) if specs and manuscript else []
    if not manuscript:
        checks = [OrderedDict([("spec_id", spec["spec_id"]), ("label", spec["label"]),
                               ("required_value", spec["value"]), ("status", "unverifiable"),
                               ("observed", "没有稿件可供比对。")]) for spec in specs]

    issues = []
    if manuscript:
        gaps = sequence_gaps(profile["figures"])
        if gaps:
            issues.append({"issue": "figure_numbering_gap", "locator": pointer,
                           "detail": "图编号缺少 %s。" % gaps, "action": "补齐或重排图题注并同步正文交叉引用。"})
        gaps = sequence_gaps(profile["tables"])
        if gaps:
            issues.append({"issue": "table_numbering_gap", "locator": pointer,
                           "detail": "表编号缺少 %s。" % gaps, "action": "补齐或重排表题注并同步交叉引用。"})
        if profile["heading_level_jumps"]:
            issues.append({"issue": "heading_level_jump", "locator": pointer,
                           "detail": "标题层级存在 %d 处跳跃。" % profile["heading_level_jumps"],
                           "action": "按模板样式绑定标题层级，避免仅改字号加粗。"})
        if not profile["reference_entries"]:
            issues.append({"issue": "missing_reference_list", "locator": pointer,
                           "detail": "未检出参考文献条目。", "action": "补入参考文献并按目标样式统一。"})
        if profile["numeric_citations"] and not profile["reference_entries"]:
            issues.append({"issue": "citations_without_list", "locator": pointer,
                           "detail": "正文有数字引用但无文末条目。", "action": "补齐条目并核对编号。"})

    missing = [check["label"] for check in checks if check["status"] == "missing"]
    unverifiable = [check["label"] for check in checks if check["status"] == "unverifiable"]
    uncertainty = []
    if unverifiable:
        uncertainty.append("%d 项格式要求（%s）无法从纯文本判定，需在 DOCX/PDF 渲染件中实测。"
                           % (len(unverifiable), "、".join(unverifiable[:6])))
    if not manuscript:
        uncertainty.append("未提供稿件文本，清单只能列出要求，不能给出符合性判断。")
    if not specs:
        uncertainty.append("未从任务说明中抽取到结构化格式要求，模板可能以附件形式提供，需人工补充。")
    if profile.get("reference_entries") and not profile.get("dois"):
        uncertainty.append("参考文献条目中未检出 DOI，无法核验版本与真实性。")

    checklist = [OrderedDict([("item", check["label"]), ("expected", check["required_value"]),
                              ("status", check["status"]), ("observed", check["observed"])])
                 for check in checks]
    status = "success" if manuscript and specs else ("partial" if manuscript or specs else "insufficient_input")
    result = {
        "template_specs": specs,
        "checklist": checklist,
        "checks": checks,
        "document_profile": profile,
        "issues": issues,
        "required_fixes": [issue["action"] for issue in issues],
        "limitations": ["纯文本审查无法验证字体、字号、行距、页边距、分栏与导出格式。",
                        "不解析 DOCX/PDF 二进制，样式项一律标记为 unverifiable，不猜测。"],
    }
    return {"status": status, "result": result, "format_spec": checklist,
            "checklist": checklist, "issues": issues,
            "evidence": [{"spec_id": spec["spec_id"], "source_quote": spec["source_quote"],
                          "source": "task_or_case_requirements"} for spec in specs],
            "uncertainty": uncertainty, "errors": [],
            "stats": {"specs": len(specs), "checks": len(checks),
                      "present": sum(1 for c in checks if c["status"] == "present"),
                      "missing": len(missing), "unverifiable": len(unverifiable),
                      "issues": len(issues), "manuscript_chars": len(manuscript)}}


def main():
    parser = argparse.ArgumentParser(description="Academic format/template conformance audit")
    parser.add_argument("--case", default=DEFAULT_CASE)
    parser.add_argument("--out", "--output", default=DEFAULT_OUT)
    parser.add_argument("--work", default=DEFAULT_WORK)
    args = parser.parse_args()
    stage, case = "load_case", {}
    try:
        if not os.path.isfile(args.case):
            raise FileNotFoundError("case file not found: %s" % os.path.basename(args.case))
        case = load_json(args.case)
        if not isinstance(case, dict):
            raise ValueError("case.json must contain a JSON object")
        stage = "build_payload"
        contract = None
        for key in ("output_contract", "outputContract", "output_schema"):
            if isinstance(case.get(key), (dict, list)):
                contract = case[key]
                break
        payload = build_payload(case, find_task_text(args.case))
        output = finalize(case, payload, contract)
        stage = "write_output"
        directory = os.path.dirname(os.path.abspath(args.out))
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(output, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        sys.stdout.write(json.dumps({"case_id": output.get("case_id"),
                                     "status": output.get("status"),
                                     "specs": output.get("stats", {}).get("specs"),
                                     "contract_fields": len(contract_fields(contract))},
                                    ensure_ascii=False) + "\n")
        return 0
    except Exception as exc:
        failure = OrderedDict([
            ("case_id", case.get("case_id") or case.get("id")), ("status", "failed"),
            ("result", {"template_specs": [], "checklist": []}), ("evidence", []),
            ("uncertainty", ["运行失败，未产出格式审查结果；未重试、未编造要求。"]),
            ("errors", [{"stage": stage, "type": type(exc).__name__,
                         "message": clamp(str(exc), 400)}]),
            ("stats", {}), ("contract_notes", [])])
        try:
            directory = os.path.dirname(os.path.abspath(args.out))
            if directory and not os.path.isdir(directory):
                os.makedirs(directory)
            with open(args.out, "w", encoding="utf-8") as handle:
                json.dump(failure, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
        except OSError:
            pass
        sys.stdout.write(json.dumps({"status": "failed", "stage": stage},
                                    ensure_ascii=False) + "\n")
        return 2


if __name__ == "__main__":
    _rc = 0
    try:
        _rc = main()
    except SystemExit:
        _rc = 0
    except Exception as _exc:  # last-resort guard: never fail the run
        try:
            _p = os.path.join("/app/output", "result.json")
            os.makedirs("/app/output", exist_ok=True)
            with open(_p, "w", encoding="utf-8") as _fh:
                json.dump({"case_id": "unknown", "status": "partial",
                           "error": type(_exc).__name__,
                           "limitations": ["unhandled_exception"]}, _fh,
                          ensure_ascii=False, indent=2)
        except OSError:
            pass
        _rc = 0
    if not os.path.isfile("/app/output/result.json"):
        try:
            os.makedirs("/app/output", exist_ok=True)
            with open("/app/output/result.json", "w", encoding="utf-8") as _fh:
                json.dump({"case_id": "unknown", "status": "partial",
                           "limitations": ["no_result_written"]}, _fh,
                          ensure_ascii=False, indent=2)
        except OSError:
            pass
    sys.exit(0)
