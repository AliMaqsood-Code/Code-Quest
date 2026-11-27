/* ===== DEMO DATA — edit freely. Field names mirror the database schema. ===== */
window.DB = {
  currentUser: { user_id: 1, username: "ada_dev", email: "ada@example.com", display_name: "Ada Lovelace", bio: "Backend dev who loves graphs and coffee.", country: "UK", github_url: "github.com/ada", points: 2840, rank: 128, streak: 12, roles: ["user"], links: [{label:"Portfolio",url:"ada.dev"},{label:"LinkedIn",url:"linkedin.com/in/ada"}] },
  languages: [
    { language_version_id: 1, name: "Python 3.12" }, { language_version_id: 2, name: "JavaScript (Node 20)" },
    { language_version_id: 3, name: "Java 21" }, { language_version_id: 4, name: "C++ 17" }
  ],
  problems: [
    { problem_id: 1, slug: "two-sum", title: "Two Sum", difficulty: "easy", categories: ["Arrays","Hash Tables"], tags: ["beginner"], acceptance: 52, solved: true, time_limit_ms: 1000, memory_limit_mb: 256,
      statement: "Given an array of integers <code>nums</code> and an integer <code>target</code>, return the indices of the two numbers that add up to <code>target</code>. Each input has exactly one solution.",
      examples: [{input:"nums = [2,7,11,15], target = 9", output:"[0,1]", explanation:"nums[0] + nums[1] = 9"}], hints: ["Think about what value you need to find for each element.","A hash map gives O(1) lookups."] },
    { problem_id: 2, slug: "valid-parentheses", title: "Valid Parentheses", difficulty: "easy", categories: ["Stacks","Strings"], tags: ["stack"], acceptance: 41, solved: true, time_limit_ms: 1000, memory_limit_mb: 256,
      statement: "Given a string containing only <code>()[]{}</code>, determine whether the brackets are correctly matched and nested.",
      examples: [{input:'s = "()[]{}"', output:"true", explanation:"All pairs close in order."}], hints: ["A stack mirrors nesting."] },
    { problem_id: 3, slug: "longest-substring", title: "Longest Substring Without Repeats", difficulty: "medium", categories: ["Strings","Sliding Window"], tags: ["two-pointers"], acceptance: 34, solved: false, time_limit_ms: 2000, memory_limit_mb: 256,
      statement: "Given a string <code>s</code>, find the length of the longest substring without repeating characters.",
      examples: [{input:'s = "abcabcbb"', output:"3", explanation:'The answer is "abc".'}], hints: ["Maintain a window and a set of seen characters."] },
    { problem_id: 4, slug: "course-schedule", title: "Course Schedule", difficulty: "medium", categories: ["Graphs"], tags: ["topological-sort","bfs"], acceptance: 45, solved: false, time_limit_ms: 2000, memory_limit_mb: 256,
      statement: "There are <code>n</code> courses with prerequisite pairs. Determine whether you can finish all courses (i.e. the graph has no cycle).",
      examples: [{input:"n = 2, prerequisites = [[1,0]]", output:"true", explanation:"Take course 0 then 1."}], hints: ["Detect a cycle with Kahn's algorithm."] },
    { problem_id: 5, slug: "median-two-sorted", title: "Median of Two Sorted Arrays", difficulty: "hard", categories: ["Arrays","Binary Search"], tags: ["divide-conquer"], acceptance: 29, solved: false, time_limit_ms: 2000, memory_limit_mb: 256,
      statement: "Given two sorted arrays, return the median of the combined array in <code>O(log(m+n))</code> time.",
      examples: [{input:"nums1 = [1,3], nums2 = [2]", output:"2.0", explanation:"Merged: [1,2,3]."}], hints: ["Binary search the partition of the smaller array."] },
    { problem_id: 6, slug: "word-ladder", title: "Word Ladder", difficulty: "hard", categories: ["Graphs","Strings"], tags: ["bfs"], acceptance: 27, solved: false, time_limit_ms: 3000, memory_limit_mb: 512,
      statement: "Find the length of the shortest transformation sequence from <code>beginWord</code> to <code>endWord</code>, changing one letter at a time.",
      examples: [{input:'hit → cog', output:"5", explanation:"hit → hot → dot → dog → cog"}], hints: ["Model words as graph nodes and run BFS."] }
  ],
  submissions: [
    { id: 9041, problem_id: 1, language: "Python 3.12", status: "accepted", runtime_ms: 48, submitted_at: "2 hours ago" },
    { id: 9038, problem_id: 3, language: "Python 3.12", status: "wrong_answer", runtime_ms: 61, submitted_at: "Yesterday" },
    { id: 9020, problem_id: 2, language: "JavaScript (Node 20)", status: "accepted", runtime_ms: 72, submitted_at: "2 days ago" }
  ],
  contests: [
    { contest_id: 1, title: "Weekly Contest 42", description: "4 problems · 90 minutes · rated", status: "live", starts: "Today, 18:00", ends: "Today, 19:30", participants: 812, registered: true, problems: [1,3,4,5] },
    { contest_id: 2, title: "Graph Theory Sprint", description: "Focused BFS/DFS/Dijkstra challenges", status: "upcoming", starts: "Sat, 16:00", ends: "Sat, 17:30", participants: 355, registered: false, problems: [4,6] },
    { contest_id: 3, title: "Beginner Bash #7", description: "Warm-up contest for new coders", status: "ended", starts: "Last Sunday", ends: "Last Sunday", participants: 1204, registered: true, problems: [1,2] }
  ],
  leaderboard: [
    { user: "grace_h", score: 400, solved: 4, penalty: 1320 }, { user: "linus_t", score: 400, solved: 4, penalty: 1710 },
    { user: "ada_dev", score: 300, solved: 3, penalty: 1105 }, { user: "margaret_h", score: 300, solved: 3, penalty: 1490 },
    { user: "alan_t", score: 200, solved: 2, penalty: 640 }, { user: "dennis_r", score: 200, solved: 2, penalty: 905 }
  ],
  discussions: [
    { discussion_id: 1, title: "O(n) approach for Two Sum — am I missing something?", author: "linus_t", problem: "Two Sum", created: "3h ago", is_locked: false, body: "I used a single pass with a hash map. Is there any case where this fails with duplicates?",
      comments: [{ author: "grace_h", body: "Works fine — you insert after checking, so duplicates are handled.", created: "2h ago", reactions: 5, replies: [{ author: "linus_t", body: "That makes sense, thanks!", created: "1h ago", reactions: 1 }] }] },
    { discussion_id: 2, title: "Best way to learn dynamic programming?", author: "margaret_h", problem: null, created: "Yesterday", is_locked: false, body: "Looking for a structured path. Any recommendations?", comments: [{ author: "alan_t", body: "Try the DP learning path on this site, it builds up nicely.", created: "20h ago", reactions: 8, replies: [] }] },
    { discussion_id: 3, title: "Contest 41 editorial thread", author: "admin", problem: null, created: "3 days ago", is_locked: true, body: "Post your questions about the editorial here.", comments: [] }
  ],
  solutions: [
    { title: "Hash map, single pass", author: "grace_h", problem: "Two Sum", language: "Python", votes: 214, official: true },
    { title: "Monotonic stack explained", author: "dennis_r", problem: "Valid Parentheses", language: "Java", votes: 98, official: false },
    { title: "Sliding window with last-seen index", author: "alan_t", problem: "Longest Substring", language: "C++", votes: 77, official: false }
  ],
  paths: [
    { learning_path_id: 1, title: "Arrays & Hashing Fundamentals", difficulty: "easy", description: "Build core intuition with the most common interview patterns.", steps: [
      { title: "Two Sum", status: "completed" }, { title: "Valid Parentheses", status: "completed" }, { title: "Group Anagrams", status: "in_progress" }, { title: "Top K Frequent Elements", status: "not_started" }] },
    { learning_path_id: 2, title: "Graphs from Zero", difficulty: "medium", description: "BFS, DFS, topological sort and shortest paths.", steps: [
      { title: "Number of Islands", status: "completed" }, { title: "Course Schedule", status: "not_started" }, { title: "Word Ladder", status: "not_started" }] }
  ],
  teams: [
    { team_id: 1, name: "Null Pointers", description: "University ACM team", role: "owner", members: [{n:"ada_dev",r:"owner"},{n:"grace_h",r:"member"},{n:"alan_t",r:"member"}] },
    { team_id: 2, name: "Big-O Brigade", description: "Weekend contest crew", role: "member", members: [{n:"linus_t",r:"owner"},{n:"ada_dev",r:"member"}] }
  ],
  groups: [
    { group_id: 1, name: "Interview Prep 2026", description: "Private study group", role: "admin", members: 14 },
    { group_id: 2, name: "Course Project Buddies", description: "Flask + SQLAlchemy help", role: "member", members: 6 }
  ],
  invitations: [{ type: "team", name: "Stack Overflowers", from: "dennis_r" }, { type: "group", name: "DP Study Circle", from: "margaret_h" }],
  achievements: [
    { name: "First Blood", icon: "flag", desc: "Solve your first problem", earned: true }, { name: "Week Warrior", icon: "flame", desc: "7-day streak", earned: true },
    { name: "Contest Debut", icon: "trophy", desc: "Join a contest", earned: true }, { name: "Graph Guru", icon: "users", desc: "Solve 10 graph problems", earned: false },
    { name: "Helpful Hand", icon: "star", desc: "Get 50 solution votes", earned: false }, { name: "Hard Mode", icon: "zap", desc: "Solve a hard problem", earned: false }
  ],
  points: [
    { reason: "Solved: Valid Parentheses", delta: 20, date: "2 days ago" }, { reason: "Achievement: Week Warrior", delta: 50, date: "3 days ago" },
    { reason: "Contest 41 performance", delta: 120, date: "Last week" }, { reason: "Hint penalty", delta: -5, date: "Last week" }
  ],
  notifications: [
    { id: 1, type: "contest", title: "Weekly Contest 42 is live", message: "Your registered contest started.", url: "#/contests/1", created: "10m ago", read: false },
    { id: 2, type: "discussion", title: "grace_h replied to your thread", message: "“Works fine — you insert after checking…”", url: "#/discussions/1", created: "2h ago", read: false },
    { id: 3, type: "submission", title: "Submission accepted", message: "Two Sum · Python 3.12 · 48 ms", url: "#/problems/1", created: "2h ago", read: true },
    { id: 4, type: "achievement", title: "Achievement unlocked: Week Warrior", message: "+50 points", url: "#/profile", created: "3d ago", read: true }
  ]
};
