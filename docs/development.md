# 开发与分发

## 文件职责

- `skills/`：两个 Skill 的规范及各自的 schema、源模块；`runtime-tool.md` 是共用的运行说明。
- `tooling/runtime/`：共用校验、Excel 支持和命令路由源码。
- `tooling/`：维护者的构建、校验、打包和评估工具。
- `tests/`：工具回归测试与合成夹具，不是项目生成的自动化用例。
- `bin/`：各系统运行文件和版本、源码契约、文件哈希记录。

维护者保留完整源码；分系统 ZIP 排除 `scripts/` 构建输入、`tooling/`、`tests/`、Git 状态和开发文档。两个 Skill 的指令、schema、界面元数据及共同运行说明保留。需要修改工具时，从源码仓库重建；安装后的 Agent 使用可执行文件，不执行维护源码。

## 本地验证

维护者使用 Python 3.10 或更新版本：

```text
python -m pip install -r tooling/requirements-dev.txt
python -B -m unittest discover -s tests -v
python -B tooling/validate_package.py
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .claude-plugin/marketplace.json --strict
```

两个 Skill 再运行宿主提供的 `skill-creator/scripts/quick_validate.py`。Codex CLI 未提供插件验证命令时，使用仓库包校验器检查其清单和资源。

根目录 `CLAUDE.md` 是维护者上下文，不作为安装插件的项目上下文；Claude 校验器可能提示该已有警告。日常规范始终由 `skills/` 提供。

## 原生构建与精简包

```text
python -B tooling/build_runtime.py --output-dir bin/<host-target>
python -B tooling/smoke_runtime.py --runtime bin/<host-target>/wewo-qa
python -B tooling/package_plugin.py --target <host-target> --output <outside-repository>/wewo-qa-skills.zip
python -B tooling/validate_package.py --release
```

Windows 的运行文件名为 `wewo-qa.exe`。目标为 windows-x64、linux-x64、macos-arm64、macos-x64。构建工作目录由系统临时目录管理；分发 ZIP 输出到显式指定的外部目录。运行包版本固定并不足以证明同步，发布校验还比较源码契约和二进制哈希。

CI 的同一工作流支持 push、pull_request 和手动触发，运行仓库测试、四平台原生构建/冒烟、分系统打包及合并发布校验；不用维护第二份重复构建流程。分系统 ZIP 不携带维护源码，既有 Git 市场安装仍包含完整仓库。

## 方法与执行评估

工具测试验证覆盖引用、Excel 编辑合并、冻结预期、断言证据、缺失检查和假通过等约束，不能证明业务理解完整。

`tests/fixtures/forward-design-requirement.txt` 是独立需求设计评估的原始合成材料。生成草稿置于仓库外，需求确认和 XMind 确认分别记录实际评估角色的回复，不冒充公司批准。

`tests/fixtures/ui-oracle-benchmark.html` 提供正确、数量错误和关联错误模式。实际生成原生测试代码、运行并检查报告，才能验证代码执行链路。旧的 `tooling/evaluate_ui_observations.py` 只比较已捕获的原始浏览器观察：输入含 mode、repeat、before_at、after_at、before/after 字段；工具不操作浏览器，不验证捕获真实性，正确观察的自动化门禁仍为 NO_CODE_EXECUTION。

公司验收仍需相同需求版本、确认的项目上下文、公司 XMind/Excel 标准和测试人员评审。用具体漏项、虚构规则、准备可复现性、断言有效性及受控错误识别结果衡量；不凭层级、叶子数量或 schema 通过认定公司标准合格。

不得提交公司产物、秘密、登录态或真实生产数据。旧基线按当前规范重新审查，不进行静默升级。
