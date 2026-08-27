#!/usr/bin/env python3
"""Build the Canine Onset Atlas page from data/*.json.

Emits two files:
  dist/index.html    standalone page (doctype + head + body) for local use
  dist/artifact.html content-only fragment for publishing as a Claude Artifact
"""
import json, glob, os, math

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
DIST = os.path.join(ROOT, "dist")

GROUP_ORDER = ["Sporting", "Hound", "Working", "Terrier", "Toy", "Non-Sporting", "Herding"]

SYSTEMS = {
    "ortho":  "Orthopaedic",
    "cardio": "Cardiac",
    "resp":   "Respiratory",
    "neuro":  "Neurologic",
    "eye":    "Ophthalmic",
    "skin":   "Dermatologic",
    "endo":   "Endocrine",
    "onc":    "Neoplastic",
    "gi":     "GI / hepatic",
    "uro":    "Urogenital",
    "heme":   "Haematologic",
    "immune": "Immune",
    "metab":  "Metabolic",
    "dental": "Dental",
    "repro":  "Reproductive",
}

SEV_LABEL = {
    "mild": "Mild",
    "moderate": "Moderate",
    "serious": "Serious",
    "limiting": "Life-limiting",
}

# Growth-plate closure by size class, in years - sets the end of the puppy band.
GROWTH_END = {"toy": 0.75, "small": 1.0, "medium": 1.25, "large": 1.5, "giant": 2.0}

LIFELONG_MONTHS = 200  # onset windows reaching this far are "lifelong / from birth"


def load():
    groups = []
    for path in glob.glob(os.path.join(DATA, "*.json")):
        d = json.load(open(path, encoding="utf-8"))
        if "group" not in d or "breeds" not in d:
            continue          # reference data (ofa_stats.json etc), not a breed file
        groups.append(d)
    groups.sort(key=lambda g: GROUP_ORDER.index(g["group"]))

    breeds = []
    for g in groups:
        for b in g["breeds"]:
            b["group"] = g["group"]
            # axis maximum: cover the IQR, the mean with headroom, and every
            # non-lifelong onset window, rounded up to a whole year
            ends = [d["on"][1] / 12 for d in b["dz"] if d["on"][1] < LIFELONG_MONTHS]
            axis = max(b["life"]["p75"] + 1.5, b["life"]["mean"] * 1.3, max(ends) + 0.5)
            b["axisMax"] = max(12, math.ceil(axis))
            b["growthEnd"] = GROWTH_END[b["size"]]
            b["dz"].sort(key=lambda d: (d["on"][0], d["on"][1]))
            breeds.append(b)
    breeds.sort(key=lambda b: b["name"])
    return breeds


def stats(breeds):
    n_dz = sum(len(b["dz"]) for b in breeds)
    mean_all = sum(b["life"]["mean"] for b in breeds) / len(breeds)
    return len(breeds), n_dz, round(mean_all, 1)


CSS = r"""
:root{
  color-scheme: light;
  --bg:#f6f8f9; --surface:#ffffff; --surface-2:#eaeef2; --surface-3:#f1f4f7;
  --line:#dbe2e9; --line-strong:#c3cdd7;
  --ink:#0f161c; --ink-2:#46525e; --ink-3:#6e7c89;
  --accent:#1c5cab; --accent-2:#2a78d6; --accent-soft:#e4edfa;
  --band-puppy:rgba(28,92,171,.055);
  --band-adult:transparent;
  --band-senior:rgba(120,86,20,.055);
  --band-geri:rgba(160,60,50,.075);
  --shadow:0 1px 2px rgba(15,22,28,.06),0 8px 24px -16px rgba(15,22,28,.28);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme: dark;
    --bg:#0d1216; --surface:#141a20; --surface-2:#1b232a; --surface-3:#182027;
    --line:#27313a; --line-strong:#38454f;
    --ink:#edf2f6; --ink-2:#a6b3be; --ink-3:#77858f;
    --accent:#5598e7; --accent-2:#3987e5; --accent-soft:#152941;
    --band-puppy:rgba(85,152,231,.075);
    --band-adult:transparent;
    --band-senior:rgba(250,178,25,.06);
    --band-geri:rgba(208,59,59,.085);
    --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -16px rgba(0,0,0,.8);
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --bg:#0d1216; --surface:#141a20; --surface-2:#1b232a; --surface-3:#182027;
  --line:#27313a; --line-strong:#38454f;
  --ink:#edf2f6; --ink-2:#a6b3be; --ink-3:#77858f;
  --accent:#5598e7; --accent-2:#3987e5; --accent-soft:#152941;
  --band-puppy:rgba(85,152,231,.075);
  --band-adult:transparent;
  --band-senior:rgba(250,178,25,.06);
  --band-geri:rgba(208,59,59,.085);
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px -16px rgba(0,0,0,.8);
}
/* severity = reserved status palette, fixed in both themes, always paired with a text label */
:root{ --sev-mild:#0ca30c; --sev-moderate:#fab219; --sev-serious:#ec835a; --sev-limiting:#d03b3b; }

*{box-sizing:border-box}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:"Source Sans 3","Segoe UI",system-ui,sans-serif;
  font-size:15px; line-height:1.5; -webkit-font-smoothing:antialiased;
}
h1,h2,h3{font-family:Archivo,"Segoe UI",system-ui,sans-serif;text-wrap:balance}
.mono,.num{font-family:"IBM Plex Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums}
a{color:var(--accent)}
:focus-visible{outline:2px solid var(--accent-2);outline-offset:2px;border-radius:3px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}

/* ---------- header ---------- */
.top{border-bottom:1px solid var(--line);background:var(--surface);padding:20px clamp(16px,3vw,32px) 18px}
.top-in{max-width:1400px;margin:0 auto;display:flex;flex-wrap:wrap;gap:20px;align-items:flex-end;justify-content:space-between}
.brand h1{margin:0;font-size:clamp(21px,2.4vw,27px);font-weight:700;letter-spacing:-.02em;font-stretch:110%}
.brand p{margin:5px 0 0;color:var(--ink-2);font-size:14px;max-width:64ch}
.counts{display:flex;gap:22px;flex-wrap:wrap}
.counts div{text-align:right}
.counts b{display:block;font-family:"IBM Plex Mono",monospace;font-size:19px;font-weight:500;letter-spacing:-.02em}
.counts span{font-size:10.5px;text-transform:uppercase;letter-spacing:.09em;color:var(--ink-3)}

/* ---------- shell ---------- */
.shell{max-width:1400px;margin:0 auto;display:grid;grid-template-columns:264px minmax(0,1fr);align-items:start}
@media (max-width:900px){.shell{grid-template-columns:1fr}}

.rail{border-right:1px solid var(--line);background:var(--surface);position:sticky;top:0;max-height:100vh;display:flex;flex-direction:column}
@media (max-width:900px){.rail{position:static;max-height:none;border-right:none;border-bottom:1px solid var(--line)}}
.rail-search{padding:14px 14px 10px;border-bottom:1px solid var(--line)}
.rail-search input{width:100%;padding:8px 10px;font:inherit;font-size:14px;background:var(--surface-3);color:var(--ink);border:1px solid var(--line-strong);border-radius:6px}
.rail-search input::placeholder{color:var(--ink-3)}
.rail-list{overflow-y:auto;padding:6px 8px 20px;flex:1}
.rail-group{font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;color:var(--ink-3);padding:14px 8px 5px;font-weight:600}
.rail-b{display:flex;justify-content:space-between;align-items:baseline;gap:8px;width:100%;text-align:left;padding:6px 9px;border:0;border-radius:6px;background:transparent;color:var(--ink);font:inherit;font-size:14px;cursor:pointer}
.rail-b:hover{background:var(--surface-2)}
.rail-b[aria-current="true"]{background:var(--accent-soft);color:var(--accent);font-weight:600}
.rail-b em{font-style:normal;font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--ink-3);font-variant-numeric:tabular-nums}
.rail-b[aria-current="true"] em{color:var(--accent)}

/* ---------- panel ---------- */
.panel{padding:clamp(18px,2.6vw,30px) clamp(16px,3vw,32px) 60px;min-width:0}
.bhead{display:flex;flex-wrap:wrap;gap:18px 30px;align-items:flex-end;justify-content:space-between;margin-bottom:22px}
.bhead h2{margin:0;font-size:clamp(24px,3.1vw,34px);font-weight:700;letter-spacing:-.025em;font-stretch:110%}
.bmeta{margin:4px 0 0;color:var(--ink-2);font-size:13.5px}
.tiles{display:flex;gap:10px;flex-wrap:wrap}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:9px 14px;min-width:104px}
.tile span{display:block;font-size:10.5px;text-transform:uppercase;letter-spacing:.09em;color:var(--ink-3);margin-bottom:2px}
.tile b{font-family:"IBM Plex Mono",monospace;font-size:20px;font-weight:500;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.tile i{font-style:normal;font-size:12px;color:var(--ink-3);margin-left:3px}

/* ---------- lifespan strip ---------- */
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin-bottom:16px;box-shadow:var(--shadow)}
.card > h3{margin:0 0 3px;font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:var(--ink-3);font-weight:600}
.card > p.hint{margin:0 0 18px;font-size:12.5px;color:var(--ink-3);max-width:82ch}
.strip{position:relative;height:80px;margin:0 6px}
.strip-track{position:absolute;left:0;right:0;top:36px;height:10px;border-radius:5px;background:var(--surface-2)}
.strip-iqr{position:absolute;top:31px;height:20px;border-radius:5px;background:var(--accent-soft);border:1px solid var(--accent)}
.strip-mark{position:absolute;top:20px;height:42px;width:2px;background:var(--accent);border-radius:1px}
.strip-mark.mode{background:transparent;border-left:2px dashed var(--accent);width:0}
.strip-mark.ref{background:var(--line-strong);top:27px;height:28px}
.strip-lab{position:absolute;top:0;font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--ink);white-space:nowrap;font-variant-numeric:tabular-nums;font-weight:500}
.strip-lab.low{top:auto;bottom:0;color:var(--ink-2);font-weight:400}
.strip-ends{position:absolute;left:0;right:0;bottom:0;display:flex;justify-content:space-between;font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:var(--ink-3)}

/* ---------- burden matrix ---------- */
/* sequential single-hue ramp: step 0 is "nothing in play" and recedes to the surface */
:root{
  --s0:#f1f4f7; --s1:#dce9fa; --s2:#bdd6f5; --s3:#98bdef;
  --s4:#6fa2e8; --s5:#4885db; --s6:#2d68b5; --s7:#1c4a87; --s8:#103261;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --s0:#151b21; --s1:#17293e; --s2:#1c3757; --s3:#234873;
    --s4:#2c5b93; --s5:#3a73b4; --s6:#4f93d4; --s7:#78b0e8; --s8:#a9cbf6;
  }
}
:root[data-theme="dark"]{
  --s0:#151b21; --s1:#17293e; --s2:#1c3757; --s3:#234873;
  --s4:#2c5b93; --s5:#3a73b4; --s6:#4f93d4; --s7:#78b0e8; --s8:#a9cbf6;
}

.msec{border-bottom:1px solid var(--line);background:var(--surface)}
.msec-in{max-width:1400px;margin:0 auto;padding:clamp(18px,2.6vw,28px) clamp(16px,3vw,32px) clamp(22px,3vw,30px)}
.mhead{display:flex;flex-wrap:wrap;gap:12px 26px;align-items:flex-end;justify-content:space-between;margin-bottom:6px}
.mhead h2{margin:0;font-size:17px;font-weight:600;letter-spacing:-.01em}
.mhead p{margin:5px 0 0;font-size:12.5px;color:var(--ink-3);max-width:84ch}
.mctl{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;margin:14px 0 4px}
.mctl label{font-size:10.5px;text-transform:uppercase;letter-spacing:.09em;color:var(--ink-3);font-weight:600}
.mctl select{font:inherit;font-size:12.5px;padding:4px 8px;background:var(--surface);color:var(--ink);border:1px solid var(--line-strong);border-radius:5px}
.mscale{display:flex;align-items:center;gap:7px;margin-left:auto;font-size:11px;color:var(--ink-3);font-family:"IBM Plex Mono",monospace}
.mscale i{display:block;width:17px;height:10px}

.mscroll{overflow-x:auto;margin-top:12px}
.mgrid{min-width:760px}
.mrow{display:grid;grid-template-columns:186px minmax(0,1fr);align-items:center;height:13px}
.mrow + .mrow{margin-top:1px}
.mlab{
  display:flex;justify-content:space-between;align-items:baseline;gap:8px;
  font-size:11px;line-height:1;padding:0 9px 0 0;white-space:nowrap;overflow:hidden;
  cursor:pointer;border:0;background:transparent;color:var(--ink-2);font-family:inherit;
}
.mlab span{overflow:hidden;text-overflow:ellipsis}
.mlab em{font-style:normal;font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--ink-3);flex:none}
.mlab:hover{color:var(--ink)}
.mrow[data-cur="1"] .mlab{color:var(--accent);font-weight:600}
.mrow[data-cur="1"] .mlab em{color:var(--accent)}
.mcells{position:relative;display:grid;grid-template-columns:repeat(48,1fr);gap:1px;height:13px}
.mcells i{display:block;height:100%;border-radius:1px}
.mrow[data-cur="1"] .mcells{outline:1.5px solid var(--accent);outline-offset:1.5px;border-radius:2px}
.mlife{position:absolute;top:-1px;bottom:-1px;width:0;border-left:1.5px solid var(--ink);opacity:.45;pointer-events:none}
.c.s0{background:var(--s0)} .c.s1{background:var(--s1)} .c.s2{background:var(--s2)}
.c.s3{background:var(--s3)} .c.s4{background:var(--s4)} .c.s5{background:var(--s5)}
.c.s6{background:var(--s6)} .c.s7{background:var(--s7)} .c.s8{background:var(--s8)}

.maxis{display:grid;grid-template-columns:186px minmax(0,1fr);margin-top:7px}
.maxis-t{position:relative;height:15px}
.maxis-t span{position:absolute;top:1px;transform:translateX(-50%);font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--ink-3);font-variant-numeric:tabular-nums}
.mprof{display:grid;grid-template-columns:186px minmax(0,1fr);align-items:end;margin-bottom:8px}
.mprof-l{font-size:10px;text-transform:uppercase;letter-spacing:.09em;color:var(--ink-3);font-weight:600;padding-right:9px;text-align:right}
.mprof-b{display:grid;grid-template-columns:repeat(48,1fr);grid-template-rows:30px;gap:1px;align-items:end}
.mprof-b i{display:block;background:var(--ink-3);border-radius:1px 1px 0 0}
.mfoot{margin-top:12px;font-size:12px;color:var(--ink-3);max-width:88ch}

#mtip{
  position:fixed;z-index:60;pointer-events:none;max-width:320px;
  background:var(--surface);border:1px solid var(--line-strong);border-radius:7px;
  padding:9px 11px;font-size:12.5px;box-shadow:0 6px 22px -8px rgba(0,0,0,.45);
  opacity:0;transition:opacity .1s;
}
#mtip b{display:block;font-size:13px;margin-bottom:1px}
#mtip .age{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--ink-3);margin-bottom:6px;display:block}
#mtip ul{margin:0;padding-left:15px}
#mtip li{margin:1px 0}
#mtip .none{color:var(--ink-3)}

/* ---------- controls ---------- */
.controls{display:flex;flex-wrap:wrap;gap:14px 22px;align-items:center;margin-bottom:14px}
.scrub{display:flex;align-items:center;gap:11px;flex:1 1 300px;min-width:250px}
.scrub label{font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:var(--ink-3);font-weight:600;white-space:nowrap}
.scrub input[type=range]{flex:1;min-width:110px;accent-color:var(--accent)}
.scrub output{font-family:"IBM Plex Mono",monospace;font-size:13.5px;min-width:66px;color:var(--ink);font-variant-numeric:tabular-nums}
.btn{font:inherit;font-size:12.5px;padding:5px 11px;border-radius:6px;cursor:pointer;background:var(--surface);border:1px solid var(--line-strong);color:var(--ink-2)}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.btn[aria-pressed="true"]{background:var(--accent-soft);border-color:var(--accent);color:var(--accent);font-weight:600}
.chips{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:14px}
.chip{font:inherit;font-size:11.5px;padding:3.5px 9px;border-radius:20px;cursor:pointer;background:var(--surface);border:1px solid var(--line);color:var(--ink-3)}
.chip:hover{border-color:var(--line-strong);color:var(--ink-2)}
.chip[aria-pressed="true"]{background:var(--accent-soft);border-color:var(--accent);color:var(--accent);font-weight:600}

/* ---------- legend ---------- */
.legend{display:flex;flex-wrap:wrap;gap:5px 18px;align-items:center;font-size:12px;color:var(--ink-2);margin-bottom:6px}
.legend .k{display:inline-flex;align-items:center;gap:6px}
.swatch{width:22px;height:9px;border-radius:3px;flex:none}
.legend .bands{margin-left:auto;color:var(--ink-3);font-size:11.5px}

/* ---------- timeline ---------- */
.tl{border:1px solid var(--line);border-radius:10px;background:var(--surface);overflow:hidden;box-shadow:var(--shadow)}
.tl-scroll{overflow-x:auto}
.tl-in{min-width:660px}
.grid{display:grid;grid-template-columns:minmax(210px,270px) minmax(0,1fr)}
.axis{border-bottom:1px solid var(--line);background:var(--surface-3)}
.axis.lab{padding:8px 14px;font-size:10.5px;text-transform:uppercase;letter-spacing:.09em;color:var(--ink-3);font-weight:600;align-self:end}
.axis.track{position:relative;height:38px}
.tick{position:absolute;bottom:5px;transform:translateX(-50%);font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--ink-3);white-space:nowrap;font-variant-numeric:tabular-nums}
.bandlab{position:absolute;top:5px;font-size:9.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-3);white-space:nowrap;overflow:hidden}

.row{display:contents}
.rname{padding:7px 14px;border-bottom:1px solid var(--line);font-size:13.5px;line-height:1.32;display:flex;flex-direction:column;gap:1px;justify-content:center}
.rname .sys{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--ink-3)}
.rtrack{position:relative;border-bottom:1px solid var(--line);height:100%;min-height:40px}
.rtrack::after{content:"";position:absolute;top:0;bottom:0;left:var(--age,0%);width:1px;background:var(--accent);opacity:.5;pointer-events:none}
.bar{position:absolute;top:50%;transform:translateY(-50%);height:14px;border-radius:4px;border:0;padding:0;cursor:pointer;min-width:9px}
.bar:hover{filter:brightness(1.08);box-shadow:0 0 0 2px var(--surface),0 0 0 3px var(--ink-3)}
.bar.mild{background:var(--sev-mild)} .bar.moderate{background:var(--sev-moderate)}
.bar.serious{background:var(--sev-serious)} .bar.limiting{background:var(--sev-limiting)}
.off .rname,.off .rtrack .bar{opacity:.22}

/* detail */
.det{grid-column:1/-1;border-bottom:1px solid var(--line);background:var(--surface-3);padding:14px 18px}
.det h4{margin:0 0 8px;font-size:15px;font-weight:600;font-family:Archivo,sans-serif}
.det dl{display:grid;grid-template-columns:auto minmax(0,1fr);gap:5px 14px;margin:0;font-size:13.5px}
.det dt{color:var(--ink-3);font-size:11px;text-transform:uppercase;letter-spacing:.08em;padding-top:3px;white-space:nowrap}
.det dd{margin:0;max-width:80ch}
.pill{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11px;font-weight:600;color:#12171c}
.pill.mild{background:var(--sev-mild);color:#fff} .pill.moderate{background:var(--sev-moderate)}
.pill.serious{background:var(--sev-serious)} .pill.limiting{background:var(--sev-limiting);color:#fff}

/* table view */
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:10.5px;text-transform:uppercase;letter-spacing:.09em;color:var(--ink-3);background:var(--surface-3);position:sticky;top:0}
td.num{font-family:"IBM Plex Mono",monospace;white-space:nowrap;font-variant-numeric:tabular-nums}

.empty{padding:34px 18px;text-align:center;color:var(--ink-3);font-size:14px}
footer{max-width:1400px;margin:0 auto;padding:26px clamp(16px,3vw,32px) 46px;border-top:1px solid var(--line);color:var(--ink-3);font-size:12.5px}
footer p{margin:0 0 8px;max-width:82ch}
footer b{color:var(--ink-2);font-weight:600}
"""


BODY = r"""
<header class="top"><div class="top-in">
  <div class="brand">
    <h1>Canine Onset Atlas</h1>
    <p>Breed-associated disease plotted against the age it usually shows up, with longevity
       statistics for each breed. Drag the age marker to see what is in play for the dog in
       front of you.</p>
  </div>
  <div class="counts">
    <div><b class="num">__NB__</b><span>Breeds</span></div>
    <div><b class="num">__ND__</b><span>Conditions</span></div>
    <div><b class="num">__MA__ y</b><span>Mean, all breeds</span></div>
  </div>
</div></header>

<section class="msec"><div class="msec-in">
  <div class="mhead">
    <div>
      <h2>Disease burden across every breed and every age</h2>
      <p>One row per breed, one column per four months of life. Cell darkness is how many
         conditions are inside their onset window at that age &mdash; the whole set on one
         screen. The vertical rule on each row is that breed&rsquo;s mean lifespan.</p>
    </div>
  </div>
  <div class="mctl">
    <label for="msort">Order</label>
    <select id="msort">
      <option value="life">Mean lifespan, shortest first</option>
      <option value="cluster">Similarity of burden shape</option>
      <option value="peak">Peak burden</option>
      <option value="total">Total burden</option>
      <option value="group">AKC group</option>
      <option value="name">Breed name</option>
    </select>
    <button class="btn" id="mweight" aria-pressed="false">Weight by severity</button>
    <div class="mscale">
      <span id="mscalelo">0</span>
      <i style="background:var(--s1)"></i><i style="background:var(--s2)"></i>
      <i style="background:var(--s3)"></i><i style="background:var(--s4)"></i>
      <i style="background:var(--s5)"></i><i style="background:var(--s6)"></i>
      <i style="background:var(--s7)"></i><i style="background:var(--s8)"></i>
      <span id="mscalehi"></span>
    </div>
  </div>

  <div class="mscroll"><div class="mgrid">
    <div class="mprof">
      <div class="mprof-l">All breeds</div>
      <div class="mprof-b" id="mprof"></div>
    </div>
    <div id="mrows"></div>
    <div class="maxis"><div></div><div class="maxis-t" id="maxis"></div></div>
  </div></div>

  <p class="mfoot" id="mfoot"></p>
</div></section>

<div class="shell">
  <aside class="rail">
    <div class="rail-search">
      <input id="q" type="search" placeholder="Search breeds and conditions" aria-label="Search breeds and conditions">
    </div>
    <div class="rail-list" id="rail"></div>
  </aside>

  <main class="panel">
    <div class="bhead">
      <div>
        <h2 id="bname"></h2>
        <p class="bmeta" id="bmeta"></p>
      </div>
      <div class="tiles" id="tiles"></div>
    </div>

    <section class="card">
      <h3>Lifespan</h3>
      <p class="hint" id="lifehint"></p>
      <div class="strip" id="strip"></div>
    </section>

    <div class="controls">
      <div class="scrub">
        <label for="age">Age marker</label>
        <input id="age" type="range" min="0" max="192" step="1" value="0">
        <output id="ageout" for="age">birth</output>
      </div>
      <button class="btn" id="onlyactive" aria-pressed="false">Only what is live at this age</button>
      <button class="btn" id="viewtoggle" aria-pressed="false">Table view</button>
    </div>

    <div class="chips" id="syschips"></div>

    <div class="legend">
      <span class="k"><i class="swatch" style="background:var(--sev-mild)"></i>Mild</span>
      <span class="k"><i class="swatch" style="background:var(--sev-moderate)"></i>Moderate</span>
      <span class="k"><i class="swatch" style="background:var(--sev-serious)"></i>Serious</span>
      <span class="k"><i class="swatch" style="background:var(--sev-limiting)"></i>Life-limiting</span>
      <span class="bands">Shaded bands: puppy &middot; adult &middot; senior &middot; past mean lifespan</span>
    </div>

    <div class="tl"><div class="tl-scroll"><div class="tl-in" id="tlin"></div></div></div>
  </main>
</div>

<footer>
  <p><b>Read the bars as onset, not risk.</b> A bar marks the interval in which clinical signs
     typically first appear in an affected dog of that breed. It says nothing about how likely
     this dog is to be affected, and a condition absent from a breed&rsquo;s list is not
     excluded in that breed.</p>
  <p><b>Mean lifespan</b> is anchored to published life tables, principally McMillan et&nbsp;al.
     2024 (<i>Scientific Reports</i>, 584,734 dogs) reconciled with Kennel Club survey data.
     <b>Modal lifespan is estimated, not published</b> &mdash; age-at-death distributions are
     left-skewed, so the most common age at death sits above the mean. It is labelled
     <i>est.</i> everywhere it appears and should be quoted as an estimate.</p>
  <p>Onset windows are clinical consensus ranges drawn from Gough, Thomas &amp; O&rsquo;Neill,
     <i>Breed Predispositions to Disease in Dogs and Cats</i> (3rd&nbsp;ed.), the OFA/CHIC
     screening schedules, OMIA, the ACVO Blue Book, and breed-specific primary literature.
     Full source list and derivation notes in <code>SOURCES.md</code>. Version __VER__.</p>
</footer>
"""


JS = r"""
const D = __DATA__, SYS = __SYS__, SEVL = __SEVL__;
const REF_MEAN = __MA__;
const $ = s => document.querySelector(s);

let cur = D.find(b => b.name === "Labrador Retriever") || D[0];
let ageM = 0, onlyActive = false, tableView = false, sysOff = new Set(), query = "";
let rows = [];

const yr = m => m / 12;
const fmtAge = m => m === 0 ? "birth"
  : (m < 12 ? m + " mo" : Math.floor(m / 12) + "y" + (m % 12 ? " " + (m % 12) + "m" : ""));
const esc = s => (s || "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const pct = (y, max) => Math.max(0, Math.min(100, y / max * 100));

/* ---------- rail ---------- */
function buildRail(){
  const q = query.toLowerCase();
  const groups = {};
  for (const b of D){
    if (q && !(b.name.toLowerCase().includes(q) || b.dz.some(d => d.n.toLowerCase().includes(q)))) continue;
    (groups[b.group] = groups[b.group] || []).push(b);
  }
  const order = ["Sporting","Hound","Working","Terrier","Toy","Non-Sporting","Herding"];
  let h = "";
  for (const g of order){
    if (!groups[g]) continue;
    h += '<div class="rail-group">' + g + '</div>';
    for (const b of groups[g])
      h += '<button class="rail-b" data-b="' + esc(b.name) + '" aria-current="' + (b === cur) + '">'
         + '<span>' + esc(b.name) + '</span><em>' + b.life.mean.toFixed(1) + 'y</em></button>';
  }
  $("#rail").innerHTML = h || '<div class="empty">No breed or condition matches that search.</div>';
}

/* ---------- lifespan strip ---------- */
function labPos(x){
  if (x < 10) return "left:0;";
  if (x > 90) return "right:0;";
  return "left:" + x + "%;transform:translateX(-50%);";
}
function buildStrip(){
  const L = cur.life, max = cur.axisMax;
  const x = y => pct(y, max);
  const xm = x(L.mean), xo = x(L.mode), xr = x(REF_MEAN);
  const showRef = Math.abs(REF_MEAN - L.mean) > 0.4;
  let h = '<div class="strip-track"></div>'
        + '<div class="strip-iqr" style="left:' + x(L.p25) + '%;width:' + (x(L.p75) - x(L.p25)) + '%"></div>';
  if (showRef) h += '<div class="strip-mark ref" style="left:' + xr + '%"></div>';
  h += '<div class="strip-mark" style="left:' + xm + '%"></div>'
     + '<span class="strip-lab" style="' + labPos(xm) + '">mean ' + L.mean.toFixed(1) + 'y</span>'
     + '<div class="strip-mark mode" style="left:' + xo + '%"></div>'
     + '<span class="strip-lab low" style="' + labPos(xo) + '">mode ' + L.mode + 'y est.</span>'
     + '<div class="strip-ends"><span>birth</span><span>' + max + 'y</span></div>';
  $("#strip").innerHTML = h;
  $("#lifehint").innerHTML =
    "Shaded box is the interquartile range of age at death, " + L.p25 + "&ndash;" + L.p75
    + "y &mdash; half of dogs die inside it. Solid line is the mean, dashed line the estimated "
    + "modal age at death."
    + (showRef ? " Grey line is the all-breed mean of " + REF_MEAN + "y for comparison." : "");
}

/* ---------- life-stage bands ---------- */
function bandCss(b){
  const max = b.axisMax, p = y => (y / max * 100).toFixed(2) + "%";
  const g = b.growthEnd, s = b.life.mean * 0.75, m = b.life.mean;
  return "linear-gradient(to right,"
    + "var(--band-puppy) 0,var(--band-puppy) " + p(g) + ","
    + "var(--band-adult) " + p(g) + ",var(--band-adult) " + p(s) + ","
    + "var(--band-senior) " + p(s) + ",var(--band-senior) " + p(m) + ","
    + "var(--band-geri) " + p(m) + ",var(--band-geri) 100%)";
}

/* ---------- timeline ---------- */
function isLive(d){ return ageM >= d.on[0] && ageM <= d.on[1]; }
function visible(d){
  if (sysOff.has(d.sys)) return false;
  if (onlyActive && !isLive(d)) return false;
  if (query){
    const q = query.toLowerCase();
    if (!cur.name.toLowerCase().includes(q) && !d.n.toLowerCase().includes(q)) return false;
  }
  return true;
}

function buildTL(){
  const b = cur, max = b.axisMax, bg = bandCss(b);
  rows = b.dz.filter(visible);
  if (tableView){ buildTable(); return; }
  if (!rows.length){ $("#tlin").innerHTML = '<div class="empty">Nothing matches the current filters.</div>'; return; }

  const step = max > 12 ? 2 : 1;
  let ticks = '<span class="tick" style="left:0;transform:none">birth</span>';
  for (let y = step; y <= max; y += step) ticks += '<span class="tick" style="left:' + pct(y, max) + '%">' + y + 'y</span>';

  const g = b.growthEnd, s = b.life.mean * 0.75, m = b.life.mean;
  const bl = (lab, a, z) => '<span class="bandlab" style="left:' + pct(a, max) + '%;max-width:'
    + (pct(z, max) - pct(a, max)) + '%">' + lab + '</span>';
  const bands = bl("puppy", 0, g) + bl("adult", g, s) + bl("senior", s, m) + bl("past mean", m, max);

  let h = '<div class="grid"><div class="axis lab">Condition</div>'
        + '<div class="axis track" style="background:' + bg + '">' + bands + ticks + '</div>';
  rows.forEach((d, i) => {
    const lifelong = d.on[1] >= 200;
    const a = pct(yr(d.on[0]), max), z = lifelong ? 100 : pct(yr(d.on[1]), max);
    const w = Math.max(z - a, 1.4);
    const dim = (ageM > 0 && !isLive(d)) ? " off" : "";
    const span = lifelong ? "present lifelong" : fmtAge(d.on[0]) + " to " + fmtAge(d.on[1]);
    h += '<div class="row' + dim + '">'
       + '<div class="rname"><span>' + esc(d.n) + '</span><span class="sys">' + SYS[d.sys]
       + (lifelong ? " &middot; lifelong" : "") + '</span></div>'
       + '<div class="rtrack" style="background:' + bg + '">'
       + '<button class="bar ' + d.sev + '" style="left:' + a + '%;width:' + w + '%" data-i="' + i + '"'
       + ' aria-label="' + esc(d.n) + ': ' + SEVL[d.sev] + ', onset ' + span + '"'
       + ' title="' + esc(d.n) + ' - ' + SEVL[d.sev] + ' - ' + span + '"></button>'
       + '</div></div>';
  });
  $("#tlin").innerHTML = h + '</div>';
}

function buildTable(){
  if (!rows.length){ $("#tlin").innerHTML = '<div class="empty">Nothing matches the current filters.</div>'; return; }
  let h = '<table><thead><tr><th>Condition</th><th>System</th><th>Onset</th><th>Impact</th>'
        + '<th>Inheritance</th><th>Test</th></tr></thead><tbody>';
  for (const d of rows){
    const ll = d.on[1] >= 200;
    h += '<tr><td>' + esc(d.n)
       + (d.note ? '<br><span style="color:var(--ink-3);font-size:12.5px">' + esc(d.note) + '</span>' : "")
       + '</td><td>' + SYS[d.sys] + '</td>'
       + '<td class="num">' + (ll ? "lifelong" : fmtAge(d.on[0]) + " &ndash; " + fmtAge(d.on[1])) + '</td>'
       + '<td><span class="pill ' + d.sev + '">' + SEVL[d.sev] + '</span></td>'
       + '<td>' + esc(d.inh) + '</td><td>' + esc(d.test) + '</td></tr>';
  }
  $("#tlin").innerHTML = h + '</tbody></table>';
}

/* OFA figures are screening results from voluntarily submitted breeding stock,
   not breed prevalence, so the metric and the caveat always travel with them. */
function ofaRow(o){
  const carrier = (o.carrier !== undefined)
    ? ' &middot; ' + o.carrier + '% carrier' : "";
  const pooled = o.pooled
    ? ' OFA does not separate this breed&rsquo;s varieties, so the figure is pooled across them.' : "";
  return '<dt>OFA</dt><dd><b class="mono">' + o.pct + '%</b> '
    + esc(o.metric.toLowerCase().replace(/ %$/, "")) + carrier
    + ' <span class="mono" style="color:var(--ink-3)">n=' + o.n.toLocaleString() + '</span>'
    + '<div style="color:var(--ink-3);font-size:12px;margin-top:3px">'
    + 'Screened dogs submitted to OFA, overwhelmingly breeding candidates &mdash; not breed '
    + 'prevalence. Phenotypic screens read low because affected animals often go unsubmitted; '
    + 'DNA results describe a population actively selected against the mutation.' + pooled
    + '</div></dd>';
}

function openDetail(i){
  const d = rows[i];
  document.querySelectorAll(".det").forEach(e => e.remove());
  const rowEls = $("#tlin").querySelectorAll(".row");
  if (!rowEls[i]) return;
  const ll = d.on[1] >= 200;
  const div = document.createElement("div");
  div.className = "det";
  div.innerHTML = '<h4>' + esc(d.n) + '</h4><dl>'
    + '<dt>Onset</dt><dd class="mono">' + (ll ? "present lifelong" : fmtAge(d.on[0]) + " to " + fmtAge(d.on[1])) + '</dd>'
    + '<dt>System</dt><dd>' + SYS[d.sys] + '</dd>'
    + '<dt>Impact</dt><dd><span class="pill ' + d.sev + '">' + SEVL[d.sev] + '</span></dd>'
    + '<dt>Inheritance</dt><dd>' + esc(d.inh) + '</dd>'
    + (d.test ? '<dt>Test</dt><dd>' + esc(d.test) + '</dd>' : "")
    + (d.note ? '<dt>Note</dt><dd>' + esc(d.note) + '</dd>' : "")
    + (d.ofa ? ofaRow(d.ofa) : "")
    + '</dl>';
  rowEls[i].querySelector(".rtrack").after(div);
}

/* ---------- header + chips ---------- */
function buildHead(){
  const b = cur, L = b.life;
  $("#bname").textContent = b.name;
  $("#bmeta").textContent = b.group + " group · " + b.size + " · " + b.dz.length + " conditions tracked";
  $("#tiles").innerHTML =
      '<div class="tile"><span>Mean lifespan</span><b>' + L.mean.toFixed(1) + '<i>y</i></b></div>'
    + '<div class="tile"><span>Modal lifespan</span><b>' + L.mode + '<i>y est.</i></b></div>'
    + '<div class="tile"><span>Typical range</span><b>' + L.p25 + '–' + L.p75 + '<i>y</i></b></div>';
  const used = [];
  for (const d of b.dz) if (used.indexOf(d.sys) === -1) used.push(d.sys);
  $("#syschips").innerHTML = used.map(s =>
    '<button class="chip" data-s="' + s + '" aria-pressed="' + !sysOff.has(s) + '">' + SYS[s] + '</button>').join("");
  const maxM = b.axisMax * 12;
  const el = $("#age");
  el.max = maxM;
  if (ageM > maxM) ageM = maxM;
  el.value = ageM;
  $("#ageout").textContent = fmtAge(ageM);
  document.documentElement.style.setProperty("--age", (ageM / maxM * 100) + "%");
}

function render(){ buildRail(); buildHead(); buildStrip(); buildTL(); }

/* ---------- events ---------- */
$("#rail").addEventListener("click", e => {
  const btn = e.target.closest(".rail-b"); if (!btn) return;
  cur = D.find(b => b.name === btn.dataset.b);
  sysOff.clear();
  render();
  markMatrix();
});
$("#q").addEventListener("input", e => {
  query = e.target.value.trim();
  const q = query.toLowerCase();
  if (q){
    const hit = D.find(b => b.name.toLowerCase().includes(q));
    if (hit) cur = hit;
  }
  render();
});
$("#age").addEventListener("input", e => {
  ageM = +e.target.value;
  $("#ageout").textContent = fmtAge(ageM);
  document.documentElement.style.setProperty("--age", (ageM / +e.target.max * 100) + "%");
  buildTL();
});
$("#onlyactive").addEventListener("click", e => {
  onlyActive = !onlyActive;
  e.currentTarget.setAttribute("aria-pressed", onlyActive);
  buildTL();
});
$("#viewtoggle").addEventListener("click", e => {
  tableView = !tableView;
  e.currentTarget.setAttribute("aria-pressed", tableView);
  e.currentTarget.textContent = tableView ? "Timeline view" : "Table view";
  buildTL();
});
$("#syschips").addEventListener("click", e => {
  const c = e.target.closest(".chip"); if (!c) return;
  const s = c.dataset.s;
  if (sysOff.has(s)) sysOff.delete(s); else sysOff.add(s);
  c.setAttribute("aria-pressed", !sysOff.has(s));
  buildTL();
});
$("#tlin").addEventListener("click", e => {
  const bar = e.target.closest(".bar"); if (!bar) return;
  openDetail(+bar.dataset.i);
});

render();

/* ================= BURDEN MATRIX ================= */
const BINS = 48, BIN_M = 4, MAT_MAX_M = BINS * BIN_M;   // 4-month bins across 0-16y
const SEV_W = { mild: 1, moderate: 2, serious: 3, limiting: 4 };
let mWeighted = false, mSort = "life", mOrder = null, mClusterOrder = null;

function burdenVec(b, weighted){
  const v = new Array(BINS).fill(0);
  for (const d of b.dz){
    const w = weighted ? SEV_W[d.sev] : 1;
    const lo = Math.max(0, Math.floor(d.on[0] / BIN_M));
    const hi = Math.min(BINS - 1, Math.floor(Math.min(d.on[1], MAT_MAX_M - 1) / BIN_M));
    for (let i = lo; i <= hi; i++) v[i] += w;
  }
  return v;
}
function conditionsAt(b, bin){
  const lo = bin * BIN_M, hi = lo + BIN_M - 1;
  return b.dz.filter(d => d.on[0] <= hi && d.on[1] >= lo);
}

/* average-linkage agglomerative clustering via Lance-Williams update.
   Vectors are normalised to sum 1 first, so breeds cluster on the SHAPE of their
   burden across life rather than on how many conditions they happen to have. */
function clusterOrder(){
  if (mClusterOrder) return mClusterOrder;
  const n = D.length;
  const norm = D.map(b => {
    const v = burdenVec(b, true), s = v.reduce((a, x) => a + x, 0) || 1;
    return v.map(x => x / s);
  });
  const CD = [];
  for (let i = 0; i < n; i++){
    CD[i] = [];
    for (let j = 0; j < n; j++){
      let t = 0;
      for (let k = 0; k < BINS; k++){ const d = norm[i][k] - norm[j][k]; t += d * d; }
      CD[i][j] = Math.sqrt(t);
    }
  }
  const alive = D.map((_, i) => i);
  const members = D.map((_, i) => [i]);
  while (alive.length > 1){
    let bi = 0, bj = 1, best = Infinity;
    for (let a = 0; a < alive.length; a++)
      for (let c = a + 1; c < alive.length; c++){
        const v = CD[alive[a]][alive[c]];
        if (v < best){ best = v; bi = a; bj = c; }
      }
    const I = alive[bi], J = alive[bj];
    const nI = members[I].length, nJ = members[J].length;
    for (const k of alive){
      if (k === I || k === J) continue;
      const d = (nI * CD[I][k] + nJ * CD[J][k]) / (nI + nJ);
      CD[I][k] = d; CD[k][I] = d;
    }
    members[I] = members[I].concat(members[J]);
    alive.splice(bj, 1);
  }
  mClusterOrder = members[alive[0]].map(i => D[i].name);
  return mClusterOrder;
}

function matrixOrder(){
  const withV = D.map(b => {
    const v = burdenVec(b, mWeighted);
    return { b: b, peak: Math.max.apply(null, v), total: v.reduce((a, x) => a + x, 0) };
  });
  if (mSort === "cluster"){
    const ord = clusterOrder();
    return ord.map(n => D.find(b => b.name === n));
  }
  const GRP = ["Sporting","Hound","Working","Terrier","Toy","Non-Sporting","Herding"];
  const cmp = {
    life:  (x, y) => x.b.life.mean - y.b.life.mean || x.b.name.localeCompare(y.b.name),
    peak:  (x, y) => y.peak - x.peak || x.b.name.localeCompare(y.b.name),
    total: (x, y) => y.total - x.total || x.b.name.localeCompare(y.b.name),
    name:  (x, y) => x.b.name.localeCompare(y.b.name),
    group: (x, y) => GRP.indexOf(x.b.group) - GRP.indexOf(y.b.group) || x.b.name.localeCompare(y.b.name),
  }[mSort];
  return withV.sort(cmp).map(x => x.b);
}

function buildMatrix(){
  const order = matrixOrder();
  const vecs = new Map();
  let gmax = 0;
  for (const b of D){ const v = burdenVec(b, mWeighted); vecs.set(b.name, v); for (const x of v) if (x > gmax) gmax = x; }
  const step = v => v <= 0 ? 0 : Math.max(1, Math.min(8, Math.ceil(v / gmax * 8)));

  let h = "";
  for (const b of order){
    const v = vecs.get(b.name);
    let cells = "";
    for (let i = 0; i < BINS; i++) cells += '<i class="c s' + step(v[i]) + '" data-i="' + i + '"></i>';
    const lifeX = Math.min(100, b.life.mean / (MAT_MAX_M / 12) * 100);
    const pk = Math.max.apply(null, v);
    h += '<div class="mrow" data-b="' + esc(b.name) + '" data-cur="' + (b === cur ? 1 : 0) + '">'
       + '<button class="mlab" type="button"><span>' + esc(b.name) + '</span><em>'
       + b.life.mean.toFixed(1) + '</em></button>'
       + '<div class="mcells" aria-label="' + esc(b.name) + ': peak burden ' + pk
       + ' conditions, mean lifespan ' + b.life.mean.toFixed(1) + ' years">' + cells
       + '<span class="mlife" style="left:' + lifeX + '%"></span></div></div>';
  }
  $("#mrows").innerHTML = h;

  // population profile: total burden across all breeds at each age
  const prof = new Array(BINS).fill(0);
  for (const b of D){ const v = vecs.get(b.name); for (let i = 0; i < BINS; i++) prof[i] += v[i]; }
  const pmax = Math.max.apply(null, prof) || 1;
  let ph = "";
  for (let i = 0; i < BINS; i++) ph += '<i style="height:' + Math.max(2, Math.round(prof[i] / pmax * 30)) + 'px"></i>';
  $("#mprof").innerHTML = ph;

  let ax = '<span style="left:0;transform:none">birth</span>';
  for (let y = 2; y <= 16; y += 2) ax += '<span style="left:' + (y / 16 * 100) + '%">' + y + 'y</span>';
  $("#maxis").innerHTML = ax;

  $("#mscalehi").textContent = gmax;
  const peakBin = prof.indexOf(Math.max.apply(null, prof));
  $("#mfoot").innerHTML =
    "Two waves are visible in almost every row: developmental and congenital disease in the "
    + "first two years, then a second rise as neoplastic and degenerative disease take over. "
    + "Across all " + D.length + " breeds the busiest window is "
    + fmtAge(peakBin * BIN_M) + "&ndash;" + fmtAge(peakBin * BIN_M + BIN_M) + ". "
    + (mWeighted ? "Cells are weighted by clinical impact (mild 1 to life-limiting 4)."
                 : "Cells count conditions, unweighted.")
    + " Ordering by similarity of burden shape groups breeds with comparable disease "
    + "architecture, regardless of how many conditions each carries.";
}

function markMatrix(){
  const rows = $("#mrows").querySelectorAll(".mrow");
  rows.forEach(r => r.dataset.cur = (r.dataset.b === cur.name) ? "1" : "0");
}

/* tooltip */
const mtip = document.createElement("div");
mtip.id = "mtip";
document.body.appendChild(mtip);
function hideTip(){ mtip.style.opacity = "0"; }
$("#mrows").addEventListener("mousemove", e => {
  const cell = e.target.closest(".c");
  if (!cell){ hideTip(); return; }
  const row = cell.closest(".mrow");
  const b = D.find(x => x.name === row.dataset.b);
  const bin = +cell.dataset.i;
  const list = conditionsAt(b, bin);
  mtip.innerHTML = "<b>" + esc(b.name) + "</b><span class='age'>"
    + fmtAge(bin * BIN_M) + " to " + fmtAge(bin * BIN_M + BIN_M) + "</span>"
    + (list.length
        ? "<ul>" + list.slice(0, 8).map(d => "<li>" + esc(d.n) + " <span style='color:var(--ink-3)'>"
            + SEVL[d.sev].toLowerCase() + "</span></li>").join("")
          + (list.length > 8 ? "<li class='none'>and " + (list.length - 8) + " more</li>" : "")
          + "</ul>"
        : "<span class='none'>Nothing in its onset window</span>");
  mtip.style.opacity = "1";
  const pad = 14;
  let x = e.clientX + pad, y = e.clientY + pad;
  const r = mtip.getBoundingClientRect();
  if (x + r.width > window.innerWidth - 8) x = e.clientX - r.width - pad;
  if (y + r.height > window.innerHeight - 8) y = e.clientY - r.height - pad;
  mtip.style.left = x + "px"; mtip.style.top = Math.max(8, y) + "px";
});
$("#mrows").addEventListener("mouseleave", hideTip);
$("#mrows").addEventListener("click", e => {
  const row = e.target.closest(".mrow"); if (!row) return;
  const b = D.find(x => x.name === row.dataset.b);
  if (!b || b === cur) return;
  cur = b; sysOff.clear();
  render();
  markMatrix();
  const sh = document.querySelector(".shell");
  if (sh && sh.scrollIntoView) sh.scrollIntoView({ block: "start", behavior: "smooth" });
});
$("#msort").addEventListener("change", e => { mSort = e.target.value; buildMatrix(); });
$("#mweight").addEventListener("click", e => {
  mWeighted = !mWeighted;
  e.currentTarget.setAttribute("aria-pressed", mWeighted);
  buildMatrix();
});

buildMatrix();
"""


def build():
    breeds = load()
    nb, nd, mean_all = stats(breeds)
    vpath = os.path.join(ROOT, "VERSION")
    ver = open(vpath).read().strip() if os.path.exists(vpath) else "0.1.0"

    body = (BODY.replace("__NB__", str(nb)).replace("__ND__", str(nd))
                .replace("__MA__", str(mean_all)).replace("__VER__", "v" + ver))
    js = (JS.replace("__DATA__", json.dumps(breeds, separators=(",", ":"), ensure_ascii=False))
            .replace("__SYS__", json.dumps(SYSTEMS))
            .replace("__SEVL__", json.dumps(SEV_LABEL))
            .replace("__MA__", str(mean_all)))

    head = ('<title>Canine Onset Atlas</title>\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
            'family=Archivo:wght@600;700&family=IBM+Plex+Mono:wght@400;500&'
            'family=Source+Sans+3:wght@400;600&display=swap">\n'
            "<style>" + CSS + "</style>\n")

    fragment = head + body + "\n<script>\n" + js + "\n</script>\n"
    standalone = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                  '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
                  + head + "</head>\n<body>\n" + body
                  + "\n<script>\n" + js + "\n</script>\n</body>\n</html>\n")

    os.makedirs(DIST, exist_ok=True)
    open(os.path.join(DIST, "index.html"), "w", encoding="utf-8").write(standalone)
    open(os.path.join(DIST, "artifact.html"), "w", encoding="utf-8").write(fragment)
    print("built %d breeds / %d conditions / mean %sy -> dist/index.html, dist/artifact.html"
          % (nb, nd, mean_all))


if __name__ == "__main__":
    build()
