# Wewo QA Skills

面向测试人员的 Codex / Claude Code 插件，当前版本 **0.2.0**，包含两个 Skill。

| Skill | 职责 |
| --- | --- |
| `wewo-qa-case-designer` | 读取需求，与测试人员澄清并确认，生成 XMind 和三份 Excel 用例。 |
| `wewo-qa-case-executor` | 根据已审查用例和测试环境，检查并补齐权限、数据及工具条件，在独立测试工程中编写并运行自动化测试，输出报告。 |

## 从需求到测试报告

生成和执行阶段均不要求提供产品源码。Designer 负责明确业务预期并设计测试；开发将功能部署到测试环境后，Executor 根据用例开展验收自动化。目标可以是实际需求中的 Web、移动端、桌面端或接口；能否执行取决于对应的控制、观察和环境能力。

| 阶段 | Skill 的工作 | 进入下一步的条件 |
| --- | --- | --- |
| 1. 理解需求 | 阅读原始材料，逐项提取规则，围绕业务主题澄清目标、角色、状态、流程、异常和上下游影响。 | 关键业务问题已解决，无法读取的材料已补充或明确排除。 |
| 2. 确认需求 | 审查业务完整性、回答衍生分支和规则来源，向测试人员展示完整需求总结。 | 测试人员真实确认当前总结；确认前不生成 XMind，包括草稿。 |
| 3. 设计测试点 | 从确认的规则推导适用维度、条件取值、场景和独立结果，冻结覆盖计划，生成并审查 XMind。 | 每个独立可验证结果都有对应测试点，测试人员明确确认当前 XMind。 |
| 4. 设计测试用例 | 写明前置条件、数据、操作步骤、逐项预期、观察位置和清理方法，评估自动化条件，审查后导出三份 Excel。 | 用例可复现、断言可检查、来源可追溯，三份文件读取校验一致。 |
| 5. 检查执行条件 | 核对交付基线与 Excel 修改，检查实际环境，集中询问缺少的账号、角色、数据、权限、设备和工具。 | 每个用例与目标的交互、观察、数据准备、清理和工具条件已核实；其他阻塞项保留原因。 |
| 6. 编写并运行测试 | 在独立测试工程中复用或编写自动化代码，审查步骤和全部断言，实际运行具备条件的用例。 | 保存实际环境及版本、测试代码、原生结果、观察值、准备和清理证据。 |
| 7. 汇总报告 | 汇总全部执行、重试、脚本修复和未执行范围，输出 Excel 报告及证据链接。 | 报告覆盖所选范围；全部受阻时也输出未完成报告和具体缺口。 |

### 生成阶段的质量约束

- **澄清不按轮数结束。** 每轮围绕一个业务主题，使用开放问题或有依据的选项。部分回答只关闭已回答的问题；新分支会继续追问，受影响的旧决定会重新检查。保留真实问答，中断后可核对历史恢复。
- **先推导覆盖，再写测试点。** 按当前需求选择等价类、边界值、决策表、状态迁移等方法，不套用试用项目的业务事实。测试点拆到独立结果，不固定树深度或用例数量；一个完整业务用例可包含多个明确断言。
- **变更需要重新审查。** 需求变化重新确认需求；测试点变化重新审查和确认；Excel 修改先导入、处理冲突、复审，再同步全部视图。工具不能代替测试人员确认，也不能保证业务理解绝对正确或覆盖穷尽。

完整规则见 [Designer](skills/wewo-qa-case-designer/SKILL.md) 和 [Executor](skills/wewo-qa-case-executor/SKILL.md)。

### 执行与报告的边界

用例中的“自动化”是设计阶段的可行性评估，包含候选方式和前提条件，不代表已经生成代码或当前环境已就绪。Executor 会再次逐项核实。人工用例保留在所选范围和报告中，不冒充自动执行；变更自动化评估需要审查并更新基线。

执行时保持确认的业务预期。需要界面观察的断言必须实际检查界面；接口定义的预期可使用接口验收测试。辅助接口准备数据不能代替界面检查，模拟或单元测试不能代替部署环境验收。缺少或冲突的业务预期返回 Designer 澄清；账号、数据、定位和工具等执行条件由 Executor 处理。

报告列出所选、已执行、阻塞和人工范围，已检查与应检查的断言、环境版本、失败原因、清理问题及执行历史。每次执行保留原始证据，脚本修复或重试不会抹掉先前结果；部署版本变化启动新一轮执行。最终自动化结论包括通过、失败、未完成、未执行代码或无可自动化用例。跳过、缺证据、清理失败或零执行均不能算整体通过。

## 测试人员的交付物

```text
<workspace>/
|-- qa-artifacts/<feature>/
|   |-- test-points.xmind
|   |-- test-cases.smoke.xlsx
|   |-- test-cases.regression.xlsx
|   |-- test-cases.full.xlsx
|   |-- test-execution-report.xlsx  # 执行后生成
|   `-- .qa-state/                 # 需求、确认、用例基线及执行证据
`-- qa-automation/<artifact-id>/   # 持久化测试代码、配置和依赖声明
```

三份 Excel 使用同一基线和稳定编号，范围关系为**冒烟 ⊆ 回归 ⊆ 全量**。测试人员可以编辑生成的可编辑内容，应保留编号和模板结构；由 AI 导入并复审变更。没有适用冒烟或回归用例时，仍生成明确标注为空的对应文件。

交给 Executor 或迁移到另一台电脑时，携带**整个用例交付目录，包括 `.qa-state/`**，不能只复制某一份 Excel。内部记录无需测试人员手动编辑，但用于校验来源、确认和执行证据。已有授权自动化工程可直接复用，否则创建上图中的独立工程；后续复跑也应保留该工程及报告引用的证据文件。

Skill 指令与示例使用英文。交付物支持中文和英文：优先遵循用户指定语言，其次是持续澄清所用语言，再次是原始材料语言，无法判断时默认中文。报告沿用用例语言；原始引文、标识符和作为测试依据的字面值保持原样。

## 调用时提供什么

生成阶段提供原始需求材料、已知业务背景和期望范围。执行阶段提供完整交付目录、已部署的测试环境入口、希望执行的套件及目标；已有账号获取方式、数据或自动化工程也可一并说明。其余具体缺口由 Skill 检查后提出。

```text
$wewo-qa-case-designer 请根据提供的需求材料，与我澄清并确认后生成测试点和用例。

$wewo-qa-case-executor 用例目录为 qa-artifacts/<feature>，测试环境为 <entry>，
请执行回归套件；先检查缺少的权限、数据和运行条件，再编写并执行测试，输出报告。
```

## 安装与调用

提供两个发布源，按网络条件选择一个即可：

| 发布源 | 仓库 |
| --- | --- |
| GitHub | [successfulspring/wewo-qa-skills](https://github.com/successfulspring/wewo-qa-skills) |
| 公司 GitLab | [skills/wewo-qa-skills](http://192.168.1.205/skills/wewo-qa-skills) |

两端共享同一套 Skill、版本和运行工具，各自的市场清单指向各自仓库。GitLab 发布版从内网获取插件；需要能访问公司网络，并具备该仓库的读取权限。市场名和插件名均为 `wewo-qa-skills`，选择一个来源安装。

Codex：选择一条命令添加市场后，在桌面插件界面安装 `wewo-qa-skills`。

```text
codex plugin marketplace add successfulspring/wewo-qa-skills
# 或使用公司 GitLab
codex plugin marketplace add http://192.168.1.205/skills/wewo-qa-skills.git
```

Claude Code：同样选择一个市场来源，再安装插件。

```text
claude plugin marketplace add successfulspring/wewo-qa-skills
# 或使用公司 GitLab
claude plugin marketplace add http://192.168.1.205/skills/wewo-qa-skills.git

claude plugin install wewo-qa-skills@wewo-qa-skills
```

新会话中使用 `$wewo-qa-case-designer` / `$wewo-qa-case-executor`；Claude Code 使用 `/wewo-qa-skills:wewo-qa-case-designer` / `/wewo-qa-skills:wewo-qa-case-executor`。

Git 市场安装取得完整源码仓库。CI 同时提供按系统裁剪的 ZIP 分发包，只包含 Skill 指令、插件配置、许可说明和当前系统的运行工具，排除维护源码和仓库测试。本地插件加载方式取决于宿主；ZIP 不会自动替换市场安装。

源码许可：[MIT](LICENSE)。运行工具依赖声明：[Third-party notices](THIRD_PARTY_NOTICES.md)。

## 维护仓库

```text
skills/   两个 Skill 的规范、资源和构建输入；共同运行说明只有一份
bin/      各系统运行工具及版本、源码契约和文件哈希记录
tooling/  构建、校验、打包及共享运行源码
tests/    工具回归测试和合成夹具
.github/  构建与分发流程
```

`skills/` 是唯一规范源，安装包从它生成。源码和工具测试供维护者使用，构建临时文件位于系统临时目录。版本变更通过 Git 历史查看。

维护者使用 Python 3.12，安装依赖后验证仓库：

```text
python -m pip install -r tooling/requirements-dev.txt
python -B -m unittest discover -s tests
python -B tooling/validate_package.py
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .claude-plugin/marketplace.json --strict
```

如宿主提供 Skill 校验器，再分别校验两个 `SKILL.md`。根目录 `CLAUDE.md` 是维护上下文，Claude 插件校验可能提示它不作为安装插件的项目上下文加载。

修改运行源码后，在对应系统重建、运行冒烟检查并打包：

```text
python -B tooling/build_runtime.py --output-dir bin/<host-target>
python -B tooling/smoke_runtime.py --runtime bin/<host-target>/wewo-qa
python -B tooling/package_plugin.py --target <host-target> --output <outside-repository>/wewo-qa-skills.zip
```

目标为 `windows-x64`、`linux-x64`、`macos-arm64`、`macos-x64`；Windows 文件名为 `wewo-qa.exe`。普通包校验会列出待重建的目标，不能代替发布检查。四个平台完成构建、原生冒烟和打包后，发布前必须执行：

```text
python -B tooling/validate_package.py --release
```

CI 在各平台构建、冒烟和打包，再收集四个平台的产物检查版本、源码契约和文件哈希。CI 上传的运行工具及 ZIP **不会自动写回 Git 仓库或更新已安装插件**；从 Git 市场分发时，维护者仍须确保仓库中的对应运行工具已同步。打包后的 README 保留测试人员说明，去掉本维护章节。

`tooling/requirements-dev.txt` 声明构建依赖范围，并非每个平台的依赖锁定清单。更新依赖或运行工具时，根据实际构建环境和二进制收集内容核对第三方声明，包括传递依赖、可选依赖和本机库；PyInstaller 构建工具与被打入产物的组件应分别说明。

双平台发布沿用 `wewo-skills` 的方式：`origin` 对应 GitHub，`company-gitlab` 对应公司 GitLab；共享改动从 GitHub `main` 合入 GitLab 发布分支，保留 GitLab 自身的市场来源、所有者及插件链接。两个宿主的市场必须指向同一个发布仓库，校验器会拒绝混用来源。每次同步后验证两端的 `skills/`、维护源码和 `bin/` 一致，并分别运行发布校验。GitHub Actions 负责原生构建；GitLab 分发经验证的相同运行工具。这是两个独立远端，推送一个不会自动同步另一个，不能把 GitHub 分支直接覆盖到 GitLab 发布分支。

工具校验通过只说明产物和执行证据符合约束，业务理解及覆盖仍需测试人员确认。第三方声明随运行工具分发；公司产物、凭据和登录态不提交到仓库。仅在用户明确要求上传当前修改时推送 GitHub。
