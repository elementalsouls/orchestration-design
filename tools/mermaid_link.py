"""Turn a Mermaid diagram into a pre-filled mermaid.live edit URL.

mermaid.live stores the whole editor state in the URL fragment as
`#pako:<base64url(zlib(json))>`. Building that here means the human clicks
once and the diagram is already loaded — no copy-paste step to get wrong.

Usage:
    python mermaid_link.py diagram.mmd
    cat diagram.mmd | python mermaid_link.py
Self-check:
    python mermaid_link.py --selftest
"""

from __future__ import annotations

import base64
import json
import sys
import zlib


def live_url(code: str, theme: str = "default") -> str:
    state = {
        "code": code.strip(),
        "mermaid": json.dumps({"theme": theme}),
        "autoSync": True,
        "updateDiagram": True,
    }
    raw = json.dumps(state).encode("utf-8")
    packed = zlib.compress(raw, 9)
    return "https://mermaid.live/edit#pako:" + base64.urlsafe_b64encode(packed).decode()


def decode(url: str) -> dict:
    """Inverse of live_url — used by the self-check to prove the payload survives."""
    frag = url.split("#pako:", 1)[1]
    frag += "=" * (-len(frag) % 4)                      # restore stripped padding
    return json.loads(zlib.decompress(base64.urlsafe_b64decode(frag)))


def _selftest() -> int:
    for code in [
        "flowchart TD\n  A --> B",
        # the real thing: unicode, quotes, <br/>, nested brackets
        'flowchart TD\n  S([start]) --> d["discover (fn)<br/><small>list 6 checks</small>"]\n'
        '  d -->|"next"| d\n  d --> E([end])',
    ]:
        url = live_url(code)
        assert url.startswith("https://mermaid.live/edit#pako:")
        assert decode(url)["code"] == code.strip(), "payload did not round-trip"
        assert " " not in url, "url contains a space — would break on paste"
    print("OK: payload round-trips, URL is paste-safe.")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    src = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    print(live_url(src))
