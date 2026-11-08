#!/usr/bin/env python3
"""上线前自检：actor.json / INPUT_SCHEMA / main.py / Dockerfile / 输出字段 一致性。

用法: python3 tools/check_actors.py [repo_root]
"""
import json
import os
import re
import subprocess
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/2T/reposity/indigo-apple/automation-portfolio")
ACTORS_DIR = os.path.join(ROOT, "apify-actors")

REQUIRED_META = ["actorSpecification", "name", "title", "version", "buildTag"]
errors, warnings, ok = [], [], []


def err(a, m):
    errors.append(f"[{a}] {m}")


def warn(a, m):
    warnings.append(f"[{a}] {m}")


def check(name):
    d = os.path.join(ACTORS_DIR, name)
    aj_path = os.path.join(d, ".actor", "actor.json")
    if not os.path.exists(aj_path):
        err(name, ".actor/actor.json 缺失")
        return
    aj = json.load(open(aj_path, encoding="utf-8"))

    # 1) 基础字段
    for k in REQUIRED_META:
        if not aj.get(k):
            err(name, f"actor.json 缺字段 {k}")
    if aj.get("actorSpecification") != 1:
        err(name, "actorSpecification 必须是 1")
    if not re.fullmatch(r"[a-z0-9-]{3,63}", aj.get("name", "")):
        err(name, f"name 不合规（只能小写字母/数字/连字符）: {aj.get('name')}")

    # 2) 相对路径（相对 .actor 目录）
    for key in ("dockerfile", "input", "readme"):
        rel = aj.get(key)
        if not rel:
            warn(name, f"actor.json 没写 {key}")
            continue
        target = os.path.normpath(os.path.join(d, ".actor", rel))
        if not os.path.exists(target):
            err(name, f"{key} 指向的文件不存在: {rel} -> {target}")
        else:
            ok.append(f"[{name}] {key} -> {rel} ✓")

    # 3) Dataset 视图字段
    fields = (((aj.get("storages") or {}).get("dataset") or {})
              .get("views", {}).get("overview", {}).get("transformation", {}).get("fields"))
    if not fields:
        warn(name, "dataset view 未定义 fields（Store 预览会显示全部原始字段）")

    # 4) INPUT_SCHEMA
    schema_props = {}
    sch_path = os.path.join(d, ".actor", "INPUT_SCHEMA.json")
    if os.path.exists(sch_path):
        sch = json.load(open(sch_path, encoding="utf-8"))
        if sch.get("schemaVersion") != 1:
            err(name, "INPUT_SCHEMA schemaVersion 必须是 1")
        schema_props = sch.get("properties", {}) or {}
        for pname, p in schema_props.items():
            if p.get("type") == "array" and "items" not in p:
                warn(name, f"input {pname} 是 array 但没有 items 定义")
            if "default" not in p and pname not in (sch.get("required") or []):
                warn(name, f"input {pname} 没有 default（用户必须手填）")

    # 5) main.py 用到的 input key 必须在 schema 里
    main_py = os.path.join(d, "src", "main.py")
    if not os.path.exists(main_py):
        err(name, "src/main.py 缺失")
    else:
        src = open(main_py, encoding="utf-8").read()
        used = set(re.findall(r"inp\.get\(\s*['\"]([A-Za-z0-9_]+)['\"]", src))
        for u in sorted(used):
            if u not in schema_props:
                err(name, f"main.py 读了 {u}，但 INPUT_SCHEMA 没定义")
        if "await Actor.push_data" not in src:
            err(name, "main.py 没有 push_data，PPE 的 dataset-item 事件不会产生")

    # 6) Dockerfile / requirements
    df = os.path.join(d, "Dockerfile")
    if not os.path.exists(df):
        err(name, "Dockerfile 缺失")
    else:
        content = open(df, encoding="utf-8").read()
        m = re.search(r"^FROM\s+(\S+)", content, re.M)
        if not m:
            err(name, "Dockerfile 没有 FROM")
        else:
            ok.append(f"[{name}] base image: {m.group(1)}")
        if not re.search(r'"python"\s*,\s*"-m"\s*,\s*"src"|python -m src', content):
            warn(name, "Dockerfile CMD 不是 python -m src，确认入口正确")
        for need in ("requirements.txt",):
            if need not in content:
                warn(name, f"Dockerfile 没引用 {need}")

    req = os.path.join(d, "requirements.txt")
    if os.path.exists(req):
        ok.append(f"[{name}] requirements: {open(req).read().strip()}")
    for f in ("__init__.py", "logic.py"):
        if not os.path.exists(os.path.join(d, "src", f)):
            err(name, f"src/{f} 缺失")

    # 7) 语法
    for f in ("main.py", "logic.py"):
        p = os.path.join(d, "src", f)
        if os.path.exists(p):
            r = subprocess.run([sys.executable, "-m", "py_compile", p],
                               capture_output=True, text=True)
            if r.returncode != 0:
                err(name, f"{f} 语法错误: {r.stderr.strip().splitlines()[-1]}")

    return {"name": name, "dir": d, "fields": fields or [], "schema": schema_props}


actors = [x for x in sorted(os.listdir(ACTORS_DIR))
          if os.path.isdir(os.path.join(ACTORS_DIR, x)) and not x.startswith(".")]
print(f"发现 {len(actors)} 个 Actor: {actors}\n")

infos = [i for i in (check(a) for a in actors) if i]

# 8) 运行时输出字段 vs dataset view 字段（抽样跑一次 logic）
sys.path.insert(0, ROOT)
print("── 运行时字段校验 ──")
for info in infos:
    name = info["name"]
    sys.path.insert(0, os.path.join(info["dir"], "src"))
    for m in [m for m in list(sys.modules) if m == "logic"]:
        del sys.modules[m]
    try:
        import logic  # noqa: PLC0415
    except Exception as e:  # noqa: BLE001
        err(name, f"import logic 失败: {e}")
        sys.path.pop(0)
        continue
    try:
        if name == "funding-arb":
            rows, errs, n = logic.scan(["okx", "gate"], min_apr=0, top=3)
        elif name == "defi-yield":
            rows = logic.scan(logic.fetch_pools(), min_tvl=50_000_000, min_apy=3, top=3)
        else:
            rows = logic.scan(logic.fetch_markets(pages=1), min_daily=0.5, top=3)
    except Exception as e:  # noqa: BLE001
        err(name, f"运行时异常: {type(e).__name__}: {e}")
        sys.path.pop(0)
        continue
    sys.path.pop(0)
    if not rows:
        warn(name, "抽样运行返回 0 条（可能只是当前无满足条件的数据）")
        continue
    got = set(rows[0])
    want = set(info["fields"])
    missing = want - got
    extra = got - want
    if missing:
        err(name, f"dataset view 里的字段运行时不产出: {sorted(missing)}")
    if extra:
        warn(name, f"运行时字段未在 dataset view 中展示: {sorted(extra)}")
    if not missing and not extra:
        ok.append(f"[{name}] 输出字段与 dataset view 完全一致（{len(got)} 个）")

print("\n".join("  ✓ " + x for x in ok))
if warnings:
    print("\n⚠️ 警告:")
    print("\n".join("  - " + w for w in warnings))
if errors:
    print("\n❌ 错误:")
    print("\n".join("  - " + e for e in errors))
    sys.exit(1)
print(f"\n✅ {len(infos)} 个 Actor 检查通过（0 错误, {len(warnings)} 警告）")
