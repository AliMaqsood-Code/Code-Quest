(() => {
App.pages.teams = () => {
  const card = (name, desc, role, extra) => `<div class="col-md-6"><div class="card p-3 h-100"><div class="d-flex justify-content-between"><strong>${name}</strong><span class="chip">${role}</span></div><div class="small text-secondary mb-2">${desc}</div>${extra}</div></div>`;
  App.view(App.title("Teams & Groups", `<button class="btn btn-primary btn-sm" onclick="App.toast('Demo: create form goes here')">Create</button>`) + `
  ${DB.invitations.length ? `<div class="card p-3 mb-3"><strong class="mb-2">Pending invitations</strong>${DB.invitations.map((i, k) => `<div class="d-flex justify-content-between align-items-center py-1"><span class="small">${i.from} invited you to the ${i.type} <strong>${i.name}</strong></span><span><button class="btn btn-primary btn-sm" data-acc="${k}">Accept</button> <button class="btn btn-ghost btn-sm" data-acc="${k}">Decline</button></span></div>`).join("")}</div>` : ""}
  <h3 class="h6 text-secondary text-uppercase">Teams</h3><div class="row g-3 mb-4">${DB.teams.map(t => card(t.name, t.description, t.role, `<div>${t.members.map(m => `<span class="chip">${m.n}${m.r === "owner" ? " (owner)" : ""}</span>`).join("")}</div>`)).join("")}</div>
  <h3 class="h6 text-secondary text-uppercase">Private groups</h3><div class="row g-3">${DB.groups.map(g => card(g.name, g.description, g.role, `<div class="small">${g.members} members</div>`)).join("")}</div>`);
  document.querySelectorAll("[data-acc]").forEach(b => b.onclick = () => { DB.invitations.splice(+b.dataset.acc, 1); App.toast("Done"); App.pages.teams(); });
};
})();
