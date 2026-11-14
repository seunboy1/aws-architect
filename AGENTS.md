# aws-architect

This repo is an agent skill. The skill is `skills/aws-architect/SKILL.md`; its scripts, references and assets sit beside it.

## Using it from an agent without skill support

When the user asks for an AWS architecture diagram, a draw.io diagram of a cloud system, an AWS cost estimate or a calculator.aws link, read `skills/aws-architect/SKILL.md` and follow it. Run its commands from `skills/aws-architect/`.

## Changing it

- `SKILL.md` is the product. Every word of it is read on each use, so keep it short and move detail into `references/`.
- Keep instructions neutral across agents. Name a tool (Playwright, a question tool) only as an example.
- Scripts use the Python 3 standard library only. Run both tests before publishing:
  `python3 skills/aws-architect/scripts/test_build.py` and `python3 skills/aws-architect/scripts/test_calculator_link.py`.
- Add a `CHANGELOG.md` entry for each release. Keep the version the same in `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json` and `gemini-extension.json`. `python3 check_package.py` fails when they differ.
- Each release needs a fresh `aws-architect.skill` (Claude desktop and claude.ai install it from the release):
  `mkdir -p dist && rm -f dist/aws-architect.skill && (cd skills && zip -qr ../dist/aws-architect.skill aws-architect -x '*/__pycache__/*' '*.DS_Store')`,
  then `gh release create vX.Y.Z dist/aws-architect.skill`.
