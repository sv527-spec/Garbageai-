/* Habit Board — vanilla JS PWA. All data is stored on-device via localStorage. */

const STORAGE_KEY = "habitboard_v2";
const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const DAY_SHORT = ["M", "T", "W", "T", "F", "S", "S"];
const MONTHS = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
const INTENSITY = ["#232323", "#33461c", "#4f6b1f", "#7fa62b", "#c6ff4a"];

// ---------- date helpers ----------
function pad2(n) { return String(n).padStart(2, "0"); }
function toISO(d) { return `${d.getFullYear()}-${pad2(d.getMonth()+1)}-${pad2(d.getDate())}`; }
function todayISO(offset = 0) {
  const d = new Date();
  d.setDate(d.getDate() + offset);
  return toISO(d);
}
function mondayOf(date) {
  const d = new Date(date);
  const day = (d.getDay() + 6) % 7; // Mon=0
  d.setDate(d.getDate() - day);
  d.setHours(0,0,0,0);
  return d;
}
function addDays(date, n) {
  const d = new Date(date);
  d.setDate(d.getDate() + n);
  return d;
}
function fmtShort(d) {
  return `${MONTHS[d.getMonth()]} ${d.getDate()}`;
}
function weekKey(mondayDate) { return toISO(mondayDate); }
function weekLabel(mondayDate) {
  const sunday = addDays(mondayDate, 5);
  return `${fmtShort(mondayDate)} – ${fmtShort(sunday)}`;
}
function getWeeksList() {
  const weeks = [];
  const thisMonday = mondayOf(new Date());
  for (let i = 0; i < 8; i++) {
    const m = addDays(thisMonday, -7 * i);
    weeks.push({ key: weekKey(m), monday: m, label: i === 0 ? `This week (${weekLabel(m)})` : weekLabel(m) });
  }
  return weeks;
}
function dateForWeekDay(mondayDate, dayAbbr) {
  const idx = WEEKDAYS.indexOf(dayAbbr);
  return toISO(addDays(mondayDate, idx));
}

// ---------- storage ----------
function defaultState() {
  const habits = ["MORNING_RUN", "READ_30MIN", "NO_DOOMSCROLL", "CODE_1HR", "COLD_DMS"].map((name, i) => ({
    id: "h" + i,
    name,
    createdAt: todayISO(),
    reminder: { enabled: false, time: "07:00", mode: "notification" },
  }));
  const subjects = [
    { id: "t1", name: "DATA_STRUCTURES", day: "Mon", time: "09:00" },
    { id: "t2", name: "DATA_STRUCTURES", day: "Wed", time: "09:00" },
    { id: "t3", name: "OPERATING_SYS", day: "Tue", time: "11:00" },
    { id: "t4", name: "OPERATING_SYS", day: "Thu", time: "11:00" },
    { id: "t5", name: "LINEAR_ALGEBRA", day: "Mon", time: "14:00" },
    { id: "t6", name: "LINEAR_ALGEBRA", day: "Fri", time: "14:00" },
  ];
  return {
    habits,
    checkins: {},
    subjects,
    attendance: {},
    settings: { theme: "dark", notifPermissionAsked: false },
    tab: "today",
  };
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    const parsed = JSON.parse(raw);
    return { ...defaultState(), ...parsed, settings: { ...defaultState().settings, ...(parsed.settings||{}) } };
  } catch (e) {
    return defaultState();
  }
}

let state = loadState();
let modal = null; // {type: 'habitDetail'|'reminder'|'manageClasses', ...}
let ringing = null;
let toastMsg = null;
let timers = [];

function save() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (e) {}
}

function setState(patch) {
  state = { ...state, ...patch };
  save();
  render();
}

function showToast(msg) {
  toastMsg = msg;
  render();
  setTimeout(() => { toastMsg = null; render(); }, 2200);
}

// ---------- icons (inline svg) ----------
const ICON = {
  bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
  check: '<polyline points="20 6 9 17 4 12"/>',
  x: '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
  plus: '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
  trash: '<polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>',
  activity: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
  calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
  pie: '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
  home: '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
  alarm: '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2"/><path d="M5 3 2 6"/><path d="M22 6l-3-3"/>',
  volume: '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>',
  sun: '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>',
  moon: '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
  upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
};
function icon(name, size = 16, color = "currentColor") {
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICON[name] || ""}</svg>`;
}

// ---------- audio ----------
function beep(durationMs = 1200) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "square";
    osc.frequency.value = 880;
    gain.gain.value = 0.05;
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    setTimeout(() => { osc.stop(); ctx.close(); }, durationMs);
  } catch (e) {}
}

// ---------- derived data ----------
function isDone(habitId, dateISO) {
  return !!(state.checkins[habitId] && state.checkins[habitId][dateISO]);
}
function toggleCheckin(habitId, dateISO) {
  const cur = { ...(state.checkins[habitId] || {}) };
  if (cur[dateISO]) delete cur[dateISO];
  else cur[dateISO] = true;
  setState({ checkins: { ...state.checkins, [habitId]: cur } });
}
function streakOf(habitId) {
  let s = 0;
  for (let k = 0; k < 90; k++) {
    if (isDone(habitId, todayISO(-k))) s++;
    else break;
  }
  return s;
}
function totalDone(habitId) {
  return Object.keys(state.checkins[habitId] || {}).length;
}
function rateOf(habitId, days = 35) {
  let done = 0;
  for (let k = 0; k < days; k++) if (isDone(habitId, todayISO(-k))) done++;
  return Math.round((done / days) * 100);
}
function overallRate(days = 35) {
  if (!state.habits.length) return 0;
  const rates = state.habits.map((h) => rateOf(h.id, days));
  return Math.round(rates.reduce((a, b) => a + b, 0) / rates.length);
}
function bestStreak() {
  return Math.max(0, ...state.habits.map((h) => streakOf(h.id)));
}

function attendanceInRange(subjectId, fromDate, toDateExclusive) {
  let present = 0, absent = 0;
  Object.entries(state.attendance).forEach(([key, val]) => {
    const [sid, date] = key.split("_");
    if (subjectId && sid !== subjectId) return;
    if (fromDate && date < fromDate) return;
    if (toDateExclusive && date >= toDateExclusive) return;
    if (val === "present") present++;
    else if (val === "absent") absent++;
  });
  return { present, absent, total: present + absent };
}

// ---------- reminders ----------
function scheduleReminders() {
  timers.forEach(clearTimeout);
  timers = [];
  state.habits.forEach((h) => {
    if (!h.reminder || !h.reminder.enabled) return;
    const [hh, mm] = h.reminder.time.split(":").map(Number);
    const target = new Date();
    target.setHours(hh, mm, 0, 0);
    if (target.getTime() < Date.now()) target.setDate(target.getDate() + 1);
    const delay = Math.min(target.getTime() - Date.now(), 2147483000);
    const t = setTimeout(() => {
      if (isDone(h.id, todayISO())) { scheduleReminders(); return; }
      if (h.reminder.mode === "notification" && "Notification" in window && Notification.permission === "granted") {
        new Notification("Habit Board", { body: `${h.name.replaceAll("_"," ")} isn't done yet` });
      } else if (h.reminder.mode === "notification") {
        showToast(`Reminder: ${h.name.replaceAll("_"," ")} isn't done yet`);
      } else {
        ringing = h.id;
        beep(1500);
        render();
      }
      scheduleReminders();
    }, delay);
    timers.push(t);
  });
}

// ---------- theme ----------
function applyTheme() {
  document.documentElement.setAttribute("data-theme", state.settings.theme === "light" ? "light" : "dark");
}

// ---------- render root ----------
const root = document.getElementById("root");

function render() {
  applyTheme();
  root.innerHTML = `
    <div class="app">
      <div class="header">
        <div class="header-left">
          ${logoSVG(30)}
          <span class="header-title">Habit Board</span>
        </div>
        <span class="badge">${new Date().getFullYear()}</span>
      </div>
      <div class="content" id="content"></div>
      <div class="bottom-nav">
        ${navBtn("today", "home", "Today")}
        ${navBtn("classes", "calendar", "Classes")}
        ${navBtn("report", "pie", "Report")}
        ${navBtn("settings", "settings", "Settings")}
      </div>
    </div>
    ${modal ? renderModal() : ""}
    ${ringing ? renderAlarmOverlay() : ""}
    ${toastMsg ? `<div class="toast">${toastMsg}</div>` : ""}
  `;
  document.getElementById("content").innerHTML = renderTab();
  attachEvents();
}

function logoSVG(size) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 48 48" fill="none">
    <rect x="1" y="1" width="46" height="46" rx="13" fill="#111111" stroke="#262626"/>
    <path d="M9 26.5L15.5 26.5L18.5 18L22.5 34L26 22L29 30L32.5 21.5L39 21.5" stroke="#c6ff4a" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    <circle cx="39" cy="21.5" r="2.4" fill="#c6ff4a"/>
  </svg>`;
}

function navBtn(tab, iconName, label) {
  return `<button class="nav-btn ${state.tab === tab ? "active" : ""}" data-nav="${tab}">
    ${icon(iconName, 18)}<span>${label.toUpperCase()}</span>
  </button>`;
}

function renderTab() {
  if (state.tab === "today") return renderToday();
  if (state.tab === "classes") return renderClasses();
  if (state.tab === "report") return renderReport();
  if (state.tab === "settings") return renderSettings();
  return "";
}

// ---------- TODAY ----------
function renderToday() {
  const today = todayISO();
  return `
    <div class="section-label">TODAY</div>
    <div class="add-row">
      <input type="text" id="newHabitInput" placeholder="New habit e.g. DRINK_WATER" style="flex:1" maxlength="30" />
      <button class="btn btn-accent" id="addHabitBtn" style="padding:0 14px;display:flex;align-items:center;">${icon("plus",16,"#0a0a0a")}</button>
    </div>
    ${state.habits.length === 0 ? `<div class="empty-note">No habits yet. Add your first one above.</div>` : ""}
    ${state.habits.map((h) => {
      const done = isDone(h.id, today);
      return `
      <div class="habit-row">
        <div class="habit-left">
          <button class="checkbox ${done ? "done" : ""}" data-toggle="${h.id}">${done ? icon("check", 15, "#0a0a0a") : ""}</button>
          <button class="habit-name" data-open="${h.id}">${h.name}</button>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <button class="icon-btn ${h.reminder.enabled ? "active" : ""}" data-remind="${h.id}">${icon("bell",15)} ${h.reminder.enabled ? h.reminder.time : "SET"}</button>
          <button class="trash-btn" data-delhabit="${h.id}">${icon("trash",14)}</button>
        </div>
      </div>`;
    }).join("")}
  `;
}

function habitDetailHTML(h) {
  const cells = [];
  for (let k = 34; k >= 0; k--) {
    const d = todayISO(-k);
    cells.push({ d, done: isDone(h.id, d) });
  }
  return `
    <div class="modal-header">
      <span style="font-size:13px;font-weight:600;">${h.name}</span>
      <button class="icon-btn" data-close-modal>${icon("x",18)}</button>
    </div>
    <div class="stat-grid" style="margin-bottom:16px;">
      <div class="stat-card highlight"><div class="stat-label">STREAK</div><div class="stat-value accent">${streakOf(h.id)}d</div></div>
      <div class="stat-card"><div class="stat-label">TOTAL</div><div class="stat-value">${totalDone(h.id)}</div></div>
      <div class="stat-card"><div class="stat-label">35D RATE</div><div class="stat-value">${rateOf(h.id)}%</div></div>
    </div>
    <div class="field-label">LAST 35 DAYS — tap to edit</div>
    <div class="heat-grid">
      ${cells.map((c) => `<button class="heat-cell" data-heatday="${h.id}|${c.d}" style="border:none;cursor:pointer;background:${c.done ? "#c6ff4a" : "#232323"};" title="${c.d}"></button>`).join("")}
    </div>
    <div style="margin-top:18px;">
      <button class="btn btn-ghost" style="width:100%;padding:10px 0;" data-remind="${h.id}" data-close-modal-after="1">${icon("bell",14)} &nbsp;Set reminder</button>
    </div>
  `;
}

// ---------- CLASSES (timetable) ----------
function ensureWeekVar() {
  if (!state._selWeek) state._selWeek = getWeeksList()[0].key;
}
function renderClasses() {
  ensureWeekVar();
  const weeks = getWeeksList();
  const monday = new Date(state._selWeek);
  const times = [...new Set(state.subjects.map((s) => s.time))].sort();

  const rows = times.map((time) => {
    const cells = WEEKDAYS.map((day) => {
      const subj = state.subjects.find((s) => s.day === day && s.time === time);
      if (!subj) return `<div class="tt-cell"></div>`;
      const date = dateForWeekDay(monday, day);
      const st = state.attendance[`${subj.id}_${date}`] || "none";
      return `<div class="tt-cell">
        <button class="tt-chip ${st}" data-cycle="${subj.id}|${date}">${subj.name.replace(/_/g, " ")}</button>
      </div>`;
    }).join("");
    return `<div class="tt-row"><div class="tt-time">${time}</div>${cells}</div>`;
  }).join("");

  return `
    <div class="section-label">WEEK<span></span></div>
    <select id="weekSelect" style="width:100%;">
      ${weeks.map((w) => `<option value="${w.key}" ${w.key === state._selWeek ? "selected" : ""}>${w.label}</option>`).join("")}
    </select>

    <div class="section-label">TIMETABLE<span>${icon("calendar",13)}</span></div>
    ${state.subjects.length === 0 ? `<div class="empty-note">No classes yet. Add subjects below.</div>` : `
    <div class="timetable-grid">
      <div class="tt-head"><span></span>${WEEKDAYS.map((d) => `<span>${d}</span>`).join("")}</div>
      ${rows}
    </div>
    <div class="empty-note">Tap a class to cycle: unmarked → present → absent.</div>
    `}

    <div class="section-label">MANAGE_CLASSES<span></span></div>
    <div class="add-row" style="flex-wrap:wrap;">
      <input type="text" id="newClassName" placeholder="Subject name" style="flex:1;min-width:110px;" maxlength="24" />
      <select id="newClassDay">${WEEKDAYS.map((d) => `<option value="${d}">${d}</option>`).join("")}</select>
      <input type="time" id="newClassTime" value="09:00" />
      <button class="btn btn-accent" id="addClassBtn" style="padding:0 14px;display:flex;align-items:center;">${icon("plus",16,"#0a0a0a")}</button>
    </div>
    ${[...new Set(state.subjects.map((s) => s.name))].map((name) => {
      const slots = state.subjects.filter((s) => s.name === name);
      return `<div class="subject-list-row row">
        <span style="font-size:12px;">${name.replace(/_/g," ")} <span style="color:var(--muted);font-size:10px;">(${slots.map(s=>s.day+" "+s.time).join(", ")})</span></span>
        <button class="trash-btn" data-delsubject="${name}">${icon("trash",14)}</button>
      </div>`;
    }).join("")}
  `;
}

// ---------- REPORT ----------
function renderReport() {
  ensureWeekVar();
  const weeks = getWeeksList();
  const scope = state._reportScope || "overall";

  let fromDate = null, toDate = null;
  if (scope !== "overall") {
    const m = new Date(scope);
    fromDate = toISO(m);
    toDate = toISO(addDays(m, 6));
    toDate = toISO(addDays(new Date(toDate), 1));
  }

  const subjectNames = [...new Set(state.subjects.map((s) => s.name))];
  const subjectStats = subjectNames.map((name) => {
    const ids = state.subjects.filter((s) => s.name === name).map((s) => s.id);
    let present = 0, absent = 0;
    ids.forEach((id) => {
      const r = attendanceInRange(id, fromDate, toDate);
      present += r.present; absent += r.absent;
    });
    const total = present + absent;
    return { name, present, absent, pct: total ? Math.round((present/total)*100) : null };
  });

  const overallAtt = attendanceInRange(null, fromDate, toDate);
  const attPct = overallAtt.total ? Math.round((overallAtt.present/overallAtt.total)*100) : null;

  const weeklyBar = [];
  for (let k = 6; k >= 0; k--) {
    const d = todayISO(-k);
    const dow = new Date(d).getDay();
    const count = state.habits.filter((h) => isDone(h.id, d)).length;
    weeklyBar.push({ label: DAY_SHORT[(dow + 6) % 7], count });
  }
  const maxCount = Math.max(1, ...weeklyBar.map((b) => b.count));

  return `
    <div class="section-label">OVERVIEW</div>
    <div class="stat-grid">
      <div class="stat-card highlight"><div class="stat-label">HABIT RATE</div><div class="stat-value accent">${overallRate()}%</div></div>
      <div class="stat-card"><div class="stat-label">ATTENDANCE</div><div class="stat-value">${attPct === null ? "--" : attPct + "%"}</div></div>
      <div class="stat-card"><div class="stat-label">STREAK</div><div class="stat-value">${bestStreak()}d</div></div>
    </div>

    <div class="section-label">WEEKLY_COMPLETIONS</div>
    <div class="card" style="padding:16px 10px;">
      <div style="display:flex;align-items:flex-end;gap:8px;height:110px;">
        ${weeklyBar.map((b) => `
          <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;justify-content:flex-end;height:100%;">
            <div style="width:100%;max-width:22px;border-radius:4px 4px 0 0;background:var(--accent);height:${(b.count/maxCount)*80}px;min-height:${b.count>0?4:0}px;"></div>
            <span style="font-size:9.5px;color:var(--muted);">${b.label}</span>
          </div>`).join("")}
      </div>
    </div>

    <div class="section-label">CLASS_ATTENDANCE<span></span></div>
    <select id="reportWeekSelect" style="width:100%;margin-bottom:12px;">
      <option value="overall" ${scope === "overall" ? "selected" : ""}>Overall</option>
      ${weeks.map((w) => `<option value="${w.key}" ${w.key === scope ? "selected" : ""}>${w.label}</option>`).join("")}
    </select>

    ${overallAtt.total === 0 ? `<div class="empty-note">No attendance marked ${scope === "overall" ? "yet" : "for this week"}. Mark it in Classes.</div>` : `
    <div class="card" style="display:flex;align-items:center;gap:16px;margin-bottom:14px;">
      ${donutSVG(overallAtt.present, overallAtt.absent)}
      <div style="font-size:11px;color:var(--muted);display:flex;flex-direction:column;gap:6px;">
        <span><span style="color:var(--accent);">■</span> Present ${overallAtt.present}</span>
        <span><span style="color:var(--red);">■</span> Absent ${overallAtt.absent}</span>
      </div>
    </div>
    ${subjectStats.filter(s=>s.pct!==null).map((s) => `
      <div class="subject-list-row">
        <div class="row"><span style="font-size:12px;">${s.name.replace(/_/g," ")}</span><span style="font-size:11px;color:var(--muted);">${s.pct}%</span></div>
        <div class="bar-track"><div class="bar-fill" style="width:${s.pct}%;"></div></div>
      </div>`).join("")}
    `}
  `;
}

function donutSVG(present, absent) {
  const total = present + absent || 1;
  const pPct = present / total;
  const r = 34, c = 2 * Math.PI * r;
  const presentLen = c * pPct;
  return `<svg width="88" height="88" viewBox="0 0 88 88">
    <circle cx="44" cy="44" r="${r}" fill="none" stroke="var(--red)" stroke-width="12"/>
    <circle cx="44" cy="44" r="${r}" fill="none" stroke="var(--accent)" stroke-width="12"
      stroke-dasharray="${presentLen} ${c - presentLen}" stroke-dashoffset="${c*0.25}" transform="rotate(0 44 44)"/>
    <text x="44" y="49" text-anchor="middle" font-size="15" fill="var(--text)" font-weight="700">${Math.round(pPct*100)}%</text>
  </svg>`;
}

// ---------- SETTINGS ----------
function renderSettings() {
  const notifState = ("Notification" in window) ? Notification.permission : "unsupported";
  return `
    <div class="section-label">APPEARANCE</div>
    <div class="settings-row">
      <div>
        <div class="settings-title">Theme</div>
        <div class="settings-sub">Matte black by default</div>
      </div>
      <div class="segmented" style="width:150px;">
        <button data-theme-choice="dark" class="${state.settings.theme!=="light"?"active":""}">${icon("moon",13)} Dark</button>
        <button data-theme-choice="light" class="${state.settings.theme==="light"?"active":""}">${icon("sun",13)} Light</button>
      </div>
    </div>

    <div class="section-label">NOTIFICATIONS</div>
    <div class="settings-row">
      <div>
        <div class="settings-title">Browser notifications</div>
        <div class="settings-sub">Status: ${notifState}</div>
      </div>
      <button class="btn btn-ghost" style="padding:8px 12px;" id="askNotifBtn">Allow</button>
    </div>
    ${state.habits.map((h) => `
      <div class="settings-row">
        <span class="settings-title">${h.name}</span>
        <span class="settings-sub" style="color:${h.reminder.enabled?"var(--accent)":"var(--muted)"};">${h.reminder.enabled ? `${h.reminder.time} · ${h.reminder.mode}` : "off"}</span>
      </div>`).join("")}

    <div class="section-label">DATA</div>
    <div class="settings-row">
      <div>
        <div class="settings-title">Export backup</div>
        <div class="settings-sub">Save all your data as a file</div>
      </div>
      <button class="btn btn-ghost" style="padding:8px 12px;display:flex;align-items:center;gap:6px;" id="exportBtn">${icon("download",14)} Export</button>
    </div>
    <div class="settings-row">
      <div>
        <div class="settings-title">Import backup</div>
        <div class="settings-sub">Restore from a file</div>
      </div>
      <label class="btn btn-ghost" style="padding:8px 12px;display:flex;align-items:center;gap:6px;cursor:pointer;">
        ${icon("upload",14)} Import
        <input type="file" id="importFile" accept="application/json" style="display:none;" />
      </label>
    </div>
    <div class="settings-row">
      <div>
        <div class="settings-title" style="color:var(--red);">Reset all data</div>
        <div class="settings-sub">Deletes habits, classes and history</div>
      </div>
      <button class="btn btn-ghost" style="padding:8px 12px;color:var(--red);" id="resetBtn">Reset</button>
    </div>

    <div class="section-label">ABOUT</div>
    <div class="empty-note">Habit Board v1.0 — data is stored only on this device.</div>
  `;
}

// ---------- modal ----------
function renderModal() {
  let body = "";
  if (modal.type === "habitDetail") {
    const h = state.habits.find((x) => x.id === modal.id);
    if (!h) return "";
    body = habitDetailHTML(h);
  } else if (modal.type === "reminder") {
    const h = state.habits.find((x) => x.id === modal.id);
    if (!h) return "";
    body = reminderModalHTML(h);
  }
  return `<div class="modal-overlay" id="modalOverlay"><div class="modal-sheet" id="modalSheet">${body}</div></div>`;
}

function reminderModalHTML(h) {
  const r = h.reminder;
  return `
    <div class="modal-header">
      <span style="font-size:13px;font-weight:600;">${h.name} REMINDER</span>
      <button class="icon-btn" data-close-modal>${icon("x",18)}</button>
    </div>
    <div class="row" style="margin-bottom:16px;">
      <span style="font-size:12px;color:var(--muted);">Enable reminder</span>
      <button class="toggle ${r.enabled?"on":""}" id="remEnable"><div class="toggle-dot"></div></button>
    </div>
    <div style="margin-bottom:16px;">
      <div class="field-label">Time</div>
      <input type="time" id="remTime" value="${r.time}" style="width:100%;" />
    </div>
    <div style="margin-bottom:20px;">
      <div class="field-label">Alert type</div>
      <div class="segmented">
        <button data-mode="notification" class="${r.mode==="notification"?"active":""}">${icon("bell",14)} Notification</button>
        <button data-mode="alarm" class="${r.mode==="alarm"?"active":""}">${icon("alarm",14)} Alarm</button>
      </div>
    </div>
    <button class="btn btn-accent" id="saveReminderBtn" style="width:100%;padding:12px 0;font-size:13px;">Save reminder</button>
  `;
}

function renderAlarmOverlay() {
  const h = state.habits.find((x) => x.id === ringing);
  if (!h) return "";
  return `<div class="alarm-overlay">
    ${icon("volume",40,"#c6ff4a")}
    <div style="font-size:15px;font-weight:700;">${h.name}</div>
    <div style="font-size:12px;color:var(--muted);">Still not marked done today</div>
    <button class="btn btn-accent" id="dismissAlarm" style="padding:10px 24px;">Dismiss</button>
  </div>`;
}

// ---------- events ----------
function attachEvents() {
  document.querySelectorAll("[data-nav]").forEach((b) => b.onclick = () => setState({ tab: b.dataset.nav }));

  // today
  document.querySelectorAll("[data-toggle]").forEach((b) => b.onclick = () => toggleCheckin(b.dataset.toggle, todayISO()));
  document.querySelectorAll("[data-open]").forEach((b) => b.onclick = () => { modal = { type: "habitDetail", id: b.dataset.open }; render(); });
  document.querySelectorAll("[data-remind]").forEach((b) => b.onclick = () => { modal = { type: "reminder", id: b.dataset.remind }; render(); });
  document.querySelectorAll("[data-delhabit]").forEach((b) => b.onclick = () => {
    if (!confirm("Delete this habit and its history?")) return;
    const habits = state.habits.filter((h) => h.id !== b.dataset.delhabit);
    const checkins = { ...state.checkins };
    delete checkins[b.dataset.delhabit];
    setState({ habits, checkins });
  });
  const addHabitBtn = document.getElementById("addHabitBtn");
  if (addHabitBtn) addHabitBtn.onclick = () => {
    const input = document.getElementById("newHabitInput");
    const name = input.value.trim().toUpperCase().replace(/\s+/g, "_");
    if (!name) return;
    const habit = { id: "h" + Date.now(), name, createdAt: todayISO(), reminder: { enabled: false, time: "07:00", mode: "notification" } };
    setState({ habits: [...state.habits, habit] });
  };

  // classes
  const weekSelect = document.getElementById("weekSelect");
  if (weekSelect) weekSelect.onchange = () => { state._selWeek = weekSelect.value; render(); };
  document.querySelectorAll("[data-cycle]").forEach((b) => b.onclick = () => {
    const [sid, date] = b.dataset.cycle.split("|");
    const key = `${sid}_${date}`;
    const cur = state.attendance[key] || "none";
    const next = cur === "none" ? "present" : cur === "present" ? "absent" : "none";
    const attendance = { ...state.attendance };
    if (next === "none") delete attendance[key]; else attendance[key] = next;
    setState({ attendance });
  });
  const addClassBtn = document.getElementById("addClassBtn");
  if (addClassBtn) addClassBtn.onclick = () => {
    const name = document.getElementById("newClassName").value.trim().toUpperCase().replace(/\s+/g, "_");
    const day = document.getElementById("newClassDay").value;
    const time = document.getElementById("newClassTime").value;
    if (!name || !time) return;
    const subj = { id: "t" + Date.now(), name, day, time };
    setState({ subjects: [...state.subjects, subj] });
  };
  document.querySelectorAll("[data-delsubject]").forEach((b) => b.onclick = () => {
    if (!confirm("Remove this subject and its attendance?")) return;
    const name = b.dataset.delsubject;
    const idsToRemove = state.subjects.filter((s) => s.name === name).map((s) => s.id);
    const subjects = state.subjects.filter((s) => s.name !== name);
    const attendance = { ...state.attendance };
    Object.keys(attendance).forEach((k) => { if (idsToRemove.includes(k.split("_")[0])) delete attendance[k]; });
    setState({ subjects, attendance });
  });

  // report
  const reportWeekSelect = document.getElementById("reportWeekSelect");
  if (reportWeekSelect) reportWeekSelect.onchange = () => { state._reportScope = reportWeekSelect.value; render(); };

  // settings
  document.querySelectorAll("[data-theme-choice]").forEach((b) => b.onclick = () => {
    setState({ settings: { ...state.settings, theme: b.dataset.themeChoice } });
  });
  const askNotifBtn = document.getElementById("askNotifBtn");
  if (askNotifBtn) askNotifBtn.onclick = () => { if ("Notification" in window) Notification.requestPermission().then(() => render()); };
  const exportBtn = document.getElementById("exportBtn");
  if (exportBtn) exportBtn.onclick = () => {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `habit-board-backup-${todayISO()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };
  const importFile = document.getElementById("importFile");
  if (importFile) importFile.onchange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const data = JSON.parse(reader.result);
        state = { ...defaultState(), ...data };
        save();
        render();
        showToast("Backup imported");
      } catch (err) { alert("Couldn't read that file."); }
    };
    reader.readAsText(file);
  };
  const resetBtn = document.getElementById("resetBtn");
  if (resetBtn) resetBtn.onclick = () => {
    if (!confirm("This deletes everything on this device. Continue?")) return;
    state = defaultState();
    save();
    render();
  };

  // modal
  const overlay = document.getElementById("modalOverlay");
  if (overlay) overlay.onclick = (e) => { if (e.target === overlay) { modal = null; render(); } };
  document.querySelectorAll("[data-close-modal]").forEach((b) => b.onclick = () => { modal = null; render(); });
  document.querySelectorAll("[data-heatday]").forEach((b) => b.onclick = () => {
    const [hid, d] = b.dataset.heatday.split("|");
    toggleCheckin(hid, d);
    modal = { type: "habitDetail", id: hid };
    render();
  });

  if (modal && modal.type === "reminder") {
    const h = state.habits.find((x) => x.id === modal.id);
    let draft = { ...h.reminder };
    const remEnable = document.getElementById("remEnable");
    if (remEnable) remEnable.onclick = () => { draft.enabled = !draft.enabled; remEnable.classList.toggle("on"); };
    document.querySelectorAll("[data-mode]").forEach((b) => b.onclick = () => {
      draft.mode = b.dataset.mode;
      document.querySelectorAll("[data-mode]").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
    });
    const saveBtn = document.getElementById("saveReminderBtn");
    if (saveBtn) saveBtn.onclick = () => {
      const time = document.getElementById("remTime").value;
      draft.time = time;
      if (draft.mode === "notification" && "Notification" in window) Notification.requestPermission();
      const habits = state.habits.map((x) => x.id === h.id ? { ...x, reminder: draft } : x);
      modal = null;
      setState({ habits });
      scheduleReminders();
    };
  }

  const dismissAlarm = document.getElementById("dismissAlarm");
  if (dismissAlarm) dismissAlarm.onclick = () => { ringing = null; render(); };
}

// ---------- init ----------
render();
scheduleReminders();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./service-worker.js").catch(() => {});
  });
}
