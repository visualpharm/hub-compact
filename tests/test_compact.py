"""The plugin on the real hub page: headless Chrome, the page on a throwaway journal (helpers come from the hub's own
tests). Run: python3 tests/test_compact.py (hub code: HUB_CORE, else ~/projects/agents-hub-core).

What is checked, at phone, tablet and desktop widths:
- the page loads with the plugin and without JS errors;
- nothing scrolls sideways and the session header stays on one row;
- no visible text is smaller than 13 px, and secondary text keeps a 4.5:1 contrast;
- no coloured edge marks a row, a message or a card;
- the quick-answers plugin (answer by clicking an option, text selection in the feed) works the same with this plugin
  loaded: its own test suite is run again on top of it (QUICK_ANSWERS, else ~/projects/hub-quick-answers)."""
import importlib
import json
import os
import subprocess
import sys
import unittest

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUB = os.environ.get("HUB_CORE") or os.path.expanduser("~/projects/agents-hub-core")
QUICK = os.environ.get("QUICK_ANSWERS") or os.path.expanduser("~/projects/hub-quick-answers")
sys.path.insert(0, HUB)
sys.path.insert(0, os.path.join(PLUGIN, "dev"))

import tests  # noqa: E402, F401 — hub tests: own state and config folders, never the machine's
from tests import test_web_e2e  # noqa: E402
import serve  # noqa: E402 — the demo data

CDP = os.path.join(PLUGIN, "tests", "cdp.mjs")
MINE = {"compact": {"path": PLUGIN, "web": "main.js"}}
BASE = {"dev": {"enabled": False}, "agent_dev": {"enabled": False}, "update": {"enabled": False}}
WIDTHS = (360, 390, 820, 1440)
ROUTES = ("s/hub", "s/billing", "s/mobile-app", "s/web-shop", "sessions", "schedule", "settings")
READY = ("document.documentElement.classList.contains('cx') && document.querySelectorAll('aside .srow:not(.nav)').length > 3"
         " && getComputedStyle(document.querySelector('aside .srow')).paddingLeft === '8px'")

OVERFLOW = "document.documentElement.scrollWidth - innerWidth"
# the header's own row: everything except the meta line and the settings tabs, which take a row of their own by design
ONE_ROW = """(() => { const h = document.querySelector('main .head'); if (!h || !h.offsetParent) return 1;
  const tops = [...h.children].filter((c) => !c.matches('.head-meta, .seg.tabs') && c.getBoundingClientRect().width > 0)
    .map((c) => { const r = c.getBoundingClientRect(); return Math.round(r.top + r.height / 2); });
  return new Set(tops.map((t) => Math.round(t / 8))).size <= 2 && Math.max(...tops) - Math.min(...tops) < 10 ? 1 : tops; })()"""
SMALL = """(() => { const out = []; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) { if (!n.nodeValue.trim()) continue; const e = n.parentElement;
    if (e.closest('.sr, script, style, [hidden]')) continue; const cs = getComputedStyle(e), fs = parseFloat(cs.fontSize);
    const r = e.getBoundingClientRect(); if (!r.width || !r.height || fs === 0 || cs.visibility === 'hidden') continue;
    if (fs < 13) out.push([e.className || e.tagName, fs, n.nodeValue.trim().slice(0, 30)]); }
  return out.slice(0, 8); })()"""
CONTRAST = """(() => { const c = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const rgb = (v) => { c.clearRect(0, 0, 1, 1); c.fillStyle = '#fff'; c.fillRect(0, 0, 1, 1); c.fillStyle = v; c.fillRect(0, 0, 1, 1);
    return [...c.getImageData(0, 0, 1, 1).data].slice(0, 3); };
  const lum = (p) => { const [r, g, b] = p.map((x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const bg = (e) => { for (; e; e = e.parentElement) { const v = getComputedStyle(e).backgroundColor;
    if (v && !/, 0\\)$|\\/ 0\\)$|transparent/.test(v)) return v; } return '#fff'; };
  const bad = [];
  for (const e of document.querySelectorAll('.srow .lb, .row .meta, .hint, .job .meta, .about-facts dt, .aside-foot .counts span, .status')) {
    const r = e.getBoundingClientRect(); if (!r.width || !e.textContent.trim()) continue;
    const a = lum(rgb(getComputedStyle(e).color)), b = lum(rgb(bg(e)));
    const k = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05); if (k < 4.5) bad.push([e.className, Math.round(k * 10) / 10]); }
  return bad.slice(0, 8); })()"""
EDGES = """[...document.querySelectorAll('.srow.blocked, .strip-row, .row.from > .b, .reply-box, .board-detail')].filter((e) => {
  const cs = getComputedStyle(e); return /inset 3px/.test(cs.boxShadow) || (parseFloat(cs.borderLeftWidth) >= 2 && parseFloat(cs.borderTopWidth) < 2); }).length"""


@unittest.skipUnless(test_web_e2e.READY, "Google Chrome and node are needed")
class Compact(test_web_e2e.PageInChrome):
    def setUp(self):
        super().setUp()
        cfg = os.environ["HUB_CONFIG"]
        with open(cfg) as f:
            saved = f.read()
        self.addCleanup(lambda: open(cfg, "w").write(saved))
        with open(cfg, "w") as f:
            json.dump({**BASE, "extensions": MINE}, f)
        serve.seed(self)

    def page(self, *steps):
        r = subprocess.run(["node", "--experimental-websocket", CDP, str(self.cdp), json.dumps(list(steps))],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr[:1500])
        return json.loads(r.stdout)

    def open(self, route, width, *steps, dark=False):
        got = self.page({"go": f"http://127.0.0.1:{self.port}/#/{route}", "width": width, "dark": dark}, {"until": READY, "ms": 15000},
                        {"sleep": 300}, *steps)
        self.assertTrue(got[1]["until"], f"{route} at {width}: the plugin did not load")
        return [g["eval"] for g in got if "eval" in g]

    def test_every_screen_fits_reads_and_marks_nothing_with_an_edge(self):
        for width in WIDTHS:
            for route in ROUTES:
                with self.subTest(width=width, route=route):
                    over, row, small, contrast, edges = self.open(route, width, {"eval": OVERFLOW}, {"eval": ONE_ROW},
                                                                  {"eval": SMALL}, {"eval": CONTRAST}, {"eval": EDGES})
                    self.assertLessEqual(over, 0, "the page scrolls sideways")
                    self.assertEqual(row, 1, "the header wrapped to a second row")
                    self.assertEqual(small, [], "text smaller than 13 px")
                    self.assertEqual(contrast, [], "secondary text below 4.5:1")
                    self.assertEqual(edges, 0, "a coloured edge marks a row or a card")

    def test_dark_theme_reads_too(self):
        shots = os.environ.get("COMPACT_SHOTS")   # a folder: keep dark screenshots for a look
        for route, width in (("s/hub", 1440), ("s/billing", 390), ("sessions", 390), ("schedule", 820)):
            with self.subTest(route=route, width=width):
                keep = [{"shot": os.path.join(shots, f"dark-{route.replace('/', '-')}-{width}.png"), "width": width}] if shots else []
                dark, small, contrast = self.open(route, width, {"eval": "matchMedia('(prefers-color-scheme: dark)').matches"},
                                                  {"eval": SMALL}, {"eval": CONTRAST}, *keep, dark=True)
                self.assertTrue(dark)
                self.assertEqual(small, [])
                self.assertEqual(contrast, [])

    def test_the_page_is_denser_than_stock(self):
        rows = "[...document.querySelectorAll('aside .srow:not(.nav)')].map((r) => r.getBoundingClientRect().height).reduce((a, b) => a + b, 0)"
        head = "document.querySelector('main .head').getBoundingClientRect().height"
        with_plugin = self.open("s/hub", 1440, {"eval": rows}, {"eval": head})
        stock = self.open("s/hub", 1440, {"eval": "document.documentElement.classList.remove('cx'), 1"}, {"sleep": 200},
                          {"eval": rows}, {"eval": head})[1:]
        self.assertLess(with_plugin[0], stock[0] * 0.85)   # the session list: at least 15% shorter
        self.assertLess(with_plugin[1], stock[1])

    def test_removing_the_class_restores_the_stock_page(self):
        got = self.open("s/hub", 1440, {"eval": "getComputedStyle(document.querySelector('aside .srow')).paddingTop"},
                        {"eval": "document.documentElement.classList.remove('cx'), 1"}, {"sleep": 200},
                        {"eval": "getComputedStyle(document.querySelector('aside .srow')).paddingTop"})
        self.assertEqual([got[0], got[2]], ["4px", "7px"])


def _only_own(cls, own):
    """The hub's page tests are inherited with the helpers; they are the hub's to run, not this suite's."""
    for name in dir(cls):
        if name.startswith("test_") and name not in own:
            setattr(cls, name, None)


_only_own(Compact, [n for n in vars(Compact) if n.startswith("test_")])


def _with_quick():
    """The quick-answers suite again, with this plugin loaded on top."""
    if not os.path.isfile(os.path.join(QUICK, "tests", "test_quick_answers.py")):
        return None
    sys.path.insert(0, os.path.join(QUICK, "tests"))
    their = importlib.import_module("test_quick_answers")

    class QuickAnswersUnderCompact(their.QuickAnswers):
        def setUp(self):
            super().setUp()
            with open(os.environ["HUB_CONFIG"], "w") as f:
                json.dump({**BASE, "extensions": {"quick-answers": {"path": QUICK, "web": "main.js"}, **MINE}}, f)

        def open(self, *steps, width=1300):
            # same as theirs, but the steps start only when this plugin's styles are in: they move things on the page
            ready = "!!document.querySelector('.ask-card.quick')" if self.asked else "!!document.querySelector('.feed .row')"
            styled = "getComputedStyle(document.querySelector('.feed')).paddingTop === '14px'"
            got = self.page({"go": f"http://127.0.0.1:{self.port}/#/s/a", "width": width}, {"until": ready, "ms": 15000},
                            {"until": styled, "ms": 8000}, *steps)
            self.assertTrue(got[2]["until"], "the plugin did not load next to quick-answers")
            return got[:2] + got[3:]

    _only_own(QuickAnswersUnderCompact, [n for n in vars(their.QuickAnswers) if n.startswith("test_")])
    return QuickAnswersUnderCompact


QuickAnswersUnderCompact = _with_quick()
if QuickAnswersUnderCompact is None:
    del QuickAnswersUnderCompact

if __name__ == "__main__":
    unittest.main(verbosity=2)
