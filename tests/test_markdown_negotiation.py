"""`Accept: text/markdown` on a page with a Markdown twin serves the twin at the page's own URL;
browsers keep HTML, and both answers carry `Vary: Accept` so a cache cannot mix them up."""

from __future__ import annotations

import pytest

from treg.bootstrap_http import _prefers_markdown

MD = {"accept": "text/markdown, text/html;q=0.8"}
BROWSER = {"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}


@pytest.mark.parametrize("accept,expected", [
    ("text/markdown", True),
    ("text/markdown, text/html;q=0.8", True),
    ("text/html, text/markdown", True),               # a tie goes to Markdown, which was asked for
    ("text/html;q=1, text/markdown;q=0.5", False),
    ("text/html,application/xhtml+xml,*/*;q=0.8", False),
    ("*/*", False),
    ("", False),
    ("text/markdown;q=0", False),
    ("text/markdown;q=oops", False),
])
def test_prefers_markdown(accept, expected):
    assert _prefers_markdown(accept) is expected


@pytest.mark.parametrize("path", ["/workflows/find-and-verify-a-lead-list", "/agents/claude-code"])
async def test_negotiated_twin_matches_the_md_url(clients, path):
    twin = await clients.get(path + ".md")
    negotiated = await clients.get(path, headers=MD)
    assert negotiated.status_code == 200
    assert negotiated.headers["content-type"].startswith("text/markdown")
    assert negotiated.text == twin.text
    assert "accept" in negotiated.headers["vary"].lower()

    page = await clients.get(path, headers=BROWSER)
    assert page.headers["content-type"].startswith("text/html")
    assert "accept" in page.headers["vary"].lower()


async def test_aliased_twins(clients):
    r = await clients.get("/tutorial", headers=MD)
    assert r.status_code == 200 and r.text == (await clients.get("/tutorial.md")).text


async def test_pages_without_a_twin_are_untouched(clients):
    r = await clients.get("/pricing", headers=MD)
    assert r.headers["content-type"].startswith("text/html")
    assert "accept" not in r.headers.get("vary", "").lower()
    # A path that already names its twin is served as before.
    md = await clients.get("/workflows/find-and-verify-a-lead-list.md", headers=BROWSER)
    assert md.headers["content-type"].startswith("text/markdown")


async def test_unknown_page_stays_a_404(clients):
    assert (await clients.get("/workflows/no-such-workflow", headers=MD)).status_code == 404
