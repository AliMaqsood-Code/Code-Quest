(() => {
const E = App.esc;
App.pages.profile = () => {
  const u = DB.currentUser, since = Store.user ? new Date(Store.user.created_at).toLocaleDateString(undefined, { month: "short", year: "numeric" }) : "";
  const links = [...(u.github_url ? [{ label: "GitHub", url: u.github_url }] : []), ...u.links], saved = DB.bookmarks.map(id => DB.problems.find(p => p.problem_id === id)).filter(Boolean);
  App.view(`<div class="card p-4 mb-3"><div class="d-flex gap-3 align-items-center flex-wrap"><div class="av" style="width:72px;height:72px;font-size:1.4rem;border-radius:16px">${App.initials(u.display_name)}</div>
    <div class="flex-grow-1"><h2 class="h4 page-title m-0">${E(u.display_name)}</h2><div class="text-secondary small">@${E(u.username)} · ${E(u.email)}${u.country ? " · " + E(u.country) : ""} · ${u.roles.join(", ")} · member since ${since}</div>${u.bio ? `<div class="mt-1">${E(u.bio)}</div>` : ""}
    <div class="mt-2">${links.map(l => `<span class="chip">${E(l.label)}</span>`).join("")}</div></div>
    <div class="d-flex gap-2"><button class="btn btn-ghost btn-sm" data-bs-toggle="modal" data-bs-target="#edit">Edit profile</button><button id="out" class="btn btn-ghost btn-sm">Log out</button></div></div></div>
  <div class="row g-3"><div class="col-lg-7 d-grid gap-3 align-content-start"><div class="card p-3"><strong class="mb-2">Achievements</strong><div class="row g-2">${DB.achievements.map(a => `<div class="col-4"><div class="card ach ${a.earned ? "" : "locked"}"><div class="ico">${App.i(a.icon)}</div><div class="small fw-semibold">${a.name}</div><div class="small text-secondary">${a.desc}</div></div></div>`).join("")}</div></div>
    <div class="card p-3"><strong class="mb-2">Saved problems</strong>${saved.map(p => `<a href="#/problems/${p.problem_id}" class="d-flex justify-content-between py-2 border-top text-body"><span>${p.title}</span>${App.diff(p.difficulty)}</a>`).join("") || `<div class="small text-secondary">Nothing saved yet. Use “Save” on a problem page.</div>`}</div></div>
  <div class="col-lg-5"><div class="card p-3"><strong class="mb-2">Points ledger</strong>${DB.points.map(p => `<div class="d-flex justify-content-between py-2 border-top small"><span>${p.reason}<div class="text-secondary">${p.date}</div></span><strong class="${p.delta > 0 ? "text-success" : "text-danger"}">${p.delta > 0 ? "+" : ""}${p.delta}</strong></div>`).join("") || `<div class="small text-secondary">No activity yet.</div>`}</div></div></div>
  <div class="modal fade" id="edit" tabindex="-1"><div class="modal-dialog modal-dialog-centered"><div class="modal-content"><div class="modal-header border-0"><h5 class="modal-title">Edit profile</h5><button class="btn-close" data-bs-dismiss="modal"></button></div>
    <div class="modal-body d-grid gap-2"><input id="dn" class="form-control" placeholder="Display name" value="${E(u.display_name)}"><input id="co" class="form-control" placeholder="Country" value="${E(u.country)}"><input id="gh" class="form-control" placeholder="GitHub URL" value="${E(u.github_url)}"><textarea id="bi" class="form-control" rows="3" placeholder="Bio">${E(u.bio)}</textarea></div>
    <div class="modal-footer border-0"><button id="save" class="btn btn-primary btn-sm">Save</button></div></div></div></div>`);
  App.$("#out").onclick = () => App.$("#logout").click();
  App.$("#save").onclick = () => {
    u.display_name = App.$("#dn").value.trim() || u.display_name; u.country = App.$("#co").value.trim(); u.github_url = App.$("#gh").value.trim(); u.bio = App.$("#bi").value.trim(); Store.save();
    bootstrap.Modal.getInstance(App.$("#edit")).hide(); App.toast("Profile updated"); setTimeout(() => { App.shell(); App.pages.profile(); }, 300);
  };
};
})();
