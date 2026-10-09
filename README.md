# Wewo QA Skills

面向测试人员的 Codex / Claude Code 插件，当前版本 **0.2.0**，包含两个 Skill。

| Skill | 职责 |
| --- | --- |
| `wewo-qa-case-designer` | 读取需求，与测试人员澄清并确认，生成 XMind 和三份 Excel 用例。 |
| `wewo-qa-case-executor` | 结合已审查用例、项目源码和测试环境，编写并运行自动化测试，输出报告。 |

## 使用流程

需求文档、图片或链接 → 多轮理解与澄清 → 确认最终需求 → 生成并确认 XMind → 生成冒烟、回归、全量 Excel → 在开发完成后生成并运行自动化代码 → 测试报告。

生成阶段不需要产品代码。测试点按具体、独立可验证的业务结果拆分，不限制树的层级。执行阶段保持需求预期，逐项检查实际结果；未检查的断言、跳过的测试和阻塞项不能算通过。

## 测试人员的交付物

```text
qa-artifacts/<feature>/
|-- test-points.xmind
|-- test-cases.smoke.xlsx
|-- test-cases.regression.xlsx
|-- test-cases.full.xlsx
|-- test-execution-report.xlsx  # 执行后生成
`-- .qa-state/                 # 内部记录和证据，无需手动编辑
```

三份 Excel 使用同一基线和稳定编号。编辑后由 AI 导入、复审并同步全部文件。自动化源码保存在实际项目的测试目录；报告链接到原生报告、截图和执行证据。

## 安装与调用

Codex：添加市场后，在桌面插件界面安装 `wewo-qa-skills`。

```text
codex plugin marketplace add successfulspring/wewo-qa-skills
```

Claude Code：

```text
claude plugin marketplace add successfulspring/wewo-qa-skills
claude plugin install wewo-qa-skills@wewo-qa-skills
```

新会话中使用 `$wewo-qa-case-designer` / `$wewo-qa-case-executor`；Claude Code 使用 `/wewo-qa-skills:wewo-qa-case-designer` / `/wewo-qa-skills:wewo-qa-case-executor`。

Git 市场安装取得完整源码仓库。CI 同时提供按系统裁剪的 ZIP 分发包，只包含 Skill 指令、插件配置、许可说明和当前系统的运行工具，排除维护源码和仓库测试。本地插件加载方式取决于宿主；ZIP 不会自动替换市场安装。

产物工具无需测试人员安装 Python 或依赖。项目自动化测试使用项目已有或 Agent 配置的测试运行环境。

源码许可：[MIT](LICENSE)。运行工具依赖声明：[Third-party notices](THIRD_PARTY_NOTICES.md)。

## 维护仓库

```text
skills/   两个 Skill 的规范、资源和构建输入；共同运行说明只有一份
bin/      各系统已验证的运行工具
tooling/  构建、校验、打包及共享运行源码
tests/    工具回归测试和合成夹具
docs/     开发、版本历史和来源说明
.github/  构建与分发流程
```

[开发与验证](docs/development.md) · [版本历史](docs/CHANGELOG.md) · [开源来源](docs/OPEN_SOURCE_FOUNDATIONS.md)

`skills/` 是唯一规范源，安装包从它生成。历史记录和开发说明不参与日常 Skill 使用，构建临时文件位于系统临时目录。
