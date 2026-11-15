(() => {
App.pages.dashboard = () => {
  const u = DB.currentUser, P = id => DB.problems.find(p => p.problem_id === id);
  const kpi = (v, l, d) => `<div class="col-6 col-xl-3"><div class="card kpi p-3"><div class="lbl">${l}</div><div class="v">${v}</div><div class="d">${d}</div></div></div>`;
  const live = DB.contests.find(c => c.status === "live"), path = DB.paths[0], done = path.steps.filter(s => s.status === "completed").length;
  let seed = 7, heat = ""; for (let i = 0; i < 182; i++) { seed = (seed * 9301 + 49297) % 233280; const r = seed / 233280; heat += `<i class="${r > .85 ? "l4" : r > .7 ? "l3" : r > .5 ? "l2" : r > .35 ? "l1" : ""}"></i>`; }
  const seg = [[74, "easy", "var(--ok)"], [38, "medium", "var(--warn)"], [6, "hard", "var(--bad)"]], tot = 118, C = 2 * Math.PI * 42; let off = 0;
  const ring = seg.map(([n, , c]) => { const l = n / tot * C - 3, s = `<circle cx="55" cy="55" r="42" fill="none" stroke="${c}" stroke-width="9" stroke-dasharray="${l} ${C - l}" stroke-dashoffset="${-off}" transform="rotate(-90 55 55)" stroke-linecap="round"/>`; off += n / tot * C; return s; }).join("");
  App.view(`
  <div class="d-flex justify-content-between align-items-end mb-4 flex-wrap gap-2"><div><h1 class="page-title m-0">Good evening, ${u.display_name.split(" ")[0]}</h1><div class="text-secondary">You're on a ${u.streak}-day streak. Solve one more today to extend it.</div></div><a href="#/problems/3" class="btn btn-primary">${App.i("play")} Daily problem</a></div>
  <div class="row g-3 mb-3">${kpi(tot, "Problems solved", "+4 this week")}${kpi(u.points.toLocaleString(), "Total points", "+170 this month")}${kpi("#" + u.rank, "Global rank", "↑ 12 places")}${kpi(u.streak + " days", "Current streak", "Best: 21 days")}</div>
  <div class="row g-3 mb-3">
    <div class="col-lg-8"><div class="card p-3 h-100"><div class="d-flex justify-content-between mb-3"><strong>Activity</strong><span class="lbl">Last 26 weeks</span></div><div class="heat">${heat}</div></div></div>
    <div class="col-lg-4"><div class="card p-3 h-100"><strong class="mb-2">Solved by difficulty</strong><div class="d-flex align-items-center gap-3"><svg width="110" height="110" viewBox="0 0 110 110">${ring}<text x="55" y="53" text-anchor="middle" font-size="20" font-weight="650" fill="currentColor">${tot}</text><text x="55" y="69" text-anchor="middle" font-size="9" fill="var(--mut)">SOLVED</text></svg>
    <div class="small w-100">${seg.map(([n, d, c]) => `<div class="d-flex justify-content-between py-1"><span class="text-capitalize"><span style="color:${c}">●</span> ${d}</span><b>${n}</b></div>`).join("")}</div></div></div></div></div>
  <div class="row g-3">
    <div class="col-lg-8"><div class="card"><div class="d-flex justify-content-between p-3 pb-2"><strong>Recent submissions</strong><a href="#/problems" class="small text-secondary">View all</a></div>
      <div class="table-responsive"><table class="table table-hover align-middle"><thead><tr><th>Problem</th><th>Language</th><th>Status</th><th>Runtime</th><th>When</th></tr></thead><tbody>
      ${DB.submissions.map(s => `<tr onclick="location.hash='#/problems/${s.problem_id}'"><td class="fw-medium">${P(s.problem_id).title}</td><td class="text-secondary">${s.language}</td><td>${App.status(s.status)}</td><td>${s.runtime_ms} ms</td><td class="text-secondary">${s.submitted_at}</td></tr>`).join("")}</tbody></table></div></div></div>
    <div class="col-lg-4 d-grid gap-3 align-content-start">
      <div class="card p-3"><div class="d-flex justify-content-between mb-1"><strong>${live.title}</strong>${App.status(live.status)}</div><div class="small text-secondary mb-3">${live.description} · ends ${live.ends}</div><a href="#/contests/${live.contest_id}" class="btn btn-outline-primary btn-sm">Enter contest</a></div>
      <div class="card p-3"><strong>${path.title}</strong><div class="small text-secondary mb-2">${done} of ${path.steps.length} steps complete</div><div class="progress mb-3"><div class="progress-bar" style="width:${done / path.steps.length * 100}%"></div></div><a href="#/learning" class="btn btn-outline-primary btn-sm">Continue</a></div>
    </div></div>`);
};
})();
