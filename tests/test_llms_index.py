"""llms.txt carries a map of the generated pages by their Markdown twins, and /llms-full.txt joins
llms.txt with every bundled guide, so an agent finds the page it needs instead of guessing a URL."""

from __future__ import annotations

import re


def _links(text: str) -> list[str]:
    return re.findall(r"\]\((https?://[^)\s]+)\)", text)


async def test_llms_txt_lists_every_generated_page_by_its_markdown_twin(clients):
    from treg import agent_pages
    from treg.config import get_settings

    base = get_settings().public_url.rstrip("/")
    text = (await clients.get("/llms.txt")).text
    for slug in agent_pages.WORKFLOWS:
        assert f"({base}/workflows/{slug}.md)" in text, slug
    for slug in agent_pages.USE_CASE_PAGES:
        assert f"({base}/use-cases/{slug}.md)" in text, slug
    assert f"({base}/agents/claude-code.md)" in text
    assert "/agents/grok-bot.md" not in text          # that page redirects; list only what answers
    assert f"{base}/llms-full.txt" in text
    # The index sits before `## Optional`, the part of an llms.txt a reader may skip.
    assert text.index("## Workflows") < text.index("## Optional")
    assert "{BASE}" not in text
    # Agents truncate long index files; keep this one well under the common 50,000-character cut.
    assert len(text) < 50_000


async def test_every_page_link_in_llms_txt_answers(clients):
    from treg.config import get_settings

    base = get_settings().public_url.rstrip("/")
    text = (await clients.get("/llms.txt")).text
    for url in _links(text):
        if not url.startswith(base) or url.endswith("/llms-full.txt"):
            continue
        path = url[len(base):]
        r = await clients.get(path)
        assert r.status_code == 200, path
        if path.endswith(".md") and not path.startswith(("/skill.md", "/tutorial", "/quickstart",
                                                         "/integrate", "/feedback", "/gtm-engineering")):
            assert r.headers["content-type"].startswith("text/markdown"), path


async def test_llms_full_joins_llms_txt_and_the_guides(clients):
    full = await clients.get("/llms-full.txt")
    assert full.status_code == 200
    body = full.text
    llms = (await clients.get("/llms.txt")).text
    assert body.startswith(llms.rstrip("\n")[:200])
    skill = (await clients.get("/skill.md")).text
    assert skill.strip()[:300] in body
    assert "<!-- source: " in body and "/quickstart.md -->" in body
    assert "{BASE}" not in body


async def test_self_hosted_llms_txt_has_no_page_index(monkeypatch):
    """The generated pages exist only on the hosted service; a self-hosted registry must not send an
    agent to them."""
    from httpx import ASGITransport, AsyncClient

    from treg.api import app
    from treg.config import get_settings

    monkeypatch.setenv("TREG_PUBLIC_URL", "https://registry.example.internal")
    get_settings.cache_clear()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://registry") as c:
            text = (await c.get("/llms.txt")).text
            assert "## Workflows" not in text and "/workflows/" not in text
            assert "llms-full.txt" not in text
            assert (await c.get("/llms-full.txt")).status_code == 200
    finally:
        get_settings.cache_clear()
