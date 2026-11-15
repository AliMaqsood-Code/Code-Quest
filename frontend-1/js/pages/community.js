(() => {
/* Discussions, published solutions, notifications */
App.pages.discussions = ([id]) => id ? thread(+id) : forum();
App.pages.notifications = () => {
  App.view(App.title("Notifications", `<button id="all" class="btn btn-sm btn-ghost">Mark all read</button>`) +
    `<div class="d-grid gap-2">${DB.notifications.map(n => `<a href="${n.url}" class="card p-3 text-body ${n.read ? "" : "unread"}"><div class="d-flex justify-content-between"><strong>${n.title}</strong><small class="text-secondary">${n.created}</small></div><div class="small text-secondary">${n.message}</div></a>`).join("")}</div>`);
  App.$("#all").onclick = () => { DB.notifications.forEach(n => n.read = true); App.pages.notifications(); App.updateBadge(); };
};

function forum() {
  App.view(App.title("Discussions", `<button class="btn btn-primary btn-sm" data-bs-toggle="collapse" data-bs-target="#new">New thread</button>`) + `
  <div id="new" class="collapse mb-3"><div class="card p-3 d-grid gap-2"><input id="nt" class="form-control" placeholder="Title"><textarea id="nb" class="form-control" rows="3" placeholder="What's on your mind?"></textarea><button id="post" class="btn btn-primary btn-sm ms-auto">Post</button></div></div>
  <ul class="nav nav-pills tabs mb-3"><li class="nav-item"><button class="nav-link active" data-bs-toggle="pill" data-bs-target="#t1">Threads</button></li><li class="nav-item"><button class="nav-link" data-bs-toggle="pill" data-bs-target="#t2">Solutions</button></li></ul>
  <div class="tab-content"><div class="tab-pane fade show active" id="t1"><div class="d-grid gap-2">${DB.discussions.map(d => `<a href="#/discussions/${d.discussion_id}" class="card hover p-3 text-body"><div class="d-flex justify-content-between"><strong>${d.is_locked ? "" : ""}${d.title}</strong><small class="text-secondary">${d.created}</small></div><div class="small text-secondary">by ${d.author} ${d.problem ? "· " + d.problem : ""} · ${d.comments.length}</div></a>`).join("")}</div></div>
  <div class="tab-pane fade" id="t2"><div class="card p-3"><table class="table align-middle"><thead><tr><th>Solution</th><th>Problem</th><th>Lang</th><th>Votes</th></tr></thead><tbody>${DB.solutions.map(s => `<tr><td>${s.title} ${s.official ? '<span class="badge st-live">Official</span>' : ""}<div class="small text-secondary">by ${s.author}</div></td><td>${s.problem}</td><td>${s.language}</td><td>▲ ${s.votes}</td></tr>`).join("")}</tbody></table></div></div></div>`);
  App.$("#post").onclick = () => {
    const t = App.$("#nt").value.trim(); if (!t) return App.toast("Please add a title");
    DB.discussions.unshift({ discussion_id: Date.now(), title: t, author: DB.currentUser.username, problem: null, created: "just now", is_locked: false, body: App.$("#nb").value, comments: [] });
    App.toast("Thread posted"); forum();
  };
}

function thread(id) {
  const d = DB.discussions.find(x => x.discussion_id === id); if (!d) return forum();
  const cm = (c, nested) => `<div class="${nested ? "comment mt-2" : "card p-3 mb-2"}"><div class="small"><strong>${c.author}</strong> <span class="text-secondary">· ${c.created}</span></div><div>${c.body}</div><div class="small mt-1"><a href="#" data-like>▲ ${c.reactions}</a></div>${c.replies.map(r => cm({ ...r, replies: [] }, true)).join("")}</div>`;
  App.view(`<a href="#/discussions" class="small">← All threads</a><div class="card p-3 my-3"><h2 class="h4 page-title">${d.title}</h2><div class="small text-secondary mb-2">by ${d.author} · ${d.created}</div><p class="m-0">${d.body}</p></div>
  ${d.comments.map(c => cm(c)).join("")}
  ${d.is_locked ? `<div class="alert alert-secondary">This thread is locked.</div>` : `<div class="card p-3"><textarea id="cb" class="form-control mb-2" rows="2" placeholder="Write a reply…"></textarea><button id="rep" class="btn btn-primary btn-sm ms-auto">Reply</button></div>`}`);
  document.querySelectorAll("[data-like]").forEach(a => a.onclick = e => { e.preventDefault(); a.textContent = "▲ " + (parseInt(a.textContent.replace(/\D/g, "")) + 1); });
  const r = App.$("#rep"); if (r) r.onclick = () => { const b = App.$("#cb").value.trim(); if (!b) return; d.comments.push({ author: DB.currentUser.username, body: b, created: "just now", reactions: 0, replies: [] }); thread(id); };
}
})();
