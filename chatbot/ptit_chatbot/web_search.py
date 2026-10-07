"""Small, bounded live search over PTIT's official WordPress sites."""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from threading import Lock
from time import monotonic
from urllib.parse import urlparse

from langchain_core.documents import Document

from .query import search_terms

OFFICIAL_SITES = (
    ("PTIT Tuyển sinh", "https://tuyensinh.ptit.edu.vn"),
    ("PTIT", "https://ptit.edu.vn"),
)
USER_AGENT = "PTIT-Assistant/1.0 (official-site search)"
MAX_RESULTS_PER_SITE = 2
MAX_TEXT_PER_PAGE = 4200
SEARCH_CACHE_TTL = 600
_BOILERPLATE = {"nav", "header", "footer", "aside", "script", "style", "noscript", "svg", "form"}
_CACHE = {}
_CACHE_LOCK = Lock()


class _ReadablePage(HTMLParser):
    """Extract headings, paragraphs, list items and table cells from HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.parts = []
        self.title = []
        self.in_title = False
        self.capture_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _BOILERPLATE:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = True
        if tag in {"h1", "h2", "h3", "p", "li", "td", "th"}:
            self.capture_depth += 1

    def handle_endtag(self, tag):
        if tag in _BOILERPLATE and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = False
        if tag in {"h1", "h2", "h3", "p", "li", "td", "th"} and self.capture_depth:
            self.capture_depth -= 1
            self.parts.append("\n")

    def handle_data(self, data):
        text = re.sub(r"\s+", " ", data).strip()
        if not text or self.skip_depth:
            return
        if self.in_title:
            self.title.append(text)
        if self.capture_depth:
            self.parts.append(text)


def _request(url: str, accept: str = "text/html,application/json") -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": accept},
    )
    with urllib.request.urlopen(request, timeout=7) as response:
        return response.read(1_500_000)


def _is_official_url(url: str, site_url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    official_host = (urlparse(site_url).hostname or "").lower()
    return host == official_host or host.endswith("." + official_host)


def _parse_html(url: str, html: bytes) -> Document | None:
    parser = _ReadablePage()
    parser.feed(html.decode("utf-8", errors="replace"))
    content = re.sub(r"\n{2,}", "\n", " ".join(parser.parts)).strip()
    if len(content) < 100:
        return None
    title = " ".join(parser.title).strip() or urlparse(url).path.rsplit("/", 2)[-2]
    return Document(
        page_content=content[:MAX_TEXT_PER_PAGE],
        metadata={"source": url, "title": title, "kind": "official_web"},
    )


def _search_api(site_url: str, query: str) -> list[tuple[str, str]]:
    endpoint = site_url + "/wp-json/wp/v2/search?" + urllib.parse.urlencode(
        {"search": query, "per_page": MAX_RESULTS_PER_SITE}
    )
    try:
        payload = json.loads(_request(endpoint, "application/json"))
    except (OSError, ValueError, urllib.error.URLError):
        return []
    results = []
    if isinstance(payload, list):
        for item in payload:
            url = item.get("url", "")
            title = item.get("title", "")
            if isinstance(title, dict):
                title = title.get("rendered", "")
            if url and _is_official_url(url, site_url):
                results.append((str(title), url))
    return results


def _search_html(site_url: str, query: str) -> list[tuple[str, str]]:
    """Fallback for official WordPress sites where the REST search is disabled."""
    search_url = site_url + "/?" + urllib.parse.urlencode({"s": query})
    try:
        html = _request(search_url).decode("utf-8", errors="replace")
    except (OSError, UnicodeError, urllib.error.URLError):
        return []

    class Links(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.href = None
            self.text = []
            self.items = []

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                self.href = dict(attrs).get("href")
                self.text = []

        def handle_endtag(self, tag):
            if tag == "a" and self.href:
                title = re.sub(r"\s+", " ", " ".join(self.text)).strip()
                self.items.append((title, urllib.parse.urljoin(site_url, self.href)))
                self.href = None

        def handle_data(self, data):
            if self.href:
                self.text.append(data)

    parser = Links()
    parser.feed(html)
    seen = set()
    results = []
    for title, url in parser.items:
        path = urlparse(url).path.rstrip("/")
        if (
            title
            and path
            and url not in seen
            and _is_official_url(url, site_url)
            and not any(part in path for part in ("/wp-content/", "/category/", "/tag/", "/author/"))
        ):
            seen.add(url)
            results.append((title, url))
        if len(results) >= MAX_RESULTS_PER_SITE:
            break
    return results


def _fetch_page(candidate: tuple[str, str], site_name: str, site_url: str) -> Document | None:
    title, url = candidate
    if not _is_official_url(url, site_url):
        return None
    try:
        page = _parse_html(url, _request(url))
    except (OSError, UnicodeError, urllib.error.URLError, ValueError):
        return None
    if page:
        if title:
            page.metadata["title"] = title
        page.metadata["source_label"] = site_name
    return page


def _site_results(site_name: str, site_url: str, query: str) -> list[Document]:
    candidates = _search_api(site_url, query)
    if not candidates:
        candidates = _search_html(site_url, query)
    with ThreadPoolExecutor(max_workers=MAX_RESULTS_PER_SITE) as executor:
        return [
            page
            for page in executor.map(
                lambda candidate: _fetch_page(candidate, site_name, site_url), candidates
            )
            if page
        ]


def search_official_sites(question: str) -> list[Document]:
    """Fetch a few current matching pages from PTIT's two official websites."""
    query = search_terms(question)
    if not query:
        return []
    cache_key = query.casefold()
    now = monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached and now - cached[0] < SEARCH_CACHE_TTL:
            return cached[1]

    with ThreadPoolExecutor(max_workers=len(OFFICIAL_SITES)) as executor:
        batches = executor.map(
            lambda site: _site_results(site[0], site[1], query), OFFICIAL_SITES
        )
        results = [document for batch in batches for document in batch]
    with _CACHE_LOCK:
        _CACHE[cache_key] = (monotonic(), results)
    return results
