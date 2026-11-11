#!/usr/bin/env python3
"""Turn a diagram spec (JSON) into an editable draw.io file, and lint it.

Usage: python build_drawio.py spec.json out.drawio [--lint-only]

The spec uses ABSOLUTE coordinates for everything; this script converts them to the
parent-relative ones draw.io wants. The lint catches the mistakes that make generated
diagrams look wrong: lines through icons or labels, overlapping boxes, items outside their
group, an arrow leaving through its own label, and icon names not yet seen to render.
Exit code 1 means errors; warnings do not fail the build.
"""
import json
import sys
from xml.sax.saxutils import quoteattr

# category -> (fill, gradient)
CATS = {
    "compute": ("#D05C17", "#F78E04"), "integ": ("#BC1356", "#FF4F8B"),
    "db": ("#3334B9", "#4D72F3"), "storage": ("#277116", "#60A337"),
    "security": ("#C7131F", "#F54749"), "net": ("#5A30B5", "#945DF2"),
    "mgmt": ("#BC1356", "#F34482"), "ai": ("#116D5B", "#4AB29A"),
    "dev": ("#3334B9", "#4D72F3"), "user": ("#232F3D", "#232F3D"),
}
# icon name -> (category, direct_shape, verified_to_render). Source of truth: references/icons.md
ICONS = {}


def _add(cat, direct, verified, names):
    for n in names.split():
        ICONS[n] = (cat, direct, verified)


_add("compute", False, True, "lambda fargate")
_add("integ", False, True, "api_gateway sqs")
_add("db", False, True, "dynamodb aurora")
_add("storage", False, True, "s3")
_add("security", False, True, "waf secrets_manager identity_and_access_management key_management_service")
_add("mgmt", False, True, "cloudtrail config cloudwatch_2 budgets")
_add("ai", False, True, "bedrock")
_add("net", True, True, "nat_gateway application_load_balancer endpoints")
_add("user", True, True, "user")
# Verified by rendering scripts/icon_sheet.py (see references/icons.md for how to add more).
_add("compute", False, True, "ec2 ecs eks batch elastic_beanstalk lightsail app_runner ecr amplify")
_add("storage", False, True, "elastic_file_system elastic_block_store backup")
_add("db", False, True, "rds elasticache redshift neptune documentdb_with_mongodb_compatibility memorydb_for_redis keyspaces timestream athena glue emr quicksight lake_formation")
_add("net", False, True, "cloudfront route_53 transit_gateway direct_connect global_accelerator privatelink virtual_private_cloud")
_add("net", True, True, "network_load_balancer internet_gateway vpn_gateway site_to_site_vpn customer_gateway router")
_add("integ", False, True, "sns eventbridge step_functions appsync mq kinesis kinesis_data_firehose appflow simple_email_service")
_add("security", False, True, "cognito shield guardduty security_hub inspector certificate_manager detective macie firewall_manager network_firewall")
_add("mgmt", False, True, "systems_manager cloudformation organizations control_tower xray trusted_advisor cloudwatch")
_add("dev", False, True, "codebuild codepipeline codecommit codedeploy")
_add("ai", False, True, "sagemaker textract rekognition comprehend lex polly transcribe kendra")
_add("user", True, True, "users mobile_client client internet corporate_data_center traditional_server")
# Second batch verified the same way.
_add("db", False, True, "elasticsearch_service database_migration_service glue_databrew data_exchange")
_add("integ", False, True, "managed_streaming_for_kafka managed_workflows_for_apache_airflow kinesis_data_analytics kinesis_video_streams")
_add("storage", False, True, "datasync transfer_family storage_gateway snowball fsx")
_add("net", False, True, "cloud_map app_mesh elastic_load_balancing")
_add("dev", False, True, "codeartifact")
_add("security", False, True, "security_lake verified_access directory_service")
_add("compute", False, True, "iot_core auto_scaling2")
_add("ai", False, True, "bedrock_agentcore")

PTS = ("points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[0,1,0],"
       "[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];")
GROUP_BASE = ("points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],"
              "[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;"
              "fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;"
              "shape=mxgraph.aws4.group;verticalAlign=top;align=left;spacingLeft=30;dashed=0;")
GROUPS = {
    "account": GROUP_BASE + "grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;fontColor=#232F3E;",
    "vpc": GROUP_BASE + "grIcon=mxgraph.aws4.group_vpc;strokeColor=#8C4FFF;fillColor=none;fontColor=#5A30B5;",
    "public_subnet": GROUP_BASE + "grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7AA116;fillColor=#F2F6E8;fontColor=#248814;",
    "private_subnet": GROUP_BASE + "grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#00A4A6;fillColor=#E6F6F7;fontColor=#147EBA;",
    "zone": ("rounded=1;arcSize=2;dashed=1;dashPattern=6 4;strokeColor=#8D99A8;fillColor=none;verticalAlign=top;align=left;"
             "spacingLeft=10;spacingTop=2;fontSize=11;fontColor=#545B64;container=1;collapsible=0;recursiveResize=0;html=1;whiteSpace=wrap;"),
}
BOX_STYLE = "rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#F2F4F7;strokeColor=#5F6B7A;fontColor=#232F3E;fontSize=12;"
TEXT_STYLE = "text;html=1;align=left;verticalAlign=middle;whiteSpace=wrap;fontColor=#232F3E;"
EDGE_BASE = ("edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#545B64;"
             "strokeWidth=1.5;endArrow=block;endFill=1;endSize=5;fontSize=10;fontColor=#545B64;labelBackgroundColor=#FFFFFF;")
PORTS = {"R": (1, 0.5), "L": (0, 0.5), "T": (0.5, 0), "B": (0.5, 1)}
SIZE = 60


def port(p):
    return tuple(PORTS[p]) if isinstance(p, str) else tuple(p)


def node_rect(n):
    if n.get("box"):
        return (n["x"], n["y"], n["w"], n["h"])
    return (n["cx"] - SIZE // 2, n["top"], SIZE, SIZE)


def label_rect(n):
    """Estimated box of the text under/over/left of an icon (None for boxes: text is inside)."""
    if n.get("box"):
        return None
    x, y, w, h = node_rect(n)
    lines = [n["label"]] + ([n["sub"]] if n.get("sub") else [])
    tw = max(len(n["label"]) * 6.6, len(n.get("sub", "")) * 5.4) + 8
    th = 15 * len(lines)
    pos = n.get("label_pos", "bottom")
    if pos == "bottom":
        return (x + w / 2 - tw / 2, y + h + 2, tw, th)
    if pos == "top":
        return (x + w / 2 - tw / 2, y - th - 2, tw, th)
    return (x - tw - 4, y + h / 2 - th / 2, tw, th)  # left


def overlap(a, b, tol=1):
    return a[0] + tol < b[0] + b[2] and b[0] + tol < a[0] + a[2] and a[1] + tol < b[1] + b[3] and b[1] + tol < a[1] + a[3]


def inside(inner, outer, margin=0):
    return (inner[0] >= outer[0] + margin and inner[1] >= outer[1] + margin and
            inner[0] + inner[2] <= outer[0] + outer[2] - margin and inner[1] + inner[3] <= outer[1] + outer[3] - margin)


def seg_hits(p, q, r, tol=1):
    x1, y1, x2, y2 = min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1])
    if y1 == y2:
        return r[1] + tol < y1 < r[1] + r[3] - tol and x1 < r[0] + r[2] - tol and x2 > r[0] + tol
    if x1 == x2:
        return r[0] + tol < x1 < r[0] + r[2] - tol and y1 < r[1] + r[3] - tol and y2 > r[1] + tol
    return False


def edge_points(e, nodes):
    a, b = nodes[e["from"]], nodes[e["to"]]
    (ax, ay, aw, ah), (bx, by, bw, bh) = node_rect(a), node_rect(b)
    px, py = port(e["exit"])
    qx, qy = port(e["entry"])
    return [(ax + px * aw, ay + py * ah)] + [tuple(v) for v in e.get("via", [])] + [(bx + qx * bw, by + qy * bh)]


def lint(spec):
    errs, warns = [], []
    nodes = {n["id"]: n for n in spec.get("nodes", [])}
    groups = {g["id"]: g for g in spec.get("groups", [])}
    ids = [x["id"] for x in spec.get("nodes", []) + spec.get("groups", []) + spec.get("edges", [])]
    for i in {i for i in ids if ids.count(i) > 1}:
        errs.append(f"duplicate id: {i}")
    canvas = spec.get("canvas", {"width": 1900, "height": 1260})
    grect = {k: (g["x"], g["y"], g["w"], g["h"]) for k, g in groups.items()}
    if len(nodes) > 14 or len(spec.get("edges", [])) > 12:
        warns.append(f"{len(nodes)} nodes and {len(spec.get('edges', []))} edges is over the budget (14 / 12); consider an overview plus detail diagrams")
    per_line = (canvas["width"] - 80) / 5.0
    if len(spec.get("footnote", "")) > 2 * per_line:
        warns.append("footnote is too long for two lines at this canvas width; shorten it or widen the canvas")
    for g in groups.values():
        if g.get("kind", "zone") not in GROUPS:
            errs.append(f"group {g['id']}: unknown kind '{g.get('kind')}' (use {', '.join(GROUPS)})")
        if g.get("parent") and g["parent"] in grect and not inside(grect[g["id"]], grect[g["parent"]]):
            errs.append(f"group {g['id']} sticks out of its parent {g['parent']}")
    items = []  # (id, kind, rect)
    for n in nodes.values():
        if n.get("box") is None and n.get("icon") not in ICONS:
            errs.append(f"node {n['id']}: icon '{n.get('icon')}' is not in the icon table (references/icons.md)")
        elif not n.get("box") and not ICONS[n["icon"]][2]:
            warns.append(f"node {n['id']}: icon '{n['icon']}' has not been seen to render; check it in the preview")
        if len(n["label"]) > 28 or len(n.get("sub", "")) > 40:
            warns.append(f"node {n['id']}: label is long; shorten it so it stays under its neighbours")
        r, lr = node_rect(n), label_rect(n)
        p = n.get("parent")
        if p and p in grect and not inside(r, grect[p], 4):
            errs.append(f"node {n['id']} is outside its group {p}")
        if p and p in grect and lr and not inside(lr, grect[p]):
            warns.append(f"node {n['id']}: its label may stick out of group {p}")
        if r[0] < 0 or r[1] < 0 or r[0] + r[2] > canvas["width"] or r[1] + r[3] > canvas["height"]:
            errs.append(f"node {n['id']} is outside the canvas")
        items.append((n["id"], "icon", r))
        if lr:
            items.append((n["id"], "label", lr))
    for i, (ia, ka, ra) in enumerate(items):
        for ib, kb, rb in items[i + 1:]:
            if ia != ib and overlap(ra, rb):
                errs.append(f"{ka} of {ia} overlaps {kb} of {ib}")
    for e in spec.get("edges", []):
        if e["from"] not in nodes or e["to"] not in nodes:
            errs.append(f"edge {e['id']}: unknown node in from/to")
            continue
        if "exit" not in e or "entry" not in e:
            errs.append(f"edge {e['id']}: set exit and entry (R, L, T, B or [x, y] fractions)")
            continue
        pts = edge_points(e, nodes)
        a, b = nodes[e["from"]], nodes[e["to"]]
        for p, q in zip(pts, pts[1:]):
            if p[0] != q[0] and p[1] != q[1]:
                warns.append(f"edge {e['id']}: diagonal segment {p}->{q}; add 'via' points so every segment is horizontal or vertical")
                continue
            for oid, o in nodes.items():
                for kind, rr in (("icon", node_rect(o)), ("label", label_rect(o))):
                    if rr and oid not in (e["from"], e["to"]) and seg_hits(p, q, rr):
                        errs.append(f"edge {e['id']} passes through the {kind} of {oid}")
            for nid, o in ((e["from"], a), (e["to"], b)):  # an arrow must not cross its own end's label
                lr = label_rect(o)
                if lr and seg_hits(p, q, lr):
                    errs.append(f"edge {e['id']} runs through the label of {nid}; move that label to another side")
        for gid, g in groups.items():  # the title sits in the top-left of its group
            tw = (35 if g.get("kind", "zone") != "zone" else 15) + len(g["label"]) * 6.5
            title = (g["x"], g["y"], tw, 26)
            if any(seg_hits(p, q, title) for p, q in zip(pts, pts[1:])):
                warns.append(f"edge {e['id']} runs through the title of group {gid}; route it lower or to the side")
        for nid, o, pt in ((e["from"], a, port(e["exit"])), (e["to"], b, port(e["entry"]))):
            side = {"bottom": pt[1] == 1, "top": pt[1] == 0, "left": pt[0] == 0}.get(o.get("label_pos", "bottom"), False)
            if label_rect(o) and side:
                errs.append(f"edge {e['id']} attaches to {nid} on the side where its label is; use label_pos on another side")
    return errs, warns


def build(spec):
    abs_pos = {"1": (0, 0)}
    cells, edge_cells = [], []

    def vertex(cid, value, style, x, y, w, h, parent):
        px, py = abs_pos.get(parent or "1", (0, 0))
        abs_pos[cid] = (x, y)
        cells.append(f'<mxCell id="{cid}" value={quoteattr(value)} style={quoteattr(style)} vertex="1" parent="{parent or "1"}">'
                     f'<mxGeometry x="{x - px}" y="{y - py}" width="{w}" height="{h}" as="geometry"/></mxCell>')

    def lab(n):
        v = f"<b>{n['label']}</b>"
        return v + (f'<br><font color="#545B64" style="font-size:10px">{n["sub"]}</font>' if n.get("sub") else "")

    if spec.get("title"):
        vertex("title", f"<b>{spec['title']}</b>", TEXT_STYLE + "fontSize=18;", 40, 2, 1100, 30, "1")
    if spec.get("subtitle"):
        vertex("subtitle", spec["subtitle"], TEXT_STYLE + "fontSize=11;fontColor=#545B64;", 40, 24, 1400, 20, "1")
    for g in sorted(spec.get("groups", []), key=lambda g: g.get("depth", 0)):  # parents are listed first
        vertex(g["id"], g["label"], GROUPS[g.get("kind", "zone")], g["x"], g["y"], g["w"], g["h"], g.get("parent"))
    for n in spec.get("nodes", []):
        if n.get("box"):
            vertex(n["id"], lab(n), BOX_STYLE, n["x"], n["y"], n["w"], n["h"], n.get("parent"))
            continue
        cat, direct, _ = ICONS[n["icon"]]
        fill, grad = CATS[cat]
        pos = {"bottom": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
               "top": "verticalLabelPosition=top;verticalAlign=bottom;align=center;",
               "left": "labelPosition=left;verticalLabelPosition=middle;align=right;verticalAlign=middle;spacingRight=6;"
               }[n.get("label_pos", "bottom")]
        if direct:
            shape = f"outlineConnect=0;gradientColor=none;fillColor={fill};strokeColor=none;shape=mxgraph.aws4.{n['icon']};"
        else:
            shape = (f"outlineConnect=0;gradientColor={grad};gradientDirection=north;fillColor={fill};strokeColor=#ffffff;"
                     f"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{n['icon']};")
        x, y, w, h = node_rect(n)
        vertex(n["id"], lab(n), f"sketch=0;{PTS}{shape}dashed=0;html=1;fontSize=11;fontColor=#232F3E;aspect=fixed;{pos}", x, y, w, h, n.get("parent"))
    nodes = {n["id"]: n for n in spec.get("nodes", [])}
    for e in spec.get("edges", []):  # edges last, so they draw on top of every group
        ex, ey = port(e["exit"])
        nx, ny = port(e["entry"])
        s = EDGE_BASE + f"exitX={ex};exitY={ey};exitDx=0;exitDy=0;entryX={nx};entryY={ny};entryDx=0;entryDy=0;"
        s += "dashed=1;dashPattern=6 4;strokeWidth=1.2;" if e.get("dashed") else ""
        s += "jumpStyle=arc;jumpSize=10;" if e.get("hop") else ""
        via = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in e.get("via", []))
        geo = '<Array as="points">' + via + "</Array>" if via else ""
        edge_cells.append(f'<mxCell id="{e["id"]}" value={quoteattr(e.get("label", ""))} style={quoteattr(s)} edge="1" parent="1" '
                          f'source="{e["from"]}" target="{e["to"]}"><mxGeometry relative="1" as="geometry">'
                          f'{geo}</mxGeometry></mxCell>')
    if spec.get("footnote"):
        c = spec.get("canvas", {"width": 1900, "height": 1260})
        vertex("footnote", spec["footnote"], TEXT_STYLE + "fontSize=10;fontColor=#545B64;", 40, c["height"] - 50, c["width"] - 80, 30, "1")
    c = spec.get("canvas", {"width": 1900, "height": 1260})
    return ('<mxfile host="app.diagrams.net"><diagram id="arch" name="Architecture">'
            f'<mxGraphModel dx="{c["width"]}" dy="{c["height"]}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
            f'fold="1" page="1" pageScale="1" pageWidth="{c["width"]}" pageHeight="{c["height"]}" math="0" shadow="0"><root>'
            '<mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + "".join(edge_cells) +
            '</root></mxGraphModel></diagram></mxfile>')


def depth_sort(spec):
    """Order groups so a parent always comes before its children."""
    by_id = {g["id"]: g for g in spec.get("groups", [])}

    def d(g):
        return 0 if not g.get("parent") or g["parent"] not in by_id else 1 + d(by_id[g["parent"]])
    for g in by_id.values():
        g["depth"] = d(g)
    return spec


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if not args or ("--lint-only" not in argv and len(args) < 2):
        print(__doc__)
        return 2
    spec = depth_sort(json.load(open(args[0], encoding="utf-8")))
    errs, warns = lint(spec)
    for w in warns:
        print("WARN ", w)
    for e in errs:
        print("ERROR", e)
    if errs:
        print(f"{len(errs)} error(s): fix the spec and rebuild.")
        return 1
    if "--lint-only" not in argv:
        open(args[1], "w", encoding="utf-8").write(build(spec))
        print(f"wrote {args[1]} ({len(spec.get('nodes', []))} nodes, {len(spec.get('edges', []))} edges, {len(warns)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
