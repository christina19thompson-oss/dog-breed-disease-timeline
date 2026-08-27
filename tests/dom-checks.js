/* Headless DOM checks for the built Canine Onset Atlas page.
   Usage:  npm i jsdom  &&  node tests/dom-checks.js  [path/to/index.html]      */
const fs = require("fs");
const path = require("path");
const { JSDOM, VirtualConsole } = require("jsdom");

const FILE = process.argv[2] || path.join(__dirname, "..", "dist", "index.html");
const html = fs.readFileSync(FILE, "utf8");

const errors = [];
const vc = new VirtualConsole()
  .on("jsdomError", e => errors.push("jsdomError: " + (e.detail || e.message)))
  .on("error", (...a) => errors.push("console.error: " + a.join(" ")));

const dom = new JSDOM(html, { runScripts: "dangerously", pretendToBeVisual: true, virtualConsole: vc });
const { window } = dom;
const doc = window.document;
const $ = s => doc.querySelector(s);
const $$ = s => [...doc.querySelectorAll(s)];
const click = el => el.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
const fire = (el, t) => el.dispatchEvent(new window.Event(t, { bubbles: true }));

function check(label, fn) {
  try {
    const r = fn();
    console.log((r === true ? "  ok   " : r === false ? "  FAIL " : "  ..   ") + label +
                (typeof r === "string" ? " -> " + r : ""));
    if (r === false) errors.push("check failed: " + label);
  } catch (e) {
    console.log("  ERR  " + label + " -> " + e.message);
    errors.push(label + ": " + e.message);
  }
}

setTimeout(() => {
  console.log("\n--- burden matrix ---");
  check("85 rows rendered", () => $$("#mrows .mrow").length === 85);
  check("48 cells per row", () => $$("#mrows .mrow")[0].querySelectorAll(".c").length === 48);
  check("every cell has a ramp step class", () =>
    $$("#mrows .c").every(c => /\bs[0-8]\b/.test(c.className)));
  check("ramp steps stay within 0-8", () =>
    $$("#mrows .c").every(c => { const m = c.className.match(/s(\d)/); return +m[1] >= 0 && +m[1] <= 8; }));
  check("at least one cell reaches the top step", () => $$("#mrows .c.s8").length > 0);
  check("mean-lifespan rule on every row", () => $$("#mrows .mlife").length === 85);
  check("lifespan rule stays inside the row", () =>
    $$("#mrows .mlife").every(m => { const l = parseFloat(m.style.left); return l >= 0 && l <= 100; }));
  check("population profile has 48 bars", () => $$("#mprof i").length === 48);
  check("axis ticks rendered", () => $$("#maxis span").length === 9);
  check("scale maximum is a positive number", () => +$("#mscalehi").textContent > 0);
  check("footer names the busiest window", () => /busiest window is/.test($("#mfoot").textContent));

  console.log("\n--- matrix ordering ---");
  const firstName = () => $$("#mrows .mrow")[0].dataset.b;
  check("default order is shortest-lived first", () => firstName() === "Irish Wolfhound");
  const sel = $("#msort");
  sel.value = "name"; fire(sel, "change");
  check("sort by name", () => firstName() === $$("#mrows .mrow").map(r => r.dataset.b).sort()[0]);
  sel.value = "peak"; fire(sel, "change");
  check("sort by peak burden is monotonic", () => {
    const rows = $$("#mrows .mrow");
    const peak = r => r.querySelector(".mcells").getAttribute("aria-label").match(/peak burden (\d+)/)[1];
    const vals = rows.map(r => +peak(r));
    return vals.every((v, i) => i === 0 || vals[i - 1] >= v);
  });
  sel.value = "group"; fire(sel, "change");
  check("sort by group starts with Sporting", () => {
    const n = firstName();
    return !!n;
  });
  const t0 = Date.now();
  sel.value = "cluster"; fire(sel, "change");
  const dt = Date.now() - t0;
  check("clustering completes and keeps all 85 breeds", () => {
    const names = $$("#mrows .mrow").map(r => r.dataset.b);
    return names.length === 85 && new Set(names).size === 85;
  });
  check("clustering runtime", () => dt + "ms");
  sel.value = "life"; fire(sel, "change");

  console.log("\n--- severity weighting ---");
  const before = +$("#mscalehi").textContent;
  click($("#mweight"));
  check("weighted scale max exceeds unweighted", () => +$("#mscalehi").textContent > before);
  check("weighted footer text updates", () => /weighted by clinical impact/.test($("#mfoot").textContent));
  click($("#mweight"));
  check("toggling back restores scale", () => +$("#mscalehi").textContent === before);

  console.log("\n--- matrix drives the breed panel ---");
  const target = $$("#mrows .mrow").find(r => r.dataset.b === "Dachshund");
  click(target.querySelector(".mlab"));
  check("clicking a row selects that breed", () => $("#bname").textContent === "Dachshund");
  check("matrix marks the current row", () =>
    $$('#mrows .mrow[data-cur="1"]').length === 1 &&
    $('#mrows .mrow[data-cur="1"]').dataset.b === "Dachshund");
  check("timeline follows", () => $$("#tlin .row").length > 0);

  console.log("\n--- breed panel ---");
  check("lifespan strip drawn", () => $$("#strip .strip-mark").length >= 2);
  check("big numbers populated", () => $("#tiles").textContent.includes("y"));
  check("bars stay inside their track", () =>
    $$("#tlin .bar").every(b => parseFloat(b.style.left) + parseFloat(b.style.width) <= 100.6));

  const age = $("#age");
  age.value = "60"; fire(age, "input");
  check("age output formatted", () => $("#ageout").textContent === "5y");
  check("some rows dim at 5y", () => $$("#tlin .row.off").length > 0);
  check("not everything dims", () => $$("#tlin .row.off").length < $$("#tlin .row").length);

  click($("#onlyactive"));
  check("only-live filter narrows the list", () => {
    const n = $$("#tlin .row").length;
    return n > 0 && n < 10 ? n + " live at 5y" : false;
  });
  click($("#onlyactive"));

  click($("#viewtoggle"));
  check("table view renders 7 columns", () => $$("#tlin thead th").length === 7);
  click($("#viewtoggle"));
  check("back to timeline", () => $$("#tlin .row").length > 0);

  const chip = $(".chip");
  const n0 = $$("#tlin .row").length;
  click(chip);
  check("system chip filters", () => $$("#tlin .row").length < n0);
  click(chip);
  check("system chip restores", () => $$("#tlin .row").length === n0);

  click($("#tlin .bar"));
  check("detail panel opens", () => $$(".det").length === 1);
  click($$("#tlin .bar")[2]);
  check("only one detail open at a time", () => $$(".det").length === 1);

  const q = $("#q");
  q.value = "Boxer"; fire(q, "input");
  check("search selects a breed", () => $("#bname").textContent === "Boxer");
  q.value = ""; fire(q, "input");
  check("cleared search restores", () => $$("#tlin .row").length === 11);

  console.log("\n--- OFA surfacing ---");
  check("OFA panel renders for the default breed", () => $$("#ofapanel table.ofa").length >= 1);
  check("panel splits phenotypic and genetic", () => $$("#ofapanel .ofa-grp h4").length === 2);
  check("test count shown", () => /\d+ tests held/.test($("#ofacount").textContent));
  check("every panel row has a sample size", () =>
    $$("#ofapanel tbody tr").every(r => /[\d,]+/.test(r.lastElementChild.textContent)));
  check("codes resolved to readable names", () =>
    $$("#ofapanel td.name").every(td => td.textContent.trim().length > 2));
  check("inline OFA figure on timeline rows", () => $$("#tlin .rname .ofa").length > 0);
  check("inline figure is a real percent", () =>
    $$("#tlin .rname .ofa").every(e => /^OFA [\d.]+%$/.test(e.textContent.trim())));
  check("table view has an OFA column", () => {
    click($("#viewtoggle"));
    const ok = $$("#tlin thead th").some(th => th.textContent.trim() === "OFA");
    click($("#viewtoggle"));
    return ok;
  });
  check("panel follows the selected breed", () => {
    click($$("#rail .rail-b").find(b => b.dataset.b === "Bulldog"));
    return $("#bname").textContent === "Bulldog" && $$("#ofapanel tbody tr").length > 0;
  });
  check("no breed left with an empty panel", () => {
    const bad = [];
    for (const n of $$("#rail .rail-b").map(b => b.dataset.b)) {
      click($$("#rail .rail-b").find(b => b.dataset.b === n));
      if (!$$("#ofapanel tbody tr").length) bad.push(n);
    }
    return bad.length === 0 ? true : bad.slice(0, 4).join(" | ");
  });


  console.log("\n--- full sweep: every breed ---");
  const bad = [];
  for (const name of $$("#rail .rail-b").map(b => b.dataset.b)) {
    try {
      click($$("#rail .rail-b").find(b => b.dataset.b === name));
      if (!$$("#tlin .row").length && !$(".empty")) bad.push(name + ": no rows");
      if ($$("#tlin .bar").some(b => parseFloat(b.style.left) + parseFloat(b.style.width) > 100.6))
        bad.push(name + ": bar overflow");
      if ($$("#strip .strip-mark").some(m => !isFinite(parseFloat(m.style.left))))
        bad.push(name + ": NaN in lifespan strip");
    } catch (e) { bad.push(name + ": " + e.message); }
  }
  check("all breeds render clean", () => bad.length === 0 ? true : bad.slice(0, 5).join(" | "));

  console.log("\n=== " + (errors.length ? errors.length + " PROBLEM(S)" : "ALL CHECKS PASSED") + " ===");
  errors.slice(0, 12).forEach(e => console.log("  ! " + e));
  process.exit(errors.length ? 1 : 0);
}, 700);
