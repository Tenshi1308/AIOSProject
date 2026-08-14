// ============================================================
// AIOS Mockup — Onboarding State & Routing (demo, localStorage)
// ============================================================

const LS_USERS = 'aios_users';
const LS_STATE_PREFIX = 'aios_state_';

// ---------- Sesi aktif ----------
function getSession() {
  return {
    role: sessionStorage.getItem('aios_role') || '',
    companyId: sessionStorage.getItem('aios_company') || '',
    companyName: sessionStorage.getItem('aios_company_name') || ''
  };
}

// ---------- Akun (demo user) ----------
function seedUsers() {
  if (localStorage.getItem(LS_USERS)) return;
  const users = [
    { id: 'pt-alpha', name: 'PT Alpha', email: 'user@ptalpha.co.id', password: 'demo1234' },
    { id: 'pt-beta',  name: 'PT Beta',  email: 'user@ptbeta.co.id',  password: 'demo1234' },
    { id: 'pt-gamma', name: 'PT Gamma', email: 'user@ptgamma.co.id', password: 'demo1234' }
  ];
  localStorage.setItem(LS_USERS, JSON.stringify(users));
}

function getUsers() {
  seedUsers();
  try { return JSON.parse(localStorage.getItem(LS_USERS)) || []; }
  catch (e) { return []; }
}

function registerUser(name, email, password) {
  seedUsers();
  const users = getUsers();
  if (users.some(u => u.email.toLowerCase() === email.toLowerCase())) {
    return { ok: false, error: 'Email sudah terdaftar.' };
  }
  const id = 'co_' + Date.now().toString(36);
  users.push({ id, name, email, password });
  localStorage.setItem(LS_USERS, JSON.stringify(users));
  return { ok: true, id };
}

function findUser(email, password) {
  const u = getUsers().find(x => x.email.toLowerCase() === email.trim().toLowerCase());
  if (!u) return { ok: false, error: 'Akun tidak ditemukan. Silakan daftar terlebih dahulu.' };
  if (u.password !== password) return { ok: false, error: 'Password salah.' };
  return { ok: true, user: u };
}

// ---------- State onboarding per company ----------
function defaultState() {
  return {
    paid: false,
    connection: null,        // { engine, host, port, name, user }
    mappingValidated: false,
    mapping: null,           // hasil analisis skema
    mappingVersion: 0,
    schemaChanged: false     // flag untuk popup C14
  };
}

function getState(companyId) {
  try {
    const raw = localStorage.getItem(LS_STATE_PREFIX + companyId);
    if (raw) return Object.assign(defaultState(), JSON.parse(raw));
  } catch (e) {}
  return defaultState();
}

function setState(companyId, patch) {
  const next = Object.assign(getState(companyId), patch);
  localStorage.setItem(LS_STATE_PREFIX + companyId, JSON.stringify(next));
  return next;
}

// ---------- Gate routing setelah login (C1..C6 flow) ----------
// Payment -> Connect DB -> Validasi Mapping -> Home
function getOnboardingStep(companyId) {
  const s = getState(companyId);
  if (!s.paid) return 'payment';
  if (!s.connection) return 'connect';
  if (!s.mapping || !s.mappingValidated) return 'validate';
  return 'ready';
}

function companyLogin(companyId) {
  const user = getUsers().find(u => u.id === companyId);
  sessionStorage.setItem('aios_role', 'company');
  sessionStorage.setItem('aios_company', companyId);
  sessionStorage.setItem('aios_company_name', user ? user.name : companyId);
  routeCompany();
}

function routeCompany() {
  const { companyId } = getSession();
  if (!companyId) { window.location.href = 'login.html'; return; }
  const step = getOnboardingStep(companyId);
  const pages = { payment: 'payment.html', connect: 'connect.html', validate: 'validate-mapping.html', ready: 'home.html' };
  window.location.href = pages[step];
}

// ---------- Reset demo ----------
function resetDemo() {
  getUsers().forEach(u => localStorage.removeItem(LS_STATE_PREFIX + u.id));
  sessionStorage.clear();
  window.location.href = 'login.html';
}