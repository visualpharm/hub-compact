# Compact

A page plugin for Agents Hub: a compact redesign of the whole hub page for phone, tablet and desktop.

- Session list, headers, feed, cards, queue, composer, schedule, settings and plugin views are tighter: about a quarter
  more rows per screen.
- Density comes from spacing and structure. No text is smaller than 13 px, secondary text is dark enough to read, and
  the hub's "Text size" setting still scales everything.
- On a phone the session header is one row: a menu icon to the session list, the name, a state dot, the feed switch,
  Stop and More.
- "Waiting for you" is said by the red tag and mark, not by a coloured edge on the row; a message is attributed by the
  name in its colour, not by a bar down its side.
- Works next to `quick-answers` (answer by clicking an option, text selection in the feed): its test suite is run on
  top of this plugin.

## Install, turn off

    hub market install visualpharm/hub-compact     # installs pinned to the current commit
    hub market remove compact                      # turn it off: the stock page is back after a reload

Settings → Plugins has the same switch. The plugin only adds one class to the page (`html.cx`) and one stylesheet; it
changes no hub state.

## Develop

    python3 dev/serve.py                 # demo hub with sample data on http://127.0.0.1:1100/
    python3 dev/serve.py --off --port N  # the same page without the plugin
    dev/shots.sh 1100 /tmp/shots         # every screen at 390, 820 and 1440
    python3 tests/test_compact.py        # fit, type size, contrast, both themes, quick-answers on top

Icons come from Icons8, Material Outlined (`icons8.json`), the same family as the hub's own.
