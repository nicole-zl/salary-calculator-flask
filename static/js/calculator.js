/* =========================================================
 * 千薪万苦 · 计算器 - 前端 JS
 * 数据通过 fetch API 与后端 Flask + SQLite 交互
 * ========================================================= */

// ============== API 调用封装 ==============
const API = {
  async getConfig() {
    const r = await fetch('/api/config');
    if (r.status === 401) { location.href = '/login'; return null; }
    return r.json();
  },
  async saveConfig(data) {
    const r = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return r.json();
  },
  async getItems() {
    const r = await fetch('/api/items');
    if (r.status === 401) { location.href = '/login'; return null; }
    return r.json();
  },
  async saveItems(items) {
    const r = await fetch('/api/items', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(items)
    });
    return r.json();
  },
  async reset() {
    const r = await fetch('/api/reset', { method: 'POST' });
    return r.json();
  }
};

// 防抖保存
function debounce(fn, delay) {
  let timer = null;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

// ============== 2026 中国法定节假日 + 调休 ==============
const HOLIDAYS_2026 = {
  '2026-01-01': '元旦', '2026-01-02': '元旦', '2026-01-03': '元旦',
  '2026-02-15': '春节', '2026-02-16': '春节', '2026-02-17': '春节',
  '2026-02-18': '春节', '2026-02-19': '春节', '2026-02-20': '春节',
  '2026-02-21': '春节', '2026-02-22': '春节',
  '2026-04-04': '清明节', '2026-04-05': '清明节', '2026-04-06': '清明节',
  '2026-05-01': '劳动节', '2026-05-02': '劳动节', '2026-05-03': '劳动节',
  '2026-05-04': '劳动节', '2026-05-05': '劳动节',
  '2026-06-19': '端午节', '2026-06-20': '端午节', '2026-06-21': '端午节',
  '2026-09-25': '中秋节', '2026-09-26': '中秋节', '2026-09-27': '中秋节',
  '2026-10-01': '国庆节', '2026-10-02': '国庆节', '2026-10-03': '国庆节',
  '2026-10-04': '国庆节', '2026-10-05': '国庆节', '2026-10-06': '国庆节',
  '2026-10-07': '国庆节', '2026-10-08': '国庆节'
};
const WORKDAY_OVERRIDE_2026 = {
  '2026-02-14': '春节调休', '2026-02-28': '春节调休',
  '2026-04-26': '劳动节调休', '2026-09-22': '端午节调休',
  '2026-10-10': '国庆节调休'
};

function dateKey(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function isWorkday(date) {
  const key = dateKey(date);
  if (HOLIDAYS_2026[key]) return { work: false, name: HOLIDAYS_2026[key] };
  if (WORKDAY_OVERRIDE_2026[key]) return { work: true, name: WORKDAY_OVERRIDE_2026[key] };
  const dow = date.getDay();
  return { work: dow >= 1 && dow <= 5, name: dow === 0 || dow === 6 ? '周末' : '工作日' };
}

function countWorkdaysInMonth(year, month) {
  const days = new Date(year, month + 1, 0).getDate();
  let count = 0;
  for (let d = 1; d <= days; d++) {
    if (isWorkday(new Date(year, month, d)).work) count++;
  }
  return count;
}

// ============== 时间工具 ==============
function parseTimeToMinutes(t) {
  if (!t) return 0;
  const [h, m] = t.split(':').map(Number);
  return h * 60 + m;
}

function nowMinutes(date) {
  const d = date || new Date();
  return d.getHours() * 60 + d.getMinutes() + d.getSeconds() / 60;
}

function calcWorkedMinutes(workStart, workEnd, lunchStart, lunchEnd, now) {
  const ws = parseTimeToMinutes(workStart);
  const we = parseTimeToMinutes(workEnd);
  const ls = parseTimeToMinutes(lunchStart);
  const le = parseTimeToMinutes(lunchEnd);
  const cur = nowMinutes(now);
  if (cur <= ws) return 0;
  if (cur >= we) return Math.max(0, (we - ws) - Math.max(0, Math.min(we, le) - Math.max(ws, ls)));
  let worked = cur - ws;
  if (cur > le) {
    worked -= Math.max(0, Math.min(le, we) - Math.max(ls, ws));
  } else if (cur > ls) {
    worked -= (cur - ls);
    worked = Math.max(0, ls - ws);
  }
  return Math.max(0, worked);
}

function calcTotalWorkMinutes(workStart, workEnd, lunchStart, lunchEnd) {
  const ws = parseTimeToMinutes(workStart);
  const we = parseTimeToMinutes(workEnd);
  const ls = parseTimeToMinutes(lunchStart);
  const le = parseTimeToMinutes(lunchEnd);
  return Math.max(0, (we - ws) - Math.max(0, Math.min(we, le) - Math.max(ws, ls)));
}

function calcRemainMinutes(workStart, workEnd, lunchStart, lunchEnd, now) {
  const we = parseTimeToMinutes(workEnd);
  const cur = nowMinutes(now);
  if (cur >= we) return 0;
  const ws = parseTimeToMinutes(workStart);
  const ls = parseTimeToMinutes(lunchStart);
  const le = parseTimeToMinutes(lunchEnd);
  if (cur < le) {
    const workedBeforeLunch = cur < ws ? 0 : Math.min(cur, ls) - ws;
    const total = calcTotalWorkMinutes(workStart, workEnd, lunchStart, lunchEnd);
    return Math.max(0, total - Math.max(0, workedBeforeLunch));
  }
  return Math.max(0, we - cur);
}

// ============== 配置与状态 ==============
const defaultConfig = {
  salary: 10000, workDaysPerMonth: '', workStart: '09:00', workEnd: '18:00',
  lunchStart: '12:00', lunchEnd: '13:00', payDay: 10,
  theme: 'light', tips: '下班不是奖励，是边界。',
  settingsOpen: false, itemsOpen: false
};

let config = Object.assign({}, defaultConfig);
let items = [];
let tipsText = defaultConfig.tips;

// ============== DOM ==============
const $ = (id) => document.getElementById(id);
const els = {
  salary: $('salary'), workDaysPerMonth: $('workDaysPerMonth'),
  workStart: $('workStart'), workEnd: $('workEnd'),
  lunchStart: $('lunchStart'), lunchEnd: $('lunchEnd'),
  payDay: $('payDay'),
  cdH: $('cdH'), cdM: $('cdM'), cdS: $('cdS'),
  countdownBody: $('countdownBody'), holidayBody: $('holidayBody'),
  holidayText: $('holidayText'), countdownSub: $('countdownSub'),
  dayProgress: $('dayProgress'),
  earnedToday: $('earnedToday'), earnedSub: $('earnedSub'),
  remainToEarn: $('remainToEarn'), totalToday: $('totalToday'),
  perMinute: $('perMinute'), perSecond: $('perSecond'),
  tipsText: $('tipsText'), itemsList: $('itemsList'),
  itemName: $('itemName'), itemPrice: $('itemPrice'), itemUnit: $('itemUnit'),
  btnAddItem: $('btnAddItem'),
  daysToPayday: $('daysToPayday'), paydayMeta: $('paydayMeta'),
  monthWorkDays: $('monthWorkDays'), monthWorkMeta: $('monthWorkMeta'),
  monthEarned: $('monthEarned'), monthEarnedMeta: $('monthEarnedMeta'),
  monthBar: $('monthBar'),
  monthRemain: $('monthRemain'), monthRemainMeta: $('monthRemainMeta'),
  dailyHours: $('dailyHours'), dailyHoursMeta: $('dailyHoursMeta'),
  hourlyRate: $('hourlyRate'),
  btnTheme: $('btnTheme'), btnReset: $('btnReset'), toast: $('toast'),
  settingsPanel: $('settingsPanel'), settingsPreview: $('settingsPreview'),
  itemsPanel: $('itemsPanel'), itemsPreview: $('itemsPreview'),
  itemsConfigList: $('itemsConfigList')
};

// ============== 持久化（防抖保存到后端） ==============
const persistConfig = debounce(() => {
  API.saveConfig({
    salary: Number(config.salary) || 0,
    workDaysPerMonth: config.workDaysPerMonth,
    workStart: config.workStart, workEnd: config.workEnd,
    lunchStart: config.lunchStart, lunchEnd: config.lunchEnd,
    payDay: Number(config.payDay) || 10,
    theme: config.theme, tips: tipsText,
    settingsOpen: els.settingsPanel.open,
    itemsOpen: els.itemsPanel.open
  });
}, 500);

const persistItems = debounce(() => {
  API.saveItems(items);
}, 500);

// ============== 初始化 ==============
function applyConfigToForm() {
  els.salary.value = config.salary || '';
  els.workDaysPerMonth.value = config.workDaysPerMonth || '';
  els.workStart.value = config.workStart;
  els.workEnd.value = config.workEnd;
  els.lunchStart.value = config.lunchStart;
  els.lunchEnd.value = config.lunchEnd;
  els.payDay.value = config.payDay;
  els.tipsText.textContent = tipsText;
  els.settingsPanel.open = !!config.settingsOpen;
  els.itemsPanel.open = !!config.itemsOpen;
  updateSettingsPreview();
  updateItemsPreview();
}

function updateSettingsPreview() {
  const salary = Number(config.salary) || 0;
  const workDays = Number(config.workDaysPerMonth) || 0;
  const parts = [];
  parts.push(`月薪 ¥${salary.toLocaleString()}`);
  if (workDays > 0) parts.push(`每月 ${workDays} 天`);
  parts.push(`${config.workStart}–${config.workEnd}`);
  els.settingsPreview.textContent = parts.join(' · ');
}

function updateItemsPreview() {
  const total = items.length;
  const selected = items.find(it => it.selected);
  const selName = selected ? selected.name : '未选择';
  els.itemsPreview.textContent = `共 ${total} 项 · 展示：${selName}`;
}

function bindConfigInputs() {
  const map = {
    salary: 'salary', workDaysPerMonth: 'workDaysPerMonth',
    workStart: 'workStart', workEnd: 'workEnd',
    lunchStart: 'lunchStart', lunchEnd: 'lunchEnd', payDay: 'payDay'
  };
  Object.entries(map).forEach(([elKey, cfgKey]) => {
    els[elKey].addEventListener('input', () => {
      let v = els[elKey].value;
      if (['salary', 'workDaysPerMonth', 'payDay'].includes(cfgKey)) {
        v = v === '' ? '' : Number(v);
      }
      config[cfgKey] = v;
      persistConfig();
      updateSettingsPreview();
      update();
    });
  });

  els.tipsText.addEventListener('blur', () => {
    tipsText = els.tipsText.textContent.trim() || defaultConfig.tips;
    persistConfig();
    showToast('Tips 已保存');
  });
  els.tipsText.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); els.tipsText.blur(); }
  });
}

// ============== 主题 ==============
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  els.btnTheme.textContent = theme === 'dark' ? '☀️' : '🌙';
  config.theme = theme;
  persistConfig();
}

function initTheme() {
  document.documentElement.setAttribute('data-theme', config.theme || 'light');
  els.btnTheme.textContent = config.theme === 'dark' ? '☀️' : '🌙';
}

// ============== 实物换算 ==============
function renderItemsDisplay(earned, perMinuteVal) {
  const selected = items.find(it => it.selected);
  if (!selected) {
    els.itemsList.innerHTML = `
      <div class="item-empty">
        <div class="empty-icon">🎯</div>
        <div>请在配置中选择一个实物进行展示</div>
        <div class="link" id="openItemsPanel">点击展开下方配置</div>
      </div>`;
    const openLink = document.getElementById('openItemsPanel');
    if (openLink) {
      openLink.addEventListener('click', () => {
        els.itemsPanel.open = true;
        persistConfig();
        els.itemsPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
    }
    return;
  }
  const price = Number(selected.price) || 0;
  const perMin = Number(perMinuteVal) || 0;
  const canBuyCount = price > 0 ? (earned / price) : 0;
  const minutesNeeded = perMin > 0 ? (price / perMin) : 0;
  const canBuyDisplay = canBuyCount >= 100 ? canBuyCount.toFixed(0) : canBuyCount.toFixed(2);
  const minutesDisplay = minutesNeeded >= 100 ? minutesNeeded.toFixed(0) : minutesNeeded.toFixed(1);
  const progressPct = price > 0 ? Math.min(100, (earned / price) * 100) : 0;

  els.itemsList.innerHTML = `
    <div class="item-hero">
      <div class="item-hero-head">
        <div class="item-hero-name">${escapeHtml(selected.name)}</div>
        <div class="item-hero-price">¥${price.toFixed(2)} <span class="item-hero-unit">/ ${escapeHtml(selected.unit)}</span></div>
      </div>
      <div class="item-hero-canbuy">
        <div class="canbuy-label">已赚可买</div>
        <div class="canbuy-value">
          <span class="canbuy-num">${canBuyDisplay}</span>
          <span class="canbuy-unit">${escapeHtml(selected.unit)}</span>
        </div>
      </div>
      <div class="progress-ring item-progress">
        <div style="width: ${progressPct.toFixed(1)}%"></div>
      </div>
      <div class="item-progress-label">
        ${canBuyCount >= 1 ? `已攒 ${Math.floor(canBuyCount)} ${escapeHtml(selected.unit)} 🎉` : `还差 ¥${(price - earned).toFixed(2)} 即可买 1 ${escapeHtml(selected.unit)}`}
      </div>
      <div class="item-hero-minutes">
        <div class="minutes-icon">⏱️</div>
        <div class="minutes-content">
          <div class="minutes-label">赚到 1 ${escapeHtml(selected.unit)} 需要</div>
          <div class="minutes-value">${minutesDisplay} <span class="minutes-unit">分钟</span></div>
        </div>
      </div>
    </div>`;
}

function renderItemsConfig() {
  if (!items.length) {
    els.itemsConfigList.innerHTML = `<div class="config-empty">还没有添加任何实物 · 在下方添加你的"快乐单位" ☕</div>`;
    return;
  }
  els.itemsConfigList.innerHTML = items.map((it, idx) => {
    const isSelected = !!it.selected;
    const price = Number(it.price) || 0;
    return `
      <div class="config-item ${isSelected ? 'selected-item' : ''}" data-idx="${idx}">
        <label class="ci-radio-wrap">
          <input type="radio" name="itemSelect" class="toggle-select" data-idx="${idx}" ${isSelected ? 'checked' : ''} title="选中后展示在上方" />
          <div class="ci-info">
            <div class="ci-name">${escapeHtml(it.name)}</div>
            <div class="ci-meta">¥${price.toFixed(2)} / ${escapeHtml(it.unit)}</div>
          </div>
        </label>
        <div class="ci-stats">
          <div class="ci-stat">
            <div class="ci-stat-label">已赚可买</div>
            <div class="ci-stat-value" data-idx="${idx}" data-type="canBuy">0.00<span class="ci-stat-unit">${escapeHtml(it.unit)}</span></div>
          </div>
          <div class="ci-stat ci-stat--highlight">
            <div class="ci-stat-label">需上班</div>
            <div class="ci-stat-value" data-idx="${idx}" data-type="minutes">0.0<span class="ci-stat-unit">分钟</span></div>
          </div>
        </div>
        <span class="ci-del" data-idx="${idx}" title="删除">×</span>
      </div>`;
  }).join('');

  els.itemsConfigList.querySelectorAll('.toggle-select').forEach(el => {
    el.addEventListener('change', () => {
      const idx = Number(el.getAttribute('data-idx'));
      items.forEach((it, i) => { it.selected = (i === idx); });
      persistItems();
      updateItemsPreview();
      renderItemsConfig();
      update();
    });
  });

  els.itemsConfigList.querySelectorAll('.config-item').forEach(row => {
    row.addEventListener('click', (e) => {
      if (e.target.classList.contains('ci-del') || e.target.closest('.ci-stats')) return;
      const idx = Number(row.getAttribute('data-idx'));
      items.forEach((it, i) => { it.selected = (i === idx); });
      persistItems();
      updateItemsPreview();
      renderItemsConfig();
      update();
    });
  });

  els.itemsConfigList.querySelectorAll('.ci-del').forEach(el => {
    el.addEventListener('click', (e) => {
      e.stopPropagation();
      const idx = Number(el.getAttribute('data-idx'));
      const wasSelected = items[idx].selected;
      items.splice(idx, 1);
      if (wasSelected && items.length > 0) items[0].selected = true;
      persistItems();
      updateItemsPreview();
      renderItemsConfig();
      update();
      showToast('已删除');
    });
  });
}

function updateItemsConfigNumbers(earned, perMinuteVal) {
  if (!items.length) return;
  const earnedNum = Number(earned) || 0;
  const perMin = Number(perMinuteVal) || 0;
  els.itemsConfigList.querySelectorAll('.ci-stat-value').forEach(el => {
    const idx = Number(el.getAttribute('data-idx'));
    const type = el.getAttribute('data-type');
    const it = items[idx];
    if (!it) return;
    const price = Number(it.price) || 0;
    if (type === 'canBuy') {
      const count = price > 0 ? (earnedNum / price) : 0;
      const display = count >= 100 ? count.toFixed(0) : count.toFixed(2);
      el.innerHTML = `${display}<span class="ci-stat-unit">${escapeHtml(it.unit)}</span>`;
    } else if (type === 'minutes') {
      const minutes = perMin > 0 ? (price / perMin) : 0;
      const display = minutes >= 100 ? minutes.toFixed(0) : minutes.toFixed(1);
      el.innerHTML = `${display}<span class="ci-stat-unit">分钟</span>`;
    }
  });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

// ============== 数字滚动动画 ==============
const numAnimators = {};
function setNumber(el, value, formatter) {
  formatter = formatter || (v => v.toFixed(2));
  const key = el.id;
  if (!numAnimators[key]) numAnimators[key] = { current: 0, target: 0, raf: null };
  const anim = numAnimators[key];
  anim.target = Number(value) || 0;
  if (anim.raf) cancelAnimationFrame(anim.raf);
  const step = () => {
    const diff = anim.target - anim.current;
    if (Math.abs(diff) < 0.01) {
      anim.current = anim.target;
      el.textContent = formatter(anim.current);
      anim.raf = null;
      return;
    }
    anim.current += diff * 0.18;
    el.textContent = formatter(anim.current);
    anim.raf = requestAnimationFrame(step);
  };
  step();
}

// ============== Toast ==============
let toastTimer = null;
function showToast(msg) {
  els.toast.textContent = msg;
  els.toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => els.toast.classList.remove('show'), 1800);
}

// ============== 主更新逻辑 ==============
let lastSecond = -1;

function update() {
  const now = new Date();
  const wd = isWorkday(now);

  if (!wd.work) {
    els.countdownBody.style.display = 'none';
    els.holidayBody.style.display = 'block';
    const isHoliday = wd.name !== '周末';
    els.holidayText.textContent = isHoliday
      ? `🌴 ${wd.name}快乐 · 今天休假`
      : `🛌 周末快乐 · 今天休假`;
    setNumber(els.earnedToday, 0);
    setNumber(els.remainToEarn, 0);
    setNumber(els.totalToday, 0);
    setNumber(els.perMinute, 0);
    setNumber(els.perSecond, 0);
    if (els.earnedSub) els.earnedSub.textContent = '🌴 今天休假，快乐无边';
    renderItemsDisplay(0, 0);
    updateItemsConfigNumbers(0, 0);
    els.dayProgress.style.width = '0%';
    els.countdownSub.textContent = '今日休假';
  } else {
    els.countdownBody.style.display = 'block';
    els.holidayBody.style.display = 'none';

    const totalWorkMin = calcTotalWorkMinutes(config.workStart, config.workEnd, config.lunchStart, config.lunchEnd);
    const workedMin = calcWorkedMinutes(config.workStart, config.workEnd, config.lunchStart, config.lunchEnd, now);
    const remainMin = calcRemainMinutes(config.workStart, config.workEnd, config.lunchStart, config.lunchEnd, now);

    const we = parseTimeToMinutes(config.workEnd);
    const cur = nowMinutes(now);
    const remainTotalMin = Math.max(0, we - cur);
    const hours = Math.floor(remainTotalMin / 60);
    const mins = Math.floor(remainTotalMin % 60);
    const secs = 59 - now.getSeconds();
    const cdH = String(hours).padStart(2, '0');
    const cdM = String(mins).padStart(2, '0');
    const cdS = String(Math.max(0, secs)).padStart(2, '0');

    if (lastSecond !== now.getSeconds()) {
      els.cdH.textContent = cdH;
      els.cdM.textContent = cdM;
      els.cdS.textContent = cdS;
      els.cdS.classList.remove('pulse');
      void els.cdS.offsetWidth;
      els.cdS.classList.add('pulse');
      lastSecond = now.getSeconds();
    }

    const progress = totalWorkMin > 0 ? Math.min(100, (workedMin / totalWorkMin) * 100) : 0;
    els.dayProgress.style.width = progress.toFixed(1) + '%';
    els.countdownSub.textContent = `今日工作进度 ${progress.toFixed(1)}%`;

    const salary = Number(config.salary) || 0;
    const workDays = Number(config.workDaysPerMonth) || countWorkdaysInMonth(now.getFullYear(), now.getMonth());
    const perMinuteVal = workDays > 0 && totalWorkMin > 0 ? salary / workDays / totalWorkMin : 0;
    const perSecondVal = perMinuteVal / 60;
    const earned = perMinuteVal * workedMin;
    const remain = perMinuteVal * remainMin;
    const totalToday = perMinuteVal * totalWorkMin;

    setNumber(els.earnedToday, earned);
    setNumber(els.remainToEarn, remain);
    setNumber(els.totalToday, totalToday);
    setNumber(els.perMinute, perMinuteVal);
    setNumber(els.perSecond, perSecondVal);

    if (els.earnedSub) {
      const pct = totalToday > 0 ? (earned / totalToday) * 100 : 0;
      if (pct >= 99) els.earnedSub.textContent = '🎉 今日已圆满搬砖！';
      else if (pct >= 75) els.earnedSub.textContent = `🔥 已完成 ${pct.toFixed(0)}% · 冲刺中`;
      else if (pct >= 40) els.earnedSub.textContent = `⚡ 已完成 ${pct.toFixed(0)}% · 状态不错`;
      else if (pct > 0) els.earnedSub.textContent = `🌱 已完成 ${pct.toFixed(0)}% · 继续加油`;
      else els.earnedSub.textContent = '⏰ 刚刚开始搬砖…';
    }

    renderItemsDisplay(earned, perMinuteVal);
    updateItemsConfigNumbers(earned, perMinuteVal);

    updateStats(now, workDays, totalWorkMin, perMinuteVal);
  }
}

function updateStats(now, workDays, totalWorkMin, perMinuteVal) {
  const payDay = Number(config.payDay) || 10;
  let payday = new Date(now.getFullYear(), now.getMonth(), payDay);
  if (payday < now) payday = new Date(now.getFullYear(), now.getMonth() + 1, payDay);
  const daysToPay = Math.ceil((payday - now) / (1000 * 60 * 60 * 24));
  els.daysToPayday.textContent = daysToPay;
  els.paydayMeta.textContent = `下次发薪日：${payday.getFullYear()}-${String(payday.getMonth()+1).padStart(2,'0')}-${String(payday.getDate()).padStart(2,'0')}`;

  els.monthWorkDays.textContent = workDays;
  const todayWorkInfo = isWorkday(now);
  els.monthWorkMeta.textContent = todayWorkInfo.work ? `今日：${todayWorkInfo.name}` : `今日休假`;

  const salary = Number(config.salary) || 0;
  const dailySalary = workDays > 0 ? salary / workDays : 0;
  let monthEarnedCalc = 0;
  let workedDaysCount = 0;
  const y = now.getFullYear(), m = now.getMonth();
  const daysInMonth = new Date(y, m + 1, 0).getDate();
  for (let d = 1; d <= daysInMonth; d++) {
    const date = new Date(y, m, d);
    const w = isWorkday(date);
    if (!w.work) continue;
    if (date.getDate() < now.getDate()) {
      monthEarnedCalc += dailySalary;
      workedDaysCount++;
    } else if (date.getDate() === now.getDate()) {
      const totalWorkMinToday = calcTotalWorkMinutes(config.workStart, config.workEnd, config.lunchStart, config.lunchEnd);
      const workedMinToday = calcWorkedMinutes(config.workStart, config.workEnd, config.lunchStart, config.lunchEnd, now);
      const ratio = totalWorkMinToday > 0 ? workedMinToday / totalWorkMinToday : 0;
      monthEarnedCalc += dailySalary * ratio;
      workedDaysCount += ratio;
    }
  }
  setNumber(els.monthEarned, monthEarnedCalc);
  const monthPct = salary > 0 ? (monthEarnedCalc / salary * 100) : 0;
  els.monthEarnedMeta.textContent = `已工作 ${workedDaysCount.toFixed(1)} 天 · ${monthPct.toFixed(1)}%`;
  els.monthBar.style.width = Math.min(100, monthPct).toFixed(1) + '%';

  const monthRemain = Math.max(0, salary - monthEarnedCalc);
  setNumber(els.monthRemain, monthRemain);
  const remainDays = workDays - workedDaysCount;
  els.monthRemainMeta.textContent = `剩余 ${remainDays.toFixed(1)} 个工作日`;

  const hours = totalWorkMin / 60;
  els.dailyHours.textContent = hours.toFixed(2) + ' 小时';
  els.dailyHoursMeta.textContent = `${parseTimeToMinutes(config.workStart)/60|0}:${String(parseTimeToMinutes(config.workStart)%60).padStart(2,'0')} - ${config.workEnd} (扣午休)`;

  const hourly = totalWorkMin > 0 ? perMinuteVal * 60 : 0;
  setNumber(els.hourlyRate, hourly);
}

// ============== 事件绑定 ==============
function bindEvents() {
  els.btnAddItem.addEventListener('click', () => {
    const name = els.itemName.value.trim();
    const price = parseFloat(els.itemPrice.value);
    const unit = els.itemUnit.value.trim();
    if (!name) { showToast('请输入实物名称'); return; }
    if (!price || price <= 0) { showToast('请输入单价'); return; }
    if (!unit) { showToast('请输入单位'); return; }
    items.push({ name, price, unit, selected: items.length === 0 });
    persistItems();
    els.itemName.value = '';
    els.itemPrice.value = '';
    els.itemUnit.value = '';
    updateItemsPreview();
    renderItemsConfig();
    update();
    showToast('已添加');
  });

  [els.itemName, els.itemPrice, els.itemUnit].forEach(el => {
    el.addEventListener('keydown', e => {
      if (e.key === 'Enter') els.btnAddItem.click();
    });
  });

  els.btnTheme.addEventListener('click', () => {
    const cur = document.documentElement.getAttribute('data-theme');
    applyTheme(cur === 'dark' ? 'light' : 'dark');
  });

  els.btnReset.addEventListener('click', async () => {
    if (!confirm('确定要重置所有数据吗？\n（包含工资配置、实物换算、Tips）')) return;
    await API.reset();
    // 重新加载配置和实物
    const cfg = await API.getConfig();
    Object.assign(config, cfg);
    tipsText = cfg.tips;
    items = await API.getItems();
    applyConfigToForm();
    renderItemsConfig();
    update();
    showToast('已重置');
  });

  els.settingsPanel.addEventListener('toggle', () => {
    config.settingsOpen = els.settingsPanel.open;
    persistConfig();
  });
  els.itemsPanel.addEventListener('toggle', () => {
    config.itemsOpen = els.itemsPanel.open;
    persistConfig();
  });
}

// ============== 启动 ==============
async function init() {
  // 加载后端配置
  const cfg = await API.getConfig();
  if (!cfg) return;
  Object.assign(config, cfg);
  tipsText = cfg.tips || defaultConfig.tips;

  // 加载实物列表
  const itemsData = await API.getItems();
  if (itemsData === null) return;
  items = itemsData;

  initTheme();
  applyConfigToForm();
  bindConfigInputs();
  bindEvents();
  renderItemsConfig();
  update();
  // 每秒更新一次
  setInterval(update, 1000);
}

document.addEventListener('DOMContentLoaded', init);
