(() => {
const NEXT = { not_started: "in_progress", in_progress: "completed", completed: "not_started" }, LBL = { not_started: "Start", in_progress: "Mark done", completed: "Reset" };
App.pages.learning = () => {
  const ic = { completed: `<span style="color:var(--ok)">${App.i("check")}</span>`, in_progress: `<span style="color:var(--ac)">${App.i("clock")}</span>`, not_started: `<span class="text-secondary">${App.i("circle")}</span>` };
  App.view(App.title("Learning paths") + `<div class="row g-3">${DB.paths.map((p, pi) => {
    const done = p.steps.filter(s => s.status === "completed").length, pct = Math.round(done / p.steps.length * 100);
    return `<div class="col-lg-6"><div class="card p-3 h-100"><div class="d-flex justify-content-between"><strong>${p.title}</strong>${App.diff(p.difficulty)}</div>
    <div class="small text-secondary my-2">${p.description}</div><div class="progress mb-1"><div class="progress-bar" style="width:${pct}%"></div></div><div class="small text-secondary mb-3">${pct}% complete</div>
    ${p.steps.map((s, i) => `<div class="d-flex justify-content-between align-items-center py-2 border-top"><span>${ic[s.status]} ${i + 1}. ${s.title}</span><span class="d-flex align-items-center gap-2">${s.problem_id ? `<a class="small" href="#/problems/${s.problem_id}">Open</a>` : ""}<button class="btn btn-ghost btn-sm" data-step="${pi},${i}">${LBL[s.status]}</button></span></div>`).join("")}</div></div>`;
  }).join("")}</div>`);
  document.querySelectorAll("[data-step]").forEach(b => b.onclick = () => {
    const [pi, i] = b.dataset.step.split(",").map(Number), s = DB.paths[pi].steps[i]; s.status = NEXT[s.status];
    if (s.status === "completed") App.toast("Step completed: " + s.title); App.pages.learning();
  });
};
})();
