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
[hidden]{display:none!important}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1000px;margin:0 auto;padding:24px 16px 80px}
h1{font-size:24px;margin:0 0 4px}.sub{color:var(--muted);margin:0 0 18px}
.stats{display:grid;grid-template-columns:repeat(auto-fill,minmax(105px,1fr));gap:10px;margin-bottom:16px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px}
.stat b{display:block;font-size:22px}.stat span{color:var(--muted);font-size:13px}
details.panel{margin-top:12px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin-bottom:16px}
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
.head{flex:1;min-width:0}.head .meta b{color:var(--ink);font-weight:600}
.fit{flex:none;width:52px;height:52px;border-radius:12px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-weight:700;font-size:19px;line-height:1}
.fit small{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-top:3px}
.fit.hi{background:var(--ok-bg);color:var(--ok)}.fit.mid{background:var(--likely-bg);color:var(--likely)}.fit.lo{background:var(--chip);color:var(--muted)}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.tags .badge{margin:0}.badge.plain{background:var(--chip);color:var(--muted);font-weight:600}
.match{font-size:13px;margin:8px 0 2px;display:flex;flex-wrap:wrap;gap:4px 14px}.match .ok{color:var(--ok)}.match .gapt{color:var(--gap)}
.fitnote{margin:8px 0 0;font-size:14px}
.chips-row{display:flex;flex-wrap:wrap;gap:6px;width:100%;align-items:center}.sep{width:1px;height:20px;background:var(--line);margin:0 2px}
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
.settings{display:grid;gap:10px;margin-top:10px}.settings label{display:grid;gap:4px;font-size:14px;color:var(--muted)}
.settings label.check{display:flex;align-items:center;gap:8px;color:var(--ink)}.settings label.check input{width:auto}
.settings input,.settings textarea{font:inherit;color:var(--ink);background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px;min-height:0}
.glance{margin:10px 0 4px;font-size:14px}.glance p{margin:0 0 6px}
.gcols{display:grid;grid-template-columns:1fr 1fr;gap:4px 16px}@media(max-width:720px){.gcols{grid-template-columns:1fr}}
.g h5{margin:4px 0 2px;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
.g ul{margin:0;padding-left:18px}.g li{margin:2px 0}
.why{font-size:12.5px;color:var(--muted);margin-top:6px}.why .ev{font-style:italic}
.lookupbox{margin-top:10px;padding:10px 12px;border:1px dashed var(--line);border-radius:10px}
.person{padding:8px 0;border-top:1px solid var(--line)}.person:first-of-type{border-top:0}
.empty{text-align:center;color:var(--muted);padding:40px}
.warn{background:var(--check-bg);color:var(--check);border-radius:10px;padding:10px 14px;margin-bottom:12px;font-size:14px}
"""

JS = r"""
const DATA = JSON.parse(document.getElementById('data').textContent);
const KEY = 'ajh-state-v1';
let state = {};
try { state = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) {}
const byId = {}; DATA.jobs.forEach(j => { byId[j.id] = j; });
let db = null, sample = null, mcp = null;
const lookups = {};
const timers = {};
const st = k => (state[k] = state[k] || {});
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ago = iso => { if (!iso) return 'date unknown'; const d = (Date.now() - new Date(iso)) / 864e5;
  return d < 1 ? 'today' : d < 2 ? 'yesterday' : Math.floor(d) + ' days ago'; };
const LABEL = {ELIGIBLE: 'Eligible from Jordan', LIKELY: 'Likely eligible', CHECK: 'Check eligibility'};
const setSync = t => { const el = document.getElementById('sync'); if (el) el.textContent = t; };

function save(j) {
  const s = st(j.key);
  s.updatedAt = new Date().toISOString();
  try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  if (!db) return;
  clearTimeout(timers[j.id]);
  timers[j.id] = setTimeout(() => {
    db.doc('state/' + j.id).set(Object.assign({}, state[j.key], {key: j.key}))
      .then(() => setSync('Synced across your devices'))
      .catch(err => setSync('Not synced (' + ((err && err.code) || 'error') + ') — saved on this device'));
  }, 700);
}

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
  const fallback = () => { const t = document.createElement('textarea'); t.value = text; document.body.appendChild(t); t.select();
    document.execCommand('copy'); t.remove(); done(); };
  if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, fallback); else fallback();
}

function card(j) {
  const s = st(j.key);
  const c = j.contacts;
  const el = document.createElement('div');
  el.className = 'card' + (s.status && s.status !== 'todo' ? ' done' : '');
  el.dataset.id = j.id;
  const found = [
    ...c.people.map(p => `<div>👤 ${esc(p)} <span class="hint">(named in posting)</span></div>`),
    ...c.emails.map(e => `<div>✉️ <a href="mailto:${esc(e.email)}">${esc(e.email)}</a> <span class="hint">(${esc(e.kind)}, in posting)</span></div>`)
  ].join('') || '<div class="hint">The posting doesn\'t name anyone. Use the searches below.</div>';
  const fitCls = j.fit_score >= 75 ? 'hi' : j.fit_score >= 55 ? 'mid' : 'lo';
  const have = j.matched_skills.slice(0, 8), gaps = j.gaps;
  el.innerHTML = `
  <div class="top">
    <div class="head">
      <h3 class="title"><a href="${esc(j.url)}" target="_blank" rel="noopener">${esc(j.title)}</a></h3>
      <div class="meta"><b>${esc(j.company)}</b> · ${esc(j.location || '—')}</div>
      <div class="meta">${ago(j.posted)} · ${j.salary_note === 'Not listed' ? 'salary not listed' : '💵 ' + esc(j.salary_note)}${j.job_type ? ' · ' + esc(j.job_type) : ''} · via ${esc(j.source)}</div>
    </div>
    <div class="fit ${fitCls}" title="How well this matches your resume">${j.fit_score}<small>fit</small></div>
  </div>
  <div class="tags"><span class="badge ${j.eligibility}" title="${esc(j.eligibility_reason)}">${LABEL[j.eligibility] || j.eligibility}</span>${j.is_new ? '<span class="badge NEW">NEW</span>' : ''}<span class="badge plain">${esc(j.category)}</span><span class="badge plain">${esc(j.level)}</span></div>
  ${glance(j.summary)}
  ${(have.length || gaps.length) ? `<div class="match">${have.length ? '<span class="ok">✓ ' + have.map(esc).join(', ') + '</span>' : ''}${gaps.length ? '<span class="gapt">Gaps: ' + gaps.map(esc).join(', ') + '</span>' : ''}</div>` : ''}
  <div class="why">${esc(j.eligibility_reason)}${j.eligibility_evidence ? ` <span class="ev">“${esc(j.eligibility_evidence)}”</span>` : ''}</div>
  <div class="actions">
    <button class="btn primary" data-interested>I'm interested →</button>
    <a class="btn" href="${esc(j.url)}" target="_blank" rel="noopener">Full posting ↗</a>
    ${['todo','applied','emailed','skip'].map(x => `<button data-status="${x}" class="${(s.status||'todo')===x?'on':''}">${{todo:'To do',applied:'Applied',emailed:'Emailed',skip:'Not for me'}[x]}</button>`).join('')}
  </div>
  <details class="more"${s.open ? ' open' : ''}>
    <summary>Recruiter contact &amp; email draft</summary>
    <div class="lookupbox">
      <div class="actions" style="margin-top:0"><button data-lookup hidden>🔎 Find the recruiter for me</button><span class="hint" data-lookup-msg></span></div>
      <div data-lookup-out></div>
    </div>
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
        <textarea data-f="body"></textarea>
        <div class="actions">
          <button data-copy="body">Copy email</button>
          <a class="btn primary" data-gmail target="_blank" rel="noopener">Open in Gmail ↗</a>
          <a class="btn" data-mailto>Email app</a>
          <button data-rewrite hidden>✨ Rewrite with Claude</button>
          <button data-copy="prompt" class="noai" title="Paste into Claude for a sharper rewrite">Copy prompt for Claude</button>
        </div>
        <div class="hint" data-ai></div>
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
  const body = $('[data-f=body]'), note = $('[data-f=note]'), subject = $('[data-f=subject]');
  body.value = s.body || fill(j.drafts.body, s.first);
  note.value = s.note || fill(j.drafts.linkedin_note, s.first);
  if (sample) { $('[data-rewrite]').hidden = false; $('.noai').hidden = true; }
  const gm = () => {
    $('[data-gmail]').href = 'https://mail.google.com/mail/?view=cm&fs=1' + (s.to ? '&to=' + encodeURIComponent(s.to) : '') +
      '&su=' + encodeURIComponent(subject.value) + '&body=' + encodeURIComponent(body.value);
    $('[data-mailto]').href = 'mailto:' + encodeURIComponent(s.to || '') + '?subject=' + encodeURIComponent(subject.value) +
      '&body=' + encodeURIComponent(body.value);
  };
  const refresh = () => {
    const g = guesses(s.first, s.last, s.domain || j.contacts.domain);
    $('.guesses').innerHTML = g.length ? '<div class="hint" style="margin-top:6px">Likely addresses — <b>unverified guesses</b>. First.last@ is the most common format. Tap one to use it:</div>' +
      g.map(x => `<div class="guess"><a href="#" data-use="${esc(x)}">${esc(x)}</a></div>`).join('') : '';
    $('.guesses').querySelectorAll('[data-use]').forEach(a => a.onclick = e => { e.preventDefault(); s.to = a.dataset.use; $('[data-f=to]').value = s.to; save(j); gm(); });
    $('[data-count]').textContent = `(${note.value.length}/300)`;
    gm();
  };
  el.querySelectorAll('input[data-f]').forEach(inp => inp.oninput = () => {
    const f = inp.dataset.f, oldFirst = s.first;
    s[f] = f === 'subject' ? inp.value : inp.value.trim();
    if (f === 'first') {
      if (!s.body) body.value = fill(j.drafts.body, s.first);
      else { body.value = body.value.replace(new RegExp('^Hi ' + (oldFirst || 'there') + ','), 'Hi ' + (s.first || 'there') + ','); s.body = body.value; }
      if (!s.note) note.value = fill(j.drafts.linkedin_note, s.first);
    }
    save(j); refresh();
  });
  body.oninput = () => { s.body = body.value; save(j); gm(); };
  note.oninput = () => { s.note = note.value; save(j); refresh(); };
  el.querySelectorAll('[data-status]').forEach(b => b.onclick = () => {
    s.status = b.dataset.status; save(j);
    el.querySelectorAll('[data-status]').forEach(x => x.classList.toggle('on', x === b));
    el.classList.toggle('done', s.status !== 'todo');
  });
  el.querySelectorAll('[data-copy]').forEach(b => b.onclick = () => {
    const w = b.dataset.copy;
    copy(w === 'subject' ? subject.value : w === 'body' ? body.value : w === 'note' ? note.value
      : fill(j.drafts.claude_prompt, s.first), b);
  });
  $('[data-rewrite]').onclick = async () => {
    const btn = $('[data-rewrite]'), out = $('[data-ai]');
    btn.disabled = true; out.textContent = 'Claude is rewriting…';
    try {
      const prompt = fill(j.drafts.rewrite_prompt, s.first) + '\n\nCURRENT DRAFT (keep any facts I added):\n' + body.value;
      const r = await sample.json(prompt);
      if (r && r.body) {
        body.value = r.body; s.body = r.body;
        if (r.subject) { subject.value = r.subject; s.subject = r.subject; }
        if (r.linkedin_note) { note.value = r.linkedin_note.slice(0, 300); s.note = note.value; }
        save(j); refresh();
        out.innerHTML = (r.gaps && r.gaps.length) ? '<b>Prepare for:</b> ' + r.gaps.map(esc).join(' · ') : 'Rewritten ✓';
      } else out.textContent = 'Claude returned nothing usable — your draft is unchanged.';
    } catch (e) {
      out.textContent = e && e.code === 'rate_limited' ? 'Claude is busy — try again in a minute.' :
        e && e.code === 'not_granted' ? 'Claude access was declined for this page.' : 'Rewrite failed — your draft is unchanged.';
    }
    btn.disabled = false;
  };
  $('[data-interested]').onclick = () => { const d = $('details.more'); d.open = true; d.scrollIntoView({behavior: 'smooth', block: 'start'}); };
  if (mcp && DATA.lookup_trigger_id) $('[data-lookup]').hidden = false;
  $('[data-lookup]').onclick = () => findRecruiter(j, el);
  renderLookup(el, j);
  $('details.more').ontoggle = e => { s.open = e.target.open; try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (x) {} };
  refresh();
}

function glance(sm) {
  if (!sm || !(sm.overview || (sm.do && sm.do.length) || (sm.need && sm.need.length))) return '';
  const list = (h, xs) => xs && xs.length ? `<div class="g"><h5>${h}</h5><ul>${xs.map(x => `<li>${esc(x)}</li>`).join('')}</ul></div>` : '';
  return `<div class="glance">${sm.overview ? `<p>${esc(sm.overview)}</p>` : ''}<div class="gcols">${list("What you'd do", sm.do)}${list('What they want', sm.need)}</div>${sm.fit_note ? `<p class="fitnote">💡 ${esc(sm.fit_note)}</p>` : ''}</div>`;
}

function renderLookup(el, j) {
  const out = el.querySelector('[data-lookup-out]'), msg = el.querySelector('[data-lookup-msg]'), btn = el.querySelector('[data-lookup]');
  const L = lookups[j.id];
  if (!L) { out.innerHTML = ''; return; }
  if (L.status === 'searching') {
    btn.disabled = true;
    msg.textContent = 'Claude is looking this up — results appear here in a few minutes. You can leave the page.';
    out.innerHTML = '';
    return;
  }
  btn.disabled = false; btn.textContent = '🔎 Search again';
  msg.textContent = L.updatedAt ? 'Found ' + ago(L.updatedAt) : '';
  const people = (L.people || []).map((p, i) => `<div class="person">
      <div><b>${esc(p.name)}</b> <span class="badge ${p.role === 'recruiter' ? 'LIKELY' : 'ELIGIBLE'}">${esc(p.role || 'contact')}</span><div class="hint">${esc(p.title || '')}</div></div>
      <div class="actions" style="margin-top:4px">${p.linkedin ? `<a class="btn" href="${esc(p.linkedin)}" target="_blank" rel="noopener">LinkedIn ↗</a>` : ''}
        ${p.email ? `<a class="btn" href="mailto:${esc(p.email)}">${esc(p.email)}</a>` : ''}
        <button data-useperson="${i}">Write to ${esc((p.name || '').split(' ')[0])}</button></div>
    </div>`).join('');
  out.innerHTML = `<h4>Found by Claude</h4>${people || '<div class="hint">No named recruiter or hiring manager found publicly.</div>'}
    ${L.email_format ? `<div class="hint" style="margin-top:8px"><b>Email format:</b> ${esc(L.email_format)}${L.email_format_source ? ' (' + esc(L.email_format_source) + ')' : ''}</div>` : ''}
    ${L.notes ? `<div class="hint" style="margin-top:4px">${esc(L.notes)}</div>` : ''}`;
  out.querySelectorAll('[data-useperson]').forEach(b => b.onclick = () => {
    const p = L.people[+b.dataset.useperson]; const parts = (p.name || '').trim().split(/\s+/);
    const set = (f, v) => { const i = el.querySelector('input[data-f=' + f + ']'); i.value = v; i.dispatchEvent(new Event('input')); };
    set('first', parts[0] || ''); set('last', parts.slice(1).join(' '));
    if (L.domain) set('domain', L.domain);
    if (p.email) set('to', p.email);
    el.querySelector('[data-f=body]').scrollIntoView({behavior: 'smooth', block: 'center'});
  });
}

async function findRecruiter(j, el) {
  const btn = el.querySelector('[data-lookup]'), msg = el.querySelector('[data-lookup-msg]');
  btn.disabled = true; msg.textContent = 'Asking Claude to look this up…';
  try {
    if (db) await db.doc('contacts/' + j.id).set({status: 'searching', requestedAt: new Date().toISOString(), title: j.title, company: j.company});
    await mcp.callTool('Claude Code Remote', 'fire_trigger', {trigger_id: DATA.lookup_trigger_id,
      text: 'JOB: ' + JSON.stringify({id: j.id, title: j.title, company: j.company, location: j.location, url: j.url, domain_guess: j.contacts.domain})});
    msg.textContent = 'Claude is looking this up — results appear here in a few minutes. You can leave the page.';
  } catch (e) {
    const c = e && e.code;
    msg.textContent = c === 'consent_required' || c === 'not_granted' ? 'Allow the Claude Code connector for this page to use this button.' :
      'Couldn\'t start the lookup (' + (c || 'error') + '). Use the LinkedIn searches below instead.';
    if (db) db.doc('contacts/' + j.id).delete().catch(() => {});
    btn.disabled = false;
  }
}

function render() {
  const list = document.getElementById('list');
  const qv = document.getElementById('q').value.toLowerCase();
  const show = new Set([...document.querySelectorAll('[data-show]:checked')].map(x => x.dataset.show));
  const hideDone = document.getElementById('hideDone').checked;
  const newOnly = document.getElementById('newOnly').checked;
  const cats = new Set([...document.querySelectorAll('[data-cat]:checked')].map(x => x.dataset.cat));
  const sort = document.getElementById('sort').value;
  let jobs = DATA.jobs.filter(j => show.has(j.eligibility) && cats.has(j.category) && (!newOnly || j.is_new)
    && !skipList.some(n => norm(j.company).includes(n))
    && (!hideDone || !(state[j.key] && ['applied', 'skip'].includes(state[j.key].status)))
    && (!qv || (j.title + ' ' + j.company + ' ' + j.location).toLowerCase().includes(qv)));
  const rank = {ELIGIBLE: 0, LIKELY: 1, CHECK: 2};
  jobs.sort((a, b) => sort === 'date' ? (b.posted || '').localeCompare(a.posted || '')
    : sort === 'fit' ? b.fit_score - a.fit_score
    : (rank[a.eligibility] - rank[b.eligibility]) || (b.fit_score - a.fit_score) || (b.posted || '').localeCompare(a.posted || ''));
  list.innerHTML = '';
  if (!jobs.length) list.innerHTML = '<div class="empty">Nothing matches these filters.</div>';
  jobs.forEach(j => list.appendChild(card(j)));
  document.getElementById('count').textContent = jobs.length + ' of ' + DATA.jobs.length + ' jobs';
}

function applyRemote(snap) {
  snap.docChanges().forEach(ch => {
    if (ch.doc.metadata && ch.doc.metadata.hasPendingWrites) return;
    const d = ch.doc.data(); const j = byId[ch.doc.id];
    if (!d || !j) return;
    const local = state[j.key];
    if (local && local.updatedAt && d.updatedAt && local.updatedAt > d.updatedAt) return;
    state[j.key] = Object.assign({}, d, {open: local && local.open});
    const el = document.querySelector('.card[data-id="' + ch.doc.id + '"]');
    if (el && !el.contains(document.activeElement)) el.replaceWith(card(j));
  });
  try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
}

function settingsForm(cfg) {
  const f = document.getElementById('settings');
  f.floor.value = cfg.min_salary_usd; f.days.value = cfg.max_age_days;
  f.terms.value = (cfg.search_terms || []).join('\n');
  f.skip.value = (cfg.skip_companies || []).join('\n');
  f.noai.checked = cfg.skip_ai_interviews !== false;
  skipList = (cfg.skip_companies || []).map(norm).filter(Boolean);
}
const norm = x => String(x || '').toLowerCase().replace(/[^a-z0-9]/g, '');
let skipList = [];
function readSettingsForm() {
  const f = document.getElementById('settings');
  return {min_salary_usd: Math.max(0, parseInt(f.floor.value, 10) || 0), max_age_days: Math.max(1, parseInt(f.days.value, 10) || 21),
          search_terms: f.terms.value.split('\n').map(x => x.trim()).filter(Boolean).slice(0, 30),
          skip_companies: f.skip.value.split('\n').map(x => x.trim()).filter(Boolean).slice(0, 100),
          skip_ai_interviews: f.noai.checked};
}

['q', 'hideDone', 'newOnly', 'sort'].forEach(id => document.getElementById(id).addEventListener('input', render));
document.querySelectorAll('[data-show],[data-cat]').forEach(x => x.addEventListener('change', render));
settingsForm(DATA.settings);
render();

(async () => {
  if (!window.claude || !window.claude.use) { setSync('Saved on this device'); return; }
  const [d, s, m] = await Promise.all(['db', 'sample', 'mcp'].map(n => window.claude.use(n).catch(() => null)));
  sample = s; mcp = m;
  if (sample || mcp) document.querySelectorAll('.card').forEach(el => { const j = byId[el.dataset.id]; if (j) el.replaceWith(card(j)); });
  if (d) {
    db = d;
    setSync('Syncing…');
    const timer = setTimeout(() => setSync('Sync is slow — changes are saved on this device'), 10000);
    db.collection('state').onSnapshot(snap => { clearTimeout(timer); setSync('Synced across your devices'); applyRemote(snap); },
      err => { clearTimeout(timer); setSync('Sync unavailable (' + ((err && err.code) || 'error') + ') — saved on this device'); });
    db.collection('contacts').onSnapshot(snap => {
      snap.docChanges().forEach(ch => {
        if (ch.type === 'removed') delete lookups[ch.doc.id]; else lookups[ch.doc.id] = ch.doc.data();
        const el = document.querySelector('.card[data-id="' + ch.doc.id + '"]');
        if (el && byId[ch.doc.id]) renderLookup(el, byId[ch.doc.id]);
      });
    }, () => {});
    db.doc('config/settings').get().then(doc => { if (doc.exists) settingsForm(Object.assign({}, DATA.settings, doc.data())); }).catch(() => {});
    const form = document.getElementById('settings');
    form.querySelector('button').disabled = false;
    form.onsubmit = e => {
      e.preventDefault();
      const msg = document.getElementById('settingsMsg');
      db.doc('config/settings').set(readSettingsForm())
        .then(() => { msg.textContent = 'Saved. Skipped companies are hidden now; other changes apply from the next search run.';
          skipList = readSettingsForm().skip_companies.map(norm).filter(Boolean); render(); })
        .catch(err => { msg.textContent = 'Could not save (' + ((err && err.code) || 'error') + ').'; });
    };
  } else setSync('Saved on this device');
  const run = document.getElementById('runNow');
  if (mcp && DATA.trigger_id) {
    run.hidden = false;
    run.onclick = async () => {
      const msg = document.getElementById('runMsg');
      run.disabled = true; msg.textContent = 'Starting a fresh search…';
      try {
        await mcp.callTool('Claude Code Remote', 'fire_trigger', {trigger_id: DATA.trigger_id});
        msg.textContent = 'Started. Reload this page in about 10–15 minutes for the new list.';
      } catch (e) {
        const c = e && e.code;
        msg.textContent = c === 'consent_required' || c === 'not_granted' ? 'Allow the Claude Code connector for this page to use this button.' :
          c === 'server_not_connected' || c === 'not_in_manifest' || c === 'blocked_by_policy' ? 'This button isn\'t available here — the daily run still happens automatically.' :
          'Couldn\'t start it right now (' + (c || 'error') + '). The daily run still happens automatically.';
        run.disabled = false;
      }
    };
  }
})();
"""


def render_report(path, jobs, summary, settings, trigger_id="", lookup_trigger_id=""):
    data = {"jobs": jobs, "summary": summary, "trigger_id": trigger_id, "lookup_trigger_id": lookup_trigger_id, "settings": {
        "min_salary_usd": settings["min_salary_usd"], "max_age_days": settings["max_age_days"],
        "search_terms": settings["search_terms"], "skip_companies": settings.get("skip_companies", []),
        "skip_ai_interviews": settings.get("skip_ai_interviews", True)}}
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
<p class="sub">Updated {gen} · pay floor ${settings['min_salary_usd']:,}/yr · postings from the last {settings['max_age_days']} days · <span id="sync"></span></p>
<div class="actions" style="margin:-6px 0 14px"><button id="runNow" class="btn primary" hidden>Run a fresh search now</button><span class="hint" id="runMsg"></span></div>
<div class="stats">{stats}</div>
{warn}
<div class="bar">
  <input id="q" type="search" placeholder="Search title, company, location…">
  <select id="sort"><option value="best">Best match</option><option value="date">Newest</option><option value="fit">Fit score</option></select>
  <div class="chips-row">
    <label class="tog"><input type="checkbox" data-show="ELIGIBLE" checked> Eligible</label>
    <label class="tog"><input type="checkbox" data-show="LIKELY" checked> Likely</label>
    <label class="tog"><input type="checkbox" data-show="CHECK" checked> Check</label>
    <span class="sep"></span>
    <label class="tog"><input type="checkbox" data-cat="Data Engineering" checked> Data Eng</label>
    <label class="tog"><input type="checkbox" data-cat="BI & Analytics" checked> BI &amp; Analytics</label>
    <label class="tog"><input type="checkbox" data-cat="Power Platform" checked> Power Platform</label>
    <label class="tog"><input type="checkbox" data-cat="Leadership" checked> Leadership</label>
    <span class="sep"></span>
    <label class="tog"><input type="checkbox" id="newOnly"> New only</label>
    <label class="tog"><input type="checkbox" id="hideDone" checked> Hide applied/skipped</label>
  </div>
  <span class="hint" id="count"></span>
</div>
<div id="list"></div>
<details class="panel"><summary>Search settings</summary>
<form id="settings" class="settings">
  <label>Pay floor (USD / year)<input name="floor" type="number" min="0" step="5000"></label>
  <label>Only postings from the last N days<input name="days" type="number" min="1" max="60"></label>
  <label>Search terms (one per line)<textarea name="terms" rows="6"></textarea></label>
  <label>Companies to skip (one per line)<textarea name="skip" rows="4" placeholder="micro1"></textarea></label>
  <label class="check"><input type="checkbox" name="noai"> Skip jobs that use AI interviews</label>
  <div class="actions"><button type="submit" disabled>Save settings</button><span class="hint" id="settingsMsg">Saving works on the published page.</span></div>
</form></details>
<details class="panel"><summary>More places to look by hand</summary><div class="manual">{manual}</div></details>
<details class="panel"><summary>Why {summary['rejected']} jobs were ruled out</summary><ul>{reasons}</ul></details>
<p class="hint">Statuses, names and edited drafts sync across your devices on the published page (and are saved in this browser when opened as a file). Job listings come from Himalayas, Remotive, RemoteOK, Jobicy, Working Nomads, We Work Remotely, Amazon Jobs and company career boards; each card links back to the original posting.</p>
</div>
<script id="data" type="application/json">{blob}</script>
<script>{JS}</script>
</body></html>"""
    path.write_text(html, encoding="utf-8")


def _e(s):
    import html as h
    return h.escape(str(s))
