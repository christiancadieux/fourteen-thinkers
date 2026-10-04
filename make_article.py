#!/usr/bin/env python3
"""Build the reader copy of the article from medium-draft.html.

Writes article.html (the draft without its header bar and copy button) and,
if Playwright is installed, medium-article.pdf with the screenshots in place.
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))

s = open(os.path.join(HERE, "medium-draft.html"), encoding="utf-8").read()
s = re.sub(r'\s*<div class="bar">.*?</div>\n', "\n", s, count=1, flags=re.S)
s = re.sub(r"<script>.*?</script>\s*", "", s, flags=re.S)
s = s.replace("</style>", "@media print { html,body,.wrap{background:#fff!important} .wrap{max-width:none!important;padding:0!important;margin:0!important} article{border:none!important;box-shadow:none!important;padding:0!important;margin:0!important;max-width:none!important;background:#fff!important} body{font-size:10.5pt!important} figure{break-inside:avoid} h2{break-after:avoid} }\n</style>", 1)
open(os.path.join(HERE, "article.html"), "w", encoding="utf-8").write(s)
print("wrote article.html")

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright not installed; skipped the PDF")
    raise SystemExit

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(color_scheme="light")
    pg.goto("file://" + os.path.join(HERE, "article.html"))
    pg.wait_for_timeout(800)
    pg.emulate_media(media="print", color_scheme="light")
    pg.pdf(path=os.path.join(HERE, "medium-article.pdf"), format="Letter", print_background=True,
           margin={"top": "0.7in", "bottom": "0.7in", "left": "0.75in", "right": "0.75in"})
    b.close()
print("wrote medium-article.pdf")
