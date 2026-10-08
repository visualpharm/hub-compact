"""Demo hub for developing the plugin: the real hub page on a throwaway journal with neutral sample data.

    python3 dev/serve.py [--port 1100] [--off] [--with <path-to-another-plugin>]...

--off serves the same page without this plugin (the "before" side of a comparison).
Hub code: $HUB_CORE, else ~/projects/agents-hub-core.
"""
import json
import os
import sys
import threading
import time

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUB = os.environ.get("HUB_CORE") or os.path.expanduser("~/projects/agents-hub-core")
sys.path.insert(0, HUB)

import tests  # noqa: E402, F401 — hub tests: own state and config folders, never the machine's
from tests import test_web  # noqa: E402

ASK = [{"question": "Ship the new onboarding today?", "header": "Release",
        "options": [{"label": "Yes", "description": "Deploy now, watch the error rate for an hour"},
                    {"label": "Tomorrow morning", "description": "After the nightly import finishes"},
                    {"label": "No"}]}]
LONG = ("The import job is fixed. Three things changed:\n\n"
        "1. **Retries:** a failed batch is retried twice before the run stops.\n"
        "2. **Dedup:** rows are matched by order number, not by email.\n"
        "3. **Report:** the summary lists skipped rows with a reason.\n\n"
        "Tests pass (`214 passed`). Next I can switch the nightly schedule to the new job — "
        "see `docs/import.md` for the rollback steps.\n\n"
        "| Batch | Rows | Skipped |\n|---|---|---|\n| orders | 12 480 | 14 |\n| refunds | 320 | 0 |\n")


def seed(t):
    ev = lambda type, entity=None, **data: t.j.append(type, entity, data)   # noqa: E731
    own = {"channel": "cli", "owner": True}
    ev("session.requested", "hub", session_id="s-hub", cwd="/w/hub-home", kind="hub", **own)
    ev("session.started", "hub", session_id="s-hub")
    people = [("web-shop", "busy"), ("billing", "ask"), ("mobile-app", "perm"), ("docs-site", "idle"),
              ("search-index", "busy"), ("data-import", "idle"), ("design-system", "asleep"), ("analytics", "asleep")]
    for name, _ in people:
        ev("session.requested", name, session_id=f"s-{name}", cwd=f"/w/{name}", **own)
        ev("session.started", name, session_id=f"s-{name}")
    ev("session.role_set", "web-shop", role="agent", about="Storefront and checkout", **own)
    ev("session.role_set", "billing", role="agent", about="Invoices and payments", **own)

    # hub conversation: owner asks, the hub answers, sessions report
    ev("message.received", None, to="hub", text="What is everyone working on right now?", channel="web", owner=True)
    ev("turn.started", "hub", marker=None)
    ev("turn.tool", "hub", id="h1", name="Bash", input={"command": "hub status"})
    ev("turn.tool_result", "hub", id="h1", text="9 sessions", error=False)
    said = ("Four sessions are active:\n\n- `web-shop` is rebuilding the checkout page\n- `search-index` is reindexing "
            "the catalog\n- `billing` is waiting for your answer about the release\n- `mobile-app` needs a permission")
    ev("session.said", "hub", text=said)
    ev("turn.result", "hub", text=said)
    ev("message.received", None, to="hub", text="Import job fixed, 214 tests pass, summary in the task record.",
       channel="session", owner=False, sender="data-import")
    ev("message.received", None, to="hub", text="Checkout rebuild: step 3 of 5 done.", channel="session", owner=False,
       sender="web-shop")
    ev("message.received", None, to="hub", text="Ask data-import to switch the nightly schedule to the new job.",
       channel="web", owner=True)
    ev("turn.started", "hub", marker=None)
    ev("session.said", "hub", text=LONG)
    ev("turn.result", "hub", text=LONG)

    # a working session with steps
    ev("message.received", None, to="web-shop", text="Rebuild the checkout page with the new address form.",
       channel="web", owner=True)
    ev("turn.started", "web-shop", marker=None)
    for i, cmd in enumerate(("git status", "npm test -- checkout", "npm run build"), 1):
        ev("turn.tool", "web-shop", id=f"w{i}", name="Bash", input={"command": cmd})
        if i < 3:
            ev("turn.tool_result", "web-shop", id=f"w{i}", text="ok", error=False)
    ev("session.said", "web-shop", text="Address form is in place; running the build before I touch the payment step.")
    ev("turn.started", "search-index", marker=None)
    ev("turn.tool", "search-index", id="x1", name="Bash", input={"command": "python3 reindex.py --all"})

    # a question card and a permission card
    ev("message.received", None, to="billing", text="Prepare the onboarding release.", channel="web", owner=True)
    ev("turn.started", "billing", marker=None)
    ev("session.said", "billing", text="Release notes are ready and the migration is tested on staging.")
    ev("permission.requested", "billing", request_id="r1", tool="AskUserQuestion", interactive=True,
       input={"questions": ASK})
    ev("turn.started", "mobile-app", marker=None)
    ev("session.said", "mobile-app", text="The build needs a clean derived-data folder.")
    ev("permission.requested", "mobile-app", request_id="r2", tool="Bash", interactive=True,
       input={"command": "rm -rf build/DerivedData && xcodebuild -scheme App", "description": "Clean and rebuild"})

    # finished and resting sessions, schedule
    for name in ("docs-site", "data-import"):
        ev("turn.started", name, marker=None)
        ev("session.said", name, text="Done: pages are published and links are checked.")
        ev("turn.result", name, text="Done: pages are published and links are checked.")
    for name in ("design-system", "analytics"):
        ev("session.parked", name, channel="core", why="idle")
    ev("schedule.set", "j1", session="data-import", every="1h", prompt="Check the import queue", **own)
    ev("schedule.set", "j2", session="docs-site", cron="0 9 * * *", prompt="Publish the changelog", **own)
    ev("schedule.set", "j3", session="analytics", every="6h", prompt="Refresh the weekly report", **own)


def main(argv):
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else 1100
    ext = {} if "--off" in argv else {"compact": {"path": PLUGIN, "web": "main.js"}}
    more = [argv[i + 1] for i, a in enumerate(argv) if a == "--with"]
    first = {}
    for p in more:   # other plugins load first: this one styles on top of them
        p = os.path.abspath(os.path.expanduser(p))
        with open(os.path.join(p, "hub-plugin.json"), encoding="utf-8") as f:
            man = json.load(f)
        first[man["name"]] = {"path": p, "web": man["web"]}
    with open(os.environ["HUB_CONFIG"], "w") as f:
        json.dump({"dev": {"enabled": False}, "agent_dev": {"enabled": False}, "update": {"enabled": False},
                   "extensions": {**first, **ext}}, f)
    t = test_web.WebTest("test_page_and_snapshot")
    t.setUp()
    t.server.shutdown()
    t.server.server_close()
    t.server = t.web.serve(port=port)
    threading.Thread(target=t.server.serve_forever, daemon=True).start()
    seed(t)
    t.settle()
    print(f"demo hub: http://127.0.0.1:{port}/", flush=True)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        t.tearDown()


if __name__ == "__main__":
    main(sys.argv[1:])
