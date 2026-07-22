# Contributing to Five-Layer Memory

Thanks for your interest in contributing! 🎉

## Ways to Contribute

- 🐛 **Report bugs** — Open an issue with details
- 💡 **Suggest features** — Open an issue with "Feature Request" label
- 📝 **Improve docs** — Fix typos, add examples, clarify instructions
- 🔧 **Fix bugs** — Submit a PR with your fix
- ✨ **Add features** — Submit a PR with new functionality

## Development Setup

```bash
# Clone the repo
git clone https://github.com/juventini10/Five-layer-memory-system.git
cd Five-layer-memory-system

# No build step required — this is a pure documentation/template project.
# The whole repo IS the install package: point your AI at INSTALL.md to install.
```

## Pull Request Process

1. **Fork** the repo
2. **Create a branch** for your changes: `git checkout -b fix/my-fix`
3. **Make your changes** — follow the conventions below
4. **Test your changes** — if adding/modifying a Skill or step, verify it works with your AI platform
5. **Commit** with clear messages: `git commit -m "Fix: corrected path config for Trae"`
6. **Push** to your fork: `git push origin fix/my-fix`
7. **Open a PR** — describe what you changed and why

## Conventions

### Commit Messages

Format: `type: message`

Types:
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation only
- `refactor:` — Code cleanup without functional change
- `test:` — Adding/modifying tests
- `chore:` — Maintenance tasks

Examples:
```
feat: add quick-start template for beginners
fix: corrected WorkBuddy path config for IDENTITY.md
docs: clarified routing rules in INSTALL.md
```

### File Structure

- `INSTALL.md` — AI install entry point (the AI reads this to run the install)
- `references/skills/` — The 9 linked Skills (each with its own `SKILL.md`)
- `references/steps/` — The step-by-step install flow (step1–step7 + step6.5)
- `references/templates/` — Memory file templates & the memory blueprint (记忆蓝图)
- `references/questionnaire.md` — The 33-question set
- `references/最伟大的我 / 未知未知 / 成就系统 / 记忆琥珀` — Supporting subsystems
- `五层记忆系统-布洛陀-执行文件-WorkBuddy版.md` — WorkBuddy execution file
- `version.md` — Single source of truth for the package version

### Template Format

Each template should:
- Use markdown headers for sections
- Include placeholder fields like `{field-name}`
- Be platform-agnostic (platform-specific logic goes in the relevant step/SKILL.md)

### Skill / Step Changes

When modifying a Skill's `SKILL.md` or an install step:
- Keep the frontmatter (`name`, `description`) accurate
- Update `version.md` if adding significant functionality
- Test across supported platforms (WorkBuddy, Trae, QClaw) if possible
- Document platform-specific behavior clearly

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on what's best for the community
- Show empathy toward other community members

## Questions?

Open an issue with the "question" label, or start a discussion.

---

Thanks for helping make Five-Layer Memory better! 🦞
