# Changelog

## 1.1.0 (2026-11-14)

- Diagrams: every connector has a slow flow animation; a numbered "How data flows" panel sits beside the diagram, with matching number badges on the arrows.
- Diagrams: the spec is checked for unknown or misspelled keys, wrong types and bad ports before layout; labels are escaped so `<` and `&` show up.
- Cost: `calculator_link.py --check LINK usage.json` verifies a priced link (unpriced links, inputs that did not survive, Bedrock model lines recomputed from AWS's official Price List). SKILL.md makes it a required step before delivery.
- Cost: usage files are validated like the website's form: whole numbers, ranges, units and dropdown options; dropdowns accept their visible label; a Bedrock route with an unset or inconsistent model fails.
- Clearer errors for wrong service codes, label positions, group loops; network retries.

## 1.0.0 (2026-11-11)

- First release: interview, draw.io diagram, calculator.aws link.
