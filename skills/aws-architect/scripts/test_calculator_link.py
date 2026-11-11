#!/usr/bin/env python3
"""Offline checks for calculator_link.build_payload (no network)."""
import contextlib
import io

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
    "arch": {"value": "1"}}, flat["calculationComponents"]
assert parent["serviceCode"] == "parentSvc" and parent["estimateFor"] == "parentT"
assert parent["subServices"][0]["calculationComponents"]["size"] == {"value": "2048", "unit": "gb|month"}
assert any("1 million per month" in l for l in lines), lines

try:
    cl.build_payload({"name": "t", "region": "eu-west-1",
                      "services": [{"service": "flatSvc", "fields": {"typo": 1}}]}, get=FAKE.__getitem__)
    raise AssertionError("unknown field accepted")
except SystemExit as e:
    assert "unknown field 'typo'" in str(e)

print("all checks passed")
