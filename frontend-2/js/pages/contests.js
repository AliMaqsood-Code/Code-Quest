(() => {
App.pages.contests = ([id]) => id ? detail(+id) : list();

function list() {
  App.view(App.title("Contests") + `<div class="row g-3">${DB.contests.map(c => `<div class="col-md-6 col-lg-4"><div class="card hover p-3 h-100">
    <div class="d-flex justify-content-between"><strong>${c.title}</strong>${App.status(c.status)}</div>
    <div class="small text-secondary my-2">${c.description}</div>
    <div class="small mb-3">${c.starts} → ${c.ends}<br>${c.participants} participants · ${c.problems.length} problems</div>
    <div class="mt-auto d-flex gap-2"><a href="#/contests/${c.contest_id}" class="btn btn-outline-primary btn-sm">Details</a>
    ${c.status !== "ended" ? `<button class="btn btn-sm ${c.registered ? "btn-ghost" : "btn-primary"}" data-reg="${c.contest_id}">${c.registered ? "Registered" : "Register"}</button>` : ""}</div></div></div>`).join("")}</div>`);
  document.querySelectorAll("[data-reg]").forEach(b => b.onclick = () => {
    const c = DB.contests.find(x => x.contest_id === +b.dataset.reg); c.registered = !c.registered; c.participants += c.registered ? 1 : -1; if (c.registered) App.notify("Registered for " + c.title, c.starts + " → " + c.ends, "#/contests/" + c.contest_id);
    App.toast(c.registered ? "Registered for " + c.title : "Registration cancelled"); list();
  });
}

function detail(id) {
  const c = DB.contests.find(x => x.contest_id === id); if (!c) return list();
  App.view(`<a href="#/contests" class="small">← All contests</a>
  <div class="mt-2">${App.title(c.title, App.status(c.status))}</div>
  <div class="alert alert-primary py-2 small">Announcement: Clarifications will be posted here during the contest.</div>
  <div class="row g-3"><div class="col-lg-5"><div class="card p-3"><strong class="mb-2">Problems</strong>
    ${c.problems.map((pid, i) => { const p = DB.problems.find(x => x.problem_id === pid); return `<a href="#/problems/${pid}" class="d-flex justify-content-between py-2 border-bottom text-body"><span>${String.fromCharCode(65 + i)}. ${p.title}</span><span>${App.diff(p.difficulty)} <small class="text-secondary">${(i + 1) * 100} pts</small></span></a>`; }).join("")}</div></div>
  <div class="col-lg-7"><div class="card p-3"><strong class="mb-2">Leaderboard</strong><div class="table-responsive"><table class="table align-middle"><thead><tr><th>#</th><th>User</th><th>Score</th><th>Solved</th><th>Penalty</th></tr></thead><tbody>
    ${DB.leaderboard.map((r, i) => `<tr class="${r.user === DB.currentUser.username ? "table-active" : ""}"><td class="rank-${i + 1}">${i + 1}</td><td>${r.user}</td><td>${r.score}</td><td>${r.solved}</td><td>${Math.floor(r.penalty / 60)}m</td></tr>`).join("")}</tbody></table></div></div></div></div>`);
}
})();
