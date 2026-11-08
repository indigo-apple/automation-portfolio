#!/usr/bin/env python3
"""Validate an Apify dataset schema (.actor/dataset_schema.json) against the
rules the platform enforces when publishing.

Reference: docs.apify.com/platform/actors/development/actor-definition/dataset-schema

Usage:
    python3 tools/check_dataset_schema.py apify-actors/*/.actor/dataset_schema.json
"""
import json
import sys
import pathlib

DISPLAY_COMPONENTS = {"table", "list", "gallery", "text"}


def check(path):
    errs, warns = [], []
    p = pathlib.Path(path)
    s = json.loads(p.read_text())

    if s.get("actorSpecification") != 1:
        errs.append("actorSpecification must be 1")

    views = s.get("views")
    if not isinstance(views, dict) or not views:
        errs.append("views is required and must be a non-empty object")
        views = {}

    props = {}
    if "fields" in s:
        f = s["fields"]
        # Apify's validator does not register the draft 2020-12 meta-schema and
        # fails compilation with: no schema with key or ref
        # "https://json-schema.org/draft/2020-12/schema". Omit $schema entirely.
        if "$schema" in f:
            errs.append("fields.$schema must be omitted (Apify has no 2020-12 meta-schema registered)")
        if f.get("type") != "object":
            errs.append("fields.type must be 'object'")
        props = f.get("properties") or {}
        if not isinstance(props, dict) or not props:
            errs.append("fields.properties is required when fields is present")
            props = {}
        for k, v in props.items():
            if not isinstance(v, dict):
                errs.append(f"fields.properties.{k} must be an object")
                continue
            if not v.get("type"):
                errs.append(f"fields.properties.{k}.type missing")
            for meta in ("title", "description", "example"):
                if meta not in v:
                    warns.append(f"fields.properties.{k}.{meta} missing (hurts agent/MCP discoverability)")
        req = s["fields"].get("required")
        if req is not None:
            for r in req:
                if r not in props:
                    errs.append(f"fields.required references unknown property '{r}'")

    for name, v in views.items():
        loc = f"views.{name}"
        if not isinstance(v, dict):
            errs.append(f"{loc} must be an object")
            continue
        if not v.get("title"):
            errs.append(f"{loc}.title is required")
        tr = v.get("transformation")
        if not isinstance(tr, dict):
            errs.append(f"{loc}.transformation is required")
            tr = {}
        fields = tr.get("fields")
        if not isinstance(fields, list) or not fields:
            errs.append(f"{loc}.transformation.fields is required (non-empty array)")
            fields = []

        # the publish flow rejects a view without display.component
        disp = v.get("display")
        if not isinstance(disp, dict):
            errs.append(f"{loc}.display is required (this is what blocks publishing)")
        else:
            comp = disp.get("component")
            if not comp:
                errs.append(f"{loc}.display.component is required")
            elif comp not in DISPLAY_COMPONENTS:
                warns.append(f"{loc}.display.component '{comp}' not in {sorted(DISPLAY_COMPONENTS)}")
            dprops = disp.get("properties") or {}
            if not isinstance(dprops, dict):
                errs.append(f"{loc}.display.properties must be an object")
                dprops = {}
            for k in dprops:
                if props and k not in props:
                    errs.append(f"{loc}.display.properties.{k} not declared in fields.properties")
            for f in fields:
                if k_ok(f) and f not in dprops:
                    warns.append(f"{loc}: field '{f}' has no display format")

        if props:
            for f in fields:
                if k_ok(f) and f not in props:
                    errs.append(f"{loc}.transformation.fields '{f}' not declared in fields.properties")

    return errs, warns


def k_ok(f):
    return isinstance(f, str)


def main():
    targets = [a for a in sys.argv[1:] if not a.startswith("--")]
    total_e = total_w = 0
    for t in targets:
        errs, warns = check(t)
        rel = "/".join(pathlib.Path(t).parts[-3:])
        print(f"[{'OK' if not errs else 'FAIL'}] {rel}")
        for e in errs:
            print(f"    ERROR {e}")
        for w in warns[:6]:
            print(f"    warn  {w}")
        if len(warns) > 6:
            print(f"    warn  ... {len(warns)-6} more")
        total_e += len(errs)
        total_w += len(warns)
    print(f"\n{total_e} errors, {total_w} warnings")
    return 1 if total_e else 0


if __name__ == "__main__":
    sys.exit(main())
