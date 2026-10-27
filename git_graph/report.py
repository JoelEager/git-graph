"""Render the collected commit data as a self-contained interactive HTML report."""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from git_graph.commits import Commit

_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>git-graph</title>
<style>
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body { font-family: "Segoe UI", system-ui, sans-serif; margin: 0;
         padding: 1.5rem 2rem; background: #fafafa; color: #222; }
  h1 { font-size: 1.4rem; margin: 0 0 .25rem; }
  h2 { font-size: 1rem; margin: 0; }
  .meta { color: #666; font-size: .85rem; margin-bottom: 1rem; }
  .controls { display: flex; gap: 2rem; align-items: center; flex-wrap: wrap;
              background: #fff; border: 1px solid #ddd; border-radius: 6px;
              padding: .6rem 1rem; margin-bottom: 1.25rem; font-size: .9rem; }
  .controls label { margin-right: .4rem; color: #555; }
  select { font: inherit; padding: .15rem .3rem; }
  section.chart { background: #fff; border: 1px solid #ddd; border-radius: 6px;
                  padding: 1rem; margin-bottom: 1.25rem; }
  .chart-head { display: flex; gap: 1rem; align-items: center; margin-bottom: .5rem; }
  .chart-head label { font-size: .85rem; color: #555; }
  svg { display: block; width: 100%; }
  .legend { display: flex; flex-wrap: wrap; gap: .4rem 1.1rem; margin-top: .6rem;
            font-size: .8rem; }
  .legend span { display: inline-flex; align-items: center; gap: .35rem; }
  .legend i { width: .8rem; height: .8rem; border-radius: 2px; display: inline-block; }
  .empty { color: #888; font-style: italic; padding: 2rem; text-align: center; }
</style>
</head>
<body>
<h1>git-graph</h1>
<div class="meta" id="summary"></div>
<div class="controls">
  <span><label for="res">Resolution</label>
    <select id="res">
      <option value="week">Week</option>
      <option value="month" selected>Month</option>
      <option value="year">Year</option>
    </select></span>
  <span><label for="stack">Stack bars by</label>
    <select id="stack">
      <option value="repo" selected>Repo</option>
      <option value="author">Author</option>
    </select></span>
</div>
<section class="chart">
  <div class="chart-head"><h2>Chart 1</h2>
    <span><label for="metric0">Metric</label>
      <select id="metric0">
        <option value="commits" selected>Commits</option>
        <option value="lines">Lines changed</option>
      </select></span></div>
  <div id="chart0"></div>
  <div id="legend0" class="legend"></div>
</section>
<section class="chart">
  <div class="chart-head"><h2>Chart 2</h2>
    <span><label for="metric1">Metric</label>
      <select id="metric1">
        <option value="commits">Commits</option>
        <option value="lines" selected>Lines changed</option>
      </select></span></div>
  <div id="chart1"></div>
  <div id="legend1" class="legend"></div>
</section>
<script>
const DATA = __DATA__;
const NS = "http://www.w3.org/2000/svg";
const PALETTE = ["#4e79a7","#f28e2b","#e15759","#76b7b2","#59a14f","#edc948",
                 "#b07aa1","#ff9da7","#9c755f","#bab0ac","#8cd17d","#86bcb6"];
const TOP_N = 10;

const pad = n => String(n).padStart(2, "0");

function bucketStart(sec, res) {
  const d = new Date(sec * 1000);
  if (res === "year")  return new Date(d.getFullYear(), 0, 1).getTime() / 1000;
  if (res === "month") return new Date(d.getFullYear(), d.getMonth(), 1).getTime() / 1000;
  const day = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  day.setDate(day.getDate() - ((day.getDay() + 6) % 7)); // ISO week starts Monday
  return day.getTime() / 1000;
}

function bucketLabel(sec, res) {
  const d = new Date(sec * 1000);
  if (res === "year")  return String(d.getFullYear());
  if (res === "month") return d.getFullYear() + "-" + pad(d.getMonth() + 1);
  return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
}

function metricValue(c, metric) {
  return metric === "lines" ? c.p + c.m : 1;
}

function aggregate(res, stackBy, metric) {
  const buckets = new Map();   // startSec -> Map<series, value>
  const totals = new Map();    // series -> total
  for (const c of DATA.commits) {
    const key = stackBy === "author" ? c.a : DATA.repos[c.r];
    const b = bucketStart(c.t, res);
    if (!buckets.has(b)) buckets.set(b, new Map());
    const m = buckets.get(b);
    const v = metricValue(c, metric);
    m.set(key, (m.get(key) || 0) + v);
    totals.set(key, (totals.get(key) || 0) + v);
  }
  const ordered = [...totals.entries()].sort((x, y) => y[1] - x[1]).map(e => e[0]);
  const series = ordered.slice(0, TOP_N);
  if (ordered.length > TOP_N) series.push("Other");
  const rows = [...buckets.keys()].sort((a, b) => a - b).map(b => {
    const m = buckets.get(b);
    const cells = series.map(s => {
      if (s === "Other") {
        let v = 0;
        for (const [k, n] of m) if (!series.includes(k)) v += n;
        return v;
      }
      return m.get(s) || 0;
    });
    return { start: b, label: bucketLabel(b, res), cells,
             total: cells.reduce((a, x) => a + x, 0) };
  });
  return { series, rows };
}

function niceMax(v) {
  if (v <= 0) return 1;
  const pow = Math.pow(10, Math.floor(Math.log10(v)));
  for (const f of [1, 2, 2.5, 5, 10]) if (v <= f * pow) return f * pow;
  return 10 * pow;
}

function el(name, attrs) {
  const e = document.createElementNS(NS, name);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  return e;
}

function textEl(x, y, str, attrs) {
  const t = el("text", Object.assign({ x, y, "font-size": 11, fill: "#555" }, attrs));
  t.textContent = str;
  return t;
}

function fmt(n) {
  if (n >= 1e6) return (n / 1e6).toFixed(n % 1e6 ? 1 : 0) + "M";
  if (n >= 1e4) return (n / 1e3).toFixed(n % 1e3 ? 1 : 0) + "k";
  return String(Math.round(n * 100) / 100);
}

function render(slot, legendSlot, res, stackBy, metric) {
  const { series, rows } = aggregate(res, stackBy, metric);
  const host = document.getElementById(slot);
  const legend = document.getElementById(legendSlot);
  host.innerHTML = ""; legend.innerHTML = "";
  if (!rows.length) {
    host.innerHTML = '<div class="empty">No commits found</div>';
    return;
  }
  const W = Math.max(host.clientWidth, 320), H = 300;
  const m = { l: 56, r: 12, t: 10, b: 46 };
  const pw = W - m.l - m.r, ph = H - m.t - m.b;
  const yMax = niceMax(Math.max(...rows.map(r => r.total)));
  const bw = Math.max((pw / rows.length) * 0.72, 1.5);
  const svg = el("svg", { viewBox: `0 0 ${W} ${H}` });

  for (let i = 0; i <= 4; i++) {
    const v = yMax * i / 4, y = m.t + ph - ph * i / 4;
    svg.appendChild(el("line", { x1: m.l, x2: W - m.r, y1: y, y2: y,
                                 stroke: "#e6e6e6" }));
    svg.appendChild(textEl(m.l - 6, y + 4, fmt(v), { "text-anchor": "end" }));
  }
  const step = Math.ceil(rows.length / 12);
  rows.forEach((row, i) => {
    const x = m.l + pw * (i + 0.5) / rows.length;
    let y = m.t + ph;
    series.forEach((s, si) => {
      const v = row.cells[si];
      if (!v) return;
      const h = ph * v / yMax;
      y -= h;
      const r = el("rect", { x: x - bw / 2, y, width: bw, height: h,
                             fill: PALETTE[si % PALETTE.length] });
      const t = document.createElementNS(NS, "title");
      t.textContent = `${row.label}  ·  ${s}: ${fmt(v)}`;
      r.appendChild(t);
      svg.appendChild(r);
    });
    if (i % step === 0)
      svg.appendChild(textEl(x + 4, m.t + ph + 12, row.label,
        { transform: `rotate(-35 ${x + 4} ${m.t + ph + 12})` }));
  });
  svg.appendChild(el("line", { x1: m.l, x2: W - m.r, y1: m.t + ph, y2: m.t + ph,
                               stroke: "#999" }));
  host.appendChild(svg);
  series.forEach((s, i) => {
    const item = document.createElement("span");
    const sw = document.createElement("i");
    sw.style.background = PALETTE[i % PALETTE.length];
    item.appendChild(sw);
    item.appendChild(document.createTextNode(s));
    legend.appendChild(item);
  });
}

function refresh() {
  const res = document.getElementById("res").value;
  const stackBy = document.getElementById("stack").value;
  for (const i of [0, 1])
    render("chart" + i, "legend" + i, res, stackBy,
           document.getElementById("metric" + i).value);
}

const times = DATA.commits.map(c => c.t);
const range = times.length
  ? bucketLabel(Math.min(...times), "week") + " — " + bucketLabel(Math.max(...times), "week")
  : "n/a";
document.getElementById("summary").textContent =
  `${DATA.repos.length} repos · ${DATA.commits.length} commits · ${range} · ` +
  `scanned ${DATA.root} · generated ${DATA.generated}`;

for (const id of ["res", "stack", "metric0", "metric1"])
  document.getElementById(id).addEventListener("change", refresh);
let rt;
window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(refresh, 150); });
refresh();
</script>
</body>
</html>
"""


def build_html(commits: List[Commit], repos: List[Path], root: Path) -> str:
    resolved = [str(p.resolve()) for p in repos]
    index = {p: i for i, p in enumerate(resolved)}
    names = [Path(p).name for p in resolved]
    # Disambiguate repos that share a directory name.
    dupes = {n for n in names if names.count(n) > 1}
    display = [
        str(Path(p).parent.name + "/" + Path(p).name) if n in dupes else n
        for p, n in zip(resolved, names)
    ]
    payload = {
        "root": str(root),
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "repos": display,
        "commits": [
            {
                "r": index[c.repo],
                "a": c.author,
                "t": round(c.timestamp),
                "p": c.added,
                "m": c.deleted,
            }
            for c in commits
        ],
    }
    data = json.dumps(payload, separators=(",", ":"))
    return _PAGE.replace("__DATA__", data)


def write_report(html: str, output: Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output
