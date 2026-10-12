"""Fixed presentation labels only; never translate requirement or test values."""
from __future__ import annotations


DEFAULT_LANGUAGE = "zh-CN"
SUPPORTED_LANGUAGES = {DEFAULT_LANGUAGE, "en"}


def output_language(artifact):
    language = artifact["project"].get("output_language", DEFAULT_LANGUAGE)
    if language not in SUPPORTED_LANGUAGES:
        from artifact_tools import ValidationFailure
        raise ValidationFailure(["unsupported project.output_language: " + str(language)])
    return language


# Chinese labels preserve existing workbook imports. They are presentation keys,
# not business vocabulary or project-specific requirements.
ENGLISH = {
    "测试用例":"Test Cases", "必检断言":"Required Assertions", "自动化评估":"Automation Assessment",
    "运行条件":"Runtime Requirements", "设计依据":"Design Basis", "设计复查":"Design Review", "使用说明":"Instructions",
    "用例编号":"Case ID", "模块路径":"Module Path", "用例名称":"Case Title", "优先级":"Priority", "风险":"Risk",
    "冒烟":"Smoke", "回归":"Regression", "全量":"Full", "适用目标":"Applicable Targets",
    "前置条件":"Preconditions", "测试数据":"Test Data", "操作步骤":"Actions", "步骤预期":"Step Expectations",
    "测试点编号":"Test Point IDs", "需求追溯":"Requirement References", "运行条件编号":"Runtime Requirement IDs",
    "影响":"Impact", "需确认":"Confirmation Required", "清理步骤":"Cleanup", "标签":"Tags", "备注":"Notes", "变体来源":"Variant Of",
    "断言编号":"Assertion ID", "步骤序号":"Step Numbers", "检查内容":"Check Description", "观察位置":"Observation Location",
    "预期结果":"Expected Result", "所需证据":"Required Evidence", "比较方式":"Comparison", "比较值类型":"Value Type",
    "比较值":"Comparison Value", "检查时机":"Check Timing", "判定标准":"Criteria",
    "规则编号":"Rule ID", "来源片段或确认":"Source Segments or Decisions", "模型编号":"Model ID", "方法":"Method",
    "选择依据":"Selection Rationale", "覆盖项编号":"Coverage Item ID", "维度":"Dimensions", "条件":"Condition",
    "操作":"Action", "预期":"Expected", "准备方法":"Setup", "方法数据":"Method Data", "处理":"Disposition", "排除理由":"Exclusion Reason",
    "阶段":"Phase", "复查项目":"Review Check", "问题编号":"Finding ID", "范围":"Scope", "发现":"Finding",
    "状态":"Status", "解决记录":"Resolution", "目标编号":"Target ID", "可行性":"Feasibility", "执行路线":"Execution Route",
    "原因":"Reason", "条件编号":"Requirement ID", "名称":"Name", "类型":"Type", "描述":"Description", "敏感":"Sensitive",
    "提供方式":"Collection Method", "可自动化":"Automatable", "有条件自动化":"Conditional", "人工执行":"Manual",
    "高":"High", "中":"Medium", "低":"Low", "是":"Yes", "否":"No",
    "相等":"Equals", "包含文本":"Contains Text", "数值相等":"Number Equals", "数值变化":"Number Delta",
    "列表相等(忽略顺序)":"Unordered List Equals", "前后不变":"Unchanged", "证据评判":"Evidence Review",
    "文本":"Text", "数值":"Number", "布尔":"Boolean", "列表":"List", "对象":"Object", "空值":"Null", "不适用":"Not Applicable",
    "需求与测试点":"Requirements and Test Points", "已复查":"Reviewed", "项目":"Project", "说明":"Description",
    "用例集":"Suite", "可编辑":"Editing", "步骤":"Steps", "判定":"Judgment", "设计依据与复查":"Design Basis and Review",
    "修改交接":"Edit Handoff", "稳定编号":"Stable IDs", "单元格":"Cells",
    "用例文件；共享同一基线编号。":" case file; all suites share one baseline.",
    "编辑用例业务字段、必检断言、各目标自动化评估和运行条件。模块路径和主表自动化摘要由基线生成，请在对应明细表修改。":
        "Edit case business fields, required assertions, per-target automation assessments and runtime requirements. Module paths and main-sheet automation summaries are generated; edit their corresponding detail sheets.",
    "操作步骤、步骤预期、前置条件、测试数据、清理步骤和标签采用 1.、2. 连续编号；条目内换行缩进三个空格。必检断言的步骤序号指向操作编号。多个编号或引用逐行填写。":
        "Use consecutive 1., 2. numbering for actions, expectations, preconditions, data, cleanup and tags. Indent continuation lines by three spaces. Assertion step numbers reference actions. Put multiple IDs or references on separate lines.",
    "步骤预期供阅读，必检断言是执行判定依据。修改任一预期后必须重新审查二者及测试点的一致性。":
        "Step expectations support reading; required assertions determine execution judgments. After editing an expectation, review consistency between both representations and the test points.",
    "文本和数值直接填写，布尔填是/否；仅列表和对象采用 JSON。空值及不适用留空。前后不变和证据评判的比较值类型选择不适用。检查时机必须明确，证据评判填写客观标准。":
        "Enter text and numbers directly; use Yes/No for booleans and JSON only for lists and objects. Leave Null and Not Applicable values empty. Select Not Applicable for Unchanged and Evidence Review checks. Specify timing and objective evidence-review criteria.",
    "这两张表由已确认设计生成。发现遗漏时交给 Designer 更新规则、覆盖项和 XMind，再重新导出；直接修改会被拦截。":
        "These sheets are generated from the confirmed design. Ask Designer to reconcile omissions in rules, coverage and XMind before reexporting. Direct edits are rejected.",
    "修改 Excel 后使用 import-case-workbook 读回待审清单；完成语义审查后更新基线并重新导出。执行前 validate-case-workbook 必须通过。":
        "After editing Excel, use import-case-workbook to read pending changes. Review their meaning, update the baseline and reexport. validate-case-workbook must pass before execution.",
    "保留已有用例、测试点和断言编号；新增或删除时同步各明细表。新业务规则需要更新并确认 XMind。":
        "Keep existing case, point and assertion IDs. Synchronize detail sheets when adding or removing records. New business rules require an updated and confirmed XMind.",
    "此表仅定义需要什么；实际环境和安全会话引用在运行时收集。请勿填密码、令牌或登录 cookie。":
        "This sheet defines what is needed. Actual environment and secure session references are collected at execution time. Do not enter passwords, tokens or login cookies.",
    "长内容完整保存在单元格中，可在编辑栏查看；禁止在业务单元格使用公式。":
        "Long content is retained in full and can be inspected in the formula bar. Formulas are prohibited in business cells.",
    "请从下拉列表选择值":"Choose a value from the dropdown list", "无效值":"Invalid value",
    "编号":"ID", "需求片段":"Requirement Units", "追溯":"Trace References", "自动化候选":"Automation Candidate",
    "依据":"Rationale", "业务规则":"Business Rules", "设计覆盖项":"Coverage Items", "独立检查结果":"Independent Outcome",
    "动作":"Action", "测试点":"Test Points", "草案（待确认）":"Draft (awaiting confirmation)",
    "供评审的草案，尚未成为已确认的用例或执行基线。":"Draft for review; not a confirmed case or execution baseline.",
}


class ArtifactText:
    def __init__(self, language=DEFAULT_LANGUAGE):
        self.language = output_language({"project":{"output_language":language}})

    def __call__(self, label):
        if self.language == DEFAULT_LANGUAGE:
            return label
        if label in ENGLISH:
            return ENGLISH[label]
        if any("\u3400" <= char <= "\u9fff" for char in label):
            raise ValueError("missing English artifact label: " + label)
        return label

    def labels(self, values):
        return {key:self(value) for key, value in values.items()}

    def add_table(self, workbook, name, headers, rows, widths=None, choices=None):
        from xlsx_support import add_table
        sheet = add_table(workbook, self(name), [self(h) for h in headers], rows,
            {self(k):v for k,v in (widths or {}).items()},
            {self(k):[self(v) for v in values] for k,values in (choices or {}).items()})
        for validation in sheet.data_validations.dataValidation:
            validation.error = self("请从下拉列表选择值")
            validation.errorTitle = self("无效值")
        return sheet

    def read_table(self, workbook, name, headers):
        from xlsx_support import read_table
        return [{key:row[self(key)] for key in headers}
            for row in read_table(workbook, self(name), [self(h) for h in headers])]
