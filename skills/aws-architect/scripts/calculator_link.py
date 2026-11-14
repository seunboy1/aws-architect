#!/usr/bin/env python3
"""Turn a small usage file into a shareable AWS Pricing Calculator link (calculator.aws).

    python3 scripts/calculator_link.py usage.json            # posts, prints the link
    python3 scripts/calculator_link.py usage.json --dry-run  # writes the payload only
    python3 scripts/calculator_link.py --check LINK usage.json  # verifies a priced, shared link

The calculator has no public API. This posts the same JSON its own Share button posts
(see references/cost-estimate.md). Prices are not computed here: the calculator prices
every service itself when the link is opened, so serviceCost is sent as 0.
Every input is checked against the calculator's published service definitions (field ids,
units, dropdown options, whole numbers, ranges), so a mistake fails here instead of producing
a silently wrong line. --check reads the priced estimate back, confirms every input survived,
and recomputes Bedrock model lines from AWS's official Price List.
"""
import argparse
import contextlib
import difflib
import gzip
import io
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

CDN = "https://d1qsjq9pzbk1k6.cloudfront.net"
SAVE_URL = "https://dnd5zrqcec4or.cloudfront.net/Prod/v2/saveAs"
SAVED = "https://d3knqfixx3sbls.cloudfront.net/{}"  # where calculator.aws reads a saved estimate
LOCATIONS = "https://b0.p.awsstatic.com/locations/1.0/aws/current/locations.json"
PRICE_LIST = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/{}/index.json"
SKIP = {"alert", "bodyText", "condition"}
NUMERIC = {"numericInput", "percentInput", "fileSize", "frequency", "durationInput", "throughput"}
SIZES = {"kb", "mb", "gb", "tb"}
USAGE_KEYS, ENTRY_KEYS = {"name", "region", "services"}, {"service", "description", "fields", "template", "region"}
# Bedrock model dropdowns: one set per inference route; all of a route's dropdowns must name one model
MODEL_KEYS = ("modelSelection", "selectedModel_od", "selectedModel", "cacheRead", "cacheWrite")
ROUTES = {"global": "", "geo": "Geostan", "ir": "IRstan"}
_cache = {}


def fetch(url):
    if url not in _cache:
        req = urllib.request.Request(url, headers={"User-Agent": "aws-architect-skill"})
        for attempt in range(3):  # the CDN resets connections now and then
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    raw = r.read()
                break
            except urllib.error.HTTPError:
                raise
            except OSError:
                if attempt == 2:
                    raise
        _cache[url] = json.loads(gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw)
    return _cache[url]


def definition(code, get=fetch):
    """A service's definition; a wrong code gets the nearest real ones instead of a bare HTTP 403."""
    try:
        return get(f"{CDN}/data/{code}/en_US.json")
    except urllib.error.HTTPError as e:
        manifest = get(f"{CDN}/manifest/en_US.json")["awsServices"]
        names = {s["serviceCode"]: s.get("name", "").strip() for s in manifest}  # EC2's code is eC2Next
        for s in manifest:
            for t in s["templates"] if isinstance(s.get("templates"), list) else []:
                if isinstance(t, str):
                    names.setdefault(t, names[s["serviceCode"]])
        word = code.lower().removeprefix("amazon").removeprefix("aws")
        close = [k for k, n in names.items() if word and word in (k + " " + n).lower()][:8] or [
            k for k in names if k.lower() in difflib.get_close_matches(code.lower(), [k.lower() for k in names], 6, 0.5)]
        hint = ", ".join(f"{k} ({names[k]})" for k in close) or "no close match"
        raise SystemExit(f"unknown service code {code!r} (HTTP {e.code}). Did you mean: {hint}?")


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
    d = definition(code)
    for t in (t for t in d["templates"] if isinstance(t, dict)):
        if template_id and t["id"] != template_id:
            continue
        print(f"template {t['id']}  ({t.get('title') or ''})")
        for fid, c in inputs(t, {}).items():
            opts = ", ".join(f"{o['id']}={o.get('label')}" for o in c.get("options") or [])
            sizes = ", ".join(s["id"] for s in c.get("dropDownSize") or [])
            print(f"  {fid:45} {c.get('subType'):14} {c.get('label', '')[:60]}"
                  + (f"  [{opts or sizes}]" if opts or sizes else ""))


def option_label(c, value):
    return next((o.get("label") for o in c.get("options") or [] if str(o.get("id")) == str(value)), None)


def check_value(code, fid, c, val):
    """Validate one usage value against its field definition; returns (value, unit) ready to encode.

    The website does not reject bad input: it silently prices the field as empty or as its
    default, so every rule it enforces in the form is enforced here instead."""
    where = f"{code}: {fid}"
    if isinstance(val, list):
        if not 1 <= len(val) <= 2:
            raise SystemExit(f"{where}: use value or [value, unit], got {val!r}")
        value, unit = (val + [None])[:2]
    else:
        value, unit = val, None
    st = c.get("subType")
    if st == "dropdown":
        ids = {str(o.get("id")): o for o in c.get("options") or []}
        if unit is not None:
            raise SystemExit(f"{where}: a dropdown takes no unit")
        if str(value) not in ids:  # allow the label a person sees, e.g. "Anthropic: Claude Sonnet 5.5"
            by_label = [i for i, o in ids.items() if o.get("label") == value]
            if len(by_label) != 1:
                raise SystemExit(f"{where}: {value!r} is not an option. Options: "
                                 + ", ".join(f"{i} ({o.get('label')})" for i, o in ids.items()))
            value = by_label[0]
        return str(value), None
    if st in NUMERIC:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SystemExit(f"{where}: needs a number, got {value!r}")
        rules = c.get("validations") or {}
        # min/max are in the field's default unit, so only check them when no unit is given
        if rules.get("allowDecimals") is False and not float(value).is_integer():
            raise SystemExit(f"{where}: must be a whole number, got {value}")
        if unit is None and not rules.get("minValue", value) <= value <= rules.get("maxValue", value):
            raise SystemExit(f"{where} = {value} is outside {rules.get('minValue')}..{rules.get('maxValue')}")
        if unit is not None and st == "fileSize":
            allowed = {s["id"] for s in c.get("dropDownSize") or []} or SIZES
            if unit not in allowed:
                raise SystemExit(f"{where}: unit {unit!r} not allowed; use one of {sorted(allowed)}")
        if unit is not None and st == "frequency":
            allowed = {o["id"] for o in c.get("options") or []}
            if allowed and unit not in allowed:
                raise SystemExit(f"{where}: unit {unit!r} not allowed; use one of {sorted(allowed)}")
        if unit is not None and st not in ("fileSize", "frequency"):
            raise SystemExit(f"{where}: this field takes no unit, got {unit!r}")
    return value, unit


def check_models(code, fields, comps, given):
    """Bedrock: the dropdowns of one route must name one model, and the chosen route's model must be set."""
    route = comps.get("location", {}).get("value") if "location" in fields else None
    if route is None:
        return
    for suffix in set(ROUTES.values()):
        labels = {}
        for key in MODEL_KEYS:
            fid = key + suffix
            if fid in given:
                labels[fid] = (option_label(fields[fid], comps[fid]["value"]) or "").split(":")[-1].strip()
        if len(set(labels.values())) > 1:
            raise SystemExit(f"{code}: model dropdowns disagree: {labels}. Set them all to one model.")
    suffix = ROUTES.get(route)
    if suffix is not None and comps.get("tierIR", {}).get("value", "standard") == "standard":
        missing = [k + suffix for k in MODEL_KEYS[:3] if k + suffix in fields and k + suffix not in given]
        if missing:
            raise SystemExit(f"{code}: route {route!r} is selected but {missing} are not set; "
                             f"they would silently default to {option_label(fields[missing[0]], comps[missing[0]]['value'])!r}")


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
    given = entry.get("fields", {})
    if not isinstance(given, dict):
        raise SystemExit(f"{definition['serviceCode']}: fields must be an object, got {given!r}")
    for fid, val in given.items():
        if fid not in fields:
            raise SystemExit(f"{definition['serviceCode']}: unknown field {fid!r}. "
                             f"Known: {', '.join(sorted(fields))}")
        value, unit = check_value(definition["serviceCode"], fid, fields[fid], val)
        comps[fid] = encode(fields[fid], value, unit)
        log(f"  {definition['serviceCode']}: {describe(fields[fid], comps[fid])}")
    check_models(definition["serviceCode"], fields, comps, given)
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


def check_usage(usage):
    """Shape of usage.json: unknown or misspelled keys fail instead of being ignored."""
    if not isinstance(usage, dict) or set(usage) - USAGE_KEYS or not USAGE_KEYS <= set(usage):
        raise SystemExit(f"usage.json needs exactly {sorted(USAGE_KEYS)}, got {sorted(usage) if isinstance(usage, dict) else usage!r}")
    if not isinstance(usage["services"], list) or not usage["services"]:
        raise SystemExit("usage.json: services must be a non-empty list")
    for i, e in enumerate(usage["services"]):
        if not isinstance(e, dict) or "service" not in e or set(e) - ENTRY_KEYS:
            raise SystemExit(f"usage.json services[{i}]: allowed keys are {sorted(ENTRY_KEYS)} "
                             f"and 'service' is required, got {sorted(e) if isinstance(e, dict) else e!r}")


def build_payload(usage, get=fetch):
    check_usage(usage)
    manifest = get(f"{CDN}/manifest/en_US.json")["awsServices"]
    names = {loc["code"]: loc["name"] for loc in get(LOCATIONS).values() if "code" in loc}
    services = {}
    for entry in usage["services"]:
        code = entry["service"]
        region = entry.get("region", usage["region"])
        if region not in names:
            raise SystemExit(f"{code}: unknown region {region!r}")
        region_name = names[region]
        svc = build_service(entry, region, region_name, definition(code, get),
                            entry.get("template"))
        parent = parent_of(code, manifest)
        if parent:  # composite service (S3, DynamoDB, Rekognition...): wrap like the website does
            pdef = definition(parent, get)
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


def lines(estimate):
    """Priced lines of a saved estimate: (serviceCode, region, description, monthly, components)."""
    for svc in estimate["services"].values():
        for s in svc.get("subServices") or [svc]:
            yield (s["serviceCode"], s.get("region", svc.get("region")), s.get("description") or svc.get("description", ""),
                   float((s.get("serviceCost") or {}).get("monthly") or 0), s.get("calculationComponents") or {})


def model_prices(region, model, route, get=fetch):
    """Official per-1M-token prices for one Bedrock model and route, from the AWS Price List."""
    d = get(PRICE_LIST.format(region))
    found = {}
    for sku, p in d["products"].items():
        a = p["attributes"]
        ut = a.get("usagetype", "").lower()
        if (a.get("model") != model or a.get("feature") != "On-demand Inference"
                or any(w in ut for w in ("long_ctx", "_1h", "batch", "priority", "flex", "latency"))
                or ("global" in ut) != (route == "global")):
            continue
        dim = next(iter(next(iter(d["terms"]["OnDemand"][sku].values()))["priceDimensions"].values()))
        found.setdefault(a.get("inferenceType"), set()).add(float(dim["pricePerUnit"]["USD"]))
    if not found:
        raise ValueError(f"no official price for {model} ({route}) in {region}")
    return found


def one(prices, kind, model):
    v = prices.get(kind) or set()
    if kind == "Prompt cache write input tokens" and v:
        return min(v)  # 5-minute cache, the one the calculator prices; older models also list 1-hour
    if len(v) != 1:
        raise ValueError(f"{'no' if not v else 'ambiguous'} official {kind.lower()} price for {model}: {sorted(v)}")
    return next(iter(v))


def bedrock_expected(code, region, comps, get=fetch):
    """Recompute a Bedrock line the way the calculator's own working shows it, from official prices."""
    route = comps["location"]["value"]
    if comps.get("tierIR", {}).get("value", "standard") != "standard":
        raise ValueError("batch tier is not checked; check it by hand")
    sfx = ROUTES[route]
    v = lambda k, d=0: float((comps.get(k + sfx) or {}).get("value", d))  # noqa: E731
    if v("imageInput"):
        raise ValueError("image input is not checked; check it by hand")
    fields = inputs(next(t for t in definition(code, get)["templates"] if isinstance(t, dict)), {})
    label = option_label(fields["selectedModel_od" + sfx], comps["selectedModel_od" + sfx]["value"]) or ""
    model = label.split(":")[-1].strip()
    if "(" in model:
        raise ValueError(f"{model} is not checked; check it by hand")
    prices = model_prices(region, model, route, get)
    price = lambda kind: one(prices, kind, model)  # noqa: E731
    pin, pout = price("Input tokens"), price("Output tokens")
    n = v("avgRequestsPerMin") * 60 * v("hoursPerDayAtThisRate") * 30  # the calculator counts 30 days
    tin, tout = v("avgInputTokensPerRequest"), v("avgOutputTokensPerRequest")
    if v("withPromptCaching") == 1:
        r = v("cacheRate") / 100
        first = r * tin * price("Prompt cache write input tokens") + (1 - r) * tin * pin + tout * pout
        rest = r * tin * price("Prompt cache read input tokens") + (1 - r) * tin * pin + tout * pout
        return model, (first + (n - 1) * rest) / 1e6
    return model, n * (tin * pin + tout * pout) / 1e6


def check_link(link, usage=None, get=fetch, log=print):
    """Verify a priced, shared estimate. Returns the number of problems (0 = safe to send)."""
    key = link.rsplit("id=", 1)[-1]
    est = get(SAVED.format(key))
    problems = 0
    total = float((est.get("totalCost") or {}).get("monthly") or 0)
    log(f"{est.get('name')}: {total:,.2f} USD/month")
    if total == 0:
        log("  PROBLEM: the estimate is unpriced ($0). Open it, click Update estimate, then Share, and check the new link.")
        return 1
    stored = list(lines(est))
    for code, region, desc, monthly, comps in stored:
        note = ""
        if "location" in comps:  # a Bedrock model line
            try:
                model, want = bedrock_expected(code, region, comps, get)
                ok = abs(want - monthly) <= max(0.05, 0.02 * want)
                note = f"  [{model}: official price list gives {want:,.2f}{'' if ok else ' - MISMATCH'}]"
                problems += not ok
            except (ValueError, KeyError, StopIteration) as e:
                note = f"  [not checked: {e}]"
        elif monthly == 0:
            note = "  [$0: free tier, or not priced? open the link and confirm]"
        log(f"  {monthly:>12,.2f}  {code}: {desc}{note}")
    if usage:
        with contextlib.redirect_stdout(io.StringIO()):  # the inputs as this tool would send them
            want = build_payload(usage, get)
        have = [(c, comps) for c, _, _, _, comps in stored]
        for code, _, desc, _, comps in lines(want):
            match = next((h for h in have if h[0] == code and all(
                h[1].get(k, {}).get("value") == v.get("value") and h[1].get(k, {}).get("unit") == v.get("unit")
                for k, v in comps.items() if k in usage_fields(usage, code))), None)
            if match is None:
                log(f"  PROBLEM: {code} ({desc}): the link does not carry the inputs in the usage file")
                problems += 1
            else:
                have.remove(match)
    log("OK: safe to send." if problems == 0 else f"{problems} problem(s): fix them before sending this link.")
    return problems


def usage_fields(usage, code):
    return {k for e in usage["services"] if e["service"] == code for k in e.get("fields", {})}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("usage", nargs="?")
    ap.add_argument("--dry-run", action="store_true", help="write <usage>.payload.json, do not post")
    ap.add_argument("--fields", metavar="SERVICE_CODE", help="list a service's field ids, units and templates")
    ap.add_argument("--check", metavar="LINK", help="verify a priced, shared link (pass usage.json too)")
    a = ap.parse_args()
    if a.fields:
        return list_fields(a.fields)
    if a.check:
        usage = json.load(open(a.usage)) if a.usage else None
        return 1 if check_link(a.check, usage) else 0
    if not a.usage:
        ap.error("usage file required")
    payload = build_payload(json.load(open(a.usage)))
    if a.dry_run:
        out = os.path.splitext(a.usage)[0] + ".payload.json"
        json.dump(payload, open(out, "w"), indent=1)
        print(f"wrote {out} ({len(payload['services'])} services)")
        return
    print(post(payload))


if __name__ == "__main__":
    sys.exit(main())
