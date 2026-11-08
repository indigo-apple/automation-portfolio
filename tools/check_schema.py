#!/usr/bin/env python3
"""Validate (and with --fix, repair) Apify INPUT_SCHEMA.json files against
the real rules enforced by the Apify platform build validator.

Rules implemented (derived from platform error messages):
  root: schemaVersion=1, type="object", title, description, properties(dict)
  each property: title, description, type
  array property: items required, items.type required
  object property: properties required
  enum: not allowed on array items; not allowed on array level either
  editor: must be in ALLOWED_EDITORS
"""
import json
import sys
import pathlib

ALLOWED_EDITORS = {
    "textfield", "textarea", "checkbox", "select", "stringList", "json",
    "datepicker", "time", "requestListSources", "proxyConfiguration",
    "file", "hidden", "banner", "number", "toggle", "range", "radio",
}


def default_desc(name, spec):
    t = spec.get("type")
    if t == "array":
        return f"List of values for {name}."
    if t == "boolean":
        return f"Enable or disable {name}."
    if t in ("integer", "number"):
        return f"Numeric setting for {name}."
    return f"Value for {name}."


def check_file(path, fix=False):
    errs, warns = [], []
    p = pathlib.Path(path)
    s = json.loads(p.read_text())
    changed = False

    for k in ("schemaVersion", "type", "title", "description", "properties"):
        if k not in s:
            errs.append(f"root.{k} missing")
    if s.get("type") != "object":
        errs.append('root.type must be "object"')
    if s.get("schemaVersion") not in (1, None):
        errs.append("root.schemaVersion must be 1")
    if not s.get("description"):
        if fix:
            s["description"] = "Input parameters for this Actor."
            changed = True
        else:
            errs.append("root.description missing")

    for name, spec in (s.get("properties") or {}).items():
        loc = f"properties.{name}"
        for k in ("title", "description", "type"):
            if not spec.get(k):
                if fix and k == "description":
                    spec["description"] = default_desc(name, spec)
                    changed = True
                elif fix and k == "title":
                    spec["title"] = name.replace("_", " ").title()
                    changed = True
                else:
                    errs.append(f"{loc}.{k} missing")
        t = spec.get("type")
        if t == "array":
            items = spec.get("items")
            if not isinstance(items, dict) or not items.get("type"):
                errs.append(f'{loc}: array requires items:{{"type": ...}}')
            elif "enum" in items:
                errs.append(f"{loc}.items.enum not allowed by Apify")
            if "enum" in spec:
                errs.append(f"{loc}.enum on array not supported by Apify")
        if t == "object" and not isinstance(spec.get("properties"), dict):
            errs.append(f"{loc}: object requires properties")
        ed = spec.get("editor")
        if ed and ed not in ALLOWED_EDITORS:
            warns.append(f"{loc}.editor '{ed}' unknown")
        if "enum" in spec and t not in ("string", "integer", "number"):
            warns.append(f"{loc}.enum used on type {t}")
        # default must be absent or match the declared type
        py_type = {"string": str, "boolean": bool, "integer": int,
                   "number": (int, float), "array": list, "object": dict}.get(t)
        if "default" in spec:
            dv = spec["default"]
            if dv is None:
                errs.append(f"{loc}.default must not be null (omit the key instead)")
            elif py_type and not isinstance(dv, py_type):
                errs.append(f"{loc}.default must be {t}, got {type(dv).__name__}")
        if "prefill" in spec:
            warns.append(f"{loc}.prefill is deprecated (use default)")

    if changed:
        p.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n")
    return errs, warns, changed


def main():
    fix = "--fix" in sys.argv
    targets = [a for a in sys.argv[1:] if not a.startswith("--")]
    total_e = total_w = 0
    for t in targets:
        errs, warns, changed = check_file(t, fix=fix)
        rel = "/".join(pathlib.Path(t).parts[-3:])
        status = "OK" if not errs else "FAIL"
        print(f"[{status}] {rel}" + ("  (patched)" if changed else ""))
        for e in errs:
            print(f"    ERROR {e}")
        for w in warns:
            print(f"    warn  {w}")
        total_e += len(errs)
        total_w += len(warns)
    print(f"\n{total_e} errors, {total_w} warnings")
    return 1 if total_e else 0


if __name__ == "__main__":
    sys.exit(main())
