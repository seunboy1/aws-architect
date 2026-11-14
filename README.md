# aws-architect

An agent skill that turns a call transcript, a SOW, or a few quick answers into:

1. an editable AWS architecture diagram (a `.drawio` file with real AWS icons), and
2. a shareable AWS Pricing Calculator link (calculator.aws) for the same architecture, ready to send to a customer. No AWS account is needed.

It works in Claude Code, Codex, Gemini CLI, Antigravity, Cursor and any other agent that reads `SKILL.md` skills.

## How it works

Start it with a plain request ("draw the AWS architecture for this", "how much will this cost on AWS?"). The agent then:

1. **Kicks off** by asking what you have (a call transcript, a SOW or design doc, a Terraform/CDK repo, or nothing), whether you want a diagram, a cost estimate or both, the customer's stage (startup, growing, enterprise) and the Region.
2. **Interviews** you with short batches of questions tuned to your role (DevOps, solutions architect, AI/ML, data, security, developer, executive), pre-filled from whatever you gave it.
3. **Plays back** the components, groups and arrows as tables and waits for your yes.
4. **Builds** the diagram with a script, checks the spec for typos and the layout for overlaps and crossed lines, and looks at the render before handing it over. Every connector has a slow flow animation, and a numbered **How data flows** panel beside the diagram explains each step, with matching numbers on the arrows.
5. **Prices** it: agrees usage numbers with you, posts the estimate to calculator.aws, reprices it in a browser, then **verifies the final link** with `--check`: every input must survive, and model lines must match AWS's official Price List. You get the link only after it passes.

## Install

| Agent | Install |
|---|---|
| Claude Code | `/plugin marketplace add seunboy1/aws-architect`, then `/plugin install aws-architect@aws-architect` (two separate prompts) |
| Codex | `codex plugin marketplace add seunboy1/aws-architect`, then `codex plugin add aws-architect@aws-architect` |
| Gemini CLI | `gemini extensions install https://github.com/seunboy1/aws-architect` |
| Antigravity | `agy plugin install https://github.com/seunboy1/aws-architect` |
| Any agent (skills CLI) | `npx skills add seunboy1/aws-architect` (add `--agent <name>` or `--global`) |
| Claude desktop or claude.ai | Download `aws-architect.skill` from the [latest release](https://github.com/seunboy1/aws-architect/releases/latest) and upload it under Settings > Skills |
| By hand | Copy `skills/aws-architect/` into your agent's skills folder (for example `~/.claude/skills/`, `~/.codex/skills/`, `.agents/skills/`) |

Agents without skill support can read `AGENTS.md`, which points them at the skill.

## Use

> Here's the transcript from today's call with the customer. They're a startup. Create the architecture diagram and a cost estimate link.

You get:

- `diagram.drawio` (open in the draw.io desktop app or app.diagrams.net) and `spec.json`, its source. To change the diagram, ask the agent to edit the spec and rebuild. Hand edits in draw.io are lost on a rebuild.
- a `calculator.aws/#/estimate?id=...` link with per-service monthly costs, which the customer can open and adjust.

`skills/aws-architect/assets/` holds a worked example: a diagram spec and a usage file for serverless face search on Rekognition, sized for a startup (about $33/month).

## Requirements

- Python 3 (standard library only, nothing to install).
- A browser tool (for example Playwright MCP) so the agent can look at the diagram and price the calculator link. Without one, the agent hands you the link and the three clicks to price it yourself. The diagram preview loads draw.io's viewer from viewer.diagrams.net; the diagram itself is not uploaded.
- Optional: the draw.io desktop app, which lets the agent export a PNG directly.

## Known limits

- About 100 AWS icons are verified. For others, see `skills/aws-architect/references/icons.md`.
- One diagram is meant to hold about 14 icons; bigger systems are split into an overview plus detail diagrams.
- The calculator link relies on calculator.aws's undocumented save endpoint (the one its Share button uses). If AWS changes it, `skills/aws-architect/references/cost-estimate.md` explains how to re-capture the format.
- Calculator links are public to anyone who has the URL and cannot be deleted. Don't put secrets in descriptions.
- Nine services have been checked against a priced estimate (listed in `references/cost-estimate.md`); check others by hand the first time.

## License

MIT
