(() => {
const E = App.esc;
App.pages.discussions = ([id]) => id ? thread(+id) : forum();

App.pages.notifications = () => {
  const L = DB.notifications;
  App.view(App.title("Notifications", `<button id="all" class="btn btn-sm btn-ghost">Mark all read</button>`) +
    (L.length ? `<div class="d-grid gap-2">${L.map(n => `<a href="${n.url}" data-n="${n.id}" class="card p-3 text-body ${n.read ? "" : "unread"}"><div class="d-flex justify-content-between"><strong>${E(n.title)}</strong><small class="text-secondary">${App.ago(n.created)}</small></div><div class="small text-secondary">${E(n.message)}</div></a>`).join("")}</div>` : `<div class="card p-4 text-center text-secondary">You're all caught up.</div>`));
  App.$("#all").onclick = () => { L.forEach(n => n.read = true); App.pages.notifications(); App.updateBadge(); };
  document.querySelectorAll("[data-n]").forEach(a => a.addEventListener("click", () => {
    const n = L.find(x => x.id === +a.dataset.n); if (n) n.read = true; a.classList.remove("unread"); Store.save(); App.updateBadge();
  }));
};

function forum(tab) {
  App.view(App.title("Discussions", `<button class="btn btn-primary btn-sm" data-bs-toggle="collapse" data-bs-target="#new">New thread</button>`) + `
  <div id="new" class="collapse mb-3"><div class="card p-3 d-grid gap-2"><input id="nt" class="form-control" placeholder="Title"><textarea id="nb" class="form-control" rows="3" placeholder="What's on your mind?"></textarea><button id="post" class="btn btn-primary btn-sm ms-auto">Post</button></div></div>
  <ul class="nav nav-pills tabs mb-3"><li class="nav-item"><button class="nav-link active" data-bs-toggle="pill" data-bs-target="#t1">Threads</button></li><li class="nav-item"><button class="nav-link" data-bs-toggle="pill" data-bs-target="#t2">Solutions</button></li></ul>
  <div class="tab-content">
  <div class="tab-pane fade show active" id="t1"><div class="d-grid gap-2">${DB.discussions.map(d => `<a href="#/discussions/${d.discussion_id}" class="card hover p-3 text-body"><div class="d-flex justify-content-between"><strong>${E(d.title)}</strong><small class="text-secondary">${App.ago(d.created)}</small></div><div class="small text-secondary">by ${E(d.author)} ${d.problem ? "· " + E(d.problem) : ""} · ${d.comments.length} replies${d.is_locked ? " · locked" : ""}</div></a>`).join("")}</div></div>
  <div class="tab-pane fade" id="t2"><div class="card p-3"><div class="d-flex justify-content-end mb-2"><button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#pub">Publish solution</button></div>
    <div class="table-responsive"><table class="table align-middle"><thead><tr><th>Solution</th><th>Problem</th><th>Lang</th><th>Votes</th></tr></thead><tbody>${DB.solutions.map((s, i) => `<tr><td>${E(s.title)} ${s.official ? '<span class="badge st-live">Official</span>' : ""}<div class="small text-secondary">by ${E(s.author)}</div></td><td>${E(s.problem)}</td><td>${E(s.language)}</td><td><button class="btn btn-ghost btn-sm" data-vote="${i}">${s.voted ? "▲" : "△"} ${s.votes}</button> <button class="btn btn-ghost btn-sm" data-view="${i}">View</button></td></tr>`).join("")}</tbody></table></div></div></div></div>

  <div class="modal fade" id="pub" tabindex="-1"><div class="modal-dialog modal-dialog-centered modal-lg"><div class="modal-content"><div class="modal-header border-0"><h5 class="modal-title">Publish a solution</h5><button class="btn-close" data-bs-dismiss="modal"></button></div>
    <div class="modal-body d-grid gap-2"><div class="row g-2"><div class="col-md-6"><select id="sp" class="form-select">${DB.problems.map(p => `<option value="${p.problem_id}">${p.title}</option>`).join("")}</select></div><div class="col-md-6"><select id="sl" class="form-select">${DB.languages.map(l => `<option>${l.name}</option>`).join("")}</select></div></div>
    <input id="st" class="form-control" placeholder="Title"><textarea id="se" class="form-control" rows="2" placeholder="Explanation"></textarea><textarea id="sc" class="form-control" rows="6" placeholder="Code" style="font-family:'JetBrains Mono',monospace"></textarea></div>
    <div class="modal-footer border-0"><button id="sgo" class="btn btn-primary btn-sm">Publish</button></div></div></div></div>
  <div class="modal fade" id="view" tabindex="-1"><div class="modal-dialog modal-dialog-centered modal-lg"><div class="modal-content"><div class="modal-header border-0"><h5 class="modal-title" id="vt"></h5><button class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body"><p id="ve" class="small text-secondary"></p><pre class="code" id="vc"></pre></div></div></div></div>`);

  if (tab === 2) App.$('[data-bs-target="#t2"]').click();

  App.$("#post").onclick = () => {
    const t = App.$("#nt").value.trim(); if (!t) return App.toast("Please add a title");
    DB.discussions.unshift({ discussion_id: Date.now(), title: t, author: DB.currentUser.username, problem: null, created: Date.now(), is_locked: false, body: App.$("#nb").value.trim(), comments: [] });
    App.toast("Thread posted"); forum();
  };
  document.querySelectorAll("[data-vote]").forEach(b => b.onclick = () => { const s = DB.solutions[+b.dataset.vote]; s.voted = !s.voted; s.votes += s.voted ? 1 : -1; forum(2); });
  document.querySelectorAll("[data-view]").forEach(b => b.onclick = () => {
    const s = DB.solutions[+b.dataset.view];
    App.$("#vt").textContent = s.title; App.$("#ve").textContent = s.explanation || "No explanation provided."; App.$("#vc").textContent = s.code || "# Code not included for this demo entry.";
    bootstrap.Modal.getOrCreateInstance(App.$("#view")).show();
  });
  App.$("#sgo").onclick = () => {
    const t = App.$("#st").value.trim(), c = App.$("#sc").value; if (!t || !c.trim()) return App.toast("Add a title and some code");
    const p = DB.problems.find(x => x.problem_id === +App.$("#sp").value);
    DB.solutions.unshift({ title: t, author: DB.currentUser.username, problem: p.title, language: App.$("#sl").value, votes: 0, official: false, explanation: App.$("#se").value.trim(), code: c });
    bootstrap.Modal.getInstance(App.$("#pub")).hide(); App.toast("Solution published"); setTimeout(() => forum(2), 300);
  };
}

function thread(id) {
  const d = DB.discussions.find(x => x.discussion_id === id); if (!d) return forum();
  const cm = (c, ci, ri) => `<div class="${ri == null ? "card p-3 mb-2" : "comment mt-2"}"><div class="small"><strong>${E(c.author)}</strong> <span class="text-secondary">· ${App.ago(c.created)}</span></div><div>${E(c.body)}</div>
    <div class="small mt-1 d-flex gap-3"><a href="#" data-like="${ci},${ri == null ? "" : ri}" class="${c.liked ? "fw-bold" : ""}">▲ ${c.reactions}</a>${ri == null && !d.is_locked ? `<a href="#" data-rep="${ci}">Reply</a>` : ""}</div>
    ${ri == null ? `<div id="rb${ci}"></div>${c.replies.map((r, k) => cm(r, ci, k)).join("")}` : ""}</div>`;
  App.view(`<a href="#/discussions" class="small">← All threads</a><div class="card p-3 my-3"><h2 class="h4 page-title">${E(d.title)}</h2><div class="small text-secondary mb-2">by ${E(d.author)} · ${App.ago(d.created)}</div><p class="m-0">${E(d.body)}</p></div>
  ${d.comments.map((c, i) => cm(c, i)).join("")}
  ${d.is_locked ? `<div class="alert alert-secondary">This thread is locked.</div>` : `<div class="card p-3"><textarea id="cb" class="form-control mb-2" rows="2" placeholder="Write a reply…"></textarea><button id="rep" class="btn btn-primary btn-sm ms-auto">Reply</button></div>`}`);

  document.querySelectorAll("[data-like]").forEach(a => a.onclick = e => {
    e.preventDefault(); const [ci, ri] = a.dataset.like.split(","), c = ri === "" ? d.comments[ci] : d.comments[ci].replies[+ri];
    c.liked = !c.liked; c.reactions += c.liked ? 1 : -1; thread(id);
  });
  document.querySelectorAll("[data-rep]").forEach(a => a.onclick = e => {
    e.preventDefault(); const ci = +a.dataset.rep, box = App.$("#rb" + ci);
    box.innerHTML = `<div class="d-flex gap-2 my-2"><input class="form-control form-control-sm" placeholder="Write a reply…"><button class="btn btn-primary btn-sm">Send</button></div>`;
    const inp = box.querySelector("input"); inp.focus();
    box.querySelector("button").onclick = () => { const b = inp.value.trim(); if (!b) return; d.comments[ci].replies.push({ author: DB.currentUser.username, body: b, created: Date.now(), reactions: 0 }); thread(id); };
  });
  const r = App.$("#rep");
  if (r) r.onclick = () => { const b = App.$("#cb").value.trim(); if (!b) return; d.comments.push({ author: DB.currentUser.username, body: b, created: Date.now(), reactions: 0, replies: [] }); thread(id); };
}
})();
