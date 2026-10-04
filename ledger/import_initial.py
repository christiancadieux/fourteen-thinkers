"""One-off import: pull chart data out of the two chart templates into ledger.json,
and add the hand-entered forecast list. After this, ledger.json is the master and
build.py writes the chart data back into the pages."""
import json, re, subprocess, os, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

DOM_STUB = """
class N{constructor(t){this.children=[];this.attrs={};this.style={};this.classList={add(){},remove(){},toggle(){}}}
appendChild(c){this.children.push(c);return c} setAttribute(k,v){this.attrs[k]=v} addEventListener(){}
set textContent(v){this.children=[]} get textContent(){return ''} append(){} querySelectorAll(){return []}}
global.document={createElement:t=>new N(t),createElementNS:(n,t)=>new N(t),createTextNode:t=>({}),getElementById:()=>new N('div'),body:new N('body'),documentElement:new N('html'),querySelector:()=>null,querySelectorAll:()=>[]};
global.window={addEventListener(){},matchMedia:()=>({matches:false,addEventListener(){}})};
global.localStorage={getItem(){return null},setItem(){}};
"""

def chart_data(path):
    html = open(path, encoding="utf-8").read()
    js = re.search(r"<script>(.*)</script>", html, re.S).group(1)
    js = js.replace("\nstart();", "\n")
    js += "\nconsole.log(JSON.stringify({authors: AUTHORS, axes: AXES.map(a => ({id: a.id, title: a.title, low: a.low, high: a.high, s: a.s, why: a.why})), advice: ADVICE}));"
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(DOM_STUB + js)
        name = f.name
    out = subprocess.run(["node", name], capture_output=True, text=True, check=True).stdout
    os.unlink(name)
    return json.loads(out)

def charts_entry(path):
    d = chart_data(path)
    names = [a["name"] for a in d["authors"]]
    scores = []
    for ax in d["axes"]:
        for i, n in enumerate(names):
            scores.append({"axis": ax["id"], "author": n, "score": ax["s"][i], "why": ax["why"][i]})
    advice = []
    for ad in d["advice"]:
        for w in ad["who"]:
            advice.append({"advice": ad["label"], "author": names[w["i"]], "quote": w["q"]})
    return {"authors": d["authors"],
            "axes": [{k: ax[k] for k in ("id", "title", "low", "high")} for ax in d["axes"]],
            "scores": scores, "advice": advice}

# Forecasts: dated predictions as stated in synthesis.md / hidden-layer.md.
# status: open | hit | miss | partly, judged only by the authors' own later accounts.
F = [
 ("Wilkerson", "2024-11", "A war with Iran that the US cannot walk away from, because of Netanyahu", "I'm worried that we might be walking into a war that we cannot walk away from because of Netanyahu.", "2026-02-28", "hit", "The US-Israeli attack began 28 Feb 2026 and was still going in September (Wilkerson, Crooke, Hudson)."),
 ("Diesen", "2025-03", "A war on Iran would be a disaster and Iran would hit back hard", "Iran would hit back in a massive way", "2026-03", "hit", "Iran struck Gulf bases and closed Hormuz (Wolff, Hudson, Martenson)."),
 ("Webb", "2024-07", "Trump would use dollar stablecoins to entrench dollar dominance", "programmable, surveillable stablecoins to expand and entrench dollar dominance", "2026", "hit", "Werner and Hudson describe the stablecoin push as having happened."),
 ("Dixon", "2026-01", "Peace in the Middle East was coming; Iran 'already regime changed'", "already been regime changed", "2026-02-28", "miss", "The war began seven weeks later."),
 ("Crooke", "2026-03", "A long war rather than a quick one", "A long war is more likely than a quick war.", "2026-09", "hit", "The war was still on in September 2026 (Crooke, Wilkerson, Wolff)."),
 ("Martenson", "2026-02-27", "War alert the day before the attack", "war alert", "2026-02-28", "hit", "The attack came the next day."),
 ("Dolan", "2026-02-28", "The war will not unfold the way its architects expect", "I doubt it will unfold the way its architects expect.", "2026-09", "hit", "By April he and others describe a failed campaign."),
 ("Martenson", "2026-07", "Critical fuel shortages within two to three months if prices stay low", "", "2026-10", "open", "Wolff (Oct 2026) describes a diesel shortage squeezing farmers; check against Martenson's own later account."),
 ("Martenson", "2026-09", "Oil pushed down before the midterms; bond market 'ugly' in six to twelve months", "ugly", "2027-09", "open", ""),
 ("Hudson", "2026", "A world depression no later than autumn 2026", "no later than this autumn", "2026-12", "open", ""),
 ("Hudson", "2026", "Trump holds fuel prices down until the November vote and declares an emergency after it", "", "2026-11", "open", ""),
 ("Henningsen", "2026-08", "Trump will not concede on Iran before his term ends", "", "2029-01", "open", ""),
 ("Henningsen", "2026-09", "Impeachment hearings likely if the House changes hands; no lasting Ukraine settlement", "", "2027", "open", ""),
 ("Wilkerson", "2026-05", "'60/40 we don't have elections'", "60/40 we don't have elections", "2026-11-03", "open", "Resolves with the midterms."),
 ("Wilkerson", "2026-09", "A 50-50 chance that Saudi Arabia disappears as a state", "50-50 chance", "", "open", "No date given."),
 ("Crooke", "2026-07", "The US will ultimately have to capitulate", "The U.S. ultimately will have to capitulate", "", "open", "No date given."),
 ("Wolff", "2026-03", "Trump's only options: interfere in the election or lose", "interfere in the election or lose", "2026-11-03", "open", "Resolves with the midterms."),
 ("Wolff", "2026-10", "Trump will 'lose farm votes big time'", "lose farm votes big time", "2026-11-03", "open", "Resolves with the midterms."),
 ("Wolff", "2025-01", "Trump's ceasefire pressure ends Netanyahu's career", "Bye-bye, Mr. Netanyahu", "2026", "miss", "Thirteen months later they went to war together."),
 ("Noh", "2024", "War with China is 'not if, but when'", "not if, but when", "", "open", "No date given."),
 ("Greer", "1995-08", "A public extraterrestrial event within 2-10 years", "within the next 2-10 years or sooner", "2005", "miss", "Dolan (Sept 2026): no acknowledgment yet."),
 ("Greer", "2023-07", "A staged alien attack 'imminently'", "preparing to execute this plan imminently", "2024", "miss", "Not reported by any author here."),
 ("Greer", "2025", "Disclosure 'in the next year or two'", "disclosure is going to happen in the next year or two", "2027", "open", "Dolan (Sept 2026) describes managed preparations, no acknowledgment."),
 ("Doty", "2019", "Disclosure will come 'piecemeal'", "disclosure's going to happen, piecemeal", "", "partly", "Dolan (2026) describes document tranches and a reporting system, no acknowledgment."),
]

ledger = {
    "version": 1,
    "note": "Master data for synthesis.md checks and the chart pages. Edit here, then run build.py.",
    "charts": {
        "author-axes": charts_entry(os.path.join(HERE, "templates/author-axes.src.html")),
        "hidden-axes": charts_entry(os.path.join(HERE, "templates/hidden-axes.src.html")),
    },
    "forecasts": [dict(zip(("author", "made", "claim", "quote", "resolves", "status", "basis"), f)) for f in F],
}
json.dump(ledger, open(os.path.join(HERE, "ledger.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("authors", len(ledger["charts"]["author-axes"]["authors"]), "scores", len(ledger["charts"]["author-axes"]["scores"]),
      "advice", len(ledger["charts"]["author-axes"]["advice"]), "forecasts", len(F))
