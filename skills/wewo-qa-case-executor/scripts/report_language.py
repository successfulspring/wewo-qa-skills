"""Executor report labels; use the Designer's recorded delivery language."""
from artifact_language import ArtifactText

ENGLISH_REPORT = {
    "通过":"Passed", "失败":"Failed", "阻塞":"Blocked", "不稳定":"Flaky", "未执行":"Not Run", "未检查":"Not Evaluated",
    "执行汇总":"Execution Summary", "内容":"Content", "执行门禁":"Execution Gate", "运行编号":"Run ID", "目标":"Targets",
    "环境":"Environment", "构建":"Build", "开始":"Started", "结束":"Finished", "用例基线 SHA256":"Case Baseline SHA256",
    "用例 Excel SHA256":"Case Workbook SHA256", "执行条件 SHA256":"Execution Profile SHA256",
    "自动化必检断言数":"Required Automated Assertions", "已检查断言数":"Evaluated Assertions", "通过断言数":"Passed Assertions",
    "断言检查覆盖率":"Assertion Evaluation Coverage", "执行说明":"Execution Notes", "用例结果":"Case Results",
    "尝试次数":"Attempts", "执行工具":"Execution Tool", "实际观察":"Actual Observation", "失败或阻塞原因":"Failure or Blocker",
    "自动化实现":"Automation Implementation", "运行框架":"Runner", "证据路线":"Evidence Route", "测试代码快照":"Test Code Snapshot",
    "框架测试编号":"Native Test ID", "执行记录":"Execution Receipt", "框架原生报告":"Native Report", "断言结果":"Assertion Results",
    "实际结果":"Actual Result", "证据编号":"Evidence IDs", "未检查原因":"Unevaluated Reason", "各次观察引用":"Observation References",
    "证据评判理由":"Evidence Review Reasons", "证据索引":"Evidence Index", "文件路径":"File Path", "执行历史":"Execution History",
    "次数":"Attempt", "重跑类型":"Repeat Type", "重跑原因":"Repeat Reason", "重置依据":"Reset Evidence", "结果记录":"Result Record",
    "历史说明":"History Notes", "准备与清理":"Preparation and Cleanup", "时间":"Time", "环境核验":"Environment Verification",
    "数据准备":"Data Preparation", "数据清理":"Data Cleanup", "无需清理":"Not Required", "环境与就绪":"Environment and Readiness",
    "入口":"Entry", "核验依据":"Verification Evidence", "执行完成情况":"Execution Completion", "就绪状态":"Readiness",
    "用例就绪":"Case Readiness", "条件检查":"Prerequisite Checks", "人工用例数":"Manual Cases", "待核验":"Pending", "已就绪":"Ready",
    "人工用例和阻塞项保留在明细；门禁仅反映已选自动化范围，不能证明整个项目无缺陷。":
        "Manual and blocked scope remains visible. The gate covers only selected automation and does not prove the whole product defect-free.",
}


class ReportText(ArtifactText):
    def __call__(self, value):
        if self.language == "en" and value in ENGLISH_REPORT:
            return ENGLISH_REPORT[value]
        return super().__call__(value)
