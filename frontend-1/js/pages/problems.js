(() => {
App.pages.problems = ([id]) => id ? detail(+id) : list();
const bookmarks = new Set([3]);

function list() {
  App.view(App.title("Problems") + `
  <div class="card p-3"><div class="row g-2 mb-3">
    <div class="col-md-6"><input id="q" class="form-control" placeholder="Search title, category or tag…"></div>
    <div class="col-md-3"><select id="d" class="form-select"><option value="">All difficulties</option><option>easy</option><option>medium</option><option>hard</option></select></div>
    <div class="col-md-3"><select id="s" class="form-select"><option value="">All statuses</option><option value="1">Solved</option><option value="0">Unsolved</option></select></div></div>
  <div class="table-responsive"><table class="table table-hover align-middle"><thead><tr><th></th><th>Title</th><th>Categories</th><th>Difficulty</th><th>Acceptance</th></tr></thead><tbody id="rows"></tbody></table></div></div>`);
  const draw = () => {
    const q = App.$("#q").value.toLowerCase(), d = App.$("#d").value, s = App.$("#s").value;
    const r = DB.problems.filter(p => (!d || p.difficulty === d) && (s === "" || String(+p.solved) === s) && (p.title + p.categories + p.tags).toLowerCase().includes(q));
    App.$("#rows").innerHTML = r.map(p => `<tr onclick="location.hash='#/problems/${p.problem_id}'"><td>${p.solved ? App.i('check') : App.i('circle')}</td><td class="fw-medium">${p.title}</td><td>${App.chips(p.categories)}</td><td>${App.diff(p.difficulty)}</td><td>${p.acceptance}%</td></tr>`).join("") || `<tr><td colspan="5" class="text-center text-secondary py-4">No problems match.</td></tr>`;
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
    <div class="d-flex gap-2 mb-2"><select class="form-select w-auto">${DB.languages.map(l => `<option>${l.name}</option>`).join("")}</select><button id="run" class="btn btn-primary ms-auto">${App.i('play')} Submit</button></div>
    <div class="tabbar"><span class="on">solution.py</span><span>Testcases</span></div><div class="ed"><pre class="gut"></pre><textarea class="editor" spellcheck="false" wrap="off"></textarea></div>
  </div><div id="result"></div></div></div>`);
  const ed = App.$(".editor"), gut = App.$(".gut"); ed.value = "# Write your solution here\ndef solve(nums, target):\n    pass\n";
  const num = () => gut.textContent = ed.value.split("\n").map((_, i) => i + 1).join("\n"); ed.oninput = num; ed.onscroll = () => gut.style.transform = `translateY(${-ed.scrollTop}px)`; num();
  const bm = App.$("#bm"), paint = () => bm.textContent = bookmarks.has(id) ? "Saved" : "Save";
  bm.onclick = () => { bookmarks.has(id) ? bookmarks.delete(id) : bookmarks.add(id); paint(); }; paint();
  App.$("#run").onclick = () => {
    const r = App.$("#result"); r.innerHTML = `<div class="card p-3 text-secondary"><span class="spinner-border spinner-border-sm me-2"></span>Running (mock judge)…</div>`;
    setTimeout(() => {
      const ok = Math.random() > .35, rows = [["Sample 1", "ok"], ["Sample 2", "ok"], ["Hidden 1", "ok"], ["Hidden 2", ok ? "ok" : "fail"], ["Hidden 3", ok ? "ok" : "skip"]];
      r.innerHTML = `<div class="card p-3"><div class="d-flex justify-content-between mb-2"><strong>${ok ? "Accepted" : "Wrong Answer"}</strong>${App.status(ok ? "accepted" : "wrong_answer")}</div>
      <table class="table table-sm"><thead><tr><th>Test</th><th>Result</th><th>Runtime</th></tr></thead><tbody>${rows.map(([n, s]) => `<tr><td>${n}</td><td>${s === "ok" ? `<span style="color:var(--ok)">${App.i("check")}</span> Passed` : s === "fail" ? "Failed" : "Skipped"}</td><td>${s === "skip" ? "–" : 20 + Math.floor(Math.random() * 60) + " ms"}</td></tr>`).join("")}</tbody></table></div>`;
    }, 900);
  };
}
})();
