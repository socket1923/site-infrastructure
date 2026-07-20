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
        "person-first identity, form prohibition, CSP compatibility, and tabnabbing checks passed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
