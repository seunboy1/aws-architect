---
name: aws-architect
description: Create accurate, editable AWS architecture diagrams as draw.io (.drawio) files with real AWS icons, plus a shareable AWS Pricing Calculator (calculator.aws) cost estimate for the same architecture. Interviews the user according to their role and the kind of diagram needed (DevOps and platform infrastructure, solutions architecture, AI/ML and GenAI systems such as RAG and agents, data pipelines, security boundaries, CI/CD, disaster recovery, migrations, executive overviews), agrees the components and arrows with them, then generates, lints and visually checks the diagram. Use this whenever someone asks for an architecture diagram, AWS diagram, cloud or infrastructure diagram, solution architecture, network topology, GenAI or RAG architecture, data platform diagram, "draw this system", a draw.io or diagrams.net file, or a diagram for a proposal, SOW, design review or runbook, even if they don't say draw.io or AWS and even if they only describe the system in words or point at Terraform or CloudFormation files. Also use it for an AWS cost estimate, pricing calculator link, or "how much will this cost on AWS".
---

# AWS architect: diagram and cost estimate

Produce a draw.io file a reviewer would accept: every AWS service shows its real icon, nothing overlaps, no line runs through an icon or a label, and the layout reads in one direction. Free-hand diagram XML usually fails on exactly those points, so this skill moves the fragile work into a script and makes you look at the result before you call it done.

Commands below assume Python 3 (`python3`) and that you run them from this skill's folder (quote the path if it contains spaces).

The pipeline is: **kick off, interview, agree the content, write a spec, build and lint, look at it, deliver**, then (when a cost estimate is wanted) **price it as a calculator.aws link** (step 7). Do not skip a step. The interview and the look do most of the work: a diagram drawn from a vague brief is vague, and a diagram nobody looked at has defects nobody noticed.

## 0. Kick off

If the request already carries a transcript, SOW or design doc, skip to step 1 and read it. Otherwise your first message asks only this, as one short multiple-choice batch (use the host's question tool if it has one, else a numbered list):

1. **What do you have to start from?** (a) a call transcript or meeting notes: paste it or give the file path, (b) a SOW, proposal or design doc, (c) a repo with Terraform, CDK or CloudFormation, (d) nothing yet: I'll ask a few quick questions.
2. **What do you need?** Diagram, cost estimate, or both (default: both).
3. **Who is it for, and what stage is the customer?** Startup or MVP, growing product, or enterprise. This sets the default usage numbers in step 7 (see "Sizing" in `references/cost-estimate.md`).
4. **Region?** Default: the AWS Region nearest the customer's users that offers every service in the design.

Then read whatever they gave you, pre-fill the interview from it, and ask only what is still missing.

## 1. Interview

Read `references/interview.md` and use it: first the **triage** (who is this person, DevOps, solutions architect, AI/ML, data, security, developer or executive, and which kind of picture do they need), then the **core** questions, then the **role module** that fits (two if needed, for example an architect drawing an AI system), then any **picture-type add-on** (migration, disaster recovery, CI/CD). Before asking anything, look at what you already have: the conversation, and any Terraform, CDK, CloudFormation, README or design document in the working folder. Pre-fill what you can and ask the user to confirm rather than making them retype it. Ask in short batches (at most five questions at a time), offer sensible defaults, and stop interviewing once you could draw it.

If the system is too big for one readable picture (more than about 14 icons), propose an overview plus one diagram per area and do the overview first.

## 2. Agree the content before drawing

Write three small tables in chat and wait for a yes (or corrections):

- **Nodes:** name, AWS service, one-line role, which group it sits in.
- **Groups:** account, VPC, public and private subnets, "managed services outside the VPC", "security and observability".
- **Arrows:** from, to, label (1-3 words), solid or dashed (async, return or redrive paths are dashed).

This is cheap to change now and expensive to change after layout. Also settle the main flow as a numbered sentence list; it decides the layout direction.

Sanity-check the brief against how AWS works before drawing. If it contradicts itself (an "internal" load balancer in a public subnet reached from the internet, a managed service placed inside a subnet), raise it with the user, or record your assumption in the footnote and in your hand-off message. If the user insists on one diagram past the size budget, keep it, accept the linter's size warning, and say so.

## 3. Write the spec

Describe the diagram as JSON using `references/spec-format.md`; start from `assets/example-spec.json`. Use only icon names from `references/icons.md` (each was checked to render). Follow `references/layout-rules.md` for placement: one flow direction, managed services outside the VPC with only their endpoints inside, labels on the side that has no arrow, explicit connector ports.

You choose the coordinates; the script handles styles, parent-relative conversion and connector details. Keep arithmetic simple: icons are 60x60, put columns about 180-210 px apart and rows about 110-130 px apart, and leave 20 px inside group edges.

## 4. Build and lint

```bash
python3 scripts/build_drawio.py spec.json diagram.drawio
```

The linter fails the build on errors and prints warnings: lines through icons or labels, overlapping items, items outside their group, an arrow attached on the side where its own label sits, unknown icon names, missing connector ports. Fix the spec and rebuild until it is clean. Read warnings; a diagonal segment means draw.io will route that line by itself and the result is unpredictable, so add `via` points.

## 5. Look at it (mandatory)

The linter cannot see everything, and a diagram you have not looked at is unverified. Preview it:

```bash
python3 scripts/preview.py diagram.drawio --port 8765 --width <canvas width>   # run in the background
```

Open `http://127.0.0.1:8765/` in a browser tool. After each rebuild, run the same command again and reload the page: it refreshes the diagram instead of starting a second server. Stop the server when you finish (`pkill -f preview.py`).

You must see the diagram at a size where an icon glyph, a label and a line are distinguishable, because a shrunken whole-page screenshot hides overlaps and blank icons. Two ways, depending on the browser tool:
- **A tool that gives true 1:1 screenshots** (for example Playwright): set the viewport to the canvas width and the canvas height plus about 40 px (the viewer adds some padding), and take one screenshot.
- **A tool that shrinks screenshots** (for example the Claude desktop built-in browser, whose zoom only crops): keep the normal viewport and scroll with `window.scrollTo(x, y)` in chunks, taking a screenshot of each, until you have seen every region.

The preview loads draw.io's viewer script and AWS shape library from viewer.diagrams.net; the diagram itself stays on this machine. If the draw.io desktop app is installed, `python3 scripts/preview.py diagram.drawio --png out.png` exports a PNG without a browser.

Check: every icon shows an AWS glyph (a plain coloured square means a wrong icon name); no text overlaps; no line crosses an icon or a label; every arrow ends at the right icon with a head; each group holds the right children; text is readable. Fix the spec, rebuild, re-render, repeat.

If you cannot render at all (no browser tool and no draw.io CLI), say so plainly and list what you could not verify. Never write "looks good" without having looked.

## 6. Deliver

Give the user: `diagram.drawio` (opens in draw.io desktop or app.diagrams.net), `spec.json` (the source: change it and rebuild rather than patching the XML, because a rebuild overwrites hand edits), the list of assumptions you made, and anything unverified. If they ask for changes, edit the spec, rebuild, lint and re-render; do not skip the look.

If the user wants a PNG or SVG and the draw.io CLI is not installed, tell them: File > Export as in draw.io produces it.

## 7. Cost estimate as a calculator.aws link

When the user wants a cost estimate, deliver a public AWS Pricing Calculator link (no AWS account needed) for the services in the agreed diagram. Read `references/cost-estimate.md` first; it has the file format, the unit traps and the browser steps.

1. Agree usage numbers in the same table style as step 2 (volumes per month, sizes, region). Unknown sizing gets a stated placeholder, marked "indicative".
2. Write `usage.json`. Look up field ids with `python3 scripts/calculator_link.py --fields <serviceCode>`.
3. `python3 scripts/calculator_link.py usage.json --dry-run` and read every printed line: units such as "million per month" live there, and a wrong one inflates the estimate a millionfold.
4. Post it (`python3 scripts/calculator_link.py usage.json`), then **price it in a browser**: open the link, click *Update estimate*, check each line against list prices, click *Share* and give the user that second link. A link that skips this opens read-only showing $0.00. With no browser tool, give the user the first link and these three clicks to do themselves (open, *Update estimate*, *Share*), and say the totals are unpriced.
5. Deliver the final link, the monthly and 12-month totals, each line's cost, the assumptions, and any line that looks wrong.
