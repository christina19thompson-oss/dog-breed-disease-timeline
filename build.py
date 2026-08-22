#!/usr/bin/env python3
"""Build the Canine Onset Atlas page from data/*.json.

Emits:
  dist/index.html    standalone page (doctype + head + body)
  dist/artifact.html content-only fragment for publishing as a Claude Artifact
"""
import json, glob, os, math

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
DIST = os.path.join(ROOT, "dist")

GROUP_ORDER = ["Sporting", "Hound", "Working", "Terrier", "Toy", "Non-Sporting", "Herding"]

SYSTEMS = {
    "ortho": "Orthopaedic", "cardio": "Cardiac", "resp": "Respiratory",
    "neuro": "Neurologic", "eye": "Ophthalmic", "skin": "Dermatologic",
    "endo": "Endocrine", "onc": "Neoplastic", "gi": "GI / hepatic",
    "uro": "Urogenital", "heme": "Haematologic", "immune": "Immune",
    "metab": "Metabolic", "dental": "Dental", "repro": "Reproductive",
}

SEV_LABEL = {"mild": "Mild", "moderate": "Moderate",
             "serious": "Serious", "limiting": "Life-limiting"}

# Growth-plate closure by size class, in years - sets the end of the puppy band.
GROWTH_END = {"toy": 0.75, "small": 1.0, "medium": 1.25, "large": 1.5, "giant": 2.0}

LIFELONG_MONTHS = 200


def load():
    groups = []
    for path in glob.glob(os.path.join(DATA, "*.json")):
        groups.append(json.load(open(path, encoding="utf-8")))
    groups.sort(key=lambda g: GROUP_ORDER.index(g["group"]))

    breeds = []
    for g in groups:
        for b in g["breeds"]:
            b["group"] = g["group"]
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
    lo = min(breeds, key=lambda b: b["life"]["mean"])
    hi = max(breeds, key=lambda b: b["life"]["mean"])
    return len(breeds), n_dz, round(mean_all, 1), lo, hi


CSS = r"""
:root{
  color-scheme: light;
  --bg:#f7f8f9; --surface:#ffffff; --surface-2:#edeff1; --surface-3:#f2f4f5;
  --line:#e0e3e6; --line-2:#c8ced3;
  --ink:#0a0d10; --ink-2:#4a555f; --ink-3:#8a959e; --ink-4:#b4bcc3;
  --sel:#1b4f8c; --sel-soft:#e6edf6;
  --band-puppy:rgba(10,13,16,.045);
  --band-adult:transparent;
  --band-senior:rgba(10,13,16,.032);
  --band-geri:rgba(208,59,59,.075);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme: dark;
    --bg:#0a0d10; --surface:#111619; --surface-2:#1a2025; --surface-3:#161c20;
    --line:#232b31; --line-2:#39434b;
    --ink:#f0f3f5; --ink-2:#a3aeb7; --ink-3:#737e87; --ink-4:#4d565e;
    --sel:#6ba5ec; --sel-soft:#14263c;
    --band-puppy:rgba(255,255,255,.05);
    --band-adult:transparent;
    --band-senior:rgba(255,255,255,.032);
    --band-geri:rgba(208,59,59,.10);
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --bg:#0a0d10; --surface:#111619; --surface-2:#1a2025; --surface-3:#161c20;
  --line:#232b31; --line-2:#39434b;
  --ink:#f0f3f5; --ink-2:#a3aeb7; --ink-3:#737e87; --ink-4:#4d565e;
  --sel:#6ba5ec; --sel-soft:#14263c;
  --band-puppy:rgba(255,255,255,.05);
  --band-adult:transparent;
  --band-senior:rgba(255,255,255,.032);
  --band-geri:rgba(208,59,59,.10);
}
/* severity: reserved status palette, fixed in both themes, always paired with a label */
:root{ --sev-mild:#0ca30c; --sev-moderate:#fab219; --sev-serious:#ec835a; --sev-limiting:#d03b3b; }

*{box-sizing:border-box}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:"Source Sans 3","Segoe UI",system-ui,sans-serif;
  font-size:15.5px; line-height:1.55; -webkit-font-smoothing:antialiased;
}
.disp{font-family:"Big Shoulders Display","Archivo Narrow",Impact,sans-serif;font-weight:800;line-height:.88;letter-spacing:.005em}
.mono,.num{font-family:"IBM Plex Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums}
:focus-visible{outline:2px solid var(--sel);outline-offset:3px;border-radius:2px}
.wrap{max-width:1180px;margin:0 auto;padding:0 clamp(18px,4vw,44px)}
.eyebrow{font-size:11px;text-transform:uppercase;letter-spacing:.22em;color:var(--ink-3);font-weight:600}

/* ============ HERO ============ */
.hero{padding:clamp(48px,9vw,110px) 0 clamp(30px,4vw,52px);border-bottom:1px solid var(--line)}
.hero h1{
  font-family:"Big Shoulders Display","Archivo Narrow",Impact,sans-serif;
  font-weight:800; font-size:clamp(58px,13.5vw,178px); line-height:.84;
  margin:16px 0 0; letter-spacing:-.005em; text-transform:uppercase; text-wrap:balance;
}
.hero .lede{margin:26px 0 0;max-width:56ch;font-size:clamp(16px,1.5vw,19px);color:var(--ink-2)}
.hero .lede b{color:var(--ink);font-weight:600}
.figs{display:flex;flex-wrap:wrap;gap:clamp(26px,5vw,64px);margin-top:clamp(34px,5vw,58px)}
.fig b{
  display:block;font-family:"Big Shoulders Display",Impact,sans-serif;font-weight:800;
  font-size:clamp(42px,6vw,74px);line-height:.85;font-variant-numeric:tabular-nums;
}
.fig span{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.16em;color:var(--ink-3);margin-top:8px;font-weight:600}

/* ============ SPECTRUM ============ */
.spectrum{padding:clamp(44px,6vw,84px) 0 clamp(40px,5vw,70px);border-bottom:1px solid var(--line)}
.sec-head{display:flex;flex-wrap:wrap;gap:14px 40px;align-items:flex-end;justify-content:space-between;margin-bottom:clamp(24px,3vw,38px)}
.sec-head h2{
  font-family:"Big Shoulders Display",Impact,sans-serif;font-weight:800;
  font-size:clamp(30px,4.4vw,58px);line-height:.9;margin:8px 0 0;text-transform:uppercase;
}
.sec-head p{margin:8px 0 0;max-width:50ch;font-size:14px;color:var(--ink-2)}

.spec{position:relative}
.spec-axis{position:relative;height:20px;margin-bottom:10px}
.spec-axis::after{content:"";position:absolute;left:0;bottom:0;width:72%;border-bottom:1px solid var(--line)}
.spec-axis span{position:absolute;bottom:4px;transform:translateX(-50%);font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:var(--ink-3);font-variant-numeric:tabular-nums}
.spec-rows{display:flex;flex-direction:column;gap:3px}
.srow{position:relative;height:9px;border:0;padding:0;background:transparent;cursor:pointer;display:block;width:100%}
.sbar{
  position:absolute;left:0;top:2px;height:6px;border-radius:0 2.5px 2.5px 0;background:var(--ink-4);
  width:var(--w); transform-origin:left center;
}
.srow:hover .sbar{background:var(--ink-2)}
.srow[data-cur="1"] .sbar{background:var(--sel);height:9px;top:0;border-radius:0 3.5px 3.5px 0}
.slab{
  position:absolute;top:-3px;font-size:11px;white-space:nowrap;color:var(--ink-2);
  padding-left:9px;font-weight:600;pointer-events:none;
}
.slab em{font-style:normal;font-family:"IBM Plex Mono",monospace;color:var(--ink-3);font-weight:400;margin-left:7px}
.srow[data-cur="1"] .slab{color:var(--sel)}
.spec-foot{margin-top:16px;font-size:12.5px;color:var(--ink-3);max-width:64ch}

/* ============ BREED BAR ============ */
.breedbar{
  position:sticky;top:0;z-index:20;background:var(--bg);
  border-bottom:1px solid var(--line);padding:11px 0;
}
.breedbar .wrap{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center}
.breedbar .now{font-family:"Big Shoulders Display",Impact,sans-serif;font-weight:800;font-size:23px;text-transform:uppercase;line-height:1;letter-spacing:.01em}
.breedbar input{
  flex:1 1 210px;min-width:170px;max-width:330px;padding:7px 11px;font:inherit;font-size:14px;
  background:var(--surface);color:var(--ink);border:1px solid var(--line-2);border-radius:5px;
}
.breedbar input::placeholder{color:var(--ink-3)}
.breedbar select{
  padding:7px 10px;font:inherit;font-size:14px;background:var(--surface);color:var(--ink);
  border:1px solid var(--line-2);border-radius:5px;max-width:230px;
}

/* ============ BREED ============ */
.breed{padding:clamp(38px,5vw,66px) 0 clamp(50px,7vw,90px)}
.bname{
  font-family:"Big Shoulders Display",Impact,sans-serif;font-weight:800;
  font-size:clamp(44px,8.5vw,116px);line-height:.86;margin:10px 0 0;text-transform:uppercase;text-wrap:balance;
}
.bsub{margin:14px 0 0;color:var(--ink-2);font-size:15px}

.bignums{display:flex;flex-wrap:wrap;gap:clamp(24px,4.5vw,58px);margin:clamp(30px,4vw,48px) 0 0;align-items:flex-end}
.bignum b{
  display:block;font-family:"Big Shoulders Display",Impact,sans-serif;font-weight:800;
  font-size:clamp(56px,9vw,124px);line-height:.82;font-variant-numeric:tabular-nums;
}
.bignum b i{font-style:normal;font-size:.32em;color:var(--ink-3);margin-left:.12em;letter-spacing:.02em}
.bignum span{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.16em;color:var(--ink-3);margin-top:10px;font-weight:600}
.bignum.q b{font-size:clamp(34px,5vw,64px)}

/* ============ BURDEN CURVE ============ */
.burden{margin:clamp(38px,5vw,62px) 0 0}
.burden h3,.tlhead h3{
  font-family:"Big Shoulders Display",Impact,sans-serif;font-weight:800;
  font-size:clamp(21px,2.6vw,32px);text-transform:uppercase;margin:0;line-height:1;
}
.burden p.hint,.tlhead p.hint{margin:9px 0 0;font-size:13px;color:var(--ink-3);max-width:66ch}
.bwrap{position:relative;margin-top:22px}
.bwrap svg{display:block;width:100%;height:clamp(120px,16vw,190px);overflow:visible}
.bkey{display:flex;flex-wrap:wrap;gap:6px 22px;margin-top:12px;font-size:12px;color:var(--ink-2)}
.bkey i{display:inline-block;width:20px;height:9px;border-radius:2px;margin-right:7px;vertical-align:-1px}

/* ============ CONTROLS ============ */
.tlhead{margin:clamp(44px,6vw,74px) 0 0}
.controls{display:flex;flex-wrap:wrap;gap:14px 24px;align-items:center;margin:24px 0 14px}
.scrub{display:flex;align-items:center;gap:12px;flex:1 1 320px;min-width:260px}
.scrub label{font-size:11px;text-transform:uppercase;letter-spacing:.16em;color:var(--ink-3);font-weight:600;white-space:nowrap}
.scrub input[type=range]{flex:1;min-width:110px;accent-color:var(--sel)}
.scrub output{font-family:"IBM Plex Mono",monospace;font-size:14px;min-width:70px;color:var(--ink);font-variant-numeric:tabular-nums;font-weight:500}
.btn{font:inherit;font-size:12.5px;padding:6px 13px;border-radius:5px;cursor:pointer;background:var(--surface);border:1px solid var(--line-2);color:var(--ink-2)}
.btn:hover{border-color:var(--ink-3);color:var(--ink)}
.btn[aria-pressed="true"]{background:var(--ink);border-color:var(--ink);color:var(--bg);font-weight:600}
.chips{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:16px}
.chip{font:inherit;font-size:11.5px;padding:4px 10px;border-radius:20px;cursor:pointer;background:transparent;border:1px solid var(--line-2);color:var(--ink-2)}
.chip:hover{border-color:var(--ink-3);color:var(--ink)}
/* every system is on by default, so "on" is the quiet state and "off" is the marked one */
.chip[aria-pressed="false"]{color:var(--ink-4);border-color:var(--line);text-decoration:line-through}
.legend{display:flex;flex-wrap:wrap;gap:6px 20px;align-items:center;font-size:12px;color:var(--ink-2);margin-bottom:10px}
.legend .k{display:inline-flex;align-items:center;gap:7px}
.swatch{width:22px;height:9px;border-radius:2px;flex:none}
.legend .bands{margin-left:auto;color:var(--ink-3);font-size:11.5px}

/* ============ TIMELINE ============ */
.tl{border-top:2px solid var(--ink);background:transparent}
.tl-scroll{overflow-x:auto}
.tl-in{min-width:640px}
.grid{display:grid;grid-template-columns:minmax(200px,264px) minmax(0,1fr)}
.axis{border-bottom:1px solid var(--line)}
.axis.lab{padding:9px 0;font-size:10.5px;text-transform:uppercase;letter-spacing:.14em;color:var(--ink-3);font-weight:600;align-self:end}
.axis.track{position:relative;height:40px}
.tick{position:absolute;bottom:5px;transform:translateX(-50%);font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:var(--ink-3);font-variant-numeric:tabular-nums}
.bandlab{position:absolute;top:6px;font-size:9.5px;text-transform:uppercase;letter-spacing:.13em;color:var(--ink-4);white-space:nowrap;overflow:hidden;font-weight:600}

.row{display:contents}
.rname{padding:8px 16px 8px 0;border-bottom:1px solid var(--line);font-size:13.5px;line-height:1.3;display:flex;flex-direction:column;gap:2px;justify-content:center}
.rname .sys{font-size:10px;text-transform:uppercase;letter-spacing:.12em;color:var(--ink-3);font-weight:600}
.rtrack{position:relative;border-bottom:1px solid var(--line);min-height:42px}
.rtrack::after{content:"";position:absolute;top:0;bottom:0;left:var(--age,0%);width:1px;background:var(--sel);opacity:.55;pointer-events:none}
.bar{
  position:absolute;top:50%;height:15px;border-radius:2px;border:0;padding:0;cursor:pointer;min-width:9px;
  transform:translateY(-50%) scaleX(1);transform-origin:left center;
}
.anim .bar{transition:transform .5s cubic-bezier(.22,.9,.3,1);transition-delay:calc(var(--i) * 24ms)}
.anim .bar.pre{transform:translateY(-50%) scaleX(0)}
.bar:hover{filter:brightness(1.1)}
.bar:hover::after{content:"";position:absolute;inset:-3px;border:1.5px solid var(--ink);border-radius:4px}
.bar.mild{background:var(--sev-mild)} .bar.moderate{background:var(--sev-moderate)}
.bar.serious{background:var(--sev-serious)} .bar.limiting{background:var(--sev-limiting)}
.off .rname{opacity:.28} .off .rtrack .bar{opacity:.2}

.det{grid-column:1/-1;border-bottom:1px solid var(--line);background:var(--surface-3);padding:16px 18px}
.det h4{margin:0 0 10px;font-size:16px;font-weight:600;font-family:"Source Sans 3",sans-serif}
.det dl{display:grid;grid-template-columns:auto minmax(0,1fr);gap:6px 16px;margin:0;font-size:13.5px}
.det dt{color:var(--ink-3);font-size:10px;text-transform:uppercase;letter-spacing:.13em;padding-top:4px;white-space:nowrap;font-weight:600}
.det dd{margin:0;max-width:78ch}
.pill{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600;color:#0a0d10}
.pill.mild{background:var(--sev-mild);color:#fff} .pill.moderate{background:var(--sev-moderate)}
.pill.serious{background:var(--sev-serious)} .pill.limiting{background:var(--sev-limiting);color:#fff}

table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:9px 12px 9px 0;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:10px;text-transform:uppercase;letter-spacing:.13em;color:var(--ink-3);font-weight:600}
td.num{font-family:"IBM Plex Mono",monospace;white-space:nowrap;font-variant-numeric:tabular-nums}
.empty{padding:40px 0;text-align:center;color:var(--ink-3);font-size:14px}

footer{border-top:1px solid var(--line);padding:38px 0 60px;color:var(--ink-3);font-size:12.5px;margin-top:40px}
footer p{margin:0 0 10px;max-width:82ch}
footer b{color:var(--ink-2);font-weight:600}

@media (prefers-reduced-motion:reduce){
  *{transition:none!important;animation:none!important;scroll-behavior:auto!important}
  .bar{transform:translateY(-50%) scaleX(1)!important}
  .sbar{transform:none!important}
}
"""


BODY = r"""
<header class="hero"><div class="wrap">
  <div class="eyebrow">Canine Onset Atlas &middot; __VER__</div>
  <h1>The time<br>they get</h1>
  <p class="lede">Every breed carries its own diseases, and each one arrives on a schedule.
     This is <b>__ND__ breed&ndash;disease pairs across __NB__ breeds</b>, plotted against the age
     the signs actually show up &mdash; and against how long that breed lives to begin with.</p>
  <div class="figs">
    <div class="fig"><b class="num">__NB__</b><span>Breeds</span></div>
    <div class="fig"><b class="num">__ND__</b><span>Conditions mapped</span></div>
    <div class="fig"><b class="num">__LO__&ndash;__HI__</b><span>Years, shortest to longest lived</span></div>
  </div>
</div></header>

<section class="spectrum"><div class="wrap">
  <div class="sec-head">
    <div>
      <div class="eyebrow">Figure 1</div>
      <h2>Not every breed<br>gets the same life</h2>
    </div>
    <p>Mean lifespan, every breed in the set, shortest at the top. The
       __LONAME__ and the __HINAME__ are separated by __GAP__ years &mdash; roughly double.
       Pick any line to open that breed.</p>
  </div>
  <div class="spec">
    <div class="spec-axis" id="specaxis"></div>
    <div class="spec-rows" id="specrows"></div>
  </div>
  <p class="spec-foot">The short-lived end is dominated by giant breeds, where size itself
     drives osteosarcoma and cardiomyopathy, and by the extreme brachycephalics. One
     exception stands out: the Flat-Coated Retriever is a mid-sized dog pulled down to
     __FCR__ years by a single disease, histiocytic sarcoma.</p>
</div></section>

<div class="breedbar"><div class="wrap">
  <span class="now" id="nowname">Labrador Retriever</span>
  <input id="q" type="search" placeholder="Search breeds and conditions" aria-label="Search breeds and conditions">
  <select id="pick" aria-label="Choose a breed"></select>
</div></div>

<section class="breed"><div class="wrap">
  <div class="eyebrow">Figure 2 &middot; <span id="bgroup"></span></div>
  <h1 class="bname" id="bname"></h1>
  <p class="bsub" id="bsub"></p>

  <div class="bignums">
    <div class="bignum"><b class="num" id="nmean">0<i>y</i></b><span>Mean lifespan</span></div>
    <div class="bignum"><b class="num" id="nmode">0<i>y est.</i></b><span>Most common age at death</span></div>
    <div class="bignum q"><b class="num" id="nrange"></b><span>Half of dogs die in this window</span></div>
    <div class="bignum q"><b class="num" id="ncount"></b><span>Conditions tracked</span></div>
  </div>

  <div class="burden">
    <h3>Where the burden falls</h3>
    <p class="hint">How many of this breed&rsquo;s conditions are in their onset window at each
       age. Canine disease arrives in two waves: congenital and developmental problems in the
       first two years, then a second rise as cancer and degenerative disease take over.</p>
    <div class="bwrap" id="bwrap" aria-hidden="true"></div>
    <div class="bkey">
      <span><i style="background:var(--ink-4)"></i>All conditions in onset window</span>
      <span><i style="background:var(--sev-limiting)"></i>Serious and life-limiting only</span>
    </div>
  </div>

  <div class="tlhead">
    <h3>Every condition, by age of onset</h3>
    <p class="hint">Each bar spans the window in which signs typically first appear. Drag the age
       marker to your patient&rsquo;s age and everything outside its window dims.</p>
  </div>

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
</div></section>

<footer><div class="wrap">
  <p><b>Read the bars as onset, not risk.</b> A bar marks the interval in which clinical signs
     typically first appear in an affected dog of that breed. It says nothing about how likely
     this dog is to be affected, and a condition absent from a breed&rsquo;s list is not
     excluded in that breed.</p>
  <p><b>Mean lifespan</b> is anchored to published life tables, principally McMillan et&nbsp;al.
     2024 (<i>Scientific Reports</i>, 584,734 dogs) reconciled with Kennel Club survey data.
     <b>Modal lifespan is estimated, not published</b> &mdash; age-at-death distributions are
     left-skewed, so the most common age at death sits above the mean. It is labelled
     <i>est.</i> everywhere it appears.</p>
  <p>Onset windows are clinical consensus ranges drawn from Gough, Thomas &amp; O&rsquo;Neill,
     <i>Breed Predispositions to Disease in Dogs and Cats</i> (3rd&nbsp;ed.), the OFA/CHIC
     screening schedules, OMIA, the ACVO Blue Book, and breed-specific primary literature.
     Full source list and derivation notes in <code>SOURCES.md</code>. __VER__.</p>
</div></footer>
"""


JS = r"""
const D = __DATA__, SYS = __SYS__, SEVL = __SEVL__;
const $ = s => document.querySelector(s);
const REDUCED = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

let cur = D.find(b => b.name === "Labrador Retriever") || D[0];
let ageM = 0, onlyActive = false, tableView = false, sysOff = new Set(), query = "";
let rows = [];

const yr = m => m / 12;
const fmtAge = m => m === 0 ? "birth"
  : (m < 12 ? m + " mo" : Math.floor(m / 12) + "y" + (m % 12 ? " " + (m % 12) + "m" : ""));
const esc = s => (s || "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const pct = (y, max) => Math.max(0, Math.min(100, y / max * 100));

/* ================= SPECTRUM ================= */
const SPEC = D.slice().sort((a, b) => a.life.mean - b.life.mean);
const SLO = Math.floor(SPEC[0].life.mean) - 1;
const SHI = Math.ceil(SPEC[SPEC.length - 1].life.mean) + 1;
const SPEC_W = 72;  // bars use the left 72%, labels live in the rest
const sx = v => (v - SLO) / (SHI - SLO) * SPEC_W;

function buildSpectrum(){
  let ax = "";
  for (let y = SLO + 1; y < SHI; y++) ax += '<span style="left:' + sx(y) + '%">' + y + 'y</span>';
  $("#specaxis").innerHTML = ax;

  // selective direct labels: three shortest, three longest, and the current breed
  const shown = new Set([0, 1, 2, SPEC.length - 3, SPEC.length - 2, SPEC.length - 1]);
  let h = "";
  SPEC.forEach((b, i) => {
    const isCur = b === cur;
    const x = sx(b.life.mean);
    const lab = (shown.has(i) || isCur)
      ? '<span class="slab" style="left:' + x + '%">' + esc(b.name)
        + '<em>' + b.life.mean.toFixed(1) + 'y</em></span>' : "";
    h += '<button class="srow" data-b="' + esc(b.name) + '" data-cur="' + (isCur ? 1 : 0) + '"'
       + ' title="' + esc(b.name) + ' — mean ' + b.life.mean.toFixed(1) + ' years">'
       + '<span class="sbar" style="--w:' + sx(b.life.mean) + '%"></span>' + lab + '</button>';
  });
  $("#specrows").innerHTML = h;
  if (!REDUCED){
    const bars = $("#specrows").querySelectorAll(".sbar");
    bars.forEach((el, i) => {
      el.style.transition = "transform .55s cubic-bezier(.22,.9,.3,1) " + (i * 9) + "ms";
      el.style.transform = "scaleX(0)";
    });
    requestAnimationFrame(() => requestAnimationFrame(() => {
      bars.forEach(el => { el.style.transform = ""; });
    }));
    // never leave the chart hidden if a frame is dropped or the tab is backgrounded
    setTimeout(() => bars.forEach(el => { el.style.transform = ""; }), 1600);
  }
}
function markSpectrum(){
  $("#specrows").querySelectorAll(".dyn").forEach(el => el.remove());
  $("#specrows").querySelectorAll(".srow").forEach(el => {
    const isCur = el.dataset.b === cur.name;
    el.dataset.cur = isCur ? "1" : "0";
    if (isCur && !el.querySelector(".slab")){
      const s = document.createElement("span");
      s.className = "slab dyn";
      s.style.left = sx(cur.life.mean) + "%";
      s.innerHTML = esc(cur.name) + '<em>' + cur.life.mean.toFixed(1) + 'y</em>';
      el.appendChild(s);
    }
  });
}

/* ================= BURDEN CURVE ================= */
function buildBurden(){
  const b = cur, maxM = b.axisMax * 12, W = 1000, H = 200;
  const all = [], sev = [];
  for (let t = 0; t <= maxM; t += 1){
    let a = 0, s = 0;
    for (const d of b.dz){
      if (t >= d.on[0] && t <= d.on[1]){ a++; if (d.sev === "serious" || d.sev === "limiting") s++; }
    }
    all.push(a); sev.push(s);
  }
  const peak = Math.max(1, ...all);
  const px = t => t / maxM * W;
  const py = v => H - (v / peak) * (H - 12);
  const area = arr => {
    let p = "M0," + H;
    for (let t = 0; t <= maxM; t++) p += "L" + px(t).toFixed(1) + "," + py(arr[t]).toFixed(1);
    return p + "L" + W + "," + H + "Z";
  };
  const g = b.growthEnd * 12, sn = b.life.mean * 0.75 * 12, mn = b.life.mean * 12;
  const peakAt = all.indexOf(peak);

  let sv = '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none">';
  sv += '<rect x="0" y="0" width="' + px(g) + '" height="' + H + '" fill="var(--band-puppy)"/>';
  sv += '<rect x="' + px(sn) + '" y="0" width="' + (px(mn) - px(sn)) + '" height="' + H + '" fill="var(--band-senior)"/>';
  sv += '<rect x="' + px(mn) + '" y="0" width="' + (W - px(mn)) + '" height="' + H + '" fill="var(--band-geri)"/>';
  sv += '<path d="' + area(all) + '" fill="var(--ink-4)" opacity=".55"/>';
  sv += '<path d="' + area(sev) + '" fill="var(--sev-limiting)" opacity=".38"/>';
  sv += '<line x1="0" y1="' + H + '" x2="' + W + '" y2="' + H + '" stroke="var(--ink)" stroke-width="2" vector-effect="non-scaling-stroke"/>';
  sv += '</svg>';
  const el = $(".bwrap");
  const pkx = px(peakAt) / W * 100;
  const pkpos = pkx < 9 ? "left:0;" : pkx > 91 ? "right:0;" : "left:" + pkx + "%;transform:translateX(-50%);";
  el.innerHTML = sv
    + '<div style="position:absolute;' + pkpos + 'top:-4px;'
    + 'font-family:\'IBM Plex Mono\',monospace;font-size:10.5px;color:var(--ink-2);white-space:nowrap">'
    + 'peak ' + peak + ' at ' + fmtAge(peakAt) + '</div>'
    + '<div style="display:flex;justify-content:space-between;font-family:\'IBM Plex Mono\',monospace;'
    + 'font-size:10.5px;color:var(--ink-3);margin-top:6px"><span>birth</span><span>'
    + b.axisMax + 'y</span></div>';
}

/* ================= TIMELINE ================= */
function bandCss(b){
  const max = b.axisMax, p = y => (y / max * 100).toFixed(2) + "%";
  const g = b.growthEnd, s = b.life.mean * 0.75, m = b.life.mean;
  return "linear-gradient(to right,"
    + "var(--band-puppy) 0,var(--band-puppy) " + p(g) + ","
    + "var(--band-adult) " + p(g) + ",var(--band-adult) " + p(s) + ","
    + "var(--band-senior) " + p(s) + ",var(--band-senior) " + p(m) + ","
    + "var(--band-geri) " + p(m) + ",var(--band-geri) 100%)";
}
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

function buildTL(animate){
  const b = cur, max = b.axisMax, bg = bandCss(b);
  rows = b.dz.filter(visible);
  if (tableView){ buildTable(); return; }
  if (!rows.length){ $("#tlin").innerHTML = '<div class="empty">Nothing matches the current filters.</div>'; return; }

  const step = max > 12 ? 2 : 1;
  let ticks = '<span class="tick" style="left:0;transform:none">birth</span>';
  for (let y = step; y <= max; y += step){
    const p = pct(y, max);
    ticks += '<span class="tick" style="' + (p > 97 ? 'right:0;transform:none' : 'left:' + p + '%') + '">' + y + 'y</span>';
  }
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
       + '<button class="bar ' + d.sev + '" style="left:' + a + '%;width:' + w + '%;--i:' + Math.min(i, 22) + '" data-i="' + i + '"'
       + ' aria-label="' + esc(d.n) + ': ' + SEVL[d.sev] + ', onset ' + span + '"'
       + ' title="' + esc(d.n) + ' — ' + SEVL[d.sev] + ' — ' + span + '"></button>'
       + '</div></div>';
  });
  const box = $("#tlin");
  box.innerHTML = h + '</div>';
  const bars = box.querySelectorAll(".bar");
  box.classList.remove("anim");
  if (animate && !REDUCED){
    bars.forEach(el => el.classList.add("pre"));
    box.classList.add("anim");
    requestAnimationFrame(() => requestAnimationFrame(() =>
      bars.forEach(el => el.classList.remove("pre"))));
  }
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
    + '</dl>';
  rowEls[i].querySelector(".rtrack").after(div);
}

/* ================= HEAD ================= */
function countUp(el, to, suffix, dp){
  if (REDUCED){ el.innerHTML = to.toFixed(dp) + suffix; return; }
  const t0 = performance.now(), dur = 650;
  const tick = now => {
    const k = Math.min(1, (now - t0) / dur);
    const e = 1 - Math.pow(1 - k, 3);
    el.innerHTML = (to * e).toFixed(dp) + suffix;
    if (k < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

function buildHead(animate){
  const b = cur, L = b.life;
  $("#nowname").textContent = b.name;
  $("#bname").textContent = b.name;
  $("#bgroup").textContent = b.group + " group";
  $("#bsub").textContent = b.size.charAt(0).toUpperCase() + b.size.slice(1)
    + " breed. Growth plates close near " + b.growthEnd + " years; on the mean-lifespan model this breed is senior from "
    + (L.mean * 0.75).toFixed(1) + " years.";
  if (animate){
    countUp($("#nmean"), L.mean, "<i>y</i>", 1);
    countUp($("#nmode"), L.mode, "<i>y est.</i>", 0);
  } else {
    $("#nmean").innerHTML = L.mean.toFixed(1) + "<i>y</i>";
    $("#nmode").innerHTML = L.mode + "<i>y est.</i>";
  }
  $("#nrange").innerHTML = L.p25 + "&ndash;" + L.p75 + "<i>y</i>";
  $("#ncount").textContent = b.dz.length;

  const used = [];
  for (const d of b.dz) if (used.indexOf(d.sys) === -1) used.push(d.sys);
  $("#syschips").innerHTML = used.map(s =>
    '<button class="chip" data-s="' + s + '" aria-pressed="' + !sysOff.has(s) + '">' + SYS[s] + '</button>').join("");

  const maxM = b.axisMax * 12, el = $("#age");
  el.max = maxM;
  if (ageM > maxM) ageM = maxM;
  el.value = ageM;
  $("#ageout").textContent = fmtAge(ageM);
  document.documentElement.style.setProperty("--age", (ageM / maxM * 100) + "%");
}

function buildPicker(){
  const order = ["Sporting","Hound","Working","Terrier","Toy","Non-Sporting","Herding"];
  let h = "";
  for (const g of order){
    h += '<optgroup label="' + g + '">';
    for (const b of D) if (b.group === g)
      h += '<option value="' + esc(b.name) + '"' + (b === cur ? " selected" : "") + '>' + esc(b.name) + '</option>';
    h += '</optgroup>';
  }
  $("#pick").innerHTML = h;
}

function select(name, scroll){
  const b = D.find(x => x.name === name);
  if (!b || b === cur) return;
  cur = b;
  sysOff.clear();
  $("#pick").value = name;
  markSpectrum();
  buildHead(true);
  buildBurden();
  buildTL(true);
  const bb = $(".breedbar");
  if (scroll && bb && bb.scrollIntoView) bb.scrollIntoView({ block: "start", behavior: REDUCED ? "auto" : "smooth" });
}

/* ================= EVENTS ================= */
$("#specrows").addEventListener("click", e => {
  const r = e.target.closest(".srow"); if (!r) return;
  select(r.dataset.b, true);
});
$("#pick").addEventListener("change", e => select(e.target.value, false));
$("#q").addEventListener("input", e => {
  query = e.target.value.trim();
  const q = query.toLowerCase();
  if (q){
    const hit = D.find(b => b.name.toLowerCase().includes(q))
             || D.find(b => b.dz.some(d => d.n.toLowerCase().includes(q)));
    if (hit && hit !== cur){ select(hit.name, false); return; }
  }
  buildTL(false);
});
$("#age").addEventListener("input", e => {
  ageM = +e.target.value;
  $("#ageout").textContent = fmtAge(ageM);
  document.documentElement.style.setProperty("--age", (ageM / +e.target.max * 100) + "%");
  buildTL(false);
});
$("#onlyactive").addEventListener("click", e => {
  onlyActive = !onlyActive;
  e.currentTarget.setAttribute("aria-pressed", onlyActive);
  buildTL(false);
});
$("#viewtoggle").addEventListener("click", e => {
  tableView = !tableView;
  e.currentTarget.setAttribute("aria-pressed", tableView);
  e.currentTarget.textContent = tableView ? "Timeline view" : "Table view";
  buildTL(false);
});
$("#syschips").addEventListener("click", e => {
  const c = e.target.closest(".chip"); if (!c) return;
  const s = c.dataset.s;
  if (sysOff.has(s)) sysOff.delete(s); else sysOff.add(s);
  c.setAttribute("aria-pressed", !sysOff.has(s));
  buildTL(false);
});
$("#tlin").addEventListener("click", e => {
  const bar = e.target.closest(".bar"); if (!bar) return;
  openDetail(+bar.dataset.i);
});

buildSpectrum();
buildPicker();
buildHead(true);
buildBurden();
buildTL(true);
"""


def build():
    breeds = load()
    nb, nd, mean_all, lo, hi = stats(breeds)
    vpath = os.path.join(ROOT, "VERSION")
    ver = "v" + (open(vpath).read().strip() if os.path.exists(vpath) else "0.1.0")
    fcr = next((b for b in breeds if b["name"] == "Flat-Coated Retriever"), None)

    body = (BODY
            .replace("__NB__", str(nb)).replace("__ND__", str(nd))
            .replace("__MA__", str(mean_all)).replace("__VER__", ver)
            .replace("__LONAME__", lo["name"]).replace("__HINAME__", hi["name"])
            .replace("__LO__", str(lo["life"]["mean"])).replace("__HI__", str(hi["life"]["mean"]))
            .replace("__GAP__", str(round(hi["life"]["mean"] - lo["life"]["mean"], 1)))
            .replace("__FCR__", str(fcr["life"]["mean"]) if fcr else "9.5"))
    js = (JS.replace("__DATA__", json.dumps(breeds, separators=(",", ":"), ensure_ascii=False))
            .replace("__SYS__", json.dumps(SYSTEMS))
            .replace("__SEVL__", json.dumps(SEV_LABEL)))

    head = ('<title>Canine Onset Atlas</title>\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
            'family=Big+Shoulders+Display:wght@700;800&family=IBM+Plex+Mono:wght@400;500&'
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
    print("built %d breeds / %d conditions | spread %s (%s) - %s (%s)"
          % (nb, nd, lo["life"]["mean"], lo["name"], hi["life"]["mean"], hi["name"]))


if __name__ == "__main__":
    build()
