const $ = (id) => document.getElementById(id);
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"]/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c],
  );
const FIELD = {
  warnings: "Warnings",
  do_not_use: "Do not use",
  ask_doctor: "Ask a doctor",
  ask_doctor_or_pharmacist: "Ask a doctor or pharmacist",
  stop_use: "Stop use",
  pregnancy_or_breast_feeding: "Pregnancy / breast-feeding",
  dosage_and_administration: "Directions",
  inactive_ingredient: "Inactive ingredients",
  active_ingredient: "Active ingredient",
  when_using: "When using",
  purpose: "Purpose",
  text: "Label",
};
const AGES = [
  ["Under 2", 1],
  ["Child 2–11", 8],
  ["Teen 12–17", 15],
  ["Adult", 35],
  ["65 and over", 70],
  ["Pregnant", 30, "pregnant"],
];
const CONDS = [
  ["liver", "Liver disease or 3+ drinks a day"],
  ["ulcer", "Stomach ulcer or bleeding history"],
  ["thinner", "Takes a blood thinner"],
  ["kidney", "Kidney disease"],
  ["heart", "Heart disease or high blood pressure"],
  ["nsaid_allergy", "Allergic to aspirin or NSAIDs"],
  ["maoi", "Takes an MAOI antidepressant"],
  ["glaucoma", "Glaucoma or enlarged prostate"],
];
const state = { age: 3, conds: new Set() };
let current = null;
function profile() {
  const a = AGES[state.age],
    p = { age: a[1], pregnant: a[2] === "pregnant" };
  for (const c of state.conds) p[c] = true;
  return p;
}
function plabel() {
  const n = state.conds.size;
  return AGES[state.age][0] + (n ? ` · ${n} condition${n > 1 ? "s" : ""}` : "");
}
function score(d, p) {
  const r = [];
  const add = (points, title, evidence, stop = false) => r.push({ points, title, evidence, stop });
  const has = (id) => d.facts.warnings.find((w) => w.warning_id === id);
  const subst = (re) => d.substances.some((s) => re.test(s));
  for (const a of d.facts.age_limits) {
    if (p.age < a.under_years && p.age >= (a.min_years ?? 0)) {
      if (a.action === "do_not_use")
        add(0, `Label: do not use under ${a.under_years}`, a.evidence, true);
      else
        add(
          30,
          a.min_years != null
            ? `Label: ask a doctor for ages ${a.min_years} to under ${a.under_years}`
            : `Label: ask a doctor under ${a.under_years}`,
          a.evidence,
        );
    }
  }
  let w;
  if ((w = has("reyes_syndrome_warning")) && p.age < 18)
    add(40, "Reye's syndrome risk for children and teens", w.evidence);
  if ((w = has("liver_warning")))
    p.liver
      ? add(
          45,
          "Contains acetaminophen: liver damage risk with liver disease or alcohol",
          w.evidence,
        )
      : add(5, "Contains acetaminophen: easy to exceed the daily limit", w.evidence);
  if ((w = has("stomach_bleeding_warning"))) {
    if (p.ulcer) add(45, "NSAID with a history of ulcers or bleeding", w.evidence);
    else if (p.thinner) add(45, "NSAID plus a blood thinner raises bleeding risk", w.evidence);
    else if (p.age >= 60) add(20, "NSAID: stomach bleeding risk is higher at 60+", w.evidence);
    else add(5, "NSAID: stomach bleeding warning on label", w.evidence);
    if (p.kidney) add(25, "NSAIDs can worsen kidney disease (label: ask a doctor)", w.evidence);
  }
  if ((w = has("heart_attack_and_stroke_warning")) && p.heart)
    add(30, "NSAID with heart disease or high blood pressure", w.evidence);
  if ((w = has("nsaid_allergy_alert")) && p.nsaid_allergy)
    add(0, "Allergy alert: you're allergic to this class of drug", w.evidence, true);
  if ((w = has("nsaid_pregnancy_warning")) && p.pregnant)
    add(40, "NSAID in pregnancy: avoid in the last 3 months", w.evidence);
  if ((w = has("maoi_warning")) && p.maoi)
    add(0, "Label: do not use with an MAOI", w.evidence, true);
  if (subst(/diphenhydramine|doxylamine|chlorpheniramine/)) {
    const ev = { field: "active_ingredient", text: d.substances.join(", ") };
    if (p.age >= 65)
      add(30, "Sedating antihistamine: confusion and fall risk in older adults (AGS Beers)", ev);
    if (p.glaucoma)
      add(25, "Antihistamine with glaucoma or enlarged prostate (label: ask a doctor)", ev);
  }
  if (subst(/pseudoephedrine|phenylephrine/) && p.heart)
    add(25, "Decongestant can raise blood pressure", {
      field: "active_ingredient",
      text: d.substances.join(", "),
    });
  for (const id of [
    "acetaminophen_duplicate_use_warning",
    "diphenhydramine_duplicate_use_warning",
  ]) {
    if ((w = has(id)))
      add(0, "Don't combine with other products that contain the same ingredient", w.evidence);
  }
  const pts = r.reduce((s, x) => s + x.points, 0);
  const sc = Math.max(0, Math.min(100, 100 - pts));
  const stop = r.some((x) => x.stop);
  const tier = stop ? "red" : sc >= 75 ? "green" : sc >= 50 ? "yellow" : "red";
  r.sort((a, b) => b.stop - a.stop || b.points - a.points);
  return { score: sc, tier, stop, reasons: r };
}
const TIER = {
  green: ["ok", "Looks OK"],
  yellow: ["caution", "Use caution"],
  red: ["avoid", "Ask first"],
};
const nice = (id) =>
  id
    .replace(/_/g, " ")
    .replace(/\bnsaid\b/i, "NSAID")
    .replace(/\bmaoi\b/i, "MAOI")
    .replace(/^./, (c) => c.toUpperCase());
function altScore(c) {
  const d = {
    facts: {
      warnings: c.warnings.map((id) => ({
        warning_id: id,
        evidence: { field: "warnings", text: "" },
      })),
      age_limits: [],
    },
    substances: [c.generic.toLowerCase()],
  };
  return score(d, profile());
}
function render() {
  const d = current,
    p = profile(),
    s = score(d, p),
    f = d.facts,
    [cls, word] = TIER[s.tier];
  document.querySelectorAll(".plabel").forEach((e) => (e.textContent = plabel()));
  const why = s.reasons.length
    ? `<ol class="why">${s.reasons
        .map(
          (
            x,
          ) => `<li><b>${esc(x.title)}</b><span class="pts ${x.stop ? "stop" : ""}">${x.stop ? "Stop" : x.points ? "−" + x.points : "Note"}</span>
    <blockquote><span class="mono">${esc(FIELD[x.evidence.field] || x.evidence.field)}</span>“${esc(x.evidence.text)}”</blockquote></li>`,
        )
        .join("")}</ol>`
    : `<p>None of the label warnings apply to this profile.</p>`;
  const rows = [
    ...f.age_limits.map((a) => [
      a.action === "do_not_use" ? "Not for" : "Ask a doctor",
      `${a.min_years != null ? a.min_years + " to " : ""}under ${a.under_years}`,
    ]),
    ...f.max_daily_doses.map((m) => ["Max in 24 h", `${m.amount} ${esc(m.unit)}`]),
    ...f.allergens.map((a) => ["Allergen", esc(a.allergen)]),
  ]
    .map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`)
    .join("");
  let model = "";
  if (d.model) {
    const m = d.model;
    const miss = m.missing_on_label.length
      ? `<p class="err" style="color:var(--caution)">Products with these ingredients usually carry: ${m.missing_on_label.map((x) => esc(nice(x.warning_id))).join(", ")}. The rule extractor didn't find that wording here, so either the label omits it or words it differently. Check the box.</p>`
      : `<p style="margin-top:8px">The label's warnings match what the model expects for these ingredients.</p>`;
    model = `<section><h2>Model check</h2><div class="model"><p>Trained on ${m.trained_on.toLocaleString()} openFDA OTC labels to predict which warnings a product's ingredients and uses call for, without reading the warnings themselves.</p>
      <ul>${m.predicted
        .slice(0, 5)
        .map(
          (x) =>
            `<li>${esc(nice(x.warning_id))} <span class="mono" style="float:right">${Math.round(x.p * 100)}%</span><div class="bar2"><span style="width:${x.p * 100}%"></span></div></li>`,
        )
        .join("")}</ul>${miss}
      <p class="mono" style="margin-top:10px">Held-out F1 ${m.micro_f1} vs. rule labels · not clinically validated</p></div></section>`;
    const alts = m.neighbours
      .map((c) => ({ c, s: altScore(c) }))
      .filter((x) => x.s.score > s.score || (s.stop && !x.s.stop))
      .sort((a, b) => b.s.score - a.s.score)
      .slice(0, 3);
    if (alts.length)
      model += `<section><h2>Similar uses, fewer flags for you</h2>${alts.map(({ c, s: t }) => `<button class="alt" data-set="${esc(c.set_id)}"><span><b>${esc(c.brand)}</b><small>${esc(c.generic)} · ${Math.round(c.similarity * 100)}% similar use</small></span><span class="tag ${TIER[t.tier][0]}">${TIER[t.tier][1]}</span></button>`).join("")}
      <p class="mono" style="margin-top:8px">Nearest-neighbour match on label “uses” text</p></section>`;
  }
  $("out").innerHTML = `
    <div class="prod"><h1>${esc(d.brand)}</h1><p>${esc(d.generic)}<br>${esc(d.manufacturer)}${d.ndc ? " · NDC " + esc(d.ndc) : ""}</p></div>
    <div class="verdict ${cls}"><span class="word">${word}</span><span class="num">${s.stop ? "label stop" : s.score + " / 100"}</span><span class="sub">for ${esc(plabel().toLowerCase())}</span></div>
    <p class="proto">Prototype. Placeholder scoring, not medical advice. Ask a pharmacist.</p>
    <section><h2>Why</h2>${why}</section>
    ${rows ? `<section><h2>Read from the label</h2><dl class="facts">${rows}</dl></section>` : ""}
    ${model}
    <section><h2>Full label</h2>${d.sections.map((x) => `<details><summary>${esc(x.title)}</summary><p>${highlight(x)}</p></details>`).join("")}</section>
    <p class="foot">Source: openFDA drug label ${esc(d.set_id || "")}. Label text is shown exactly as published.</p>`;
}
function highlight(sec) {
  const spans = [];
  for (const group of ["warnings", "age_limits", "max_daily_doses", "allergens"])
    for (const x of current.facts[group])
      if (x.evidence.field === sec.field) spans.push(x.evidence.text);
  let html = esc(sec.text);
  for (const t of [...new Set(spans)].sort((a, b) => b.length - a.length)) {
    const e = esc(t);
    const i = html.indexOf(e);
    if (i >= 0 && !html.slice(0, i).endsWith("<mark>"))
      html = html.slice(0, i) + "<mark>" + e + "</mark>" + html.slice(i + e.length);
  }
  return html;
}
async function api(u) {
  const r = await fetch(u),
    j = await r.json();
  if (!r.ok || j.error) throw new Error(j.error || "Lookup failed");
  return j;
}
function show(v) {
  $("scan").classList.toggle("on", v === "scan");
  $("result").classList.toggle("on", v === "result");
  if (v === "result") $("result").scrollTop = 0;
}
async function load(u) {
  show("result");
  $("out").innerHTML = `<p class="loading">Reading the label…</p>`;
  try {
    current = await api(u);
    render();
  } catch (e) {
    $("out").innerHTML =
      `<p class="err">${esc(e.message)}</p><button class="done" onclick="show('scan')">Try another</button>`;
  }
}
const byCode = (c) => load("/api/barcode?code=" + encodeURIComponent(c));
const bySet = (id) => load("/api/label?set_id=" + encodeURIComponent(id));
$("form").onsubmit = async (e) => {
  e.preventDefault();
  const q = $("q").value.trim();
  if (!q) return;
  if (/^[\d\s-]{10,}$/.test(q)) return byCode(q);
  $("hits").innerHTML = `<p class="mono" style="margin-top:10px">Searching…</p>`;
  try {
    const hits = await api("/api/search?q=" + encodeURIComponent(q));
    $("hits").innerHTML = hits.length
      ? hits
          .slice(0, 5)
          .map(
            (h) =>
              `<button data-set="${esc(h.set_id)}">${esc(h.brand)}<small>${esc(h.generic)} · ${esc(h.manufacturer)}</small></button>`,
          )
          .join("")
      : `<p class="err">No OTC label found.</p>`;
  } catch (err) {
    $("hits").innerHTML = `<p class="err">${esc(err.message)}</p>`;
  }
};
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-set]");
  if (b) bySet(b.dataset.set);
  if (e.target.closest("[data-open-profile]")) openProfile(true);
});
$("back").onclick = () => {
  stopCam();
  show("scan");
};
api("/api/picks").then(
  (ps) =>
    ($("picks").innerHTML = ps
      .map((p) => `<button class="pick" data-code="${p.barcode}">${esc(p.name)}</button>`)
      .join("")),
);
$("picks").onclick = (e) => {
  const b = e.target.closest("[data-code]");
  if (b) byCode(b.dataset.code);
};

$("ages").innerHTML = AGES.map(
  (a, i) => `<button aria-pressed="${i === state.age}" data-age="${i}">${a[0]}</button>`,
).join("");
$("conds").innerHTML = CONDS.map(
  ([k, t]) => `<label class="tog"><span>${t}</span><input type="checkbox" value="${k}"></label>`,
).join("");
$("ages").onclick = (e) => {
  const b = e.target.closest("[data-age]");
  if (!b) return;
  state.age = +b.dataset.age;
  $("ages")
    .querySelectorAll("button")
    .forEach((x, i) => x.setAttribute("aria-pressed", i === state.age));
};
$("conds").onchange = (e) => {
  e.target.checked ? state.conds.add(e.target.value) : state.conds.delete(e.target.value);
};
function openProfile(on) {
  $("psheet").classList.toggle("on", on);
  $("scrim").classList.toggle("on", on);
  if (on) $("ages").querySelector("[aria-pressed=true]").focus();
  else {
    document.querySelectorAll(".plabel").forEach((e) => (e.textContent = plabel()));
    if (current && $("result").classList.contains("on")) render();
  }
}
$("done").onclick = $("scrim").onclick = () => openProfile(false);
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") openProfile(false);
});

let stream = null;
function stopCam() {
  if (stream) stream.getTracks().forEach((t) => t.stop());
  stream = null;
  $("video").style.display = "none";
}
$("scanbtn").onclick = async () => {
  if (!("BarcodeDetector" in window)) {
    $("hits").innerHTML =
      `<p class="err">Camera scanning needs Chrome on Android. Type the barcode digits instead.</p>`;
    return;
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    const v = $("video");
    v.srcObject = stream;
    v.style.display = "block";
    await v.play();
    const det = new BarcodeDetector({ formats: ["upc_a", "ean_13"] });
    const tick = async () => {
      if (!stream) return;
      const [hit] = await det.detect(v).catch(() => []);
      if (hit) {
        stopCam();
        byCode(hit.rawValue);
      } else requestAnimationFrame(tick);
    };
    tick();
  } catch {
    $("hits").innerHTML = `<p class="err">Couldn't open the camera.</p>`;
  }
};
