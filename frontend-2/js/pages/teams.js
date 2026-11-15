(() => {
const E = App.esc;
App.pages.teams = () => {
  const card = (name, desc, role, extra, kind, id) => `<div class="col-md-6"><div class="card p-3 h-100"><div class="d-flex justify-content-between"><strong>${E(name)}</strong><span class="chip">${role}</span></div><div class="small text-secondary mb-2">${E(desc) || "No description"}</div>${extra}<div class="mt-auto pt-2"><button class="btn btn-ghost btn-sm" data-out="${kind},${id}">${role === "owner" ? "Delete" : "Leave"}</button></div></div></div>`;
  const empty = t => `<div class="col-12"><div class="card p-3 text-secondary small">${t}</div></div>`;
  App.view(App.title("Teams & Groups", `<button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#mk">Create</button>`) + `
  ${DB.invitations.length ? `<div class="card p-3 mb-3"><strong class="mb-2">Pending invitations</strong>${DB.invitations.map((i, k) => `<div class="d-flex justify-content-between align-items-center py-1"><span class="small">${E(i.from)} invited you to the ${i.type} <strong>${E(i.name)}</strong></span><span><button class="btn btn-primary btn-sm" data-inv="${k},1">Accept</button> <button class="btn btn-ghost btn-sm" data-inv="${k},0">Decline</button></span></div>`).join("")}</div>` : ""}
  <h3 class="h6 text-secondary text-uppercase">Teams</h3><div class="row g-3 mb-4">${DB.teams.map(t => card(t.name, t.description, t.role, `<div>${t.members.map(m => `<span class="chip">${E(m.n)}${m.r === "owner" ? " (owner)" : ""}</span>`).join("")}</div>`, "team", t.team_id)).join("") || empty("You are not in any team yet. Create one to get started.")}</div>
  <h3 class="h6 text-secondary text-uppercase">Private groups</h3><div class="row g-3">${DB.groups.map(g => card(g.name, g.description, g.role, `<div class="small">${g.members} members</div>`, "group", g.group_id)).join("") || empty("No private groups yet.")}</div>
  <div class="modal fade" id="mk" tabindex="-1"><div class="modal-dialog modal-dialog-centered"><div class="modal-content"><div class="modal-header border-0"><h5 class="modal-title">Create</h5><button class="btn-close" data-bs-dismiss="modal"></button></div>
    <div class="modal-body d-grid gap-2"><select id="mt" class="form-select"><option value="team">Team</option><option value="group">Private group</option></select><input id="mn" class="form-control" placeholder="Name"><textarea id="md" class="form-control" rows="2" placeholder="Description (optional)"></textarea></div>
    <div class="modal-footer border-0"><button id="mc" class="btn btn-primary btn-sm">Create</button></div></div></div></div>`);
  const me = DB.currentUser.username, done = msg => { App.toast(msg); setTimeout(App.pages.teams, 300); };
  App.$("#mc").onclick = () => {
    const n = App.$("#mn").value.trim(), d = App.$("#md").value.trim(), t = App.$("#mt").value; if (!n) return App.toast("Please enter a name");
    t === "team" ? DB.teams.push({ team_id: Date.now(), name: n, description: d, role: "owner", members: [{ n: me, r: "owner" }] }) : DB.groups.push({ group_id: Date.now(), name: n, description: d, role: "owner", members: 1 });
    bootstrap.Modal.getInstance(App.$("#mk")).hide(); done(`${t === "team" ? "Team" : "Group"} created`);
  };
  document.querySelectorAll("[data-inv]").forEach(b => b.onclick = () => {
    const [k, ok] = b.dataset.inv.split(",").map(Number), i = DB.invitations.splice(k, 1)[0];
    if (ok) i.type === "team" ? DB.teams.push({ team_id: Date.now(), name: i.name, description: "Joined by invitation", role: "member", members: [{ n: i.from, r: "owner" }, { n: me, r: "member" }] }) : DB.groups.push({ group_id: Date.now(), name: i.name, description: "Joined by invitation", role: "member", members: 2 });
    App.toast(ok ? "Joined " + i.name : "Invitation declined"); App.pages.teams();
  });
  document.querySelectorAll("[data-out]").forEach(b => b.onclick = () => {
    const [kind, id] = b.dataset.out.split(","), L = kind === "team" ? DB.teams : DB.groups, k = kind === "team" ? "team_id" : "group_id";
    if (!confirm("Are you sure?")) return; L.splice(L.findIndex(x => String(x[k]) === id), 1); App.toast("Done"); App.pages.teams();
  });
};
})();
