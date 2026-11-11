#!/usr/bin/env python3
"""Turn a small usage file into a shareable AWS Pricing Calculator link (calculator.aws).

    python3 scripts/calculator_link.py usage.json            # posts, prints the link
    python3 scripts/calculator_link.py usage.json --dry-run  # writes the payload only

The calculator has no public API. This posts the same JSON its own Share button posts
(see references/cost-estimate.md). Prices are not computed here: the calculator prices
every service itself when the link is opened, so serviceCost is sent as 0.
Field ids and units come from the calculator's published service definitions, so a typo
fails here instead of producing a silently empty line in the estimate.
"""
import argparse
import gzip
import json
import sys
import urllib.request
import uuid
from datetime import datetime, timezone

CDN = "https://d1qsjq9pzbk1k6.cloudfront.net"
SAVE_URL = "https://dnd5zrqcec4or.cloudfront.net/Prod/v2/saveAs"
LOCATIONS = "https://b0.p.awsstatic.com/locations/1.0/aws/current/locations.json"
SKIP = {"alert", "bodyText", "condition"}
_cache = {}


def fetch(url):
    if url not in _cache:
        req = urllib.request.Request(url, headers={"User-Agent": "aws-architect-skill"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
        _cache[url] = json.loads(gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw)
    return _cache[url]


def inputs(node, out):
    """Every input component in a template, first occurrence of each id wins."""
    if isinstance(node, dict):
        if node.get("type") == "input" and "id" in node and node.get("subType") not in SKIP:
            out.setdefault(node["id"], node)
        for v in node.values():
            inputs(v, out)
    elif isinstance(node, list):
        for v in node:
            inputs(v, out)
    return out


def default_component(c):
    """What the website stores for a field the user left alone, or None."""
    st = c.get("subType")
    if st == "dropdown" and c.get("options"):
        return {"value": str(c.get("defaultDropDownItem") or c["options"][0]["id"])}
    if "defaultValue" in c:
        return encode(c, c["defaultValue"], None)
    return None


def encode(c, value, unit):
    st = c.get("subType")
    comp = {"value": str(value)}
    if st == "fileSize":
        opt = c.get("defaultOption", {})
        comp["unit"] = f"{unit or opt.get('size', 'gb')}|{opt.get('frequency', 'NA')}"
    elif st == "frequency":
        comp["unit"] = unit or c.get("defaultFrequency") or "perMonth"
    elif unit:
        comp["unit"] = unit
    return comp


def describe(c, comp):
    """'Standard queue requests = 1 million per month': the unit wording lives in option labels."""
    unit = comp.get("unit", "")
    for o in c.get("options") or []:
        if o.get("id") == unit or (c.get("subType") == "dropdown" and o.get("id") == comp["value"]):
            unit = o.get("label", unit)
    return f"{c.get('label', c['id'])} = {comp['value']} {unit}".rstrip()


def list_fields(code, template_id=None):
    d = fetch(f"{CDN}/data/{code}/en_US.json")
    for t in (t for t in d["templates"] if isinstance(t, dict)):
        if template_id and t["id"] != template_id:
            continue
        print(f"template {t['id']}  ({t.get('title') or ''})")
        for fid, c in inputs(t, {}).items():
            opts = ", ".join(f"{o['id']}={o.get('label')}" for o in c.get("options") or [])
            sizes = ", ".join(s["id"] for s in c.get("dropDownSize") or [])
            print(f"  {fid:45} {c.get('subType'):14} {c.get('label', '')[:60]}"
                  + (f"  [{opts or sizes}]" if opts or sizes else ""))


def build_service(entry, region, region_name, definition, template_id=None, log=print):
    templates = [t for t in definition["templates"] if isinstance(t, dict)]
    tpl = next((t for t in templates if t["id"] == (template_id or templates[0]["id"])), None)
    if tpl is None:
        raise SystemExit(f"{definition['serviceCode']}: no template {template_id!r}; "
                         f"choose from {[t['id'] for t in templates]}")
    fields = inputs(tpl, {})
    comps = {}
    for fid, c in fields.items():
        d = default_component(c)
        if d is not None:
            comps[fid] = d
    for fid, val in entry.get("fields", {}).items():
        if fid not in fields:
            raise SystemExit(f"{definition['serviceCode']}: unknown field {fid!r}. "
                             f"Known: {', '.join(sorted(fields))}")
        value, unit = (val + [None])[:2] if isinstance(val, list) else (val, None)
        comps[fid] = encode(fields[fid], value, unit)
        log(f"  {definition['serviceCode']}: {describe(fields[fid], comps[fid])}")
    return {
        "calculationComponents": comps,
        "serviceCode": definition["serviceCode"],
        "region": region,
        "estimateFor": tpl["id"],
        "version": definition["version"],
        "description": entry.get("description", ""),
        "serviceCost": {"monthly": 0},
        "serviceName": definition["serviceName"],
        "regionName": region_name,
    }


def parent_of(code, manifest):
    for s in manifest:
        if isinstance(s.get("templates"), list) and code in s["templates"] and s["serviceCode"] != code:
            return s["serviceCode"]
    return None


def build_payload(usage, get=fetch):
    manifest = get(f"{CDN}/manifest/en_US.json")["awsServices"]
    names = {loc["code"]: loc["name"] for loc in get(LOCATIONS).values() if "code" in loc}
    services = {}
    for entry in usage["services"]:
        code = entry["service"]
        region = entry.get("region", usage["region"])
        region_name = names.get(region, region)
        svc = build_service(entry, region, region_name, get(f"{CDN}/data/{code}/en_US.json"),
                            entry.get("template"))
        parent = parent_of(code, manifest)
        if parent:  # composite service (S3, DynamoDB, Rekognition...): wrap like the website does
            pdef = get(f"{CDN}/data/{parent}/en_US.json")
            sub = {k: svc[k] for k in ("calculationComponents", "serviceCode", "region",
                                        "estimateFor", "version", "description", "serviceCost")}
            svc = {"version": pdef["version"], "serviceCode": parent,
                   "estimateFor": pdef.get("templateId", parent), "region": region,
                   "description": svc["description"], "subServices": [sub],
                   "serviceCost": {"monthly": 0}, "serviceName": pdef["serviceName"],
                   "regionName": region_name}
        services[f"{svc['serviceCode']}-{uuid.uuid4()}"] = svc
    return {
        "name": usage["name"], "services": services, "groups": {},
        "groupSubtotal": {"monthly": 0}, "totalCost": {"monthly": 0, "upfront": 0},
        "support": {},
        "metaData": {"locale": "en_US", "currency": "USD",
                     "createdOn": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                     "source": "calculator-platform"},
    }


def post(payload):
    req = urllib.request.Request(SAVE_URL, data=json.dumps(payload).encode(), method="POST",
                                 headers={"content-type": "application/json",
                                          "referer": "https://calculator.aws/"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    key = json.loads(body["body"])["savedKey"]
    return f"https://calculator.aws/#/estimate?id={key}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("usage", nargs="?")
    ap.add_argument("--dry-run", action="store_true", help="write <usage>.payload.json, do not post")
    ap.add_argument("--fields", metavar="SERVICE_CODE", help="list a service's field ids, units and templates")
    a = ap.parse_args()
    if a.fields:
        return list_fields(a.fields)
    if not a.usage:
        ap.error("usage file required")
    payload = build_payload(json.load(open(a.usage)))
    if a.dry_run:
        out = a.usage.rsplit(".", 1)[0] + ".payload.json"
        json.dump(payload, open(out, "w"), indent=1)
        print(f"wrote {out} ({len(payload['services'])} services)")
        return
    print(post(payload))


if __name__ == "__main__":
    sys.exit(main())
