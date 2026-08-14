// ============================================================
// AIOS Mockup — Topbar user menu (profile dropdown)
// Depends on js/state.js (getSession)
// ============================================================

function logout() {
  sessionStorage.removeItem('aios_role');
  sessionStorage.removeItem('aios_company');
  sessionStorage.removeItem('aios_company_name');
  window.location.href = 'login.html';
}

// Navigasi menu untuk role Client (perusahaan)
const COMPANY_MENU = [
  { icon: '🏢', label: 'Data Perusahaan', href: 'company-data.html' },
  { icon: '🗄️', label: 'Kelola Database', href: 'settings.html' },
  { icon: '⚙️', label: 'Pengaturan', href: 'preferences.html' }
];

// Navigasi menu untuk Developer Ekasa
const DEVELOPER_MENU = [
  { icon: '📊', label: 'Developer Dashboard', href: 'developer.html' }
];

function initTopUser() {
  const box = document.getElementById('userBox');
  if (!box) return;
  const session = getSession();
  const isDev = session.role === 'developer';
  const name = isDev ? 'Ekasa Developer' : (session.companyName || session.companyId || 'Perusahaan');
  const letter = isDev ? 'E' : 'C';

  const items = (isDev ? DEVELOPER_MENU : COMPANY_MENU).map(it =>
    `<a class="um-item" href="${it.href}"><span>${it.icon}</span>${it.label}</a>`
  ).join('');

  box.innerHTML =
    `<button class="user-btn" id="userBtn">
       <span id="userLabel">${name}</span>
       <span class="avatar" id="avatarLabel">${letter}</span>
       <span class="caret">▾</span>
     </button>
     <div class="user-menu hidden" id="userMenu">
       <div class="um-head">
         <div class="um-name">${name}</div>
         <div class="um-role">${isDev ? 'Developer Ekasa' : 'Client · ' + (session.companyName || session.companyId)}</div>
       </div>
       ${items}
       <a class="um-item um-logout" href="javascript:void(0)" onclick="logout()"><span>🚪</span>Keluar</a>
     </div>`;

  const btn = box.querySelector('#userBtn');
  const menu = box.querySelector('#userMenu');

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const open = !menu.classList.contains('hidden');
    menu.classList.toggle('hidden', open);
    btn.classList.toggle('open', !open);
  });
  // tutup saat klik di luar
  document.addEventListener('click', (e) => {
    if (!box.contains(e.target)) {
      menu.classList.add('hidden');
      btn.classList.remove('open');
    }
  });
}

document.addEventListener('DOMContentLoaded', initTopUser);