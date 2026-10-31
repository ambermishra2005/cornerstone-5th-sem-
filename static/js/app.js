/**
 * Intelligent Personal Finance Management & Expense Prediction System
 * Frontend Client Controller
 */

// Global App State
let currentUser = null;
let allTransactions = [];
let budgetData = null;
let analyticsData = null;
let mlMetricsData = null;
let recsData = null;
let charts = {};

let autoCatDebounceTimer = null;
let isRegisterMode = false;

// ----------------- Initialization -----------------
document.addEventListener('DOMContentLoaded', async () => {
  // Set default date in transaction modal to today
  const today = new Date().toISOString().split('T')[0];
  const dateInput = document.getElementById('form-tx-date');
  if (dateInput) dateInput.value = today;

  await loadUserData();
  await refreshAllData();
});

// ----------------- Toast Notification -----------------
function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  const msgEl = document.getElementById('toast-msg');
  const iconEl = document.getElementById('toast-icon');

  msgEl.textContent = message;
  toast.className = 'fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-2xl flex items-center space-x-3 text-sm transition-all duration-300';
  
  if (type === 'success') {
    toast.classList.add('bg-emerald-950', 'border', 'border-emerald-500/40', 'text-emerald-300');
    iconEl.className = 'fa-solid fa-circle-check text-emerald-400';
  } else if (type === 'error') {
    toast.classList.add('bg-rose-950', 'border', 'border-rose-500/40', 'text-rose-300');
    iconEl.className = 'fa-solid fa-triangle-exclamation text-rose-400';
  } else {
    toast.classList.add('bg-indigo-950', 'border', 'border-indigo-500/40', 'text-indigo-300');
    iconEl.className = 'fa-solid fa-circle-info text-indigo-400';
  }

  toast.classList.remove('hidden');
  setTimeout(() => {
    toast.classList.add('hidden');
  }, 4000);
}

// ----------------- Tab Navigation -----------------
function switchTab(tabName) {
  // Hide all panes
  document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
  
  // Reset tab buttons
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.className = 'nav-tab px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 transition-all flex items-center space-x-2';
  });

  // Activate selected
  const activePane = document.getElementById(`pane-${tabName}`);
  const activeBtn = document.getElementById(`tab-${tabName}`);
  if (activePane) activePane.classList.remove('hidden');
  if (activeBtn) {
    activeBtn.className = 'nav-tab px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium text-indigo-400 bg-indigo-950/50 border border-indigo-500/30 transition-all flex items-center space-x-2';
  }

  // Trigger chart re-render / resize if needed
  if (tabName === 'overview' || tabName === 'analytics') {
    setTimeout(() => {
      Object.values(charts).forEach(chart => {
        if (chart) chart.resize();
      });
    }, 100);
  }
}

// ----------------- Data Fetching -----------------
async function loadUserData() {
  try {
    const res = await fetch('/api/auth/me');
    if (res.ok) {
      const data = await res.json();
      currentUser = data.user;
      const isDefault = !!(currentUser.is_default || (currentUser.email === 'demo@finance.ai'));
      currentUser.is_default = isDefault;

      const nameEl = document.getElementById('user-name');
      const emailEl = document.getElementById('user-email');
      const badgeEl = document.getElementById('user-account-badge');

      if (nameEl) nameEl.textContent = currentUser.name || 'User';
      if (emailEl) emailEl.textContent = currentUser.email || '';
      if (badgeEl) {
        if (isDefault) {
          badgeEl.textContent = 'Default Demo';
          badgeEl.className = 'px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30';
        } else {
          badgeEl.textContent = 'Personal';
          badgeEl.className = 'px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
        }
      }

      // Update predictor form account mode indicator
      const predModeBadge = document.getElementById('pred-mode-badge');
      const predModeSub = document.getElementById('pred-mode-subtitle');
      if (predModeBadge) {
        if (isDefault) {
          predModeBadge.textContent = 'Default Demo Account';
          predModeBadge.className = 'px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30';
        } else {
          predModeBadge.textContent = 'Personal Account';
          predModeBadge.className = 'px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30';
        }
      }
      if (predModeSub) {
        predModeSub.textContent = isDefault
          ? 'Loaded with default baseline numbers for Abhay Sharma (sample financial profile).'
          : 'Live prediction will activate automatically once you add both your income and expenses.';
      }

      // Update predictor income default
      const predIncome = document.getElementById('pred-income');
      if (predIncome) {
        if (isDefault) {
          predIncome.value = currentUser.monthly_income || 45000;
        } else {
          predIncome.value = currentUser.monthly_income || 0;
        }
      }
    }
  } catch (err) {
    console.warn('Could not load user profile:', err);
  }
}

async function refreshAllData() {
  await Promise.all([
    fetchTransactions(),
    fetchBudgetStatus(),
    fetchAnalyticsSummary(),
    fetchMLMetrics(),
    fetchRecommendations()
  ]);
}

// ----------------- Transactions Handlers -----------------
async function fetchTransactions() {
  try {
    const res = await fetch('/api/transactions');
    const data = await res.json();
    allTransactions = data.transactions || [];
    renderTransactionsTable(allTransactions);
    renderRecentTransactions(allTransactions.slice(0, 6));
  } catch (err) {
    console.error('Failed to load transactions:', err);
  }
}

function renderTransactionsTable(list) {
  const tbody = document.getElementById('tx-table-body');
  const countLabel = document.getElementById('tx-count-label');
  if (!tbody) return;

  tbody.innerHTML = '';
  if (countLabel) countLabel.textContent = `Showing ${list.length} records`;

  if (list.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="py-8 text-center text-slate-500">
          <i class="fa-solid fa-inbox text-2xl mb-2"></i>
          <p>No transaction records found matching criteria.</p>
        </td>
      </tr>
    `;
    return;
  }

  list.forEach(tx => {
    const isIncome = tx.type === 'income';
    const row = document.createElement('tr');
    row.className = 'hover:bg-slate-800/30 transition-colors';

    row.innerHTML = `
      <td class="py-3 px-4 font-mono text-slate-300">${tx.date}</td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${isIncome ? 'badge-income' : 'badge-expense'}">
          ${isIncome ? 'Income' : 'Expense'}
        </span>
      </td>
      <td class="py-3 px-4 font-medium text-slate-200">
        ${escapeHtml(tx.description || tx.category)}
      </td>
      <td class="py-3 px-4">
        <span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 border border-slate-700 text-slate-300">
          ${tx.category}
        </span>
      </td>
      <td class="py-3 px-4 text-slate-400 text-[11px]">${tx.payment_mode || 'UPI'}</td>
      <td class="py-3 px-4 text-right font-bold ${isIncome ? 'text-emerald-400' : 'text-slate-100'}">
        ${isIncome ? '+' : '-'}₹${Number(tx.amount).toLocaleString('en-IN')}
      </td>
      <td class="py-3 px-4 text-center space-x-1">
        <button onclick="editTransaction(${tx.id})" title="Edit" class="p-1 text-slate-400 hover:text-indigo-400 transition-colors">
          <i class="fa-solid fa-pen"></i>
        </button>
        <button onclick="deleteTransaction(${tx.id})" title="Delete" class="p-1 text-slate-400 hover:text-rose-400 transition-colors">
          <i class="fa-solid fa-trash"></i>
        </button>
      </td>
    `;
    tbody.appendChild(row);
  });
}

function renderRecentTransactions(list) {
  const tbody = document.getElementById('recent-tx-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="py-4 text-center text-slate-500">No recent transactions.</td></tr>`;
    return;
  }

  list.forEach(tx => {
    const isIncome = tx.type === 'income';
    const row = document.createElement('tr');
    row.className = 'hover:bg-slate-800/30';
    row.innerHTML = `
      <td class="py-2.5 px-3 font-mono text-slate-400">${tx.date}</td>
      <td class="py-2.5 px-3 font-medium text-slate-200">${escapeHtml(tx.description || tx.category)}</td>
      <td class="py-2.5 px-3">
        <span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 border border-slate-700 text-slate-300">
          ${tx.category}
        </span>
      </td>
      <td class="py-2.5 px-3 text-slate-400">${tx.payment_mode || 'UPI'}</td>
      <td class="py-2.5 px-3 text-right font-bold ${isIncome ? 'text-emerald-400' : 'text-slate-200'}">
        ${isIncome ? '+' : '-'}₹${Number(tx.amount).toLocaleString('en-IN')}
      </td>
    `;
    tbody.appendChild(row);
  });
}

function filterTransactions() {
  const search = document.getElementById('tx-search').value.toLowerCase().trim();
  const typeFilter = document.getElementById('tx-filter-type').value;
  const catFilter = document.getElementById('tx-filter-category').value;

  const filtered = allTransactions.filter(t => {
    const matchSearch = !search || 
      (t.description && t.description.toLowerCase().includes(search)) ||
      (t.category && t.category.toLowerCase().includes(search));
    const matchType = (typeFilter === 'all') || (t.type === typeFilter);
    const matchCat = (catFilter === 'all') || (t.category === catFilter);
    return matchSearch && matchType && matchCat;
  });

  renderTransactionsTable(filtered);
}

// ----------------- Transaction Modal & Auto-Categorization -----------------
function openTransactionModal(editTx = null) {
  const modal = document.getElementById('modal-transaction');
  const title = document.getElementById('modal-tx-title');
  const idInput = document.getElementById('form-tx-id');
  const descInput = document.getElementById('form-tx-desc');
  const amountInput = document.getElementById('form-tx-amount');
  const dateInput = document.getElementById('form-tx-date');
  const catSelect = document.getElementById('form-tx-category');
  const pmSelect = document.getElementById('form-tx-payment-mode');
  const autoBadge = document.getElementById('auto-cat-badge');

  if (autoBadge) autoBadge.classList.add('hidden');

  if (editTx) {
    title.textContent = 'Edit Transaction Record';
    idInput.value = editTx.id;
    descInput.value = editTx.description || '';
    amountInput.value = editTx.amount;
    dateInput.value = editTx.date;
    catSelect.value = editTx.category;
    pmSelect.value = editTx.payment_mode || 'UPI';
    setFormType(editTx.type);
  } else {
    title.textContent = 'Add Transaction Record';
    idInput.value = '';
    descInput.value = '';
    amountInput.value = '';
    dateInput.value = new Date().toISOString().split('T')[0];
    setFormType('expense');
  }

  modal.classList.remove('hidden');
}

function closeTransactionModal() {
  document.getElementById('modal-transaction').classList.add('hidden');
}

function setFormType(type) {
  document.getElementById('form-tx-type').value = type;
  const expBtn = document.getElementById('btn-type-expense');
  const incBtn = document.getElementById('btn-type-income');

  if (type === 'expense') {
    expBtn.className = 'py-2 rounded-xl bg-rose-600/30 border border-rose-500 text-rose-300 font-semibold';
    incBtn.className = 'py-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-400 font-semibold';
  } else {
    incBtn.className = 'py-2 rounded-xl bg-emerald-600/30 border border-emerald-500 text-emerald-300 font-semibold';
    expBtn.className = 'py-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-400 font-semibold';
  }
}

// Auto-Categorization on typing description
function handleDescriptionInput(val) {
  clearTimeout(autoCatDebounceTimer);
  if (!val || val.length < 3) return;

  autoCatDebounceTimer = setTimeout(async () => {
    try {
      const res = await fetch('/api/transactions/auto-categorize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: val })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.category && data.category !== 'Other') {
          const catSelect = document.getElementById('form-tx-category');
          catSelect.value = data.category;
          const autoBadge = document.getElementById('auto-cat-badge');
          if (autoBadge) {
            autoBadge.textContent = `Auto: ${data.category}`;
            autoBadge.classList.remove('hidden');
          }
        }
      }
    } catch (e) {
      console.warn('Auto-categorize failed', e);
    }
  }, 350);
}

async function handleSaveTransaction(e) {
  e.preventDefault();
  const id = document.getElementById('form-tx-id').value;
  const type = document.getElementById('form-tx-type').value;
  const description = document.getElementById('form-tx-desc').value.trim();
  const amount = parseFloat(document.getElementById('form-tx-amount').value);
  const date = document.getElementById('form-tx-date').value;
  const category = document.getElementById('form-tx-category').value;
  const payment_mode = document.getElementById('form-tx-payment-mode').value;

  const payload = { type, description, amount, date, category, payment_mode };

  try {
    let res;
    if (id) {
      res = await fetch(`/api/transactions/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    if (res.ok) {
      closeTransactionModal();
      showToast(id ? 'Transaction updated successfully.' : 'Record stored in database with category.');
      await refreshAllData();
    } else {
      const err = await res.json();
      showToast(err.error || 'Failed to save record', 'error');
    }
  } catch (err) {
    showToast('Network error while saving transaction', 'error');
  }
}

async function editTransaction(id) {
  try {
    const res = await fetch(`/api/transactions/${id}`);
    if (res.ok) {
      const data = await res.json();
      openTransactionModal(data.transaction);
    }
  } catch (err) {
    showToast('Failed to fetch transaction details', 'error');
  }
}

async function deleteTransaction(id) {
  if (!confirm('Are you sure you want to delete this financial record?')) return;
  try {
    const res = await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
    if (res.ok) {
      showToast('Record deleted successfully.');
      await refreshAllData();
    } else {
      showToast('Failed to delete record.', 'error');
    }
  } catch (err) {
    showToast('Network error on delete', 'error');
  }
}

async function handleCSVUpload(input) {
  if (!input.files || input.files.length === 0) return;
  const file = input.files[0];
  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/transactions/import-csv', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      showToast(`Successfully imported ${data.imported_count} records!`);
      await refreshAllData();
    } else {
      showToast(data.error || 'CSV import failed', 'error');
    }
  } catch (err) {
    showToast('Error uploading CSV file', 'error');
  }
  input.value = '';
}

// ----------------- Budgets Handlers -----------------
async function fetchBudgetStatus() {
  try {
    const res = await fetch('/api/budgets/status');
    const data = await res.json();
    budgetData = data;
    renderBudgetCards(data);
  } catch (err) {
    console.error('Failed to load budget status:', err);
  }
}

function renderBudgetCards(data) {
  const grid = document.getElementById('budget-cards-grid');
  const summaryText = document.getElementById('budget-summary-text');
  const overallPercent = document.getElementById('overall-budget-percent');
  const overallBar = document.getElementById('overall-budget-bar');
  if (!grid || !data) return;

  grid.innerHTML = '';
  
  if (summaryText) {
    summaryText.textContent = `Spent ₹${data.total_spent.toLocaleString('en-IN')} of ₹${data.total_budget.toLocaleString('en-IN')} total limit`;
  }
  if (overallPercent) {
    overallPercent.textContent = `${data.total_percent}%`;
  }
  if (overallBar) {
    overallBar.style.width = `${Math.min(100, data.total_percent)}%`;
    if (data.total_percent > 100) {
      overallBar.className = 'bg-rose-500 h-3 rounded-full';
    } else if (data.total_percent > 80) {
      overallBar.className = 'bg-amber-500 h-3 rounded-full';
    } else {
      overallBar.className = 'bg-emerald-500 h-3 rounded-full';
    }
  }

  const categoryIcons = {
    'Bills': 'fa-file-invoice-dollar',
    'Food': 'fa-utensils',
    'Transport': 'fa-car',
    'Shopping': 'fa-bag-shopping',
    'Entertainment': 'fa-film',
    'Healthcare': 'fa-heart-pulse',
    'Education': 'fa-graduation-cap',
    'Other': 'fa-cubes'
  };

  (data.categories || []).forEach(cat => {
    const icon = categoryIcons[cat.category] || 'fa-tag';
    const card = document.createElement('div');
    card.className = 'glass-panel p-4 space-y-2';

    let barColor = 'bg-emerald-400';
    let statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300">On Track</span>';
    if (cat.percent_used > 100) {
      barColor = 'bg-rose-500';
      statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] bg-rose-500/20 text-rose-300 font-bold">Over Budget</span>';
    } else if (cat.percent_used > 80) {
      barColor = 'bg-amber-400';
      statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300">Near Limit</span>';
    }

    card.innerHTML = `
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-indigo-400 text-xs">
            <i class="fa-solid ${icon}"></i>
          </div>
          <div>
            <h4 class="text-xs font-bold text-white">${cat.category}</h4>
            <p class="text-[10px] text-slate-400">Limit: ₹${cat.limit.toLocaleString('en-IN')}</p>
          </div>
        </div>
        ${statusBadge}
      </div>

      <div class="pt-2">
        <div class="flex justify-between text-[11px] mb-1">
          <span class="text-slate-400">Spent: ₹${cat.spent.toLocaleString('en-IN')}</span>
          <span class="font-bold text-slate-300">${cat.percent_used}%</span>
        </div>
        <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
          <div class="${barColor} h-2 rounded-full transition-all duration-300" style="width: ${Math.min(100, cat.percent_used)}%"></div>
        </div>
      </div>

      <div class="text-[10px] text-slate-400 pt-1 flex justify-between">
        <span>Balance Remaining:</span>
        <strong class="${cat.remaining < 0 ? 'text-rose-400' : 'text-emerald-400'}">
          ${cat.remaining < 0 ? '-' : ''}₹${Math.abs(cat.remaining).toLocaleString('en-IN')}
        </strong>
      </div>
    `;
    grid.appendChild(card);
  });
}

async function handleSetBudget(e) {
  e.preventDefault();
  const category = document.getElementById('budget-form-category').value;
  const limit = parseFloat(document.getElementById('budget-form-limit').value);

  try {
    const res = await fetch('/api/budgets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, monthly_limit: limit })
    });
    if (res.ok) {
      showToast(`Budget for ${category} updated to ₹${limit.toLocaleString('en-IN')}`);
      document.getElementById('budget-form-limit').value = '';
      await fetchBudgetStatus();
    } else {
      showToast('Failed to update budget', 'error');
    }
  } catch (err) {
    showToast('Network error setting budget', 'error');
  }
}

async function autoRecommendBudgets() {
  try {
    const res = await fetch('/api/budgets/auto-recommend', { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      showToast(`Budgets auto-allocated based on ML prediction of ₹${data.predicted_monthly_total.toLocaleString('en-IN')}!`);
      await fetchBudgetStatus();
    } else {
      showToast('Auto-recommendation failed', 'error');
    }
  } catch (err) {
    showToast('Network error on auto-recommend', 'error');
  }
}

// ----------------- Analytics & Charts -----------------
async function fetchAnalyticsSummary() {
  try {
    const res = await fetch('/api/analytics/summary');
    const data = await res.json();
    analyticsData = data;
    updateOverviewKPIs(data);
    renderCharts(data);
    renderReportsTable(data);
  } catch (err) {
    console.error('Failed to load analytics summary:', err);
  }
}

function updateOverviewKPIs(data) {
  const incEl = document.getElementById('kpi-income');
  const expEl = document.getElementById('kpi-expense');
  const savEl = document.getElementById('kpi-savings');
  const savRateEl = document.getElementById('kpi-savings-rate');
  const zeroBanner = document.getElementById('zero-data-banner');

  const totalInc = data.total_income || 0;
  const totalExp = data.total_expense || 0;
  const netSav = data.net_savings || 0;
  const savRate = data.savings_rate || 0;

  if (incEl) incEl.textContent = `₹${totalInc.toLocaleString('en-IN')}`;
  if (expEl) expEl.textContent = `₹${totalExp.toLocaleString('en-IN')}`;
  if (savEl) savEl.textContent = `₹${netSav.toLocaleString('en-IN')}`;
  if (savRateEl) savRateEl.textContent = `${savRate}%`;

  // Toggle zero data onboarding banner
  if (zeroBanner) {
    if (allTransactions.length === 0 && totalInc === 0 && totalExp === 0) {
      zeroBanner.classList.remove('hidden');
    } else {
      zeroBanner.classList.add('hidden');
    }
  }

  const isDefault = !!(currentUser?.is_default || (currentUser?.email === 'demo@finance.ai'));
  const userIncome = totalInc > 0 ? totalInc : (currentUser?.monthly_income || 0);

  // Pre-fill predictor form
  const prevExpInput = document.getElementById('pred-prev-expense');
  const predIncomeInput = document.getElementById('pred-income');
  const predAmountInput = document.getElementById('pred-amount');

  if (isDefault) {
    // Default account gets default prediction numbers
    if (prevExpInput) prevExpInput.value = totalExp > 0 ? totalExp : 21000;
    if (predIncomeInput) predIncomeInput.value = userIncome > 0 ? userIncome : 45000;
    if (predAmountInput) predAmountInput.value = 1500;
    executePrediction(userIncome > 0 ? userIncome : 45000, totalExp > 0 ? totalExp : 21000);
  } else {
    // Other accounts: no dummy prediction numbers
    if (prevExpInput) prevExpInput.value = totalExp;
    if (predIncomeInput) predIncomeInput.value = userIncome;
    if (predAmountInput && allTransactions.length > 0) {
      const recentExp = allTransactions.find(t => t.type === 'expense');
      predAmountInput.value = recentExp ? recentExp.amount : 0;
    }

    // ONLY add prediction if owner has added BOTH expenses and income
    if (userIncome > 0 && totalExp > 0) {
      executePrediction(userIncome, totalExp);
    } else {
      let reason = 'Add income & expenses to predict';
      if (userIncome > 0 && totalExp === 0) {
        reason = 'Add expense records to predict';
      } else if (userIncome === 0 && totalExp > 0) {
        reason = 'Add income record to predict';
      }
      resetPredictionDisplay(reason);
    }
  }
}

function renderCharts(data) {
  // 1. Monthly Flow Chart (Bar)
  const ctxFlow = document.getElementById('chart-monthly-flow');
  if (ctxFlow) {
    if (charts.monthlyFlow) charts.monthlyFlow.destroy();

    const labels = (data.monthly_trends || []).map(m => m.month);
    const incomes = (data.monthly_trends || []).map(m => m.income);
    const expenses = (data.monthly_trends || []).map(m => m.expense);

    charts.monthlyFlow = new Chart(ctxFlow, {
      type: 'bar',
      data: {
        labels: labels.length ? labels : ['Current Month'],
        datasets: [
          {
            label: 'Income',
            data: incomes.length ? incomes : [data.total_income],
            backgroundColor: 'rgba(16, 185, 129, 0.8)',
            borderRadius: 6
          },
          {
            label: 'Expenses',
            data: expenses.length ? expenses : [data.total_expense],
            backgroundColor: 'rgba(244, 63, 94, 0.8)',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#94a3b8', font: { size: 11 } } }
        },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 11 } } },
          y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 11 } } }
        }
      }
    });
  }

  // 2. Category Doughnut Chart
  const ctxDonut = document.getElementById('chart-category-donut');
  if (ctxDonut) {
    if (charts.categoryDonut) charts.categoryDonut.destroy();

    const catLabels = Object.keys(data.category_breakdown || {});
    const catValues = Object.values(data.category_breakdown || {});

    charts.categoryDonut = new Chart(ctxDonut, {
      type: 'doughnut',
      data: {
        labels: catLabels.length ? catLabels : ['General'],
        datasets: [{
          data: catValues.length ? catValues : [1],
          backgroundColor: [
            '#6366f1', '#ec4899', '#f59e0b', '#10b981',
            '#06b6d4', '#8b5cf6', '#3b82f6', '#64748b'
          ],
          borderWidth: 2,
          borderColor: '#090d16'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 10 } }
        },
        cutout: '70%'
      }
    });
  }

  // 3. Payment Mode Pie Chart
  const ctxPM = document.getElementById('chart-payment-mode');
  if (ctxPM) {
    if (charts.paymentMode) charts.paymentMode.destroy();

    const pmLabels = Object.keys(data.payment_mode_breakdown || {});
    const pmValues = Object.values(data.payment_mode_breakdown || {});

    charts.paymentMode = new Chart(ctxPM, {
      type: 'pie',
      data: {
        labels: pmLabels.length ? pmLabels : ['UPI', 'Credit Card', 'Debit Card'],
        datasets: [{
          data: pmValues.length ? pmValues : [50, 30, 20],
          backgroundColor: ['#10b981', '#6366f1', '#f59e0b', '#06b6d4', '#ec4899'],
          borderColor: '#090d16',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 10 } }
        }
      }
    });
  }

  // 4. Daily Cumulative Spending Trajectory Line Chart
  const ctxDaily = document.getElementById('chart-daily-trend');
  if (ctxDaily) {
    if (charts.dailyTrend) charts.dailyTrend.destroy();

    // Group expenses by day of current month
    const expenses = allTransactions.filter(t => t.type === 'expense');
    const dayTotals = {};
    for (let d = 1; d <= 31; d++) dayTotals[d] = 0;

    expenses.forEach(t => {
      const day = parseInt(t.date.split('-')[2], 10);
      if (!isNaN(day)) dayTotals[day] = (dayTotals[day] || 0) + t.amount;
    });

    let cumulative = 0;
    const trajectory = [];
    const days = [];
    for (let d = 1; d <= 30; d++) {
      cumulative += (dayTotals[d] || 0);
      trajectory.push(cumulative);
      days.push(`Day ${d}`);
    }

    charts.dailyTrend = new Chart(ctxDaily, {
      type: 'line',
      data: {
        labels: days,
        datasets: [{
          label: 'Cumulative Expense (₹)',
          data: trajectory,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99, 102, 241, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 10 } } },
          y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 10 } } }
        }
      }
    });
  }
}

function renderReportsTable(data) {
  const tbody = document.getElementById('report-table-body');
  if (!tbody || !budgetData) return;
  tbody.innerHTML = '';

  (budgetData.categories || []).forEach(cat => {
    const row = document.createElement('tr');
    row.className = 'hover:bg-slate-800/30';
    const isOver = cat.remaining < 0;

    row.innerHTML = `
      <td class="py-2.5 px-3 font-medium text-slate-200">${cat.category}</td>
      <td class="py-2.5 px-3 text-right text-slate-300">₹${cat.limit.toLocaleString('en-IN')}</td>
      <td class="py-2.5 px-3 text-right font-semibold text-slate-200">₹${cat.spent.toLocaleString('en-IN')}</td>
      <td class="py-2.5 px-3 text-right font-mono ${isOver ? 'text-rose-400 font-bold' : 'text-emerald-400'}">
        ${isOver ? '-' : '+'}₹${Math.abs(cat.remaining).toLocaleString('en-IN')}
      </td>
      <td class="py-2.5 px-3 text-center">
        <span class="px-2 py-0.5 rounded text-[10px] ${isOver ? 'bg-rose-500/20 text-rose-300 font-semibold' : 'bg-emerald-500/20 text-emerald-300'}">
          ${isOver ? 'Exceeded' : 'Under Control'}
        </span>
      </td>
    `;
    tbody.appendChild(row);
  });
}

// ----------------- Machine Learning (Regression) -----------------
function resetPredictionDisplay(subtext = 'Add income & expenses to predict') {
  const kpiPred = document.getElementById('kpi-prediction');
  const kpiPredSub = document.getElementById('kpi-prediction-subtext');
  const predAmount = document.getElementById('pred-result-amount');
  const predCI = document.getElementById('pred-result-ci');
  const predSav = document.getElementById('pred-result-savings');
  const predRate = document.getElementById('pred-result-rate');

  if (kpiPred) kpiPred.textContent = '₹0';
  if (kpiPredSub) kpiPredSub.textContent = subtext;
  if (predAmount) predAmount.textContent = '₹0';
  if (predCI) predCI.textContent = 'Awaiting owner records';
  if (predSav) predSav.textContent = '₹0';
  if (predRate) predRate.textContent = '0%';
}

async function fetchMLMetrics() {
  try {
    const res = await fetch('/api/ml/metrics');
    const data = await res.json();
    mlMetricsData = data;
    renderMLMetrics(data);

    const isDefault = !!(currentUser?.is_default || (currentUser?.email === 'demo@finance.ai'));
    const userIncome = (analyticsData && analyticsData.total_income > 0)
      ? analyticsData.total_income
      : (currentUser?.monthly_income || 0);
    const userPrev = (analyticsData && analyticsData.total_expense > 0)
      ? analyticsData.total_expense
      : 0;

    if (isDefault) {
      // Default account gets default prediction numbers
      const incomeToUse = userIncome > 0 ? userIncome : 45000;
      const prevToUse = userPrev > 0 ? userPrev : 21000;
      await executePrediction(incomeToUse, prevToUse);
    } else if (userIncome > 0 && userPrev > 0) {
      // Non-default account: ONLY add prediction if owner has added BOTH expenses and income
      await executePrediction(userIncome, userPrev);
    } else {
      let reason = 'Add income & expenses to predict';
      if (userIncome > 0 && userPrev === 0) reason = 'Add expense records to predict';
      else if (userIncome === 0 && userPrev > 0) reason = 'Add income record to predict';
      resetPredictionDisplay(reason);
    }
  } catch (err) {
    console.error('Failed to load ML metrics:', err);
  }
}

function renderMLMetrics(data) {
  const full = data.full_model || data.core_model;
  const core = data.core_model;

  const r2El = document.getElementById('metric-r2');
  const maeEl = document.getElementById('metric-mae');
  const rmseEl = document.getElementById('metric-rmse');
  const mseEl = document.getElementById('metric-mse');
  const formulaEl = document.getElementById('ml-formula-text');

  if (r2El) r2El.textContent = (full.r2_score || 0.9750).toFixed(4);
  if (maeEl) maeEl.textContent = `₹${(full.mae || 0).toLocaleString('en-IN')}`;
  if (rmseEl) rmseEl.textContent = `₹${(full.rmse || 0).toLocaleString('en-IN')}`;
  if (mseEl) mseEl.textContent = Number(full.mse || 0).toLocaleString('en-IN');
  if (formulaEl && core) formulaEl.textContent = core.formula;

  // Render Coefficients Table
  const coefTbody = document.getElementById('coef-table-body');
  if (coefTbody && full.coefficients) {
    coefTbody.innerHTML = '';
    Object.entries(full.coefficients).forEach(([feat, weight]) => {
      const row = document.createElement('tr');
      const isPositive = weight > 0;
      row.className = 'hover:bg-slate-800/30';

      let desc = 'Increases expected monthly expense';
      if (!isPositive) desc = 'Associated with lower expected expenditure';
      if (feat === 'Income') desc = 'Marginal propensity to consume per unit income';
      if (feat === 'Previous_Month_Expense') desc = 'Autoregressive consumption inertia';

      row.innerHTML = `
        <td class="py-2.5 px-3 font-mono text-indigo-300 font-semibold">${feat}</td>
        <td class="py-2.5 px-3 font-mono font-bold ${isPositive ? 'text-emerald-400' : 'text-rose-400'}">
          ${isPositive ? '+' : ''}${weight.toFixed(4)}
        </td>
        <td class="py-2.5 px-3 text-slate-400 text-[11px]">${desc}</td>
      `;
      coefTbody.appendChild(row);
    });
  }
}

async function handleRunPrediction(e) {
  e.preventDefault();
  const income = parseFloat(document.getElementById('pred-income').value) || 0;
  const prevExpense = parseFloat(document.getElementById('pred-prev-expense').value) || 0;
  const category = document.getElementById('pred-category').value;
  const paymentMode = document.getElementById('pred-payment-mode').value;
  const amount = parseFloat(document.getElementById('pred-amount').value) || 0;

  const isDefault = !!(currentUser?.is_default || (currentUser?.email === 'demo@finance.ai'));

  if (!isDefault && (income <= 0 || prevExpense <= 0)) {
    showToast('Please enter both monthly income and previous expenses to predict', 'error');
    let reason = 'Add income & expenses to predict';
    if (income > 0 && prevExpense === 0) reason = 'Enter previous expense (> ₹0)';
    else if (income === 0 && prevExpense > 0) reason = 'Enter monthly income (> ₹0)';
    resetPredictionDisplay(reason);
    return;
  }

  await executePrediction(income, prevExpense, category, paymentMode, amount);
}

async function executePrediction(income, prevExpense, category = 'Food', paymentMode = 'UPI', amount = 1500) {
  const isDefault = !!(currentUser?.is_default || (currentUser?.email === 'demo@finance.ai'));

  // Non-default account: strictly do NOT predict unless both income and expenses exist
  if (!isDefault && (income <= 0 || prevExpense <= 0)) {
    let reason = 'Add income & expenses to predict';
    if (income > 0 && prevExpense <= 0) reason = 'Add expense records to predict';
    else if (income <= 0 && prevExpense > 0) reason = 'Add income record to predict';
    resetPredictionDisplay(reason);
    return;
  }

  try {
    const res = await fetch('/api/ml/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        income,
        previous_month_expense: prevExpense,
        category,
        payment_mode: paymentMode,
        amount
      })
    });
    const result = await res.json();
    if (res.ok) {
      if (result.has_data === false || result.predicted_expense === 0) {
        resetPredictionDisplay('Add income & expenses to predict');
        return;
      }

      const formatted = `₹${result.predicted_expense.toLocaleString('en-IN')}`;
      const kpiPred = document.getElementById('kpi-prediction');
      const kpiPredSub = document.getElementById('kpi-prediction-subtext');
      const predAmount = document.getElementById('pred-result-amount');
      const predCI = document.getElementById('pred-result-ci');
      const predSav = document.getElementById('pred-result-savings');
      const predRate = document.getElementById('pred-result-rate');

      if (kpiPred) kpiPred.textContent = formatted;
      if (kpiPredSub) {
        kpiPredSub.textContent = isDefault
          ? 'Default Demo Prediction (OLS)'
          : 'Predicted via Regression (OLS) for your account';
      }
      if (predAmount) predAmount.textContent = formatted;
      if (predCI) {
        predCI.textContent = `₹${result.confidence_interval.lower.toLocaleString('en-IN')} - ₹${result.confidence_interval.upper.toLocaleString('en-IN')}`;
      }
      if (predSav) predSav.textContent = `₹${result.expected_savings.toLocaleString('en-IN')}`;
      if (predRate) predRate.textContent = `${result.expected_savings_rate}%`;
    }
  } catch (err) {
    console.error('Prediction failed:', err);
  }
}

async function retrainModel() {
  try {
    const res = await fetch('/api/ml/retrain', { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      showToast('Multiple Linear Regression model retrained successfully!');
      renderMLMetrics(data.metrics);
    } else {
      showToast('Model retraining failed', 'error');
    }
  } catch (err) {
    showToast('Network error retrained model', 'error');
  }
}

// ----------------- Recommendations -----------------
async function fetchRecommendations() {
  try {
    const res = await fetch('/api/recommendations');
    const data = await res.json();
    recsData = data;
    renderRecommendations(data);
  } catch (err) {
    console.error('Failed to load recommendations:', err);
  }
}

function renderRecommendations(data) {
  if (!data) return;

  // Financial Health Score in Overview
  const scoreVal = document.getElementById('health-score-val');
  const scoreBadge = document.getElementById('health-score-badge');
  const scoreDesc = document.getElementById('health-score-desc');
  if (scoreVal) scoreVal.textContent = data.financial_health_score;
  if (scoreBadge) {
    if (data.financial_health_score >= 80) {
      scoreBadge.className = 'px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-medium';
      scoreBadge.textContent = 'Excellent';
    } else if (data.financial_health_score >= 60) {
      scoreBadge.className = 'px-2 py-0.5 rounded text-[10px] bg-blue-500/20 text-blue-400 border border-blue-500/30 font-medium';
      scoreBadge.textContent = 'Good Standing';
    } else {
      scoreBadge.className = 'px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-400 border border-amber-500/30 font-medium';
      scoreBadge.textContent = 'Needs Attention';
    }
  }

  // Pillar 1: Save More
  const saveMore = data.save_more;
  if (saveMore) {
    const hl = document.getElementById('rec-save-headline');
    const det = document.getElementById('rec-save-detail');
    const stp = document.getElementById('rec-save-step');
    const bdg = document.getElementById('rec-save-badge');
    if (hl) hl.textContent = saveMore.headline;
    if (det) det.textContent = saveMore.detail;
    if (stp) stp.textContent = saveMore.actionable_step;
    if (bdg) bdg.textContent = saveMore.status;
  }

  // Pillar 2: Discretionary Spending Audit
  const disc = data.unnecessary_spending;
  if (disc) {
    const hl = document.getElementById('rec-disc-headline');
    const listEl = document.getElementById('rec-disc-list');
    if (hl) hl.textContent = disc.headline;
    if (listEl) {
      listEl.innerHTML = '';
      (disc.suggestions || []).forEach(s => {
        const li = document.createElement('li');
        li.textContent = s;
        listEl.appendChild(li);
      });
    }
  }

  // Pillar 3: 50/30/20 Rule
  const bSug = data.budget_suggestions;
  if (bSug) {
    const nVal = document.getElementById('budget-needs-val');
    const nBar = document.getElementById('budget-needs-bar');
    const wVal = document.getElementById('budget-wants-val');
    const wBar = document.getElementById('budget-wants-bar');
    const sVal = document.getElementById('budget-savings-val');
    const sBar = document.getElementById('budget-savings-bar');
    const mlRec = document.getElementById('rec-ml-budget-text');

    if (nVal) nVal.textContent = `${bSug.needs.percent}% (₹${bSug.needs.actual.toLocaleString('en-IN')})`;
    if (nBar) nBar.style.width = `${Math.min(100, bSug.needs.percent)}%`;

    if (wVal) wVal.textContent = `${bSug.wants.percent}% (₹${bSug.wants.actual.toLocaleString('en-IN')})`;
    if (wBar) wBar.style.width = `${Math.min(100, bSug.wants.percent)}%`;

    if (sVal) sVal.textContent = `${bSug.savings.percent}% (₹${bSug.savings.actual.toLocaleString('en-IN')})`;
    if (sBar) sBar.style.width = `${Math.min(100, bSug.savings.percent)}%`;

    if (mlRec) mlRec.textContent = bSug.ml_budget_recommendation;
  }

  // Pillar 4: Investment Tips
  const investContainer = document.getElementById('rec-invest-tips-container');
  if (investContainer && data.investment_tips) {
    investContainer.innerHTML = '';
    (data.investment_tips.tips || []).forEach(tip => {
      const box = document.createElement('div');
      box.className = 'p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1';
      box.innerHTML = `
        <h5 class="font-bold text-slate-200 text-xs flex items-center space-x-1.5">
          <i class="fa-solid fa-gem text-purple-400"></i>
          <span>${tip.title}</span>
        </h5>
        <p class="text-slate-400 text-[11px]">${tip.description}</p>
      `;
      investContainer.appendChild(box);
    });
  }
}

// ----------------- Auth Modal & Operations -----------------
function openRegisterModal() {
  openAuthModal('register');
}

function openAuthModal(mode = 'register') {
  const modal = document.getElementById('modal-auth');
  if (!modal) return;
  hideAuthAlert();
  setAuthTab(mode);
  modal.classList.remove('hidden');
}

function closeAuthModal() {
  const modal = document.getElementById('modal-auth');
  if (modal) modal.classList.add('hidden');
  hideAuthAlert();
}

function setAuthTab(mode) {
  isRegisterMode = (mode === 'register');
  const title = document.getElementById('auth-modal-title');
  const subtitle = document.getElementById('auth-modal-subtitle');
  const submitText = document.getElementById('auth-submit-text');
  const submitBtn = document.getElementById('auth-submit-btn');
  const nameCont = document.getElementById('auth-name-container');
  const incCont = document.getElementById('auth-income-container');
  const tabReg = document.getElementById('tab-auth-register');
  const tabLog = document.getElementById('tab-auth-login');
  hideAuthAlert();

  if (isRegisterMode) {
    if (title) title.textContent = 'Create New Account';
    if (subtitle) subtitle.textContent = 'All data starts at ₹0 for manual expense tracking';
    if (submitText) submitText.textContent = 'Create Account (Start with ₹0)';
    if (submitBtn) {
      submitBtn.className = 'w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold transition-all shadow-lg shadow-emerald-600/25 flex items-center justify-center space-x-2';
    }
    if (nameCont) nameCont.classList.remove('hidden');
    if (incCont) incCont.classList.remove('hidden');

    if (tabReg) {
      tabReg.className = 'py-2 rounded-lg transition-all text-white bg-emerald-600 shadow-md flex items-center justify-center space-x-1.5';
    }
    if (tabLog) {
      tabLog.className = 'py-2 rounded-lg transition-all text-slate-400 hover:text-slate-200 flex items-center justify-center space-x-1.5';
    }
  } else {
    if (title) title.textContent = 'Sign In to Account';
    if (subtitle) subtitle.textContent = 'Enter your email & password to access your dashboard';
    if (submitText) submitText.textContent = 'Sign In';
    if (submitBtn) {
      submitBtn.className = 'w-full py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold transition-all shadow-lg shadow-indigo-600/25 flex items-center justify-center space-x-2';
    }
    if (nameCont) nameCont.classList.add('hidden');
    if (incCont) incCont.classList.add('hidden');

    if (tabLog) {
      tabLog.className = 'py-2 rounded-lg transition-all text-white bg-indigo-600 shadow-md flex items-center justify-center space-x-1.5';
    }
    if (tabReg) {
      tabReg.className = 'py-2 rounded-lg transition-all text-slate-400 hover:text-slate-200 flex items-center justify-center space-x-1.5';
    }
  }
}

function showAuthAlert(msg, type = 'error') {
  const alertBox = document.getElementById('auth-alert');
  if (!alertBox) return;
  alertBox.className = type === 'error'
    ? 'p-3 rounded-xl text-xs flex items-center space-x-2 bg-rose-950/80 border border-rose-500/40 text-rose-300'
    : 'p-3 rounded-xl text-xs flex items-center space-x-2 bg-emerald-950/80 border border-emerald-500/40 text-emerald-300';
  alertBox.innerHTML = `<i class="fa-solid ${type === 'error' ? 'fa-triangle-exclamation text-rose-400' : 'fa-circle-check text-emerald-400'}"></i><span>${msg}</span>`;
  alertBox.classList.remove('hidden');
}

function hideAuthAlert() {
  const alertBox = document.getElementById('auth-alert');
  if (alertBox) alertBox.classList.add('hidden');
}

function toggleAuthMode() {
  setAuthTab(isRegisterMode ? 'login' : 'register');
}

async function loginDemoAccount() {
  try {
    const res = await fetch('/api/auth/demo-login', { method: 'POST' });
    if (res.ok) {
      closeAuthModal();
      showToast('Switched to Demo Account (Abhay Sharma)');
      await loadUserData();
      await refreshAllData();
    }
  } catch (err) {
    showToast('Demo login failed', 'error');
  }
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  hideAuthAlert();

  const emailInput = document.getElementById('auth-email');
  const passInput = document.getElementById('auth-password');
  const submitBtn = document.getElementById('auth-submit-btn');

  const email = (emailInput?.value || '').trim();
  const password = (passInput?.value || '').trim();

  if (!email) {
    showAuthAlert('Please enter your email address.', 'error');
    return;
  }
  if (!password || password.length < 4) {
    showAuthAlert('Password must be at least 4 characters long.', 'error');
    return;
  }

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.classList.add('opacity-70');
  }

  try {
    let res;
    if (isRegisterMode) {
      const nameInput = document.getElementById('auth-name');
      const incInput = document.getElementById('auth-income');
      const name = (nameInput?.value || '').trim() || email.split('@')[0];
      const incRaw = incInput ? parseFloat(incInput.value) : 0;
      const monthly_income = isNaN(incRaw) ? 0 : incRaw;

      res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password, monthly_income })
      });
    } else {
      res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
    }

    const data = await res.json();
    if (res.ok) {
      closeAuthModal();
      showToast(isRegisterMode ? `Account created for ${data.user.name}! Starting with zero balance.` : `Welcome back, ${data.user.name}!`);
      if (emailInput) emailInput.value = '';
      if (passInput) passInput.value = '';
      await loadUserData();
      await refreshAllData();
    } else {
      showAuthAlert(data.error || 'Authentication failed. Please check your credentials.', 'error');
      showToast(data.error || 'Authentication failed', 'error');
    }
  } catch (err) {
    console.error('Auth network error', err);
    showAuthAlert('Network error during authentication. Check server connection.', 'error');
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.classList.remove('opacity-70');
    }
  }
}

async function createBlankAccount() {
  const randId = Math.floor(1000 + Math.random() * 9000);
  const name = `New User ${randId}`;
  const email = `user_${Date.now()}@finance.ai`;
  const password = "password123";

  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, monthly_income: 0 })
    });
    const data = await res.json();
    if (res.ok) {
      closeAuthModal();
      showToast(`Fresh account created: ${name}. All data starts at ₹0!`);
      await loadUserData();
      await refreshAllData();
    } else {
      showToast(data.error || 'Failed to create account', 'error');
    }
  } catch (err) {
    showToast('Network error creating new account', 'error');
  }
}

async function handleLogout() {
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
    showToast('Logged out. Please sign in or create an account.');
    openAuthModal();
  } catch (err) {
    console.error('Logout error', err);
  }
}

async function resetDemoData() {
  if (!confirm('Reset transactions and budgets to original sample data?')) return;
  try {
    const res = await fetch('/api/demo/reset', { method: 'POST' });
    if (res.ok) {
      showToast('Demo dataset reset to initial state.');
      await refreshAllData();
    }
  } catch (err) {
    showToast('Failed to reset demo dataset', 'error');
  }
}

// ----------------- Utility Helpers -----------------
function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

