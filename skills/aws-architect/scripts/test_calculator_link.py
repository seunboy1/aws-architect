#!/usr/bin/env python3
"""Offline checks for calculator_link.build_payload (no network)."""
import contextlib
import io
import json
import urllib.error

import calculator_link as cl

FAKE = {
    f"{cl.CDN}/manifest/en_US.json": {"awsServices": [
        {"serviceCode": "parentSvc", "templates": ["subSvc"]},
        {"serviceCode": "flatSvc", "templates": []}]},
    cl.LOCATIONS: {"x": {"code": "eu-west-1", "name": "Europe (Ireland)"}},
    f"{cl.CDN}/data/flatSvc/en_US.json": {
        "serviceCode": "flatSvc", "serviceName": "Flat", "version": "1",
        "templates": [{"id": "t1", "cards": [{"components": [
            {"type": "input", "subType": "frequency", "id": "reqs", "defaultFrequency": "perMonth",
             "options": [{"id": "perMonth", "label": "million per month"}]},
            {"type": "input", "subType": "fileSize", "id": "mem",
             "defaultOption": {"size": "mb", "frequency": "NA"}},
            {"type": "input", "subType": "dropdown", "id": "arch", "options": [{"id": "1"}, {"id": "2"}]},
            {"type": "input", "subType": "numericInput", "id": "rpm", "defaultValue": 1,
             "validations": {"allowDecimals": False, "minValue": 0}},
            {"type": "input", "subType": "alert", "id": "note"}]}]}]},
    f"{cl.CDN}/data/subSvc/en_US.json": {
        "serviceCode": "subSvc", "serviceName": "Sub", "version": "2",
        "templates": [{"id": "subT", "components": [
            {"type": "input", "subType": "fileSize", "id": "size", "defaultValue": 16,
             "defaultOption": {"size": "gb", "frequency": "month"}}]}]},
    f"{cl.CDN}/data/parentSvc/en_US.json": {
        "serviceCode": "parentSvc", "serviceName": "Parent", "version": "3", "templateId": "parentT"},
}

usage = {"name": "t", "region": "eu-west-1", "services": [
    {"service": "flatSvc", "fields": {"reqs": [1, "perMonth"], "mem": [512, "mb"]}},
    {"service": "subSvc", "fields": {"size": [2048, "gb"]}}]}
out = io.StringIO()
with contextlib.redirect_stdout(out):
    p = cl.build_payload(usage, get=FAKE.__getitem__)
lines = out.getvalue().splitlines()
flat, parent = p["services"].values()

assert flat["estimateFor"] == "t1" and flat["regionName"] == "Europe (Ireland)"
assert flat["calculationComponents"] == {
    "reqs": {"value": "1", "unit": "perMonth"},
    "mem": {"value": "512", "unit": "mb|NA"},
    "arch": {"value": "1"}, "rpm": {"value": "1"}}, flat["calculationComponents"]
assert parent["serviceCode"] == "parentSvc" and parent["estimateFor"] == "parentT"
assert parent["subServices"][0]["calculationComponents"]["size"] == {"value": "2048", "unit": "gb|month"}
assert any("1 million per month" in l for l in lines), lines

try:
    cl.build_payload({"name": "t", "region": "eu-west-1",
                      "services": [{"service": "flatSvc", "fields": {"typo": 1}}]}, get=FAKE.__getitem__)
    raise AssertionError("unknown field accepted")
except SystemExit as e:
    assert "unknown field 'typo'" in str(e)

for bad_value, msg in ((0.1, "whole number"), (-1, "outside")):
    try:
        cl.build_payload({"name": "t", "region": "eu-west-1", "services": [
            {"service": "flatSvc", "fields": {"rpm": bad_value}}]}, get=FAKE.__getitem__)
        raise AssertionError(f"rpm={bad_value} accepted")
    except SystemExit as e:
        assert msg in str(e), str(e)


def get(url):  # like the real CDN: an unknown service code is an HTTP 403
    if url not in FAKE:
        raise urllib.error.HTTPError(url, 403, "Forbidden", None, None)
    return FAKE[url]
try:
    cl.build_payload({"name": "t", "region": "eu-west-1", "services": [{"service": "flatSvx"}]}, get=get)
    raise AssertionError("unknown service accepted")
except SystemExit as e:
    assert "unknown service code 'flatSvx'" in str(e) and "flatSvc" in str(e), str(e)

def rejects(u, msg):
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            cl.build_payload(u, get=FAKE.__getitem__)
    except SystemExit as e:
        assert msg in str(e), (msg, str(e))
        return
    raise AssertionError(f"accepted: {u}")


def one_service(fields, service="flatSvc", **extra):
    return {"name": "t", "region": "eu-west-1", "services": [dict(service=service, fields=fields, **extra)]}


# usage.json shape: misspelled or unknown keys fail instead of being ignored
rejects({"name": "t", "region": "eu-west-1", "services": [], "extra": 1}, "needs exactly")
rejects({"name": "t", "region": "eu-west-1", "services": []}, "non-empty list")
rejects({"name": "t", "region": "eu-west-1", "services": [{"service": "flatSvc", "feilds": {}}]}, "allowed keys")
rejects(one_service({}, region="eu-west-9"), "unknown region")
# values: types, units and dropdown options the website would silently drop
rejects(one_service({"rpm": "100"}), "needs a number")
rejects(one_service({"rpm": True}), "needs a number")
rejects(one_service({"reqs": [1, "perWeek"]}), "unit 'perWeek' not allowed")
rejects(one_service({"mem": [1, "pb"]}), "unit 'pb' not allowed")
rejects(one_service({"rpm": [1, "gb"]}), "takes no unit")
rejects(one_service({"arch": "3"}), "is not an option")
rejects(one_service({"arch": ["1", "x"]}), "takes no unit")
rejects(one_service({"rpm": [1, 2, 3]}), "use value or [value, unit]")

# Bedrock: one model per route, route models must be set, dropdowns may be given by label
MODELS = [{"id": "h", "label": "Anthropic: Claude Haiku 9"}, {"id": "s", "label": "Anthropic: Claude Sonnet 9"}]
BED = [{"type": "input", "subType": "dropdown", "id": "location", "options": [{"id": "global"}, {"id": "geo"}]},
       {"type": "input", "subType": "dropdown", "id": "tierIR", "options": [{"id": "standard"}, {"id": "batch"}]}]
for sfx in ("", "Geostan"):
    BED += [{"type": "input", "subType": "dropdown", "id": k + sfx, "options": MODELS}
            for k in ("modelSelection", "selectedModel", "selectedModel_od")]
    BED += [{"type": "input", "subType": "numericInput", "id": k + sfx, "defaultValue": 1,
             "validations": {"allowDecimals": False, "minValue": 0}}
            for k in ("avgRequestsPerMin", "hoursPerDayAtThisRate", "avgInputTokensPerRequest", "avgOutputTokensPerRequest")]
    BED += [{"type": "input", "subType": "dropdown", "id": k + sfx, "options": [{"id": "1"}, {"id": "0"}],
             "defaultDropDownItem": "0"} for k in ("imageInput", "withPromptCaching")]
FAKE[f"{cl.CDN}/data/bedSvc/en_US.json"] = {"serviceCode": "bedSvc", "serviceName": "Bed", "version": "1",
                                            "templates": [{"id": "bt", "components": BED}]}
FAKE[f"{cl.CDN}/manifest/en_US.json"]["awsServices"].append({"serviceCode": "bedSvc", "templates": []})
geo = {"location": "geo", "avgRequestsPerMinGeostan": 10, "hoursPerDayAtThisRateGeostan": 10,
       "avgInputTokensPerRequestGeostan": 1000, "avgOutputTokensPerRequestGeostan": 100}
sonnet = {"modelSelectionGeostan": "s", "selectedModelGeostan": "Anthropic: Claude Sonnet 9", "selectedModel_odGeostan": "s"}
rejects(one_service(geo, "bedSvc"), "would silently default to 'Anthropic: Claude Haiku 9'")
rejects(one_service({**geo, **sonnet, "selectedModelGeostan": "h"}, "bedSvc"), "model dropdowns disagree")
bed_usage = one_service({**geo, **sonnet}, "bedSvc")
with contextlib.redirect_stdout(io.StringIO()):
    bed_payload = cl.build_payload(bed_usage, get=FAKE.__getitem__)
assert next(iter(bed_payload["services"].values()))["calculationComponents"]["selectedModelGeostan"] == {"value": "s"}

# --check: recompute the model line from the official price list and compare with the priced link
def price_list(prices):
    products, terms = {}, {}
    for i, (kind, ut, usd) in enumerate(prices):
        products[str(i)] = {"attributes": {"model": "Claude Sonnet 9", "feature": "On-demand Inference",
                                           "inferenceType": kind, "usagetype": ut}}
        terms[str(i)] = {"t": {"priceDimensions": {"d": {"pricePerUnit": {"USD": str(usd)}}}}}
    return {"products": products, "terms": {"OnDemand": terms}}


FAKE[cl.PRICE_LIST.format("eu-west-1")] = price_list([
    ("Input tokens", "EU-MP:EU_input_tokens_standard-Units", 2.2),
    ("Output tokens", "EU-MP:EU_output_tokens_standard-Units", 11.0),
    ("Input tokens", "EU-MP:EU_input_tokens_global_standard-Units", 2.0),  # other route: ignored
    ("Prompt cache read input tokens", "EU-MP:EU_cache_read_tokens_standard-Units", 0.22),
    ("Prompt cache write input tokens", "EU-MP:EU_cache_write_tokens_standard-Units", 2.75),
    ("Prompt cache write input tokens", "EU-MP:EU_cache_write_tokens_1h_standard-Units", 4.4)])
expected = 10 * 60 * 10 * 30 * (1000 * 2.2 + 100 * 11.0) / 1e6  # 180,000 requests a month = 594.00


def saved(payload, monthly):
    est = json.loads(json.dumps(payload))
    for svc in est["services"].values():
        svc["serviceCost"] = {"monthly": monthly}
    est["totalCost"] = {"monthly": monthly}
    return est


def check(est, u=None):
    FAKE[cl.SAVED.format("abc")] = est
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        n = cl.check_link("https://calculator.aws/#/estimate?id=abc", u, get=FAKE.__getitem__)
    return n, out.getvalue()


n, text = check(saved(bed_payload, expected), bed_usage)
assert n == 0 and "official price list gives 594.00" in text and "safe to send" in text, text
n, text = check(saved(bed_payload, expected / 10), bed_usage)  # a tenfold price error is caught
assert n == 1 and "MISMATCH" in text, text
n, text = check(saved(bed_payload, 0), bed_usage)
assert n == 1 and "unpriced" in text, text
other = one_service({**geo, **sonnet, "avgRequestsPerMinGeostan": 11}, "bedSvc")  # link and usage file disagree
n, text = check(saved(bed_payload, expected), other)
assert n == 1 and "does not carry the inputs" in text, text

# prompt caching, against the calculator's own working for 1,800 requests (0.9208897 USD):
# cache write 0.1375, input 0.11, cache read 0.011, output 0.55 per 1M tokens, 50% hit rate
FAKE[cl.PRICE_LIST.format("eu-west-1")] = price_list([
    ("Input tokens", "EU-MP:EU_input_tokens_standard-Units", 0.11),
    ("Output tokens", "EU-MP:EU_output_tokens_standard-Units", 0.55),
    ("Prompt cache read input tokens", "EU-MP:EU_cache_read_tokens_standard-Units", 0.011),
    ("Prompt cache write input tokens", "EU-MP:EU_cache_write_tokens_standard-Units", 0.1375)])
comps = {k: {"value": v} for k, v in {"location": "geo", "selectedModel_odGeostan": "s", "avgRequestsPerMinGeostan": "1",
         "hoursPerDayAtThisRateGeostan": "1", "avgInputTokensPerRequestGeostan": "3000",
         "avgOutputTokensPerRequestGeostan": "600", "withPromptCachingGeostan": "1", "cacheRateGeostan": "50"}.items()}
model, cost = cl.bedrock_expected("bedSvc", "eu-west-1", comps, get=FAKE.__getitem__)
assert model == "Claude Sonnet 9" and abs(cost - 0.9208897) < 1e-6, cost

print("all checks passed")
