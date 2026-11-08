#!/usr/bin/env python3
"""End-to-end gate: run an Actor locally through its real container entrypoint
(`python -m src`) and validate the produced dataset items against
.actor/dataset_schema.json.

Catches the class of bug that only surfaces on the platform:
    apify_client.errors.ApifyApiError: Schema validation failed
i.e. a run that pushes rows which violate the declared output schema. The
platform rejects the whole push, so the run fails and the user gets nothing.

Usage:
    python3 tools/check_output.py apify-actors/funding-arb [...more]
    python3 tools/check_output.py --input '{"pages":1}' apify-actors/polymarket-lp

Requires: jsonschema (pip install jsonschema)
"""
import json
import os
import subprocess
import sys
import tempfile
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
STUB = ROOT / "tools" / "stub"


def default_input(actor_dir):
    """Build an input object from INPUT_SCHEMA.json defaults."""
    path = actor_dir / ".actor" / "INPUT_SCHEMA.json"
    if not path.exists():
        return {}
    schema = json.loads(path.read_text())
    return {
        name: spec["default"]
        for name, spec in (schema.get("properties") or {}).items()
        if "default" in spec
    }


def run_actor(actor_dir, inp, timeout):
    with tempfile.TemporaryDirectory() as tmp:
        inp_path = pathlib.Path(tmp) / "input.json"
        out_path = pathlib.Path(tmp) / "items.json"
        inp_path.write_text(json.dumps(inp))
        env = dict(os.environ)
        env["PYTHONPATH"] = str(STUB)
        env["STUB_INPUT_FILE"] = str(inp_path)
        env["STUB_OUT"] = str(out_path)
        proc = subprocess.run(
            [sys.executable, "-m", "src"],
            cwd=str(actor_dir), env=env, capture_output=True, text=True, timeout=timeout,
        )
        items = json.loads(out_path.read_text()) if out_path.exists() else []
        return proc, items


def validate(items, actor_dir):
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema not installed: pip install jsonschema"], []
    schema_path = actor_dir / ".actor" / "dataset_schema.json"
    if not schema_path.exists():
        return ["no .actor/dataset_schema.json"], []
    schema = json.loads(schema_path.read_text())["fields"]
    # Apify compiles the schema with an ajv setup that lacks the 2020-12
    # meta-schema, so validate with draft-07 semantics to stay faithful.
    validator = jsonschema.Draft7Validator(schema)
    errs = []
    for i, item in enumerate(items):
        for e in validator.iter_errors(item):
            errs.append(f"item[{i}].{'.'.join(map(str, e.path)) or '<root>'}: "
                        f"{e.message[:140]} | value={e.instance!r}"[:220])
            if len(errs) >= 15:
                return errs, items
    return errs, items


def main():
    argv = sys.argv[1:]
    inp = None
    if "--input" in argv:
        i = argv.index("--input")
        inp = json.loads(argv[i + 1])
        del argv[i:i + 2]
    targets = [pathlib.Path(a).resolve() for a in argv]
    if not targets:
        print(__doc__)
        return 2

    failed = 0
    for actor_dir in targets:
        name = actor_dir.name
        use_input = inp if inp is not None else default_input(actor_dir)
        print(f"[RUN ] {name}  input={json.dumps(use_input)}")
        try:
            proc, items = run_actor(actor_dir, use_input, timeout=300)
        except subprocess.TimeoutExpired:
            print(f"    ERROR timed out after 300s")
            failed += 1
            continue
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout).strip().splitlines()[-6:]
            print(f"    ERROR exit {proc.returncode}")
            for line in tail:
                print(f"          {line}")
            failed += 1
            continue
        errs, items = validate(items, actor_dir)
        if errs:
            print(f"    FAIL  {len(items)} items produced, schema violations:")
            for e in errs:
                print(f"          {e}")
            failed += 1
        else:
            print(f"    OK    {len(items)} items, all match dataset_schema.json")
            if not items:
                print("          WARNING: zero items — check filters/data source")
    print(f"\n{len(targets) - failed}/{len(targets)} actors clean")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
