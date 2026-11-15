/* Core: router, theme, icons, helpers. Pages register on App.pages. */
const P = {home:"M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",code:"m16 18 6-6-6-6M8 6l-6 6 6 6",trophy:"M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0zM17 5h3v2a3 3 0 0 1-3 3M7 5H4v2a3 3 0 0 0 3 3",chat:"M21 12a8 8 0 0 1-11.6 7.1L3 21l1.9-5.4A8 8 0 1 1 21 12z",book:"M4 5a2 2 0 0 1 2-2h14v15H6a2 2 0 0 0-2 2zM4 20a2 2 0 0 0 2 2h14v-4",users:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8",bell:"M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10.3 21a1.9 1.9 0 0 0 3.4 0",sun:"M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zM12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4",moon:"M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z",check:"M20 6 9 17l-5-5",circle:"M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z",play:"M6 4l14 8-14 8z",search:"m21 21-4.3-4.3M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14z",star:"m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z",flame:"M12 22c4 0 7-3 7-7 0-4-3-6-4-10-3 2-5 5-5 8-1-1-2-2-2-4-2 2-3 4-3 6 0 4 3 7 7 7z",lock:"M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4",plus:"M12 5v14M5 12h14",menu:"M3 6h18M3 12h18M3 18h18",clock:"M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2",msg:"M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",up:"m18 15-6-6-6 6",bulb:"M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z",flag:"M4 22V4M4 4h14l-2 4 2 4H4",crown:"m3 7 4 4 5-7 5 7 4-4-2 12H5z",bookmark:"M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z",zap:"M13 2 3 14h9l-1 8 10-12h-9z"};
const App = {
  pages: {}, q: "",
  nav: [["dashboard","Dashboard","home"],["problems","Problems","code"],["contests","Contests","trophy"],["discussions","Discuss","chat"],["learning","Learn","book"],["teams","Teams","users"]],
  $: (s, r = document) => r.querySelector(s),
  i: n => `<svg class="i" viewBox="0 0 24 24"><path d="${P[n] || P.circle}"/></svg>`,
  esc: s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])),
  ago(t) { if (typeof t === "string") return t; const m = Math.floor((Date.now() - t) / 6e4); return m < 1 ? "just now" : m < 60 ? m + "m ago" : m < 1440 ? Math.floor(m / 60) + "h ago" : Math.floor(m / 1440) + "d ago"; },
  notify(title, message, url = "#/notifications") { DB.notifications.unshift({ id: Date.now(), type: "info", title, message, url, created: Date.now(), read: false }); Store.save(); App.updateBadge(); },
  view: h => { App.$("#view").innerHTML = `<div class="fade-in">${h}</div>`; window.scrollTo(0, 0); Store.save(); },
  diff: d => `<span class="badge diff-${d} text-capitalize">${d}</span>`,
  status: s => `<span class="badge st-${s}">${s.replace("_", " ")}</span>`,
  chips: a => a.map(x => `<span class="chip">${x}</span>`).join(""),
  title: (t, right = "") => `<div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2"><h2 class="page-title m-0">${t}</h2>${right}</div>`,
  toast(msg) {
    let t = App.$("#toast");
    if (!t) { document.body.insertAdjacentHTML("beforeend", `<div class="position-fixed bottom-0 end-0 p-3" style="z-index:2000"><div id="toast" class="toast align-items-center border"><div class="toast-body"></div></div></div>`); t = App.$("#toast"); }
    App.$(".toast-body", t).textContent = msg; bootstrap.Toast.getOrCreateInstance(t, { delay: 2200 }).show();
  },
  setTheme(m) {
    document.documentElement.dataset.bsTheme = m; App.$("#theme").innerHTML = App.i(m === "dark" ? "sun" : "moon");
    try { localStorage.setItem("theme", m); } catch (e) {}
  },
  updateBadge() { App.$("#notif-count").textContent = window.DB ? DB.notifications.filter(n => !n.read).length || "" : ""; },
  initials: n => (n || "?").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase(),
  shell() {
    const u = DB.currentUser;
    App.$("#links").innerHTML = App.nav.map(([k, l, ic]) => `<a data-p="${k}" href="#/${k}">${App.i(ic)}${l}</a>`).join("");
    App.$("#me").innerHTML = `<div class="av">${App.initials(u.display_name)}</div><div><b>${App.esc(u.display_name)}</b><small>${u.points.toLocaleString()} pts</small></div>`;
  },
  route() {
    const [p, ...a] = (location.hash.slice(2) || "dashboard").split("/"), authPg = p === "login" || p === "register";
    if (!Store.user) {
      document.body.classList.add("auth-mode");
      if (!authPg) { location.hash = "#/login"; return; }
      return App.auth(p);
    }
    if (authPg) { location.hash = "#/dashboard"; return; }
    document.body.classList.remove("auth-mode"); App.shell();
    const n = App.nav.find(x => x[0] === p);
    document.querySelectorAll("#links a").forEach(l => l.classList.toggle("active", l.dataset.p === p));
    App.$("#crumb").innerHTML = `<span>CodeArena /</span> ${n ? n[1] : p[0].toUpperCase() + p.slice(1)}`;
    App.$("#side").classList.remove("open"); (App.pages[p] || App.pages.dashboard)(a); App.updateBadge();
  },
  async start() {
    await Store.ensureDemo(); Store.resume();
    App.$("#bell").insertAdjacentHTML("afterbegin", App.i("bell")); App.$("#menu").innerHTML = App.i("menu"); App.$("#s-ico").innerHTML = App.i("search");
    App.$("#menu").onclick = () => App.$("#side").classList.toggle("open");
    App.$("#gs").onkeydown = e => { if (e.key !== "Enter") return; App.q = e.target.value; e.target.value = ""; location.hash === "#/problems" ? App.route() : location.hash = "#/problems"; };
    App.$("#logout").onclick = () => { Store.logout(); location.hash = "#/login"; };
    let m = "light"; try { m = localStorage.getItem("theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"); } catch (e) {}
    App.setTheme(m);
    App.$("#theme").onclick = () => App.setTheme(document.documentElement.dataset.bsTheme === "dark" ? "light" : "dark");
    addEventListener("hashchange", App.route); addEventListener("pagehide", () => Store.save()); App.route();
  }
};
