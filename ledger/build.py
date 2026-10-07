"""Build step for the transcripts synthesis.

Reads ledger.json (master data) and sources/ (authors' own texts), then:
  1. checks every quotation in synthesis.md and the chart reasons
     against the quoted author's own texts;
  2. checks "N of the fifteen (A, B and C)" counts in synthesis.md;
  3. writes report.md (failed quotes, single-quote scores, forecast scorecard);
  4. writes the chart data from ledger.json into both chart pages
     (build/*.html for publishing, ../*.html as standalone email copies).

Run:  python3 build.py
"""
import json, os, re, glob, html as htmllib
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "sources")

def doc(name):
    """The project documents sit in the repository root or in transcripts/."""
    for d in (ROOT, os.path.join(ROOT, "transcripts")):
        if os.path.exists(os.path.join(d, name)):
            return os.path.join(d, name)
    return os.path.join(ROOT, name)

# ---------- source texts ----------

FILLERS = {"uh", "um", "uhm", "er"}

def norm(t):
    t = t.lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"\[[^\]]{0,30}\]", " ", t)  # short asides such as [laughter], [music], [sic]
    t = re.sub(r"[^a-z0-9]+", " ", t)
    out = []
    for w in t.split():
        if w in FILLERS or (out and out[-1] == w):
            continue
        out.append(w)
    return " ".join(out)

def load_sources():
    texts, files = {}, {}
    for d in sorted(os.listdir(SRC)):
        p = os.path.join(SRC, d)
        if not os.path.isdir(p):
            continue
        fl = sorted(glob.glob(os.path.join(p, "*")))
        files[d] = [os.path.relpath(f, SRC) for f in fl]
        texts[d] = {os.path.relpath(f, SRC): norm(open(f, encoding="utf-8", errors="ignore").read()) for f in fl}
    return texts, files

TEXTS, FILES = load_sources()
INDEX = json.load(open(os.path.join(SRC, "index.json")))
URL = {e["file"]: e["url"] for au in INDEX.values() for e in au if e.get("url")}

ALIASES = {"MacGregor": "CameronMacGregor", "Krapivnik": "CameronMacGregor", "Desai": "Desai-Tyson", "Tyson": "Desai-Tyson", "Brookings": "Brookings-2009"}
AUTHOR_NAMES = sorted(set(list(TEXTS.keys()) + list(ALIASES.keys())), key=len, reverse=True)

def find(quote, authors=None):
    """Return list of (author, file) where every part of the quote occurs."""
    parts = [norm(x) for x in re.split(r"\.\.\.|…", quote)]
    parts = [x for x in parts if len(x.split()) >= 2] or [norm(quote)]
    hits = []
    for au in (authors or TEXTS.keys()):
        for f, t in TEXTS.get(au, {}).items():
            if all(x in t for x in parts):
                hits.append((au, f))
    return hits

# ---------- quote checks in markdown ----------

QUOTE_RE = re.compile(r'"([^"\n]{3,}?)"')

def md_quotes(path):
    rows = []
    section = ""
    lines = open(path, encoding="utf-8").read().split("\n")
    headings = set()
    for d in ("synthesis.md",):
        headings |= {norm(l.strip("# ")) for l in open(doc(d), encoding="utf-8") if l.startswith("#")}
    recent = []  # authors named in recent lines of the same section (context)
    for ln, line in enumerate(lines, 1):
        if line.startswith("#"):
            section = line.strip("# \n")
            recent = []
            continue
        if section.lower().startswith("sources read"):
            continue
        # author mentions with positions
        ments = []
        for name in AUTHOR_NAMES:
            for m in re.finditer(r"\b" + re.escape(name) + r"\b", line):
                ments.append((m.start(), ALIASES.get(name, name)))
        ments.sort()
        for m in QUOTE_RE.finditer(line):
            q = m.group(1).strip()
            words = len(norm(q).split())
            if norm(q) in headings:
                continue
            before = [a for pos, a in ments if pos < m.start()]
            cands = list(dict.fromkeys(reversed(before)))  # nearest first, unique
            ctx = [a for a in recent if a not in cands]
            rows.append({"doc": os.path.basename(path), "line": ln, "section": section, "quote": q,
                         "words": words, "candidates": cands, "context": ctx})
        if ments:
            recent = list(dict.fromkeys([a for _, a in reversed(ments)] + recent))[:6]
    return rows

MANUAL = {}
HYP = []
ACH_DATA = []

def check_md(path):
    out = []
    for r in md_quotes(path):
        if norm(r["quote"]) in MANUAL:
            m = MANUAL[norm(r["quote"])]
            r.update(status="verified", author=m["author"], source=m["source"], note=m["note"])
            out.append(r)
            continue
        if r["words"] < 3:
            r["status"] = "term"
            out.append(r)
            continue
        hits = find(r["quote"], r["candidates"]) if r["candidates"] else []
        if not hits and r["context"]:
            hits = find(r["quote"], r["context"])
            if hits:
                r["status"] = "verified"
                r["author"], r["source"] = hits[0]
                r["note"] = "speaker inferred from earlier lines"
                out.append(r)
                continue
        if hits:
            r["status"] = "verified"
            r["author"] = hits[0][0]
            r["source"] = hits[0][1]
        else:
            anyhits = find(r["quote"])
            if anyhits:
                r["status"] = "elsewhere"
                r["found_in"] = sorted({a for a, _ in anyhits})
                r["source"] = anyhits[0][1]
            else:
                r["status"] = "not_found"
        out.append(r)
    return out

# ---------- count checks ----------

NUM = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen".split())}

def check_counts(path):
    probs = []
    pat = re.compile(r"\b([A-Za-z]+) of the (fourteen|fifteen|thirteen)\s*\(([^)]*)\)")
    for ln, line in enumerate(open(path, encoding="utf-8"), 1):
        for m in pat.finditer(line):
            n = NUM.get(m.group(1).lower())
            names = [x for x in re.split(r",\s*|\s+and\s+", m.group(3)) if x.strip()]
            if n is not None and n != len(names):
                probs.append({"line": ln, "text": m.group(0)[:120], "says": n, "lists": len(names)})
    return probs

# ---------- chart checks ----------

CURLY = re.compile(r"“([^”]{3,}?)”")

def check_chart(entry):
    single, unquoted, failed = [], [], []
    for sc in entry["scores"]:
        if sc["score"] is None:
            continue
        qs = CURLY.findall(sc["why"])
        ok = [q for q in qs if len(norm(q).split()) < 3 or norm(q) in MANUAL or find(q, [sc["author"]])]
        bad = [q for q in qs if q not in ok]
        for q in bad:
            failed.append({**sc, "quote": q, "found_in": sorted({a for a, _ in find(q)})})
        nq = len([q for q in ok if len(norm(q).split()) >= 3])
        if nq == 0:
            unquoted.append(sc)
        elif nq == 1:
            single.append(sc)
    for ad in entry["advice"]:
        for q in CURLY.findall(ad["quote"]):
            if len(norm(q).split()) >= 3 and norm(q) not in MANUAL and not find(q, [ad["author"]]):
                failed.append({"axis": "advice: " + ad["advice"], "author": ad["author"], "quote": q,
                               "found_in": sorted({a for a, _ in find(q)})})
    return single, unquoted, failed

# ---------- chart pages ----------

def js_array(name, value):
    return "const " + name + " = " + json.dumps(value, ensure_ascii=False, indent=1) + ";\n"

def quote_counts(entry, quotes):
    """Checked quotations per author: in synthesis.md, and in this chart's reasons and advice."""
    out = {}
    for a in entry["authors"]:
        n = a["name"]
        syn = sum(1 for q in quotes if q["doc"] == "synthesis.md" and q["status"] == "verified" and q.get("author") == n)
        ch = 0
        for x in [s_["why"] for s_ in entry["scores"] if s_["author"] == n and s_["score"] is not None] + \
                 [ad["quote"] for ad in entry["advice"] if ad["author"] == n]:
            ch += sum(1 for q in CURLY.findall(x) if len(norm(q).split()) >= 3 and (norm(q) in MANUAL or find(q, [n])))
        out[n] = {"synthesis": syn, "charts": ch}
    return out

def pca_map(entry):
    """Two principal components of the authors' scores, in plain Python (no numpy).
    Missing scores are filled with the question's average; each question is standardised."""
    names = [a["name"] for a in entry["authors"]]
    axes = [a["id"] for a in entry["axes"]]
    sc = {(x["author"], x["axis"]): x["score"] for x in entry["scores"] if x["score"] is not None}
    n, m = len(names), len(axes)
    cols = []
    for ax in axes:
        vals = [sc[(a, ax)] for a in names if (a, ax) in sc]
        mean = sum(vals) / len(vals)
        col = [sc.get((a, ax), mean) for a in names]
        mu = sum(col) / n
        sd = (sum((v - mu) ** 2 for v in col) / n) ** 0.5 or 1.0
        cols.append([(v - mu) / sd for v in col])
    Z = [[cols[j][i] for j in range(m)] for i in range(n)]
    C = [[sum(Z[k][a] * Z[k][b] for k in range(n)) / n for b in range(m)] for a in range(m)]
    total = sum(C[a][a] for a in range(m))
    vecs, vals = [], []
    for _ in range(3):
        v = [1.0 / (j + 1) for j in range(m)]
        for _ in range(500):
            w = [sum(C[a][b] * v[b] for b in range(m)) for a in range(m)]
            nrm = sum(x * x for x in w) ** 0.5
            v = [x / nrm for x in w]
        lam = sum(v[a] * sum(C[a][b] * v[b] for b in range(m)) for a in range(m))
        vecs.append(v); vals.append(lam)
        C = [[C[a][b] - lam * v[a] * v[b] for b in range(m)] for a in range(m)]
    # orient: x grows toward "power above countries", y toward "China as the model"
    if vecs[0][axes.index("centre")] < 0: vecs[0] = [-x for x in vecs[0]]
    if vecs[1][axes.index("china")] < 0: vecs[1] = [-x for x in vecs[1]]
    if vecs[2][axes.index("coord")] < 0: vecs[2] = [-x for x in vecs[2]]
    pts = []
    for i, a in enumerate(names):
        c = [round(sum(Z[i][j] * vecs[k][j] for j in range(m)), 3) for k in range(3)]
        pts.append({"i": i, "name": a, "c": c,
                    "missing": sum(1 for ax in axes if (a, ax) not in sc)})
    def top(v):
        idx = sorted(range(m), key=lambda j: -abs(v[j]))[:5]
        return [{"axis": axes[j], "w": round(v[j], 2)} for j in idx]
    return {"points": pts, "var": [round(v / total, 3) for v in vals], "load": [top(v) for v in vecs]}

def render(template, entry, counts=None, cases=None):
    h = open(template, encoding="utf-8").read()
    names = [a["name"] for a in entry["authors"]]
    axes = []
    for ax in entry["axes"]:
        s = {x["author"]: x for x in entry["scores"] if x["axis"] == ax["id"]}
        axes.append({**ax, "s": [s[n]["score"] for n in names], "why": [s[n]["why"] for n in names]})
    advice = []
    for ad in dict.fromkeys(a["advice"] for a in entry["advice"]):
        advice.append({"label": ad, "who": [{"i": names.index(a["author"]), "q": a["quote"]}
                                            for a in entry["advice"] if a["advice"] == ad]})
    def swap(h, start, end, new):
        i = h.index(start); j = h.index(end, i) + len(end)
        return h[:i] + new + h[j:]
    h = swap(h, "const AUTHORS = [", "];\n", js_array("AUTHORS", entry["authors"]))
    h = swap(h, "const AXES = [", "\n];\n", js_array("AXES", axes))
    h = swap(h, "const ADVICE = [", "];\n", js_array("ADVICE", advice))
    h = re.sub(r"repeat\(\d+, 1fr\)", "repeat(%d, 1fr)" % len(names), h, count=1)
    if cases is not None and "const ACH = " in h:
        payload = [{"grid": g, "scores": ach_scores(g), "scores_unstaged": ach_scores(g, True)} for g in ACH_DATA]
        i = h.index("const ACH = "); j = h.index(";\n", i) + 2
        h = h[:i] + "const ACH = " + json.dumps(payload, ensure_ascii=False) + ";\n" + h[j:]
    if cases is not None and "const HYPOTHESES = " in h:
        i = h.index("const HYPOTHESES = "); j = h.index(";\n", i) + 2
        h = h[:i] + "const HYPOTHESES = " + json.dumps(HYP, ensure_ascii=False) + ";\n" + h[j:]
    if cases is not None and "const CASES = " in h:
        i = h.index("const CASES = "); j = h.index(";\n", i) + 2
        h = h[:i] + "const CASES = " + json.dumps(cases, ensure_ascii=False) + ";\n" + h[j:]
    if "const MAP = " in h:
        i = h.index("const MAP = "); j = h.index(";\n", i) + 2
        h = h[:i] + "const MAP = " + json.dumps(pca_map(entry), ensure_ascii=False) + ";\n" + h[j:]
    if "vantage" in entry and "const VANTAGE = " in h:
        i = h.index("const VANTAGE = "); j = h.index(";\n", i) + 2
        h = h[:i] + "const VANTAGE = " + json.dumps(entry["vantage"], ensure_ascii=False) + ";\n" + h[j:]
    if counts is not None and "const QUOTECOUNTS = " in h:
        i = h.index("const QUOTECOUNTS = "); j = h.index(";\n", i) + 2
        h = h[:i] + "const QUOTECOUNTS = " + json.dumps(counts, ensure_ascii=False) + ";\n" + h[j:]
    return h

def standalone(page):
    t = page.index("</title>") + 8
    out = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1">\n' + page[:t].strip() +
           '\n<style>html{color-scheme:light dark}body{margin:0}[hidden]{display:none!important}</style>' + page[t:])
    i = out.index("</style>", out.index("--bg")) + 8
    return out[:i] + "\n</head>\n<body>\n" + out[i:].lstrip() + "\n</body>\n</html>\n"

# ---------- hypotheses ----------

def hyp_markdown(H):
    def names(xs): return ", ".join(xs) if xs else "none in this set"
    out = ["| | Hypothesis | Proposed by | Fits the material of | Cuts against | What would test it | Where it stands |",
           "|---|---|---|---|---|---|---|"]
    for h in H:
        out.append(f"| {h['id']} | {h['title']} | {h['proposed_by']} | {names(h['support'])} | {names(h['against'])} | {'; '.join(h['tests'])} | {h['status']} |")
    out.append("")
    for h in H:
        if h["id"] in ("H1", "H2"):
            continue
        out.append(f"- **{h['id']}. {h['title']}** ({h['answers']}). {h['claim']} Evidence: {h['evidence']} Objection: {h['objection']}")
    return "\n".join(out)

def write_hyp_md(H):
    p = doc("synthesis.md")
    s = open(p, encoding="utf-8").read()
    a, b = "<!-- hypotheses:start -->", "<!-- hypotheses:end -->"
    if a not in s:
        return
    i = s.index(a) + len(a); j = s.index(b)
    new = s[:i] + "\n" + hyp_markdown(H) + "\n" + s[j:]
    if new != s:
        open(p, "w", encoding="utf-8").write(new)

# ---------- evidence grid (analysis of competing hypotheses) ----------

def ach_scores(g, drop_staged=False):
    w = g["weights"]; out = {}
    for h in g["hypotheses"]:
        inc = con = 0.0; ninc = ncon = 0
        for f in g["facts"]:
            if drop_staged and f.get("staged"):
                continue
            c = f["cells"].get(h["id"], "N")
            if c == "I": inc += w[f["reliability"]]; ninc += 1
            if c == "C": con += w[f["reliability"]]; ncon += 1
        out[h["id"]] = {"inc": round(inc, 2), "con": round(con, 2), "ninc": ninc, "ncon": ncon}
    return out

def ach_markdown(g):
    a = ach_scores(g); b = ach_scores(g, True)
    order = sorted(g["hypotheses"], key=lambda h: (a[h["id"]]["inc"], -a[h["id"]]["con"]))
    sym = {"C": "fits", "I": "**against**", "N": "·"}
    out = [f"Question: **{g['question']}** Fact list fixed on {g['frozen']}. {g['note']}", "",
           "Ranking, fewest weighted facts against first (high reliability counts 1, medium 0.7, low 0.4):", "",
           "| | Explanation | From | Weighted against | Facts against | Facts that fit | Against, if possibly staged facts are dropped |",
           "|---|---|---|---|---|---|---|"]
    for h in order:
        x = a[h["id"]]; y = b[h["id"]]
        out.append(f"| {h['id']} | {h['label']} | {h['from']} | {x['inc']} | {x['ninc']} | {x['ncon']} | {y['inc']} |")
    out += ["", "The grid (\u00b7 means the fact does not bear on that explanation):", "",
            "| Fact | Kind | Reliability | " + " | ".join(h["short"] for h in g["hypotheses"]) + " |",
            "|---|---|---|" + "---|" * len(g["hypotheses"])]
    for f in g["facts"]:
        src = (f" ({f['author']}: \"{f['quote']}\")" if f.get("quote") and f.get("author") and f["author"] != "Brookings-2009"
               else (f" (Brookings, \"{f['quote']}\")" if f.get("author") == "Brookings-2009" else (f" ({f['source']})" if f.get("source") else "")))
        st = " Could be staged." if f.get("staged") else ""
        out.append(f"| {f['id']}. {f['text']}{src}{st} | {f['kind']} | {f['reliability']} | " + " | ".join(sym[f["cells"].get(h["id"], "N")] for h in g["hypotheses"]) + " |")
    out += ["", "Why each \"against\" was marked:", ""]
    for f in g["facts"]:
        for hid, why in (f.get("reasons") or {}).items():
            out.append(f"- {f['id']} against {hid}: {why}")
    diag = [f["id"] for f in g["facts"] if len(set(f["cells"].values())) > 1 and "I" in f["cells"].values()]
    out += ["", f"The facts that separate the explanations most are {', '.join(diag)}: each fits some explanations and rules against others. They are where new evidence matters most."]
    return "\n".join(out)

def check_markdown(L, c):
    F = [f for f in L["forecasts"] if f.get("check") == c["id"]]
    def line(f):
        st = f["status"] if f["status"] != "open" else "open, resolves " + (f.get("resolves") or "?")
        return f"- {f['author']}: {f['claim']} ({st})."
    out = [f"**{c['question']}** Vote on {c['vote']}; review by {c['review']}. {c['basis']}", "",
           "Forecasts on fuel and the economy:", ""]
    out += [line(f) for f in F if f.get("check_part") == "energy"]
    out += ["", "Public-data indicators (judged on public data, with the source named when marked):", ""]
    out += [line(f) for f in F if f.get("check_part") == "indicator"]
    war = [line(f) for f in F if f.get("check_part") == "war"]
    if war:
        out += ["", "Forecasts on the war after the vote:", ""] + war
    out += ["", "Also resolving on the day of the vote:", ""]
    out += [line(f) for f in F if f.get("check_part") == "election"]
    return "\n".join(out)

def write_block(name, body):
    p = doc("synthesis.md")
    s = open(p, encoding="utf-8").read()
    a, b = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
    if a not in s:
        return
    i = s.index(a) + len(a); j = s.index(b)
    new = s[:i] + "\n" + body + "\n" + s[j:]
    if new != s:
        open(p, "w", encoding="utf-8").write(new)

# ---------- main ----------

def main():
    L = json.load(open(os.path.join(HERE, "ledger.json"), encoding="utf-8"))
    for m in L.get("manual_checks", []):
        MANUAL[norm(m["quote"])] = m
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    global HYP
    HYP = L.get("hypotheses", [])
    write_hyp_md(HYP)
    global ACH_DATA
    ACH = L.get("ach", [])
    ACH_DATA = ACH
    for c in L.get("checks", []):
        write_block("check-" + c["id"], check_markdown(L, c))
    for k, g in enumerate(ACH):
        write_block("ach" if k == 0 else "ach-" + g["id"], ach_markdown(g))
    rep = ["# Ledger report", "",
           "Generated by build.py from ledger.json and sources/. Do not edit by hand.", ""]

    # quotes in the two documents
    allq = []
    for d in ("synthesis.md",):
        allq += check_md(doc(d))
    json.dump(allq, open(os.path.join(HERE, "build/quotes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    by = defaultdict(list)
    for q in allq:
        by[q["status"]].append(q)
    rep += ["## Quotations in the documents", "",
            f"{len(allq)} quotations: {len(by['verified'])} verified in the named author's own texts; "
            f"{len(by['elsewhere'])} found only in another author's texts; {len(by['not_found'])} not found in any saved text; "
            f"{len(by['term'])} short terms (one or two words) not checked. "
            f"{len([q for q in by['verified'] if q.get('note')])} of the verified ones rely on an inferred speaker or a hand check (listed in ledger.json, manual_checks).", ""]
    if by["elsewhere"]:
        rep += ["### Found under a different author (check the attribution)", ""]
        for q in by["elsewhere"]:
            rep.append(f"- {q['doc']}:{q['line']} \"{q['quote'][:90]}\" (named: {', '.join(q['candidates'][:3]) or 'none'}; found in: {', '.join(q['found_in'])})")
        rep.append("")
    if by["not_found"]:
        rep += ["### Not found in any saved text", "",
                "Usually a paraphrase inside quotation marks, a transcript spelling difference, or a source that was read online but not saved.", ""]
        for q in by["not_found"]:
            rep.append(f"- {q['doc']}:{q['line']} \"{q['quote'][:90]}\" (named: {', '.join(q['candidates'][:3]) or 'none'})")
        rep.append("")

    # counts
    probs = check_counts(doc("synthesis.md"))
    rep += ["## Counts in synthesis.md", ""]
    rep += [f"- line {p['line']}: \"{p['text']}\" says {p['says']}, lists {p['lists']}" for p in probs] or ["All \"N of the fifteen (…)\" counts match their lists."]
    rep.append("")

    # charts
    for name, entry in L["charts"].items():
        single, unquoted, failed = check_chart(entry)
        rep += [f"## Chart scores: {name}", "",
                f"{len([s for s in entry['scores'] if s['score'] is not None])} scores. "
                f"{len(single)} rest on a single checked quote; {len(unquoted)} have no checked quote in their reason "
                f"(a summary in my words). These are where more reading would pay off.", ""]
        if failed:
            rep += ["### Quotes in reasons or advice not found in the author's own texts", ""]
            rep += [f"- {f['author']}, {f['axis']}: “{f['quote'][:90]}”" + (f" (found in: {', '.join(f['found_in'])})" if f["found_in"] else "") for f in failed]
            rep.append("")
        if "vantage" in entry:
            V = entry["vantage"]; ids = {s["id"] for s in V["sides"]}
            names = {a["name"] for a in entry["authors"]}
            bad = [f"{v['author']}: unknown author" for v in V["authors"] if v["author"] not in names]
            bad += [f"{v['author']}: unknown side {k}" for v in V["authors"] for k in v["weights"] if k not in ids]
            bad += [f"{v['author']}: weights sum to {sum(v['weights'].values()):.2f}" for v in V["authors"] if abs(sum(v["weights"].values()) - 1) > 1e-6]
            bad += [f"{n}: no vantage row" for n in sorted(names - {v["author"] for v in V["authors"]})]
            rep += ["### Vantage points", "", "All authors have weights on known sides, summing to 1." if not bad else "Problems: " + "; ".join(bad), ""]
        rep += ["### Scores with no checked quote", ""]
        rep += [f"- {s['author']}, {s['axis']} = {s['score']}: {s['why'][:110]}" for s in unquoted] or ["None."]
        rep += ["", "### Scores resting on one quote", ""]
        rep += [f"- {s['author']}, {s['axis']} = {s['score']}" for s in single] or ["None."]
        rep.append("")
        tmpl = os.path.join(HERE, "templates", name + ".src.html")
        counts = quote_counts(entry, allq)
        if name == "author-axes":
            rep += ["### Checked quotations per author", "", "| Author | In synthesis.md | On the chart page | Total |", "|---|---|---|---|"]
            rep += [f"| {a} | {c['synthesis']} | {c['charts']} | {c['synthesis'] + c['charts']} |" for a, c in sorted(counts.items(), key=lambda kv: -(kv[1]['synthesis'] + kv[1]['charts']))]
            rep.append("")
        if not os.path.exists(tmpl):
            rep += [f"Template templates/{name}.src.html not found, so {name}.html was not rebuilt.", ""]
            continue
        page = render(tmpl, entry, counts, L.get("cases", []) if name == "author-axes" else None)
        open(os.path.join(HERE, "build", name + ".html"), "w", encoding="utf-8").write(page)
        open(doc(name + ".html"), "w", encoding="utf-8").write(standalone(page))

    # evidence grid quotes
    rep += ["## Evidence grid", ""]
    for g in L.get("ach", []):
        bad = [f for f in g["facts"] if f.get("quote") and f.get("author") and not (norm(f["quote"]) in MANUAL or find(f["quote"], [f["author"]]))]
        sc = ach_scores(g)
        rep.append(f"- {g['question']}: {len(g['facts'])} facts; quotes " + ("all checked." if not bad else "NOT FOUND: " + "; ".join(f['id'] for f in bad)))
        rep.append("  - weighted against: " + ", ".join(f"{k} {v['inc']}" for k, v in sorted(sc.items(), key=lambda kv: kv[1]['inc'])))
    rep.append("")

    # cases
    rep += ["## Cases", ""]
    for cs in L.get("cases", []):
        bad = [hp for hp in cs["happened"] if not (norm(hp["quote"]) in MANUAL or find(hp["quote"], [hp["author"]]))]
        rep.append(f"- {cs['title']} ({cs['date']}): {len(cs['happened'])} quotes, " + ("all checked." if not bad else "NOT FOUND: " + "; ".join(b['quote'] for b in bad)))
    rep.append("")

    # forecasts
    F = L["forecasts"]
    tally = defaultdict(lambda: defaultdict(int))
    for f in F:
        tally[f["author"]][f["status"]] += 1
    rep += ["## Forecast scorecard", "",
            "Authors' forecasts are judged by the authors' own later accounts. Indicators for the hypotheses (H…) are judged on public data, with the source named in the basis. Open forecasts list the date they resolve.", "",
            "| Author | Made | Forecast | Resolves | Status | Basis |", "|---|---|---|---|---|---|"]
    for f in sorted(F, key=lambda x: (x["status"] != "open", x["resolves"] or "9999")):
        rep.append(f"| {f['author']} | {f['made']} | {f['claim']} | {f['resolves'] or 'no date'} | {f['status']} | {f['basis']} |")
    rep += ["", "| Author | Hit | Partly | Miss | Open |", "|---|---|---|---|---|"]
    for a in sorted(tally):
        t = tally[a]
        rep.append(f"| {a} | {t['hit']} | {t['partly']} | {t['miss']} | {t['open']} |")
    rep.append("")

    open(os.path.join(HERE, "report.md"), "w", encoding="utf-8").write("\n".join(rep))
    print(f"quotes: {len(allq)} ({len(by['verified'])} verified, {len(by['elsewhere'])} elsewhere, {len(by['not_found'])} not found, {len(by['term'])} terms)")
    print(f"count problems: {len(probs)}")
    for name, entry in L["charts"].items():
        s, u, f = check_chart(entry)
        print(f"{name}: single-quote {len(s)}, unquoted {len(u)}, failed quotes {len(f)}")

if __name__ == "__main__":
    main()
