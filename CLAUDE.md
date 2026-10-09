# Claude Code maintenance context

This repository is a cross-host plugin. Follow `AGENTS.md` when maintaining it.

Installed behavior is defined only by `skills/`. `.claude-plugin/` declares the Claude Code package and marketplace; it must not contain a copied Skill tree. Use the bundled executable selected by each Skill's `references/runtime-tool.md`; artifact tooling is self-contained; generated acceptance tests reuse the project test environment.
