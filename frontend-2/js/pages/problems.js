(() => {
const E = App.esc;
App.pages.problems = ([id]) => id ? detail(+id) : list();
const START = {
  py: "# Write your solution here\ndef solve():\n    pass\n",
  js: "// Write your solution here\nfunction solve() {\n  \n}\n",
  java: "class Solution {\n    public void solve() {\n        // Write your solution here\n    }\n}\n",
  cpp: "class Solution {\npublic:\n    void solve() {\n        // Write your solution here\n    }\n};\n"
};
const FILE = { py: "solution.py", js: "solution.js", java: "Solution.java", cpp: "solution.cpp" };
const ext = n => /javascript/i.test(n) ? "js" : /python/i.test(n) ? "py" : /java/i.test(n) ? "java" : "cpp";

function list() {
  const q0 = App.q; App.q = "";
  App.view(App.title("Problems") + `
  <div class="card p-3"><div class="row g-2 mb-3">
    <div class="col-md-6"><input id="q" class="form-control" placeholder="Search title, category or tag…" value="${E(q0)}"></div>
    <div class="col-md-3"><select id="d" class="form-select"><option value="">All difficulties</option><option>easy</option><option>medium</option><option>hard</option></select></div>
    <div class="col-md-3"><select id="s" class="form-select"><option value="">All statuses</option><option value="1">Solved</option><option value="0">Unsolved</option><option value="b">Saved</option></select></div></div>
  <div class="table-responsive"><table class="table table-hover align-middle"><thead><tr><th></th><th>Title</th><th>Categories</th><th>Difficulty</th><th>Acceptance</th></tr></thead><tbody id="rows"></tbody></table></div></div>`);
  const draw = () => {
    const q = App.$("#q").value.toLowerCase(), d = App.$("#d").value, s = App.$("#s").value;
    const r = DB.problems.filter(p => (!d || p.difficulty === d) && (s === "" || (s === "b" ? DB.bookmarks.includes(p.problem_id) : String(+p.solved) === s)) && (p.title + p.categories + p.tags).toLowerCase().includes(q));
    App.$("#rows").innerHTML = r.map(p => `<tr onclick="location.hash='#/problems/${p.problem_id}'"><td>${p.solved ? App.i("check") : App.i("circle")}</td><td class="fw-medium">${p.title}</td><td>${App.chips(p.categories)}</td><td>${App.diff(p.difficulty)}</td><td>${p.acceptance}%</td></tr>`).join("") || `<tr><td colspan="5" class="text-center text-secondary py-4">No problems match.</td></tr>`;
  };
  ["q", "d", "s"].forEach(i => App.$("#" + i).oninput = draw); draw();
}

function detail(id) {
  const p = DB.problems.find(x => x.problem_id === id); if (!p) return list();
  App.view(`<a href="#/problems" class="small">← Back to problems</a>
  <div class="row g-3 mt-1">
  <div class="col-lg-5"><div class="card p-3">
    <div class="d-flex justify-content-between align-items-start"><h2 class="h4 page-title">${p.title}</h2><button id="bm" class="btn btn-sm btn-ghost"></button></div>
    <div class="mb-3">${App.diff(p.difficulty)} ${App.chips(p.categories.concat(p.tags))}</div>
    <p>${p.statement}</p>
    ${p.examples.map((e, i) => `<div class="mb-2"><strong class="small">Example ${i + 1}</strong><pre class="code">Input:  ${e.input}\nOutput: ${e.output}\n// ${e.explanation}</pre></div>`).join("")}
    <div class="small text-secondary mb-2">${p.time_limit_ms} ms · ${p.memory_limit_mb} MB</div>
    <div class="accordion accordion-flush" id="hints">${p.hints.map((h, i) => `<div class="accordion-item bg-transparent"><h2 class="accordion-header"><button class="accordion-button collapsed bg-transparent shadow-none py-2" data-bs-toggle="collapse" data-bs-target="#h${i}">Hint ${i + 1}</button></h2><div id="h${i}" class="accordion-collapse collapse" data-bs-parent="#hints"><div class="accordion-body small pt-0">${h}</div></div></div>`).join("")}</div>
  </div></div>
  <div class="col-lg-7 d-grid gap-3 align-content-start"><div class="card p-3">
    <div class="d-flex gap-2 mb-2"><select id="lang" class="form-select w-auto">${DB.languages.map(l => `<option>${l.name}</option>`).join("")}</select><button id="run" class="btn btn-primary ms-auto">${App.i("play")} Submit</button></div>
    <div class="tabbar"><span class="on" data-t="code"></span><span data-t="tc">Testcases</span></div>
    <div class="ed" id="pane-code"><pre class="gut"></pre><textarea class="editor" spellcheck="false" wrap="off"></textarea></div>
    <div id="pane-tc" class="d-none">${p.examples.map((e, i) => `<pre class="code mb-2">Case ${i + 1}\nInput:    ${e.input}\nExpected: ${e.output}</pre>`).join("")}</div>
  </div><div id="result"></div><div id="hist"></div></div></div>`);

  const ed = App.$(".editor"), gut = App.$(".gut"), sel = App.$("#lang"), tabs = document.querySelectorAll(".tabbar span");
  const key = () => `${id}:${ext(sel.value)}`, num = () => gut.textContent = ed.value.split("\n").map((_, i) => i + 1).join("\n");
  const load = () => { ed.value = DB.drafts[key()] ?? START[ext(sel.value)]; tabs[0].textContent = FILE[ext(sel.value)]; num(); };
  sel.onchange = load;
  ed.oninput = () => { DB.drafts[key()] = ed.value; Store.save(); num(); };
  ed.onscroll = () => gut.style.transform = `translateY(${-ed.scrollTop}px)`;
  ed.onkeydown = e => { if (e.key === "Tab") { e.preventDefault(); ed.setRangeText("    ", ed.selectionStart, ed.selectionEnd, "end"); ed.dispatchEvent(new Event("input")); } };
  tabs.forEach(t => t.onclick = () => { tabs.forEach(x => x.classList.toggle("on", x === t)); App.$("#pane-code").classList.toggle("d-none", t.dataset.t !== "code"); App.$("#pane-tc").classList.toggle("d-none", t.dataset.t !== "tc"); });
  load();

  const bm = App.$("#bm"), paint = () => bm.textContent = DB.bookmarks.includes(id) ? "Saved" : "Save";
  bm.onclick = () => { const i = DB.bookmarks.indexOf(id); i >= 0 ? DB.bookmarks.splice(i, 1) : DB.bookmarks.push(id); Store.save(); paint(); }; paint();

  const hist = () => { const s = DB.submissions.filter(x => x.problem_id === id); App.$("#hist").innerHTML = s.length ? `<div class="card p-3"><strong class="mb-2">Your submissions</strong><table class="table table-sm"><thead><tr><th>#</th><th>Language</th><th>Status</th><th>When</th></tr></thead><tbody>${s.map(x => `<tr><td>${x.id}</td><td>${E(x.language)}</td><td>${App.status(x.status)}</td><td class="text-secondary">${App.ago(x.submitted_at)}</td></tr>`).join("")}</tbody></table></div>` : ""; };
  hist();

  const btn = App.$("#run");
  btn.onclick = () => {
    const code = ed.value.trim();
    if (code.length < 20 || code === START[ext(sel.value)].trim()) return App.toast("Write some code before submitting");
    btn.disabled = true; App.$("#result").innerHTML = `<div class="card p-3 text-secondary"><span class="spinner-border spinner-border-sm me-2"></span>Submitting…</div>`;
    setTimeout(() => {
      const sid = Math.max(9040, ...DB.submissions.map(s => s.id)) + 1;
      DB.submissions.unshift({ id: sid, problem_id: id, language: sel.value, status: "queued", runtime_ms: null, submitted_at: Date.now() });
      App.notify("Submission received", `${p.title} · ${sel.value} — result within 24 hours`, "#/problems/" + id);
      App.$("#result").innerHTML = `<div class="card p-3"><div class="d-flex justify-content-between mb-1"><strong>Submission accepted for evaluation</strong>${App.status("queued")}</div><div class="small text-secondary">Submission #${sid} was received. The final verdict will be updated within 24 hours — you'll get a notification when it's ready.</div></div>`;
      hist(); btn.disabled = false;
    }, 700);
  };
}
})();
