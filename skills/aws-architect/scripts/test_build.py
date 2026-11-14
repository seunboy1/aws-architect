#!/usr/bin/env python3
"""Self-check: python scripts/test_build.py (no dependencies). The example must build clean; known mistakes must be caught."""
import copy, json, os, sys, xml.dom.minidom as md
sys.path.insert(0, os.path.dirname(__file__))
import build_drawio as b

spec = b.depth_sort(json.load(open(os.path.join(os.path.dirname(__file__), "..", "assets", "example-spec.json"))))
errs, warns = b.lint(spec)
assert not errs and not warns, (errs, warns)
md.parseString(b.build(spec))  # well-formed XML
assert b.build(spec).count("flowAnimation=1;flowAnimationDuration=2000;") == len(spec["edges"])  # every line animates slowly


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
assert any("label_pos" in e for e in bad(lambda s: s["nodes"][1].update(label_pos="right")))
assert any("'icon' has the wrong type" in e for e in bad(lambda s: s["nodes"][1].update(box=False, icon=None)))
s4 = copy.deepcopy(spec); s4["nodes"][1]["label"] = "Orders <API> & more"
out = b.build(s4); md.parseString(out)
assert "&amp;lt;API&amp;gt;" in out and "<API>" not in out  # escaped for HTML, then for XML
s5 = copy.deepcopy(spec); s5["groups"][0]["parent"] = s5["groups"][1]["id"]; s5["groups"][1]["parent"] = s5["groups"][0]["id"]
try:
    b.depth_sort(s5); raise AssertionError("parent loop accepted")
except SystemExit as e:
    assert "parent loop" in str(e)
out = b.build(spec)  # the example carries a flow panel and numbered arrows
assert "How data flows" in out and out.count("border-radius:9px") == len(spec["flow"]["steps"]) + len(spec["edges"])
s6 = copy.deepcopy(spec); s6["flow"]["steps"][0] = "Customer types <b>"
assert "&amp;lt;b&amp;gt;" in b.build(s6)
assert any("no line in flow.steps" in e for e in bad(lambda s: s["edges"][0].update(step=99)))
assert any("flow panel overlaps" in e for e in bad(lambda s: s["flow"].update(x=1300)))
assert any("does not fit" in e for e in bad(lambda s: s["flow"].update(y=800)))
# shape: misspelled keys, wrong types and bad ports fail before any geometry runs
assert any("did you mean 'label_pos'" in e for e in bad(lambda s: s["nodes"][1].update(lable_pos="top")))
assert any("missing 'cx'" in e for e in bad(lambda s: s["nodes"][1].pop("cx")))
assert any("wrong type" in e for e in bad(lambda s: s["nodes"][1].update(cx="300")))
assert any("exit must be" in e for e in bad(lambda s: s["edges"][0].update(exit="X")))
assert any("exit must be" in e for e in bad(lambda s: s["edges"][0].update(exit=[1.5, 0])))
assert any("via points" in e for e in bad(lambda s: s["edges"][0].update(via=[[1, "a"]])))
assert any("wrong type" in e for e in bad(lambda s: s["edges"][0].update(step="1")))
assert any("non-empty sentence" in e for e in bad(lambda s: s["flow"]["steps"].append("")))
assert any("unknown key 'colour'" in e for e in b.shape({**spec, "colour": "red"}))
s7 = copy.deepcopy(spec); s7.pop("flow")
assert any("no flow panel" in w for w in b.lint(b.depth_sort(s7))[1])
print("all checks passed")
