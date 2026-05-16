"""
generate_report.py — reads analysis.json, writes docs/index.html
"""
import json
from pathlib import Path
from datetime import datetime

ANALYSIS = Path("data/analysis.json")
OUT       = Path("docs/index.html")

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ethiopian Job Market — Live Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Sora:wght@300;400;600;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:      #0a0c10;
    --surface: #111318;
    --border:  #1e2230;
    --gold:    #c8a84b;
    --text:    #e8eaf0;
    --muted:   #5a6070;
    --accent1: #3ecfb2;
    --accent2: #e05c5c;
    --accent3: #7b8aff;
    --top1:    #c8a84b;
    --top2:    #8ea0b8;
    --top3:    #c8845a;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Sora', sans-serif; min-height: 100vh; }

  /* HEADER */
  header {
    border-bottom: 1px solid var(--border);
    padding: 2.5rem 3rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 1rem;
    background: linear-gradient(180deg, #0d1018 0%, transparent 100%);
  }
  .header-title { font-size: clamp(1.4rem, 4vw, 2.4rem); font-weight: 800; letter-spacing: -0.03em; line-height: 1.1; }
  .header-title span { color: var(--gold); }
  .header-meta { font-family: 'Space Mono', monospace; font-size: 0.7rem; color: var(--muted); text-align: right; line-height: 1.8; }
  .live-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: var(--accent1); margin-right: 5px; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }

  /* TABS */
  .tab-nav {
    display: flex;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
    padding: 0 2rem;
    overflow-x: auto;
  }
  .tab-btn {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 1rem 1.5rem;
    cursor: pointer;
    white-space: nowrap;
    transition: color 0.2s, border-color 0.2s;
  }
  .tab-btn:hover { color: var(--text); }
  .tab-btn.active { color: var(--gold); border-bottom-color: var(--gold); }
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }

  /* KPI ROW */
  .kpi-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1px;
    background: var(--border);
  }
  .kpi { background: var(--surface); padding: 1.6rem 1.8rem; display: flex; flex-direction: column; gap: 0.3rem; }
  .kpi-label { font-family: 'Space Mono', monospace; font-size: 0.62rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }
  .kpi-value { font-size: 2rem; font-weight: 800; color: var(--gold); letter-spacing: -0.04em; line-height: 1; }
  .kpi-sub { font-size: 0.7rem; color: var(--muted); }

  /* CHARTS GRID */
  .grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 1px;
    background: var(--border);
    padding: 1px;
  }
  .card { background: var(--surface); padding: 1.6rem; }
  .card.w4  { grid-column: span 4; }
  .card.w6  { grid-column: span 6; }
  .card.w8  { grid-column: span 8; }
  .card.w12 { grid-column: span 12; }
  @media (max-width: 900px) { .card.w4, .card.w6, .card.w8 { grid-column: span 12; } }
  .card-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .card-title::before { content: ''; display: inline-block; width: 3px; height: 12px; background: var(--gold); border-radius: 2px; }
  canvas { width: 100% !important; }

  /* TOP 3 PODIUM (overview) */
  .top3 { display: flex; flex-direction: column; gap: 0.75rem; }
  .top3-item {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.8rem 1rem;
    border-radius: 4px;
    background: rgba(255,255,255,0.03);
    border-left: 3px solid transparent;
  }
  .top3-item:nth-child(1) { border-color: var(--top1); }
  .top3-item:nth-child(2) { border-color: var(--top2); }
  .top3-item:nth-child(3) { border-color: var(--top3); }
  .rank { font-family: 'Space Mono', monospace; font-size: 0.65rem; color: var(--muted); min-width: 1.5rem; }
  .top3-name { flex: 1; font-size: 0.85rem; font-weight: 600; }
  .top3-count { font-family: 'Space Mono', monospace; font-size: 0.8rem; color: var(--gold); }
  .top3-bar-wrap { width: 100%; height: 3px; background: var(--border); border-radius: 2px; margin-top: 0.4rem; overflow: hidden; }
  .top3-bar { height: 100%; border-radius: 2px; }

  /* SALARY BOX */
  .salary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem; }
  .sal-item { text-align: center; }
  .sal-label { font-family: 'Space Mono', monospace; font-size: 0.6rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }
  .sal-val { font-size: 1.3rem; font-weight: 800; color: var(--accent1); letter-spacing: -0.03em; }

  /* TITLES TAB */
  .titles-podium {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: var(--border);
  }
  .podium-card { background: var(--surface); padding: 2.5rem 2rem; text-align: center; }
  .podium-card:nth-child(1) { border-top: 3px solid var(--top1); }
  .podium-card:nth-child(2) { border-top: 3px solid var(--top2); }
  .podium-card:nth-child(3) { border-top: 3px solid var(--top3); }
  .podium-rank { font-family: 'Space Mono', monospace; font-size: 0.6rem; color: var(--muted); margin-bottom: 0.6rem; letter-spacing: 0.1em; }
  .podium-title-text { font-size: 1.05rem; font-weight: 700; margin-bottom: 0.5rem; line-height: 1.3; }
  .podium-count { font-family: 'Space Mono', monospace; font-size: 2rem; font-weight: 800; letter-spacing: -0.04em; margin-bottom: 1rem; }
  .podium-card:nth-child(1) .podium-count { color: var(--top1); }
  .podium-card:nth-child(2) .podium-count { color: var(--top2); }
  .podium-card:nth-child(3) .podium-count { color: var(--top3); }
  .podium-salary {
    font-family: 'Space Mono', monospace;
    font-size: 0.68rem;
    color: var(--accent1);
    background: rgba(62,207,178,0.08);
    border-radius: 4px;
    padding: 0.45rem 0.8rem;
    display: inline-block;
    line-height: 1.6;
  }
  .podium-salary.no-data { color: var(--muted); background: rgba(255,255,255,0.03); }

  .titles-table-wrap { background: var(--surface); overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  thead tr { background: rgba(255,255,255,0.03); border-bottom: 2px solid var(--border); }
  th {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    padding: 1rem 1.2rem;
    text-align: left;
    white-space: nowrap;
  }
  td { padding: 0.8rem 1.2rem; border-bottom: 1px solid var(--border); vertical-align: middle; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,0.025); }
  .td-rank { font-family: 'Space Mono', monospace; font-size: 0.62rem; color: var(--muted); }
  .td-count { font-family: 'Space Mono', monospace; font-weight: 700; color: var(--gold); }
  .td-salary { font-family: 'Space Mono', monospace; font-size: 0.72rem; color: var(--accent1); }
  .td-salary.none { color: var(--muted); font-style: italic; font-size: 0.7rem; }
  .mini-bar-wrap { width: 100px; height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; }
  .mini-bar { height: 100%; background: var(--gold); border-radius: 2px; }
  @media (max-width: 700px) {
    .titles-podium { grid-template-columns: 1fr; }
    .hide-mobile { display: none; }
  }

  /* FOOTER */
  footer {
    padding: 2rem 3rem;
    font-family: 'Space Mono', monospace;
    font-size: 0.62rem;
    color: var(--muted);
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
</style>
</head>
<body>

<header>
  <div>
    <div class="header-title">Current Job Market in<br><span>Ethiopia 🇪🇹</span></div>
  </div>
  <div class="header-meta">
    <span class="live-dot"></span>AUTO-UPDATED<br>
    SCRAPED: {last_updated}<br>
    PERIOD: {date_start} – {date_end}
  </div>
</header>

<!-- TAB NAV -->
<nav class="tab-nav">
  <button class="tab-btn active" onclick="switchTab('overview', this)">Overview</button>
  <button class="tab-btn" onclick="switchTab('titles', this)">Job Titles Ranking</button>
</nav>

<!-- ═══════════════════════════ TAB: OVERVIEW ════════════════════════════════ -->
<div class="tab-panel active" id="tab-overview">

  <div class="kpi-row">
    <div class="kpi">
      <span class="kpi-label">Total Listings</span>
      <span class="kpi-value">{total_jobs}</span>
    </div>
    <div class="kpi">
      <span class="kpi-label">Companies Hiring</span>
      <span class="kpi-value">{total_companies}</span>
    </div>
    <div class="kpi">
      <span class="kpi-label">Industries</span>
      <span class="kpi-value">{total_industries}</span>
    </div>
    <div class="kpi">
      <span class="kpi-label">Remote Jobs</span>
      <span class="kpi-value">{remote_jobs}</span>
    </div>
    <div class="kpi">
      <span class="kpi-label">With Salary Info</span>
      <span class="kpi-value">{jobs_with_salary}</span>
      <span class="kpi-sub">of {total_jobs} listings</span>
    </div>
  </div>

  <div class="grid">
    <div class="card w12">
      <div class="card-title">Job Postings Per Week</div>
      <canvas id="weeklyChart" height="80"></canvas>
    </div>
    <div class="card w4">
      <div class="card-title">Top 3 Industries</div>
      <div class="top3" id="top3Container"></div>
    </div>
    <div class="card w8">
      <div class="card-title">Jobs by Industry</div>
      <canvas id="industryChart" height="200"></canvas>
    </div>
    <div class="card w4">
      <div class="card-title">Experience Level</div>
      <canvas id="expChart" height="220"></canvas>
    </div>
    <div class="card w4">
      <div class="card-title">Work Mode</div>
      <canvas id="modeChart" height="220"></canvas>
    </div>
    <div class="card w4">
      <div class="card-title">Contract Type</div>
      <canvas id="contractChart" height="220"></canvas>
    </div>
    <div class="card w8">
      <div class="card-title">Top In-Demand Skills</div>
      <canvas id="skillsChart" height="220"></canvas>
    </div>
    <div class="card w4">
      <div class="card-title">Education Required</div>
      <canvas id="eduChart" height="220"></canvas>
    </div>
    <div class="card w8">
      <div class="card-title">Top Hiring Companies (excl. Private Client)</div>
      <canvas id="companiesChart" height="180"></canvas>
    </div>
    <div class="card w4">
      <div class="card-title">Salary Range (ETB)</div>
      <div class="salary-grid" id="salaryBox"></div>
    </div>
    <div class="card w4">
      <div class="card-title">Gender Preference</div>
      <canvas id="genderChart" height="220"></canvas>
    </div>
  </div>

</div><!-- end tab-overview -->

<!-- ═══════════════════════════ TAB: TITLES RANKING ═════════════════════════ -->
<div class="tab-panel" id="tab-titles">

  <!-- Month selector -->
  <div style="background:var(--surface);padding:1.2rem 2rem;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:1rem;">
    <span style="font-family:'Space Mono',monospace;font-size:0.65rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;">Viewing Month</span>
    <select id="monthSelect" onchange="renderTitles(this.value)"
      style="background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:4px;
             padding:0.4rem 0.8rem;font-family:'Space Mono',monospace;font-size:0.7rem;cursor:pointer;">
    </select>
  </div>

  <!-- Top 3 podium -->
  <div class="titles-podium" id="titlesPodium"></div>

  <!-- Rest of titles: #4 onwards in a table -->
  <div class="titles-table-wrap">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Job Title</th>
          <th>Listings</th>
          <th>Salary Range (ETB)</th>
          <th class="hide-mobile">Volume</th>
        </tr>
      </thead>
      <tbody id="titlesTableBody"></tbody>
    </table>
  </div>

</div><!-- end tab-titles -->

<footer>
  <span>Ethiopian Job Market Dashboard · Powered by afriworket.com scraper</span>
  <span>Auto-generated {generated_at} · github.com/Imr-u/Job_market</span>
</footer>

<script>
const D = __ANALYSIS_JSON__;

// ── Tab switching ─────────────────────────────────────────────────────────────
function switchTab(id, btn) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + id).classList.add('active');
  btn.classList.add('active');
}

// ── Palette ───────────────────────────────────────────────────────────────────
const gold    = '#c8a84b';
const accent1 = '#3ecfb2';
const accent2 = '#e05c5c';
const accent3 = '#7b8aff';
const muted   = '#5a6070';
const border  = '#1e2230';
const PALETTE = [
  '#c8a84b','#3ecfb2','#7b8aff','#e05c5c','#e07b5c',
  '#5ce0b8','#b87bff','#ff9f7b','#7bcce0','#e0c07b',
  '#5c7be0','#c05ce0','#7be07b','#e05c9f','#9fe05c',
];
const baseOpts = {
  responsive: true,
  plugins: {
    legend: { labels: { color: '#8090a0', font: { family: 'Space Mono', size: 10 } } },
    tooltip: { backgroundColor: '#1a1e28', titleColor: '#c8a84b', bodyColor: '#8090a0' },
  },
};

// ── Weekly trend ──────────────────────────────────────────────────────────────
new Chart(document.getElementById('weeklyChart'), {
  type: 'line',
  data: {
    labels: D.weekly.labels,
    datasets: [{
      label: 'Postings',
      data: D.weekly.values,
      borderColor: gold,
      backgroundColor: gold + '22',
      pointBackgroundColor: gold,
      pointRadius: 4,
      pointHoverRadius: 6,
      fill: true,
      tension: 0.4,
    }],
  },

// ── Industry bar ──────────────────────────────────────────────────────────────
new Chart(document.getElementById('industryChart'), {
  type: 'bar',
  data: { labels: D.industry.labels, datasets: [{ label: 'Jobs', data: D.industry.values, backgroundColor: PALETTE, borderRadius: 3 }] },
  options: { ...baseOpts, indexAxis: 'y', scales: {
    x: { ticks: { color: muted, font: { family: 'Space Mono', size: 9 } }, grid: { color: border } },
    y: { ticks: { color: '#c0cad8', font: { size: 10 } }, grid: { color: 'transparent' } },
  }, plugins: { ...baseOpts.plugins, legend: { display: false } } },
});

// ── Top 3 industries podium ───────────────────────────────────────────────────
const top3El = document.getElementById('top3Container');
const top3Colors = ['#c8a84b','#8ea0b8','#c8845a'];
const maxVal = D.industry.values[0] || 1;
D.industry.top3.forEach((name, i) => {
  const idx = D.industry.labels.indexOf(name);
  const val = D.industry.values[idx];
  const pct = Math.round((val / maxVal) * 100);
  top3El.innerHTML += `
    <div class="top3-item">
      <span class="rank">#${i+1}</span>
      <div style="flex:1">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span class="top3-name">${name}</span>
          <span class="top3-count">${val}</span>
        </div>
        <div class="top3-bar-wrap">
          <div class="top3-bar" style="width:${pct}%;background:${top3Colors[i]}"></div>
        </div>
      </div>
    </div>`;
});

// ── Donut helper ──────────────────────────────────────────────────────────────
function donut(id, labels, values, colors) {
  new Chart(document.getElementById(id), {
    type: 'doughnut',
    data: { labels, datasets: [{ data: values, backgroundColor: colors || PALETTE, borderWidth: 0 }] },
    options: { ...baseOpts, cutout: '65%', plugins: { ...baseOpts.plugins,
      legend: { position: 'bottom', labels: { color: '#8090a0', font: { family: 'Space Mono', size: 9 }, boxWidth: 10, padding: 10 } }
    }},
  });
}
donut('expChart',      D.experience.labels,    D.experience.values);
donut('modeChart',     D.work_mode.labels,     D.work_mode.values,     [accent1, gold, accent3, muted]);
donut('contractChart', D.contract_type.labels, D.contract_type.values, [accent3, gold, accent1, accent2]);
donut('genderChart',   D.gender.labels,        D.gender.values,        [accent1, accent2, gold]);
donut('eduChart',      D.education.labels,     D.education.values);

// ── Skills bar ────────────────────────────────────────────────────────────────
new Chart(document.getElementById('skillsChart'), {
  type: 'bar',
  data: { labels: D.skills.labels, datasets: [{ label: 'Frequency', data: D.skills.values, backgroundColor: accent3+'cc', borderRadius: 3 }] },
  options: { ...baseOpts, indexAxis: 'y', scales: {
    x: { ticks: { color: muted, font: { family: 'Space Mono', size: 9 } }, grid: { color: border } },
    y: { ticks: { color: '#c0cad8', font: { size: 10 } }, grid: { color: 'transparent' } },
  }, plugins: { ...baseOpts.plugins, legend: { display: false } } },
});

// ── Companies bar ─────────────────────────────────────────────────────────────
new Chart(document.getElementById('companiesChart'), {
  type: 'bar',
  data: { labels: D.companies.labels, datasets: [{ label: 'Listings', data: D.companies.values, backgroundColor: accent2+'bb', borderRadius: 3 }] },
  options: { ...baseOpts, indexAxis: 'y', scales: {
    x: { ticks: { color: muted, font: { family: 'Space Mono', size: 9 } }, grid: { color: border } },
    y: { ticks: { color: '#c0cad8', font: { size: 10 } }, grid: { color: 'transparent' } },
  }, plugins: { ...baseOpts.plugins, legend: { display: false } } },
});

// ── Salary box ────────────────────────────────────────────────────────────────
const sb = document.getElementById('salaryBox');
if (D.salary) {
  const fmt = n => n.toLocaleString() + ' ETB';
  sb.innerHTML = `
    <div class="sal-item"><div class="sal-label">Median</div><div class="sal-val">${fmt(D.salary.median)}</div></div>
    <div class="sal-item"><div class="sal-label">Mean</div><div class="sal-val">${fmt(D.salary.mean)}</div></div>
    <div class="sal-item"><div class="sal-label">Min</div><div class="sal-val" style="color:var(--accent2)">${fmt(D.salary.min)}</div></div>
    <div class="sal-item"><div class="sal-label">Max</div><div class="sal-val" style="color:var(--gold)">${fmt(D.salary.max)}</div></div>`;
} else {
  sb.innerHTML = '<p style="color:var(--muted);font-size:0.8rem;padding:1rem 0;grid-column:span 2">No structured salary data available.</p>';
}

// ── TITLES RANKING TAB ────────────────────────────────────────────────────────
const podiumColors = ['#c8a84b', '#8ea0b8', '#c8845a'];

function fmtSalary(t) {
  if (t.salary_min === null) return null;
  const fmt = n => (n/1000).toFixed(0) + 'K';
  if (t.salary_min === t.salary_max) return fmt(t.salary_min) + ' ETB';
  return fmt(t.salary_min) + ' – ' + fmt(t.salary_max) + ' ETB';
}

function renderTitles(month) {
  const titles = D.monthly_titles[month] || [];
  const maxCount = titles[0]?.count || 1;

  // Podium
  const podium = document.getElementById('titlesPodium');
  podium.innerHTML = '';
  titles.slice(0, 3).forEach((t, i) => {
    const sal = fmtSalary(t);
    const salHtml = sal
      ? `<div class="podium-salary">${sal}<br><span style="font-size:0.6rem;opacity:0.7">SALARY RANGE</span></div>`
      : `<div class="podium-salary no-data">No salary data</div>`;
    podium.innerHTML += `
      <div class="podium-card">
        <div class="podium-rank"># ${t.rank} MOST LISTED</div>
        <div class="podium-title-text">${t.title}</div>
        <div class="podium-count">${t.count}</div>
        ${salHtml}
      </div>`;
  });

  // Table
  const tbody = document.getElementById('titlesTableBody');
  tbody.innerHTML = '';
  titles.slice(3).forEach(t => {
    const sal = fmtSalary(t);
    const pct = Math.round((t.count / maxCount) * 100);
    tbody.innerHTML += `
      <tr>
        <td class="td-rank">${t.rank}</td>
        <td>${t.title}</td>
        <td class="td-count">${t.count}</td>
        <td class="${sal ? 'td-salary' : 'td-salary none'}">${sal || 'not listed'}</td>
        <td class="hide-mobile">
          <div class="mini-bar-wrap"><div class="mini-bar" style="width:${pct}%"></div></div>
        </td>
      </tr>`;
  });
}

// Populate month selector and render default
const monthSelect = document.getElementById('monthSelect');
D.months_available.forEach((m, i) => {
  const opt = document.createElement('option');
  opt.value = m;
  opt.text = m;
  if (i === 0) opt.selected = true;
  monthSelect.appendChild(opt);
});
renderTitles(D.months_available[0]);
</script>
</body>
</html>"""

def generate(analysis: dict) -> None:
    kpi = analysis["kpi"]
    html = TEMPLATE.replace("__ANALYSIS_JSON__", json.dumps(analysis, ensure_ascii=False))
    html = html.replace("{last_updated}",     kpi["last_updated"])
    html = html.replace("{date_start}",       kpi["date_range_start"])
    html = html.replace("{date_end}",         kpi["date_range_end"])
    html = html.replace("{total_jobs}",       str(kpi["total_jobs"]))
    html = html.replace("{total_companies}",  str(kpi["total_companies"]))
    html = html.replace("{total_industries}", str(kpi["total_industries"]))
    html = html.replace("{remote_jobs}",      str(kpi["remote_jobs"]))
    html = html.replace("{jobs_with_salary}", str(kpi["jobs_with_salary"]))
    html = html.replace("{generated_at}",     datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"✓ Report written → {OUT}")

if __name__ == "__main__":
    analysis = json.loads(ANALYSIS.read_text())
    generate(analysis) 