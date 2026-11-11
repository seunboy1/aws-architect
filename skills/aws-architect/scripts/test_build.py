#!/usr/bin/env python3
"""Self-check: python scripts/test_build.py (no dependencies). The example must build clean; known mistakes must be caught."""
import copy, json, os, sys, xml.dom.minidom as md
sys.path.insert(0, os.path.dirname(__file__))
import build_drawio as b

spec = b.depth_sort(json.load(open(os.path.join(os.path.dirname(__file__), "..", "assets", "example-spec.json"))))
errs, warns = b.lint(spec)
assert not errs and not warns, (errs, warns)
md.parseString(b.build(spec))  # well-formed XML


def bad(change):
    s = copy.deepcopy(spec)
    change(s)
    return b.lint(b.depth_sort(s))[0]


def through_icon(s):  # api -> dlq passes through the sqs icon
    s["edges"].append({"id": "x", "from": "api", "to": "dlq", "exit": "R", "entry": "L"})
assert any("passes through" in e for e in bad(through_icon))
def own_label(s):  # sqs label is on top; attach the edge there
    s["edges"][4]["exit"] = "T"
assert any("where its label is" in e for e in bad(own_label))
assert any("not in the icon table" in e for e in bad(lambda s: s["nodes"][1].update(icon="s3_glacier")))
assert any("outside its group" in e for e in bad(lambda s: s["nodes"][6].update(cx=2000, top=400)))
assert any("overlaps" in e for e in bad(lambda s: s["nodes"][1].update(cx=480)))
def title_clash(s):  # a vertical line through the top-left title of the VPC group
    s["nodes"].append({"id": "t", "label": "T", "icon": "lambda", "cx": 270, "top": 120, "parent": "edge"})
    s["edges"].append({"id": "y", "from": "t", "to": "worker", "exit": "B", "entry": "L", "via": [[270, 345], [700, 345], [700, 430]]})
s2 = copy.deepcopy(spec); title_clash(s2)
assert any("title of group" in w for w in b.lint(b.depth_sort(s2))[1])
s3 = copy.deepcopy(spec); s3["footnote"] = "x" * 900
assert any("footnote" in w for w in b.lint(b.depth_sort(s3))[1])
print("all checks passed")
