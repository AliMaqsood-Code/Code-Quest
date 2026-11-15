(() => {
App.pages.learning = () => {
  const ic = { completed: `<span style="color:var(--ok)">${App.i("check")}</span>`, in_progress: `<span style="color:var(--ac)">${App.i("clock")}</span>`, not_started: `<span class="text-secondary">${App.i("circle")}</span>` };
  App.view(App.title("Learning paths") + `<div class="row g-3">${DB.paths.map(p => {
    const done = p.steps.filter(s => s.status === "completed").length, pct = Math.round(done / p.steps.length * 100);
    return `<div class="col-lg-6"><div class="card p-3 h-100"><div class="d-flex justify-content-between"><strong>${p.title}</strong>${App.diff(p.difficulty)}</div>
    <div class="small text-secondary my-2">${p.description}</div><div class="progress mb-1"><div class="progress-bar" style="width:${pct}%"></div></div><div class="small text-secondary mb-3">${pct}% complete</div>
    ${p.steps.map((s, i) => `<div class="d-flex justify-content-between py-2 border-top"><span>${ic[s.status]} ${i + 1}. ${s.title}</span>${App.status(s.status)}</div>`).join("")}</div></div>`;
  }).join("")}</div>`);
};
})();
