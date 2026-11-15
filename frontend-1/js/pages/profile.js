(() => {
App.pages.profile = () => {
  const u = DB.currentUser;
  App.view(`<div class="card p-4 mb-3"><div class="d-flex gap-3 align-items-center flex-wrap"><div class="av" style="width:72px;height:72px;font-size:1.4rem;border-radius:16px">${App.initials(u.display_name)}</div>
    <div class="flex-grow-1"><h2 class="h4 page-title m-0">${u.display_name}</h2><div class="text-secondary small">@${u.username} · ${u.country} · ${u.roles.join(", ")}</div><div class="mt-1">${u.bio}</div>
    <div class="mt-2">${[{ label: "GitHub", url: u.github_url }, ...u.links].map(l => `<a class="chip" href="#">${l.label}</a>`).join("")}</div></div>
    <button class="btn btn-ghost btn-sm" data-bs-toggle="modal" data-bs-target="#edit">Edit profile</button></div></div>
  <div class="row g-3"><div class="col-lg-7"><div class="card p-3"><strong class="mb-2">Achievements</strong><div class="row g-2">${DB.achievements.map(a => `<div class="col-4"><div class="card ach ${a.earned ? "" : "locked"}"><div class="ico">${App.i(a.icon)}</div><div class="small fw-semibold">${a.name}</div><div class="small text-secondary">${a.desc}</div></div></div>`).join("")}</div></div></div>
  <div class="col-lg-5"><div class="card p-3"><strong class="mb-2">Points ledger</strong>${DB.points.map(p => `<div class="d-flex justify-content-between py-2 border-top small"><span>${p.reason}<div class="text-secondary">${p.date}</div></span><strong class="${p.delta > 0 ? "text-success" : "text-danger"}">${p.delta > 0 ? "+" : ""}${p.delta}</strong></div>`).join("")}</div></div></div>
  <div class="modal fade" id="edit" tabindex="-1"><div class="modal-dialog modal-dialog-centered"><div class="modal-content"><div class="modal-header border-0"><h5 class="modal-title">Edit profile</h5><button class="btn-close" data-bs-dismiss="modal"></button></div>
    <div class="modal-body d-grid gap-2"><input id="dn" class="form-control" value="${u.display_name}"><textarea id="bi" class="form-control" rows="3">${u.bio}</textarea></div>
    <div class="modal-footer border-0"><button id="save" class="btn btn-primary btn-sm">Save</button></div></div></div></div>`);
  App.$("#save").onclick = () => { u.display_name = App.$("#dn").value || u.display_name; u.bio = App.$("#bi").value; bootstrap.Modal.getInstance(App.$("#edit")).hide(); App.toast("Profile updated"); setTimeout(() => { App.$("#me").innerHTML = `<div class="av">${App.initials(u.display_name)}</div><div><b>${u.display_name}</b><small>${u.points.toLocaleString()} pts</small></div>`; App.pages.profile(); }, 300); };
};
})();
