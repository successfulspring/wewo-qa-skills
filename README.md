# Wewo QA Skills

面向测试人员的 Codex / Claude Code 插件，当前版本 **0.3.0**，包含两个 Skill。

| Skill | 职责 |
| --- | --- |
| `wewo-qa-case-designer` | 结合产品与开发材料设计测试，生成 XMind 和三份 Excel；后续补充文档时更新受影响用例。 |
| `wewo-qa-case-executor` | 根据已审查用例和测试环境，检查并补齐权限、数据及工具条件，在独立测试工程中编写并运行自动化测试，输出报告。 |

## 从需求到测试报告

生成和执行阶段均不要求提供产品源码。Designer 负责明确业务预期并设计测试；开发将功能部署到测试环境后，Executor 根据用例开展验收自动化。目标可以是实际需求中的 Web、移动端、桌面端或接口；能否执行取决于对应的控制、观察和环境能力。

| 阶段 | Skill 的工作 | 进入下一步的条件 |
| --- | --- | --- |
| 1. 完整理解 | 读完授权材料，梳理谁操作、条件、步骤、结果、计算规则、异常和上下游影响。 | 已完整阅读或明确排除不可读材料，集中列出主要矛盾与疑问。 |
| 2. 集中确认 | 用普通业务语言展示整体理解、范围、规则和主要矛盾，请测试人员一次纠正或补充。 | 已获得整体确认；局部未知预期保持待确认，不阻止初稿。 |
| 3. 交付初稿 | 自主拆分测试点、分析边界、组织用例和优先级，同时交付 XMind、三份 Excel 和集中疑问清单。 | 明确部分完整可审查，未知预期标注待确认并关联问题；全量文件含“待确认问题”表。 |
| 4. 统一完善 | 按集中答复同步更新规则、测试点和用例，保留稳定编号；解决预期后冻结覆盖并复审。 | 正式版本无未解决的业务断言，四份文件一致；无需分别确认需求、XMind、Excel。 |
| 5. 检查执行条件 | 核对交付基线与 Excel 修改，检查实际环境，集中询问缺少的账号、角色、数据、权限、设备和工具。 | 每个用例与目标的交互、观察、数据准备、清理和工具条件已核实；其他阻塞项保留原因。 |
| 6. 编写并运行测试 | 在独立测试工程中复用或编写自动化代码，审查步骤和全部断言，实际运行具备条件的用例。 | 保存实际环境及版本、测试代码、原生结果、观察值、准备和清理证据。 |
| 7. 汇总报告 | 汇总全部执行、重试、脚本修复和未执行范围，输出 Excel 报告及证据链接。 | 报告覆盖所选范围；全部受阻时也输出未完成报告和具体缺口。 |

### 生成阶段的质量约束

- **先整体确认，再集中答疑。** 默认读完再问；设计中新疑问先记录，明确部分持续完成。每项说明不明确处、来源、影响用例和可选方式，随完整初稿交付。部分答复只解决对应问题；新出现的实质矛盾仍可能需要后续集中澄清，不承诺固定轮数。
- **先推导覆盖，再写测试点。** 按当前需求选择等价类、边界值、决策表、状态迁移等方法，不套用试用项目的业务事实。测试点拆到独立结果，不固定树深度或用例数量；一个完整业务用例可包含多个明确断言。
- **业务答复复用，变更同步复审。** 局部答复通过有来源的修订更新相关事实，不因增加对话或调整文件视图重新确认整体。Excel 修改先导入、处理冲突、复审，再同步视图。待确认预期不伪造比较值，草稿不能交给 Executor 执行；正式版本仍须关闭业务疑问并通过完整校验。

完整规则见 [Designer](skills/wewo-qa-case-designer/SKILL.md) 和 [Executor](skills/wewo-qa-case-executor/SKILL.md)。

### 产品、开发材料的交接

产品 PRD、与 AI 沟通后确认的需求总结、开发交接说明可以一起提供，也可以分批提供。产品材料足够时先设计用例，开发材料后到时复用已有结论、编号和人工修改，交付更新后的同一套文件、变更说明与集中疑问。

开发描述的“已实现、未实现、实现不同”不自动改变业务预期。已有明确批准依据的需求变更可以继承；正确行为存在真实矛盾时，相关预期待确认。文档遗漏旧规则不等于取消测试范围。交接内容建议见 [产品与开发交接指南](skills/wewo-qa-case-designer/references/handoff-guide.md)，增量处理规则见 [后续材料更新](skills/wewo-qa-case-designer/references/source-updates.md)。已有文档无需强制改成统一模板。

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

草稿和正式版本使用相同的四个公共文件名，通过状态区分；全量 Excel 包含集中疑问表，相关用例和断言显示问题编号。测试人员统一答复后由 Designer 同步更新，无需分别维护清单。

三份 Excel 使用同一基线和稳定编号，范围关系为**冒烟 ⊆ 回归 ⊆ 全量**。测试人员可以编辑生成的可编辑内容，应保留编号和模板结构；由 AI 导入并复审变更。没有适用冒烟或回归用例时，仍生成明确标注为空的对应文件。

交给 Executor 或迁移到另一台电脑时，携带**整个用例交付目录，包括 `.qa-state/`**，不能只复制某一份 Excel。内部记录无需测试人员手动编辑，但用于校验来源、确认和执行证据。已有授权自动化工程可直接复用，否则创建上图中的独立工程；后续复跑也应保留该工程及报告引用的证据文件。

Skill 指令与示例使用英文。交付物支持中文和英文：优先遵循用户指定语言，其次是持续澄清所用语言，再次是原始材料语言，无法判断时默认中文。报告沿用用例语言；原始引文、标识符和作为测试依据的字面值保持原样。

## 调用时提供什么

生成阶段提供原始需求材料、已知业务背景和期望范围。执行阶段提供完整交付目录、已部署的测试环境入口、希望执行的套件及目标；已有账号获取方式、数据或自动化工程也可一并说明。其余具体缺口由 Skill 检查后提出。

```text
$wewo-qa-case-designer 请先完整阅读材料并展示整体业务理解，集中确认后交付测试点、用例初稿和疑问清单，再根据我的统一答复完善。

$wewo-qa-case-executor 用例目录为 qa-artifacts/<feature>，测试环境为 <entry>，
请执行回归套件；先检查缺少的权限、数据和运行条件，再编写并执行测试，输出报告。
```

## 安装与调用

从本 GitHub 仓库 [successfulspring/wewo-qa-skills](https://github.com/successfulspring/wewo-qa-skills) 安装。市场名和插件名均为 `wewo-qa-skills`。

Codex：添加市场后，在桌面插件界面安装 `wewo-qa-skills`。

```text
codex plugin marketplace add successfulspring/wewo-qa-skills
```

Claude Code：添加市场，再安装插件。

```text
claude plugin marketplace add successfulspring/wewo-qa-skills

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

安装说明、插件链接和两个宿主的市场清单应指向本仓库；更新发布配置后运行包校验，确保来源一致。

工具校验通过只说明产物和执行证据符合约束，业务理解及覆盖仍需测试人员确认。第三方声明随运行工具分发；公司产物、凭据和登录态不提交到仓库。仅在用户明确要求上传当前修改时推送远端仓库。
