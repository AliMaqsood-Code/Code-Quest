(() => {
const fld = (id, label, type = "text") => `<div class="mb-3"><label class="form-label small mb-1" for="${id}">${label}</label><input id="${id}" type="${type}" class="form-control" autocomplete="off"></div>`;

App.auth = mode => {
  const reg = mode === "register";
  App.$("#auth").innerHTML = `<div class="card auth-card fade-in">
    <div class="d-flex justify-content-between align-items-center mb-4"><span class="brand p-0"><span class="logo">{ }</span>CodeArena</span><button id="at" type="button" class="icon-btn" title="Toggle theme"></button></div>
    <h1 class="page-title mb-1">${reg ? "Create your account" : "Welcome back"}</h1>
    <div class="text-secondary small mb-3">${reg ? "Solve problems, enter contests and track your progress." : "Log in to continue practising."}</div>
    <div id="err" class="alert alert-danger py-2 d-none"></div>
    ${reg ? fld("u", "Username") + fld("e", "Email", "email") + fld("p", "Password", "password") + fld("c", "Confirm password", "password") : fld("u", "Username or email") + fld("p", "Password", "password")}
    <button id="go" class="btn btn-primary w-100">${reg ? "Create account" : "Log in"}</button>
    ${reg ? "" : `<button id="demo" type="button" class="btn btn-ghost w-100 mt-2">Use demo account</button><div class="small text-secondary text-center mt-2">Demo login: <code>ada_dev</code> / <code>demo1234</code></div>`}
    <div class="small text-secondary text-center mt-3">${reg ? `Already have an account? <a href="#/login" class="fw-semibold">Log in</a>` : `New here? <a href="#/register" class="fw-semibold">Create an account</a>`}</div></div>`;

  const v = id => (App.$("#" + id) || {}).value || "", go = App.$("#go"), box = App.$("#err");
  const run = async () => {
    go.disabled = true; box.classList.add("d-none");
    const err = reg ? await Store.register({ username: v("u"), email: v("e"), password: v("p"), confirm: v("c") }) : await Store.login(v("u"), v("p"));
    go.disabled = false;
    if (err) { box.textContent = err; box.classList.remove("d-none"); return; }
    location.hash = "#/dashboard"; App.toast("Welcome, " + DB.currentUser.username + "!");
  };
  go.onclick = run;
  document.querySelectorAll("#auth input").forEach(i => i.onkeydown = e => e.key === "Enter" && run());
  const d = App.$("#demo"); if (d) d.onclick = () => { App.$("#u").value = "ada_dev"; App.$("#p").value = "demo1234"; run(); };
  const at = App.$("#at"); at.innerHTML = App.$("#theme").innerHTML;
  at.onclick = () => { App.$("#theme").click(); at.innerHTML = App.$("#theme").innerHTML; };
  App.$("#u").focus();
};
})();
