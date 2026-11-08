"""Minimal stand-in for the `apify` SDK, used to run an Actor end-to-end
locally without installing the platform package.

`apify push` builds with CMD ["python","-m","src"], which executes
src/__main__.py. Running `python src/main.py` does not exercise the same path,
so entrypoint bugs stay invisible until deployment. This stub lets
`python -m src` run for real.

Env vars:
    STUB_INPUT_FILE   path to a JSON file used as Actor input
    STUB_OUT          path where pushed dataset items are dumped on exit

The dumper is what makes tools/check_output.py able to validate real output
against .actor/dataset_schema.json before any cloud build is spent.
"""
import json
import os
import pathlib


class _Log:
    def _p(self, lvl, msg):
        print(f"[{lvl}] {msg}", flush=True)

    def info(self, msg, *a):
        self._p("INFO", msg % a if a else msg)

    def warning(self, msg, *a):
        self._p("WARN", msg % a if a else msg)

    warn = warning

    def error(self, msg, *a):
        self._p("ERROR", msg % a if a else msg)

    def debug(self, msg, *a):
        self._p("DEBUG", msg % a if a else msg)


class _Dataset:
    def __init__(self):
        self.items = []

    async def push_data(self, data):
        if isinstance(data, dict):
            self.items.append(data)
        else:
            self.items.extend(data)


class _Actor:
    log = _Log()

    def __init__(self):
        self.dataset = _Dataset()
        self.kv = {}
        self._exit_code = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        out = os.environ.get("STUB_OUT")
        if out:
            pathlib.Path(out).write_text(json.dumps(self.dataset.items, default=str))
        print(f"[STUB] dataset has {len(self.dataset.items)} item(s)", flush=True)
        return False

    async def get_input(self):
        path = os.environ.get("STUB_INPUT_FILE")
        if path and pathlib.Path(path).exists():
            return json.loads(pathlib.Path(path).read_text())
        return {}

    async def push_data(self, data):
        await self.dataset.push_data(data)

    async def set_value(self, key, value, *a, **kw):
        self.kv[key] = value
        print(f"[STUB] kv[{key}] = {value!r}"[:400], flush=True)

    async def get_value(self, key, default=None, *a, **kw):
        return self.kv.get(key, default)

    async def exit(self, exit_code=0, *a, **kw):
        self._exit_code = exit_code

    def new_client(self):
        return None


Actor = _Actor()
