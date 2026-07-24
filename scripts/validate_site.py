#!/usr/bin/env python3
"""Dependency-free static security and link checks for the Socket23 site."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "static-site" / "site"
SKIP_SCHEMES = {"mailto", "tel", "data"}
PUBLIC_ORIGIN = "https://socket23.com"
IDENTITY_CUES = re.compile(
    r"(?i)\b(company|agency|consultant|consulting|founder|ceo)\b|"
    r"free consultation|service packages?|client testimonials?|our team"
)
PRIVATE_DATA_CUES = {
    "city-level location": re.compile(r"(?i)\bSandy,?\s+Oregon\b"),
    "private IPv4 address": re.compile(
        r"(?<!\d)(?:10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)"
        r"(?:\d{1,3}\.){1,2}\d{1,3}(?!\d)"
    ),
    "MAC address": re.compile(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![0-9a-f])"),
    "active hardware detail": re.compile(r"(?i)\b(?:RTX\s*A6000|ME4024|PowerEdge\s*R620)\b"),
}
FORBIDDEN_ACTIVE_CLIENTS = re.compile(
    r"(?i)\b(?:fetch|XMLHttpRequest|WebSocket|EventSource)\s*\(|https?://"
)


class PageParser(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.links: list[tuple[str, str]] = []
        self.canonicals: list[str] = []
        self.errors: list[str] = []
        self.inline_script_depth = 0

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = {k.lower(): (v or "") for k, v in attrs_list}
        line, _ = self.getpos()
        where = f"{self.path.relative_to(ROOT)}:{line}"

        for name in attrs:
            if name.startswith("on"):
                self.errors.append(f"{where}: inline event handler {name!r} is blocked by CSP")

        if tag == "script":
            if not attrs.get("src"):
                self.inline_script_depth += 1
                self.errors.append(f"{where}: inline script is blocked by CSP")

        if tag == "iframe":
            self.errors.append(f"{where}: embedded frames are not permitted")

        if tag in {"script", "img", "source", "video", "audio"}:
            source = attrs.get("src", "")
            parsed_source = urlparse(source)
            if parsed_source.scheme in {"http", "https"}:
                self.errors.append(f"{where}: remotely hosted active/media asset {source!r} is not permitted")

        if tag == "link" and "stylesheet" in attrs.get("rel", "").lower().split():
            stylesheet = attrs.get("href", "")
            if urlparse(stylesheet).scheme in {"http", "https"}:
                self.errors.append(f"{where}: remotely hosted stylesheet {stylesheet!r} is not permitted")

        if attrs.get("target", "").lower() == "_blank":
            rel = set(attrs.get("rel", "").lower().split())
            if "noopener" not in rel:
                self.errors.append(f"{where}: target=_blank is missing rel=noopener")

        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonicals.append(attrs.get("href", ""))

        for attr in ("href", "src"):
            value = attrs.get(attr)
            if not value or value.startswith("#"):
                continue
            parsed = urlparse(value)
            if parsed.scheme == "http":
                self.errors.append(f"{where}: insecure external URL {value!r}")
            if parsed.scheme in SKIP_SCHEMES or parsed.scheme in {"http", "https"}:
                continue
            if value.startswith("//"):
                self.errors.append(f"{where}: protocol-relative URL {value!r}")
                continue
            self.links.append((where, value))

        if tag == "form":
            self.errors.append(f"{where}: public forms are not permitted on this personal static site")

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self.inline_script_depth:
            self.inline_script_depth -= 1


def resolve_local(page: Path, value: str) -> Path:
    parsed = urlparse(value)
    path = unquote(parsed.path)
    if path.startswith("/"):
        candidate = SITE / path.lstrip("/")
    else:
        candidate = page.parent / path
    if path.endswith("/") or not path:
        candidate = candidate / "index.html"
    return candidate.resolve()


def main() -> int:
    html_files = sorted(SITE.rglob("*.html"))
    if not html_files:
        print("No HTML files found", file=sys.stderr)
        return 1

    errors: list[str] = []
    expected_public_urls: set[str] = set()
    for page in html_files:
        text = page.read_text(encoding="utf-8-sig")
        parser = PageParser(page)
        parser.feed(text)
        errors.extend(parser.errors)

        relative = page.relative_to(SITE).as_posix()
        if relative != "404.html":
            route = "/" if relative == "index.html" else f"/{relative}"
            expected_canonical = f"{PUBLIC_ORIGIN}{route}"
            expected_public_urls.add(expected_canonical)
            if parser.canonicals != [expected_canonical]:
                errors.append(
                    f"{page.relative_to(ROOT)}: expected one canonical {expected_canonical!r}, "
                    f"found {parser.canonicals!r}"
                )

        cue = IDENTITY_CUES.search(text)
        if cue:
            errors.append(
                f"{page.relative_to(ROOT)}: business-era identity cue {cue.group(0)!r} is not permitted"
            )

        for label, pattern in PRIVATE_DATA_CUES.items():
            cue = pattern.search(text)
            if cue:
                errors.append(
                    f"{page.relative_to(ROOT)}: {label} {cue.group(0)!r} is not permitted in public HTML"
                )

        if page.parent.name == "work":
            for marker in ("Context", "My role", "Result", "How I validated it", "What this demonstrates"):
                if marker not in text:
                    errors.append(f"{page.relative_to(ROOT)}: case study is missing {marker!r}")

        for where, value in parser.links:
            target = resolve_local(page, value)
            try:
                target.relative_to(SITE.resolve())
            except ValueError:
                errors.append(f"{where}: local URL escapes site root: {value!r}")
                continue
            if not target.exists():
                errors.append(f"{where}: broken local URL {value!r} -> {target.relative_to(ROOT)}")

    for asset in sorted(SITE.rglob("*")):
        if not asset.is_file() or asset.suffix.lower() not in {".js", ".css", ".svg"}:
            continue
        text = asset.read_text(encoding="utf-8-sig")
        relative = asset.relative_to(ROOT)
        if asset.suffix.lower() == ".js" and FORBIDDEN_ACTIVE_CLIENTS.search(text):
            errors.append(f"{relative}: network-capable or remote client code is not permitted")
        if asset.suffix.lower() == ".css" and re.search(
            r"(?i)@import\s|url\(\s*['\"]?https?://", text
        ):
            errors.append(f"{relative}: remote stylesheet/font/image dependencies are not permitted")
        if asset.suffix.lower() == ".svg" and re.search(
            r"(?i)<(?:script|foreignObject)\b|\bon[a-z]+\s*=|"
            r"(?:href|src)\s*=\s*['\"]https?://", text
        ):
            errors.append(f"{relative}: SVG contains active or remotely hosted content")

    homepage = (SITE / "index.html").read_text(encoding="utf-8-sig")
    for marker in (
        'class="hero-art"',
        'class="role-panel"',
        "Public engineering artifacts",
        "nothing from the assistant is exposed through this public site",
    ):
        if marker not in homepage:
            errors.append(f"static-site/site/index.html: missing privacy-safe visual marker {marker!r}")

    projects_page = (SITE / "projects.html").read_text(encoding="utf-8-sig")
    if projects_page.count("data-project-filter=") != 6:
        errors.append("static-site/site/projects.html: expected six static project filters")
    if projects_page.count("data-project-category=") != 8:
        errors.append("static-site/site/projects.html: expected eight categorized project cards")

    theme_page_count = sum(
        1 for page in html_files if 'id="themeBtn"' in page.read_text(encoding="utf-8-sig")
    )
    if theme_page_count != len(html_files):
        errors.append("static-site/site: every HTML page must include the local theme control")

    sitemap = SITE / "sitemap.xml"
    try:
        root = ET.parse(sitemap).getroot()
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        actual_public_urls = {
            (node.text or "").strip() for node in root.findall("sm:url/sm:loc", namespace)
        }
        if actual_public_urls != expected_public_urls:
            errors.append(
                "static-site/site/sitemap.xml: URL set does not match canonical HTML pages; "
                f"missing={sorted(expected_public_urls - actual_public_urls)!r} "
                f"extra={sorted(actual_public_urls - expected_public_urls)!r}"
            )
    except (ET.ParseError, OSError) as exc:
        errors.append(f"static-site/site/sitemap.xml: cannot parse sitemap: {exc}")

    if errors:
        print("Static site validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Validated {len(html_files)} HTML files: links, canonicals, sitemap, case-study structure, "
        "person-first identity, privacy invariants, local-only assets, form prohibition, "
        "CSP compatibility, and tabnabbing checks passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
