"""Render the daily review page: one self-contained HTML file you open in your browser."""
import json
from datetime import datetime, timezone

MANUAL_LINKS = [
    ("Your current employer first",
     "Ask Comprehensive Logistics about staying on as a contractor from Amman before you move. "
     "It's your highest-odds lead.", ""),
    ("LinkedIn: remote data jobs open to Jordan",
     "LinkedIn's location filter set to Jordan + Remote shows postings that accept Jordan-based applicants. "
     "Turn on a daily job alert for it.",
     "https://www.linkedin.com/jobs/search/?keywords=data%20engineer&location=Jordan&f_WT=2&sortBy=DD"),
    ("LinkedIn: Power BI / BI remote, Jordan",
     "Same filter, BI-focused.",
     "https://www.linkedin.com/jobs/search/?keywords=power%20bi&location=Jordan&f_WT=2&sortBy=DD"),
    ("Bayt.com: data jobs in Jordan",
     "The biggest Middle East job board. Good for on-site Jordan and remote Gulf roles.",
     "https://www.bayt.com/en/jordan/jobs/data-engineer-jobs/"),
    ("Wellfound (startups): remote, worldwide",
     "Startup jobs; filter to Remote and 'open to anywhere'.",
     "https://wellfound.com/role/r/data-engineer"),
    ("Talent networks that place people abroad at US rates (free to join)",
     "Arc.dev, Turing, Andela, Toptal, Lemon.io and X-Team vet you once, then match you to US/EU contracts. "
     "Their interviews take time, so start now.",
     "https://arc.dev/remote-jobs"),
    ("Microsoft partners (Power Platform / Fabric consulting)",
     "Consultancies that sell Power Platform and Azure work often hire contractors in any country. "
     "Search 'Power Platform consultant remote contract'.",
     "https://www.linkedin.com/jobs/search/?keywords=power%20platform%20consultant%20contract&f_WT=2&sortBy=DD"),
]

CSS = r"""
:root{--bg:#f6f7f9;--card:#fff;--ink:#14171c;--muted:#5d6673;--line:#e3e6ea;--accent:#2f5bd3;
--ok:#1f7a4d;--ok-bg:#e3f4ea;--likely:#126b78;--likely-bg:#e0f2f4;--check:#8a5a00;--check-bg:#fbf0d9;
--chip:#eef1f5;--gap:#9b2c2c;--gap-bg:#fbe7e7;--new:#6b3fd1;--code:#f2f4f7}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f1115;--card:#171a20;--ink:#e7e9ee;--muted:#9aa3af;--line:#2a2f38;
--accent:#7aa2ff;--ok:#5fd39a;--ok-bg:#163126;--likely:#5cc8d6;--likely-bg:#12303a;--check:#f2c063;--check-bg:#352a12;
--chip:#232832;--gap:#ff9b9b;--gap-bg:#3a1c1f;--new:#b59bff;--code:#1d2129}}
:root[data-theme="dark"]{--bg:#0f1115;--card:#171a20;--ink:#e7e9ee;--muted:#9aa3af;--line:#2a2f38;
--accent:#7aa2ff;--ok:#5fd39a;--ok-bg:#163126;--likely:#5cc8d6;--likely-bg:#12303a;--check:#f2c063;--check-bg:#352a12;
--chip:#232832;--gap:#ff9b9b;--gap-bg:#3a1c1f;--new:#b59bff;--code:#1d2129}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1000px;margin:0 auto;padding:24px 16px 80px}
h1{font-size:24px;margin:0 0 4px}.sub{color:var(--muted);margin:0 0 18px}
.stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(105px,1fr));gap:10px;margin-bottom:16px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px}
.stat b{display:block;font-size:22px}.stat span{color:var(--muted);font-size:13px}
details.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin-bottom:16px}
details.panel summary{cursor:pointer;font-weight:600}
.manual{display:grid;gap:10px;margin-top:10px}.manual div{border-top:1px solid var(--line);padding-top:10px}
.manual a{font-weight:600}.manual p{margin:2px 0 0;color:var(--muted);font-size:14px}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);padding:10px 0;display:flex;flex-wrap:wrap;gap:8px;align-items:center;border-bottom:1px solid var(--line);margin-bottom:14px}
.bar input[type=search]{flex:1;min-width:180px;padding:8px 10px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink)}
.bar select,.bar label{font-size:14px}.bar select{padding:7px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink)}
.tog{display:inline-flex;align-items:center;gap:4px;background:var(--card);border:1px solid var(--line);border-radius:999px;padding:5px 10px;cursor:pointer;user-select:none}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:12px}
.card.done{opacity:.6}
.top{display:flex;gap:12px;justify-content:space-between;align-items:flex-start;flex-wrap:wrap}
.title{font-size:17px;font-weight:650;margin:0}.title a{color:inherit;text-decoration:none}.title a:hover{text-decoration:underline}
.meta{color:var(--muted);font-size:14px;margin-top:2px}
.top>div:first-child{min-width:0}.title{overflow-wrap:anywhere}
.score{font-weight:700;font-size:20px;text-align:right}.score small{display:block;font-size:12px;color:var(--muted);font-weight:500}
.badge{display:inline-block;font-size:12px;font-weight:650;border-radius:6px;padding:2px 8px;margin-right:6px}
.ELIGIBLE{color:var(--ok);background:var(--ok-bg)}.LIKELY{color:var(--likely);background:var(--likely-bg)}.CHECK{color:var(--check);background:var(--check-bg)}
.NEW{color:var(--new);border:1px solid var(--new)}
.why{margin:10px 0 6px;font-size:14px}.ev{color:var(--muted);font-size:13px;font-style:italic;overflow-wrap:anywhere}
.chips{display:flex;flex-wrap:wrap;gap:5px;margin:8px 0}.chip{font-size:12px;background:var(--chip);border-radius:6px;padding:2px 7px}
.chip.gap{background:var(--gap-bg);color:var(--gap)}
.actions{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;align-items:center}
button,.btn{font:inherit;font-size:13px;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:6px 10px;cursor:pointer;text-decoration:none;display:inline-block}
.btn.primary{background:var(--accent);border-color:var(--accent);color:#fff}
button.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
details.more{margin-top:12px;border-top:1px solid var(--line);padding-top:10px}
details.more summary{cursor:pointer;font-weight:600;font-size:14px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:10px}@media(max-width:720px){.grid{grid-template-columns:1fr}}
h4{margin:0 0 6px;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
.grid>div{min-width:0}
.links a{display:block;font-size:14px;margin:3px 0;overflow-wrap:anywhere}
.row{display:flex;gap:6px;margin:6px 0}.row input{flex:1;min-width:0;padding:7px 9px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--ink);font:inherit;font-size:14px}
.guess{overflow-wrap:anywhere;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:13px;display:flex;justify-content:space-between;gap:8px;padding:3px 0}
.hint{color:var(--muted);font-size:12px}
textarea{width:100%;min-height:260px;padding:10px;border-radius:8px;border:1px solid var(--line);background:var(--code);color:var(--ink);font:13px/1.5 ui-monospace,Menlo,Consolas,monospace}
textarea.note{min-height:90px}
.empty{text-align:center;color:var(--muted);padding:40px}
.warn{background:var(--check-bg);color:var(--check);border-radius:10px;padding:10px 14px;margin-bottom:12px;font-size:14px}
"""

JS = r"""
const DATA = JSON.parse(document.getElementById('data').textContent);
const KEY = 'ajh-state-v1';
let state = {};
try { state = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} };
const st = k => (state[k] = state[k] || {});
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ago = iso => { if (!iso) return 'date unknown'; const d = (Date.now() - new Date(iso)) / 864e5;
  return d < 1 ? 'today' : d < 2 ? 'yesterday' : Math.floor(d) + ' days ago'; };
const LABEL = {ELIGIBLE: 'Eligible from Jordan', LIKELY: 'Likely eligible', CHECK: 'Check eligibility'};

function guesses(first, last, domain) {
  first = (first || '').toLowerCase().replace(/[^a-z]/g, ''); last = (last || '').toLowerCase().replace(/[^a-z]/g, '');
  if (!first || !domain) return [];
  const g = [`${first}@${domain}`];
  if (last) g.unshift(`${first}.${last}@${domain}`), g.push(`${first[0]}${last}@${domain}`, `${first}${last[0]}@${domain}`, `${first}${last}@${domain}`, `${first}_${last}@${domain}`);
  return g;
}
function fill(text, first) { return text.split('{FIRST_NAME}').join(first || 'there'); }
function copy(text, btn) {
  const done = () => { const o = btn.textContent; btn.textContent = 'Copied ✓'; setTimeout(() => btn.textContent = o, 1200); };
  if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, () => fallback());
  else fallback();
  function fallback() { const t = document.createElement('textarea'); t.value = text; document.body.appendChild(t); t.select();
    document.execCommand('copy'); t.remove(); done(); }
}

function card(j, i) {
  const s = st(j.key);
  const c = j.contacts;
  const el = document.createElement('div');
  el.className = 'card' + (s.status && s.status !== 'todo' ? ' done' : '');
  el.dataset.i = i;
  const found = [
    ...c.people.map(p => `<div>👤 ${esc(p)} <span class="hint">(named in posting)</span></div>`),
    ...c.emails.map(e => `<div>✉️ <a href="mailto:${esc(e.email)}">${esc(e.email)}</a> <span class="hint">(${esc(e.kind)}, in posting)</span></div>`)
  ].join('') || '<div class="hint">The posting doesn\'t name anyone. Use the searches below.</div>';
  el.innerHTML = `
  <div class="top">
    <div style="flex:1;min-width:240px">
      <div><span class="badge ${j.eligibility}">${LABEL[j.eligibility] || j.eligibility}</span>${j.is_new ? '<span class="badge NEW">NEW</span>' : ''}</div>
      <h3 class="title"><a href="${esc(j.url)}" target="_blank" rel="noopener">${esc(j.title)}</a></h3>
      <div class="meta">${esc(j.company)} · ${esc(j.location || '—')} · ${ago(j.posted)} · via ${esc(j.source)}</div>
      <div class="meta">💵 ${esc(j.salary_note)}${j.job_type ? ' · ' + esc(j.job_type) : ''}</div>
    </div>
    <div class="score">${j.fit_score}<small>fit / 100</small></div>
  </div>
  <div class="why"><b>Why:</b> ${esc(j.eligibility_reason)}${j.eligibility_evidence ? `<div class="ev">${esc(j.eligibility_evidence)}</div>` : ''}</div>
  <div class="chips">${j.matched_skills.map(s => `<span class="chip">${esc(s)}</span>`).join('')}${j.gaps.map(s => `<span class="chip gap" title="Asked for in the posting, not on your resume">gap: ${esc(s)}</span>`).join('')}</div>
  <div class="actions">
    <a class="btn primary" href="${esc(j.url)}" target="_blank" rel="noopener">Open posting ↗</a>
    ${['todo','applied','emailed','skip'].map(x => `<button data-status="${x}" class="${(s.status||'todo')===x?'on':''}">${{todo:'To do',applied:'Applied',emailed:'Emailed',skip:'Skip'}[x]}</button>`).join('')}
  </div>
  <details class="more"${s.open ? ' open' : ''}>
    <summary>Contact &amp; drafts</summary>
    <div class="grid">
      <div>
        <h4>Found in the posting</h4>${found}
        <h4 style="margin-top:14px">Find the recruiter / hiring manager</h4>
        <div class="links">${c.searches.map(x => `<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.label)} ↗</a>`).join('')}</div>
        <h4 style="margin-top:14px">Who are you contacting?</h4>
        <div class="row"><input data-f="first" placeholder="First name" value="${esc(s.first||'')}"><input data-f="last" placeholder="Last name" value="${esc(s.last||'')}"></div>
        <div class="row"><input data-f="domain" placeholder="company.com" value="${esc(s.domain||c.domain)}"></div>
        <div class="hint">Domain ${esc(c.domain_source)}.</div>
        <div class="guesses"></div>
        <div class="row"><input data-f="to" placeholder="Send to (email)" value="${esc(s.to||'')}"></div>
      </div>
      <div>
        <h4>Email</h4>
        <div class="row"><input data-f="subject" value="${esc(s.subject||j.drafts.subject)}"><button data-copy="subject">Copy</button></div>
        <textarea data-f="body">${esc(s.body||'')}</textarea>
        <div class="actions">
          <button data-copy="body">Copy email</button>
          <a class="btn primary" data-gmail target="_blank" rel="noopener">Open in Gmail ↗</a>
          <a class="btn" data-mailto>Email app</a>
          <button data-copy="prompt" title="Paste into Claude for a sharper rewrite">Copy prompt for Claude</button>
          <a class="btn" href="https://claude.ai/new" target="_blank" rel="noopener">claude.ai ↗</a>
        </div>
        <h4 style="margin-top:14px">LinkedIn connection note <span class="hint" data-count></span></h4>
        <textarea class="note" data-f="note"></textarea>
        <div class="actions"><button data-copy="note">Copy note</button></div>
      </div>
    </div>
  </details>`;
  wire(el, j, s);
  return el;
}

function wire(el, j, s) {
  const $ = q => el.querySelector(q);
  const body = $('[data-f=body]'), note = $('[data-f=note]');
  if (!s.body) body.value = fill(j.drafts.body, s.first);
  note.value = s.note || fill(j.drafts.linkedin_note, s.first);
  const refresh = () => {
    const g = guesses(s.first, s.last, s.domain || j.contacts.domain);
    $('.guesses').innerHTML = g.length ? '<div class="hint" style="margin-top:6px">Likely addresses — <b>unverified guesses</b>. First.last@ is the most common format. Click one to use it:</div>' +
      g.map(x => `<div class="guess"><a href="#" data-use="${esc(x)}">${esc(x)}</a></div>`).join('') : '';
    $('.guesses').querySelectorAll('[data-use]').forEach(a => a.onclick = e => { e.preventDefault(); s.to = a.dataset.use; $('[data-f=to]').value = s.to; save(); gm(); });
    $('[data-count]').textContent = `(${note.value.length}/300)`;
    gm();
  };
  const gm = () => {
    const subj = $('[data-f=subject]').value;
    $('[data-gmail]').href = 'https://mail.google.com/mail/?view=cm&fs=1' + (s.to ? '&to=' + encodeURIComponent(s.to) : '') +
      '&su=' + encodeURIComponent(subj) + '&body=' + encodeURIComponent(body.value);
    $('[data-mailto]').href = 'mailto:' + encodeURIComponent(s.to || '') + '?subject=' + encodeURIComponent(subj) +
      '&body=' + encodeURIComponent(body.value);
  };
  el.querySelectorAll('input[data-f]').forEach(inp => inp.oninput = () => {
    const f = inp.dataset.f, oldFirst = s.first;
    s[f] = inp.value.trim();
    if (f === 'first') {
      if (!s.body) body.value = fill(j.drafts.body, s.first);
      else body.value = body.value.replace(new RegExp('^Hi ' + (oldFirst || 'there') + ','), 'Hi ' + (s.first || 'there') + ',');
      if (!s.note) note.value = fill(j.drafts.linkedin_note, s.first);
    }
    save(); refresh();
  });
  body.oninput = () => { s.body = body.value; save(); gm(); };
  note.oninput = () => { s.note = note.value; save(); refresh(); };
  el.querySelectorAll('[data-status]').forEach(b => b.onclick = () => {
    s.status = b.dataset.status; save();
    el.querySelectorAll('[data-status]').forEach(x => x.classList.toggle('on', x === b));
    el.classList.toggle('done', s.status !== 'todo');
  });
  el.querySelectorAll('[data-copy]').forEach(b => b.onclick = () => {
    const w = b.dataset.copy;
    copy(w === 'subject' ? $('[data-f=subject]').value : w === 'body' ? body.value : w === 'note' ? note.value
      : fill(j.drafts.claude_prompt, s.first), b);
  });
  $('details.more').ontoggle = e => { s.open = e.target.open; save(); };
  refresh();
}

function render() {
  const list = document.getElementById('list');
  const qv = document.getElementById('q').value.toLowerCase();
  const show = new Set([...document.querySelectorAll('[data-show]:checked')].map(x => x.dataset.show));
  const hideDone = document.getElementById('hideDone').checked;
  const sort = document.getElementById('sort').value;
  let jobs = DATA.jobs.map((j, i) => [j, i]).filter(([j]) => show.has(j.eligibility)
    && (!hideDone || !(state[j.key] && state[j.key].status && state[j.key].status !== 'todo'))
    && (!qv || (j.title + ' ' + j.company + ' ' + j.location).toLowerCase().includes(qv)));
  const rank = {ELIGIBLE: 0, LIKELY: 1, CHECK: 2};
  jobs.sort(([a], [b]) => sort === 'date' ? (b.posted || '').localeCompare(a.posted || '')
    : sort === 'fit' ? b.fit_score - a.fit_score
    : (rank[a.eligibility] - rank[b.eligibility]) || (b.fit_score - a.fit_score));
  list.innerHTML = '';
  if (!jobs.length) list.innerHTML = '<div class="empty">Nothing matches these filters.</div>';
  jobs.forEach(([j, i]) => list.appendChild(card(j, i)));
  document.getElementById('count').textContent = jobs.length + ' shown';
}
['q', 'hideDone', 'sort'].forEach(id => document.getElementById(id).addEventListener('input', render));
document.querySelectorAll('[data-show]').forEach(x => x.addEventListener('change', render));
render();
"""


def render_report(path, jobs, summary, settings):
    data = {"jobs": jobs, "summary": summary}
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    gen = datetime.now(timezone.utc).astimezone().strftime("%a %d %b %Y, %H:%M")
    counts = summary["counts"]
    stats = "".join(f'<div class="stat"><b>{v}</b><span>{k}</span></div>' for k, v in [
        ("eligible", counts.get("ELIGIBLE", 0)), ("likely", counts.get("LIKELY", 0)),
        ("check", counts.get("CHECK", 0)), ("new today", summary["new"]),
        ("ruled out", summary["rejected"]), ("scanned", summary["scanned"])])
    warn = ""
    if summary["errors"]:
        warn = '<div class="warn"><b>Some sources failed this run:</b> ' + "; ".join(
            _e(x) for x in summary["errors"]) + "</div>"
    manual = "".join(
        f'<div>{"<a href=" + chr(34) + _e(u) + chr(34) + " target=_blank rel=noopener>" + _e(t) + " ↗</a>" if u else "<b>" + _e(t) + "</b>"}<p>{_e(d)}</p></div>'
        for t, d, u in MANUAL_LINKS)
    reasons = "".join(f"<li>{_e(r)}: {n}</li>" for r, n in summary["reject_reasons"])
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Job Hunt</title><style>{CSS}</style></head>
<body><div class="wrap">
<h1>Job Hunt</h1>
<p class="sub">Generated {gen} · pay floor ${settings['min_salary_usd']:,}/yr · postings from the last {settings['max_age_days']} days</p>
<div class="stats">{stats}</div>
{warn}
<details class="panel"><summary>Also do these by hand (sites that can't be pulled automatically)</summary><div class="manual">{manual}</div></details>
<details class="panel"><summary>Why jobs were ruled out ({summary['rejected']})</summary><ul>{reasons}</ul></details>
<div class="bar">
  <input id="q" type="search" placeholder="Filter by title, company, location…">
  <label class="tog"><input type="checkbox" data-show="ELIGIBLE" checked> Eligible</label>
  <label class="tog"><input type="checkbox" data-show="LIKELY" checked> Likely</label>
  <label class="tog"><input type="checkbox" data-show="CHECK" checked> Check</label>
  <label class="tog"><input type="checkbox" id="hideDone"> Hide done</label>
  <select id="sort"><option value="best">Best first</option><option value="fit">Fit score</option><option value="date">Newest</option></select>
  <span class="hint" id="count"></span>
</div>
<div id="list"></div>
<p class="hint">Statuses, names and edited drafts are saved in this browser. Job listings come from Himalayas, Remotive, RemoteOK, Jobicy, Working Nomads, We Work Remotely, Amazon Jobs and company career boards; each card links back to the original posting.</p>
</div>
<script id="data" type="application/json">{blob}</script>
<script>{JS}</script>
</body></html>"""
    path.write_text(html, encoding="utf-8")


def _e(s):
    import html as h
    return h.escape(str(s))
