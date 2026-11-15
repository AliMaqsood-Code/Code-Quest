/* Local-storage "backend": accounts, login session and per-user data.
   Replace with Flask API calls later (register/login/logout + fetch('/api/...')). */
const Store = {
  user: null,
  mem: {},
  read(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return k in Store.mem ? Store.mem[k] : d; } },
  write(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { Store.mem[k] = v; } },
  users: () => Store.read("ca_users", []),

  async hash(s) { // demo only: never store plain passwords, even in a demo
    try { const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("codearena:" + s)); return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join(""); }
    catch (e) { return btoa(unescape(encodeURIComponent("codearena:" + s))); }
  },

  async ensureDemo() { // seeded demo account: ada_dev / demo1234
    const us = Store.users();
    if (us.some(u => u.username === "ada_dev")) return;
    us.push({ user_id: 1, username: "ada_dev", email: "ada@example.com", password_hash: await Store.hash("demo1234"), created_at: Date.now() - 90 * 864e5 });
    Store.write("ca_users", us);
  },

  resume() { const id = Store.read("ca_session", null), u = Store.users().find(x => x.user_id === id); if (u) Store.open(u); },

  open(u) {
    Store.user = u; Store.write("ca_session", u.user_id);
    window.DB = Store.read("ca_state_" + u.user_id, null) || Store.fresh(u);
    DB.bookmarks = DB.bookmarks || []; DB.drafts = DB.drafts || {};
    Store.save();
  },

  fresh(u) { // demo user gets the full seed; new users start empty
    const d = JSON.parse(JSON.stringify(SEED));
    if (u.username === "ada_dev") return d;
    d.currentUser = { user_id: u.user_id, username: u.username, email: u.email, display_name: u.username, bio: "", country: "", github_url: "", points: 0, rank: null, streak: 0, roles: ["user"], links: [], base: { easy: 0, medium: 0, hard: 0 } };
    d.problems.forEach(p => p.solved = false); d.submissions = []; d.bookmarks = []; d.drafts = {};
    d.contests.forEach(c => c.registered = false);
    d.paths.forEach(p => p.steps.forEach(s => s.status = "not_started"));
    d.teams = []; d.groups = []; d.points = []; d.achievements.forEach(a => a.earned = false);
    d.leaderboard = d.leaderboard.filter(r => r.user !== "ada_dev");
    d.notifications = [{ id: 1, type: "welcome", title: "Welcome to CodeArena", message: "Pick a problem and submit your first solution.", url: "#/problems", created: Date.now(), read: false }];
    return d;
  },

  save() { if (Store.user && window.DB) Store.write("ca_state_" + Store.user.user_id, window.DB); },

  async register({ username, email, password, confirm }) { // returns error text, or null on success
    username = username.trim(); email = email.trim().toLowerCase();
    if (!/^[A-Za-z0-9_]{3,30}$/.test(username)) return "Username must be 3–30 characters: letters, numbers or underscore.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Enter a valid email address.";
    if (password.length < 8 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) return "Password needs 8+ characters with a letter and a number.";
    if (password !== confirm) return "Passwords do not match.";
    const us = Store.users();
    if (us.some(u => u.username.toLowerCase() === username.toLowerCase())) return "That username is already taken.";
    if (us.some(u => u.email === email)) return "That email is already registered.";
    const u = { user_id: Date.now(), username, email, password_hash: await Store.hash(password), created_at: Date.now() };
    us.push(u); Store.write("ca_users", us); Store.open(u); return null;
  },

  async login(id, password) {
    id = id.trim().toLowerCase();
    const u = Store.users().find(x => x.username.toLowerCase() === id || x.email === id);
    if (!u || u.password_hash !== await Store.hash(password)) return "Incorrect username/email or password.";
    Store.open(u); return null;
  },

  logout() { Store.save(); Store.write("ca_session", null); Store.user = null; window.DB = null; }
};
