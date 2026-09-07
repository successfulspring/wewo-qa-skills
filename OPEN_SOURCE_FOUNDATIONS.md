# Open-source foundations

This plugin is Wewo-owned and independent from `wewo-skills`. Its workflow adapts proven ideas from the projects below; no third-party source code is vendored here.

- [OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills): Agent Skills packaging, progressive disclosure, and plugin distribution.
- [petrkindlmann/qa-skills](https://github.com/petrkindlmann/qa-skills): staged requirement extraction, risk analysis, coverage mapping, oracle design, and evidence-oriented browser testing. Wewo deliberately omits its unit/API/code-generation routes.
- [SeldomQA/casebook](https://github.com/SeldomQA/casebook): schema-constrained test assets, Git-friendly stable cases, and separation of case definitions from execution results.
- [DingTalk Workspace CLI](https://github.com/DingTalk-Real-AI/dingtalk-workspace-cli): read-only DingTalk document discovery and extraction when the CLI is installed and enterprise access is authorized.
- [Microsoft Playwright MCP](https://github.com/microsoft/playwright-mcp): accessibility-snapshot-first browser interaction and deterministic tool execution.
- [Docling](https://github.com/docling-project/docling) and [MarkItDown](https://github.com/microsoft/markitdown): optional document-to-structured-text adapters when already available.
- [CTRF](https://github.com/ctrf-io/ctrf): inspiration for portable, machine-readable execution outcomes. The local result contract is intentionally narrower and QA-workflow-specific.
- [Xmind Ltd/xmind-generator](https://github.com/xmindltd/xmind-generator): official modern XMind workbook and topic model used to verify the generated Zen package shape.
- [Mitscherlich/skills xmind](https://github.com/Mitscherlich/skills/tree/main/skills/xmind): an MIT-licensed, zero-dependency XMind skill supporting both XMind 8 XML and Zen/2020+ JSON. Wewo uses the same compatibility strategy while binding the renderer to its own validated test-point schema.

The JSON contracts use JSON Schema Draft 2020-12. Release builds bundle the mature Python `jsonschema` implementation into self-contained executables so testers do not install Python or packages.
