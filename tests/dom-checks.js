const fs = require("fs");
const { JSDOM } = require("jsdom");

const html = fs.readFileSync("C:/Users/chris/dog-breed-disease-timeline/dist/index.html", "utf8");

const errors = [];
const dom = new JSDOM(html, {
  runScripts: "dangerously",
  pretendToBeVisual: true,
  virtualConsole: new (require("jsdom").VirtualConsole)()
    .on("jsdomError", e => errors.push("jsdomError: " + (e.detail || e.message)))
    .on("error", (...a) => errors.push("console.error: " + a.join(" "))),
});

const { window } = dom;
const doc = window.document;
const $ = s => doc.querySelector(s);
const $$ = s => [...doc.querySelectorAll(s)];

function check(label, fn) {
  try {
    const r = fn();
    console.log((r === true ? "  ok   " : r === false ? "  FAIL " : "  ..   ") + label + (typeof r === "string" ? " -> " + r : ""));
    if (r === false) errors.push("check failed: " + label);
  } catch (e) {
    console.log("  ERR  " + label + " -> " + e.message);
    errors.push(label + ": " + e.message);
  }
}

setTimeout(() => {
  console.log("\n--- initial render ---");
  check("spectrum rows rendered (85)", () => $$(".srow").length === 85);
  check("spectrum axis ticks", () => $$(".spec-axis span").length > 3);
  check("burden svg present", () => !!$("#bwrap svg"));
  check("burden area paths (2)", () => $$("#bwrap svg path").length === 2);
  check("burden path has no NaN", () => !$$("#bwrap svg path").some(p => /NaN|Infinity/.test(p.getAttribute("d"))));
  check("breed picker options (85)", () => $$("#pick option").length === 85);
  check("timeline rows for Labrador (13)", () => $$("#tlin .row").length === 13);
  check("all bars have width", () => $$("#tlin .bar").every(b => parseFloat(b.style.width) > 0));
  check("bars stay inside track", () => $$("#tlin .bar").every(b =>
    parseFloat(b.style.left) + parseFloat(b.style.width) <= 100.6));
  check("big numbers populated", () => $("#nmean").textContent.length > 0 && $("#ncount").textContent === "13");
  check("current breed labelled in spectrum", () => $$('.srow[data-cur="1"]').length === 1);

  console.log("\n--- select Irish Wolfhound via spectrum click ---");
  const iw = $$(".srow").find(r => r.dataset.b === "Irish Wolfhound");
  iw.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("breed name updated", () => $("#bname").textContent === "Irish Wolfhound");
  check("sticky bar updated", () => $("#nowname").textContent === "Irish Wolfhound");
  check("burden re-rendered (still 2 paths)", () => $$("#bwrap svg path").length === 2);
  check("burden not NaN after switch", () => !$$("#bwrap svg path").some(p => /NaN/.test(p.getAttribute("d"))));
  check("timeline rows = 7", () => $$("#tlin .row").length === 7);
  check("spectrum marks new current", () => $('.srow[data-cur="1"]').dataset.b === "Irish Wolfhound");
  check("dynamic label added", () => !!$(".slab.dyn") || $$(".srow").findIndex(r => r.dataset.b === "Irish Wolfhound") < 3);
  check("axis max shrank for short-lived breed", () => {
    const t = $$("#tlin .tick").map(x => x.textContent).filter(x => x !== "birth");
    return t[t.length - 1];
  });

  console.log("\n--- select a second breed (regression on re-render) ---");
  $$(".srow").find(r => r.dataset.b === "Dachshund").dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("breed name = Dachshund", () => $("#bname").textContent === "Dachshund");
  check("burden survived 2nd switch", () => $$("#bwrap svg path").length === 2);
  check("only one current marker", () => $$('.srow[data-cur="1"]').length === 1);
  check("only one dyn label", () => $$(".slab.dyn").length <= 1);

  console.log("\n--- age scrubber ---");
  const age = $("#age");
  age.value = "60";
  age.dispatchEvent(new window.Event("input", { bubbles: true }));
  check("age output formatted", () => $("#ageout").textContent === "5y");
  check("some rows dimmed at 5y", () => $$("#tlin .row.off").length > 0);
  check("not all rows dimmed", () => $$("#tlin .row.off").length < $$("#tlin .row").length);

  console.log("\n--- only-active filter ---");
  $("#onlyactive").dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("filtered to live conditions only", () => {
    const n = $$("#tlin .row").length;
    return n > 0 && n < 9 ? String(n) + " rows live at 5y" : false;
  });
  $("#onlyactive").dispatchEvent(new window.MouseEvent("click", { bubbles: true }));

  console.log("\n--- table view ---");
  $("#viewtoggle").dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("table rendered", () => $$("#tlin tbody tr").length > 0);
  check("table has 6 columns", () => $$("#tlin thead th").length === 6);
  $("#viewtoggle").dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("back to timeline", () => $$("#tlin .row").length > 0);

  console.log("\n--- system chips ---");
  const chip = $(".chip");
  const before = $$("#tlin .row").length;
  chip.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("chip filters rows out", () => $$("#tlin .row").length < before);
  chip.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("chip restores rows", () => $$("#tlin .row").length === before);

  console.log("\n--- detail panel ---");
  const bar = $("#tlin .bar");
  bar.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("detail opened", () => $$(".det").length === 1);
  check("detail has content", () => $(".det h4").textContent.length > 3);
  $$("#tlin .bar")[2].dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  check("only one detail at a time", () => $$(".det").length === 1);

  console.log("\n--- search ---");
  const q = $("#q");
  q.value = "glaucoma";
  q.dispatchEvent(new window.Event("input", { bubbles: true }));
  check("search jumped to a breed with glaucoma", () => $$("#tlin .row").length > 0 || $(".empty") !== null);
  q.value = "Boxer";
  q.dispatchEvent(new window.Event("input", { bubbles: true }));
  check("search by breed name selects Boxer", () => $("#bname").textContent === "Boxer");
  q.value = "";
  q.dispatchEvent(new window.Event("input", { bubbles: true }));
  check("cleared search restores full list", () => $$("#tlin .row").length === 11);

  console.log("\n--- every breed renders without error ---");
  const names = [...doc.querySelectorAll("#pick option")].map(o => o.value);
  let bad = [];
  for (const n of names) {
    try {
      const sel = $("#pick");
      sel.value = n;
      sel.dispatchEvent(new window.Event("change", { bubbles: true }));
      if (!$$("#tlin .row").length && !$(".empty")) bad.push(n + ": no rows");
      if ($$("#bwrap svg path").some(p => /NaN/.test(p.getAttribute("d")))) bad.push(n + ": NaN burden path");
      if ($$("#tlin .bar").some(b => parseFloat(b.style.left) + parseFloat(b.style.width) > 100.6)) bad.push(n + ": bar overflow");
    } catch (e) { bad.push(n + ": " + e.message); }
  }
  check("all 85 breeds render clean", () => bad.length === 0 ? true : bad.slice(0, 5).join(" | "));

  console.log("\n=== " + (errors.length ? errors.length + " PROBLEM(S)" : "ALL CHECKS PASSED") + " ===");
  errors.slice(0, 12).forEach(e => console.log("  ! " + e));
  process.exit(errors.length ? 1 : 0);
}, 600);
