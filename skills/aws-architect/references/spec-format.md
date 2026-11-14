# Spec format

A spec is one JSON file. **All coordinates are absolute** (pixels from the top-left of the canvas); the script converts them to the parent-relative values draw.io needs. Start from `assets/example-spec.json`.

```json
{
  "title": "System name", "subtitle": "version, date, owner (optional)",
  "footnote": "one or two lines of notes, drawn at the bottom (optional)",
  "canvas": {"width": 1520, "height": 960},
  "groups": [ ... ], "nodes": [ ... ], "edges": [ ... ]
}
```

## groups
`{"id", "label", "kind", "x", "y", "w", "h", "parent"}`
- `kind`: `account` (AWS Cloud frame), `vpc`, `public_subnet`, `private_subnet`, or `zone` (dashed box for "managed services", "security", "public entry", anything else).
- `parent`: the id of the group that contains it (nest account > vpc > subnet). Omit for a top-level group. The script orders parents before children for you.

## nodes
Icon node: `{"id", "label", "sub", "icon", "cx", "top", "parent", "label_pos"}`
- `icon`: a name from `references/icons.md`. Icons are 60x60; `cx` is the centre x, `top` the top y.
- `label` is the bold name (keep it under 28 characters); `sub` is a short grey line (5 words or fewer).
- `label_pos`: where the text goes: `bottom` (default), `top` or `left`. Put it on a side with **no arrow** attached; the linter rejects an arrow that attaches on the label's side.
- `parent`: the group id the icon sits in, or omit.

Box node (for things without an AWS icon, such as a third-party service): `{"id", "label", "sub", "box": true, "x", "y", "w", "h", "parent"}`.

## edges
`{"id", "from", "to", "exit", "entry", "via", "label", "dashed", "hop"}`
- `exit` / `entry`: which side of the node the line leaves or arrives on: `"R"`, `"L"`, `"T"`, `"B"` or `[x, y]` fractions (0-1) of the node box, e.g. `[1, 0.25]` for the upper part of the right side. Always set both.
- `via`: absolute `[x, y]` waypoints. Every segment between exit point, waypoints and entry point must be horizontal or vertical. Use none when the two ports are already in line.
- Every edge is drawn with a slow flow animation (moving dashes along the arrow); there is nothing to set.
- `label`: 1-3 words; `dashed: true` for async, return or redrive paths; `hop: true` draws a small arc where this line crosses another (put it on the less important line).
- When two edges leave one side of the same icon, use different fractions (for example `[1, 0.3]` and `[1, 0.7]`) so they do not overlap.

## flow (the "How data flows" panel)
`{"x", "y", "w", "steps": ["...", "..."], "title"}` at the top level of the spec.
- Every diagram gets one: a numbered list beside the diagram that tells a reader what happens, in order ("A customer places an order in the app", "The worker saves the order").
- Give an edge `"step": n` to put the matching number badge on that arrow. Steps without an arrow (a check inside one service) are fine; an edge step with no line in `steps` is an error.
- Place it to the right of the account frame (widen the canvas; about 340 px wide), clear of every group, icon and line. The height is worked out from the text; the linter reports it if it does not fit.
- Keep each step one sentence of plain words: who or what, does what, to which data. Use the same order as the numbered main flow agreed in step 2.

## Working out coordinates
- Plan a grid first: columns about 190 px apart, rows about 120 px apart (an icon plus a two-line label needs about 100 px).
- A group must be at least 20 px bigger than its contents on every side, and 40 px taller at the top for its title.
- Put elements that exchange the most traffic next to each other and keep the main flow on one line.
- Line two icons up (same centre y or same cx) and the connector between them is a straight line with no `via`.
