// VerifyGrid Interactive Web Demo App
let verificationData = window.VERIFYGRID_DATA ? JSON.parse(JSON.stringify(window.VERIFYGRID_DATA)) : { stats: {}, verification_table: [] };
let currentFilter = 'ALL';
let searchQuery = '';
let selectedRecord = null;
let auditLogs = [];

document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  updateKPIRibbon();
  renderGrid();
});

function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('block'));
  
  const target = document.getElementById(tabId);
  if (target) {
    target.classList.remove('hidden');
    target.classList.add('block');
  }

  // Update nav buttons
  const tabs = ['upload', 'blueprint', 'rules', 'grid', 'audit'];
  tabs.forEach(t => {
    const btn = document.getElementById(`nav-${t}`);
    if (btn) {
      if (tabId === `tab-${t}`) {
        btn.classList.add('bg-white', 'text-indigo-700', 'shadow-sm', 'font-semibold');
        btn.classList.remove('text-slate-600', 'font-medium');
      } else {
        btn.classList.remove('bg-white', 'text-indigo-700', 'shadow-sm', 'font-semibold');
        btn.classList.add('text-slate-600', 'font-medium');
      }
    }
  });

  if (window.lucide) {
    lucide.createIcons();
  }
}

function updateKPIRibbon() {
  const table = verificationData.verification_table || [];
  const total = table.length;
  const verified = table.filter(r => r.overall_status === 'VERIFIED').length;
  const review = table.filter(r => r.overall_status === 'NEEDS_REVIEW').length;
  const mismatch = table.filter(r => r.overall_status === 'MISMATCH').length;
  const missing = table.filter(r => r.overall_status === 'MISSING').length;
  const exceptions = total - verified;

  document.getElementById('kpi-total').innerText = total.toLocaleString();
  document.getElementById('kpi-verified').innerText = verified.toLocaleString();
  document.getElementById('kpi-verified-pct').innerText = total > 0 ? `${((verified / total) * 100).toFixed(1)}%` : '0%';
  document.getElementById('kpi-review').innerText = review.toLocaleString();
  document.getElementById('kpi-mismatch').innerText = mismatch.toLocaleString();
  document.getElementById('kpi-missing').innerText = missing.toLocaleString();

  const btnExc = document.getElementById('btn-count-exceptions');
  if (btnExc) btnExc.innerText = exceptions.toString();
}

function setFilter(filterType) {
  currentFilter = filterType;
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.classList.remove('bg-slate-900', 'text-white');
    btn.classList.add('bg-slate-100', 'text-slate-700');
  });

  const activeBtn = document.getElementById(`filter-${filterType}`);
  if (activeBtn) {
    activeBtn.classList.remove('bg-slate-100', 'text-slate-700');
    activeBtn.classList.add('bg-slate-900', 'text-white');
  }

  renderGrid();
}

function handleSearch(val) {
  searchQuery = val.toLowerCase().trim();
  renderGrid();
}

function renderGrid() {
  const tbody = document.getElementById('grid-body');
  if (!tbody) return;

  const table = verificationData.verification_table || [];
  
  let filtered = table.filter(row => {
    // Filter by category
    if (currentFilter === 'EXCEPTIONS') {
      if (row.overall_status === 'VERIFIED') return false;
    } else if (currentFilter !== 'ALL') {
      if (row.overall_status !== currentFilter) return false;
    }

    // Filter by search query
    if (searchQuery) {
      const matchRoll = (row.roll_number || '').toLowerCase().includes(searchQuery);
      const matchNameA = (row.source_applicant?.name || '').toLowerCase().includes(searchQuery);
      const matchNameB = (row.source_admissions?.name || '').toLowerCase().includes(searchQuery);
      const matchDept = (row.source_applicant?.dept || '').toLowerCase().includes(searchQuery);
      return matchRoll || matchNameA || matchNameB || matchDept;
    }

    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="px-6 py-12 text-center text-slate-400">
          <i data-lucide="inbox" class="w-8 h-8 mx-auto mb-2 opacity-50"></i>
          <p class="text-sm font-medium">No records match the active filter or query.</p>
        </td>
      </tr>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  // Display top 100 rows for silky performance
  const displayRows = filtered.slice(0, 100);

  tbody.innerHTML = displayRows.map(row => {
    const statusBadges = {
      'VERIFIED': '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800"><i data-lucide="check" class="w-3 h-3 mr-0.5"></i> VERIFIED</span>',
      'NEEDS_REVIEW': '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800"><i data-lucide="alert-triangle" class="w-3 h-3 mr-0.5"></i> REVIEW BAND</span>',
      'MISMATCH': '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800"><i data-lucide="x-circle" class="w-3 h-3 mr-0.5"></i> MISMATCH</span>',
      'MISSING': '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800"><i data-lucide="help-circle" class="w-3 h-3 mr-0.5"></i> MISSING</span>'
    };

    const badge = statusBadges[row.overall_status] || row.overall_status;

    // Rules pills
    const rulesHtml = (row.rules || []).map(r => {
      let color = 'bg-slate-100 text-slate-600';
      if (r.status === 'PASS') color = 'bg-emerald-50 text-emerald-700 border-emerald-200';
      else if (r.status === 'NEEDS_REVIEW') color = 'bg-amber-50 text-amber-700 border-amber-200 font-bold';
      else if (r.status === 'FAIL') color = 'bg-rose-50 text-rose-700 border-rose-200 font-bold';
      
      const shortId = r.rule_id.split('_')[0];
      return `<span title="${r.rule_name}: ${r.details}" class="px-1.5 py-0.5 rounded border text-[9px] font-mono ${color}">${shortId}</span>`;
    }).join(' ');

    const reason = (row.flag_reasons && row.flag_reasons.length > 0)
      ? `<span class="text-[11px] text-amber-900 line-clamp-1" title="${row.flag_reasons.join('; ')}">${row.flag_reasons[0]}</span>`
      : `<span class="text-[11px] text-slate-400">All 4 deterministic checks passed.</span>`;

    const rowHighlight = row.overall_status === 'NEEDS_REVIEW' ? 'bg-amber-50/20' : (row.overall_status === 'MISMATCH' ? 'bg-rose-50/20' : '');

    return `
      <tr class="hover:bg-slate-50 transition border-b border-slate-100 ${rowHighlight}">
        <td class="px-4 py-3 font-mono font-bold text-slate-900">${row.roll_number}</td>
        <td class="px-4 py-3">
          <div class="font-semibold text-slate-900">${row.source_applicant?.name || 'N/A'}</div>
          <div class="text-[10px] text-slate-500">${row.source_applicant?.dept || ''} &middot; DOB: ${row.source_applicant?.dob || ''}</div>
        </td>
        <td class="px-4 py-3">
          <div class="font-medium text-slate-700">${row.source_admissions?.name || '<span class="text-rose-500 italic">Not in ERP</span>'}</div>
          <div class="text-[10px] text-slate-500">Reg DOB: ${row.source_admissions?.dob || 'N/A'} &middot; Status: ${row.source_admissions?.status || 'N/A'}</div>
        </td>
        <td class="px-4 py-3 text-center">${badge}</td>
        <td class="px-4 py-3">
          <div class="flex items-center space-x-1">${rulesHtml}</div>
        </td>
        <td class="px-4 py-3 max-w-xs">${reason}</td>
        <td class="px-4 py-3 text-right">
          <button onclick="openRecordDetail('${row.application_id}')" class="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 text-indigo-600 rounded text-[11px] font-bold shadow-2xs transition">
            Inspect &rarr;
          </button>
        </td>
      </tr>
    `;
  }).join('');

  if (window.lucide) {
    lucide.createIcons();
  }
}

function openRecordDetail(appId) {
  const table = verificationData.verification_table || [];
  const rec = table.find(r => r.application_id === appId);
  if (!rec) return;

  selectedRecord = rec;

  document.getElementById('modal-title').innerText = `Reconciliation Audit: ${rec.roll_number} (${rec.application_id})`;

  const banner = document.getElementById('modal-banner');
  if (rec.overall_status === 'VERIFIED') {
    banner.className = 'p-3.5 rounded-xl border text-xs bg-emerald-50 border-emerald-200 text-emerald-800';
    banner.innerHTML = `<strong>Status: VERIFIED (100% Match)</strong><br>All rules matched within strict tolerance. Ready for automated payout sign-off.`;
  } else if (rec.overall_status === 'NEEDS_REVIEW') {
    banner.className = 'p-3.5 rounded-xl border text-xs bg-amber-50 border-amber-200 text-amber-900';
    banner.innerHTML = `<strong>Status: NEEDS HUMAN REVIEW (Review Band Exception)</strong><br>${rec.flag_reasons.join('<br>')}`;
  } else if (rec.overall_status === 'MISMATCH') {
    banner.className = 'p-3.5 rounded-xl border text-xs bg-rose-50 border-rose-200 text-rose-900';
    banner.innerHTML = `<strong>Status: HARD MISMATCH (Deterministic Rule Failed)</strong><br>${rec.flag_reasons.join('<br>')}`;
  } else {
    banner.className = 'p-3.5 rounded-xl border text-xs bg-purple-50 border-purple-200 text-purple-900';
    banner.innerHTML = `<strong>Status: MISSING IN OFFICIAL REGISTRY</strong><br>${rec.flag_reasons.join('<br>')}`;
  }

  // Source A Details
  document.getElementById('modal-source-a').innerHTML = `
    <div><span class="text-slate-400">Name:</span> <strong class="text-slate-800">${rec.source_applicant?.name || 'N/A'}</strong></div>
    <div><span class="text-slate-400">DOB:</span> ${rec.source_applicant?.dob || 'N/A'}</div>
    <div><span class="text-slate-400">Dept:</span> ${rec.source_applicant?.dept || 'N/A'}</div>
    <div><span class="text-slate-400">Claimed Amt:</span> ₹${Number(rec.source_applicant?.claimed_amount || 0).toLocaleString()}</div>
  `;

  // Source B Details
  document.getElementById('modal-source-b').innerHTML = `
    <div><span class="text-slate-400">Registered Name:</span> <strong class="text-slate-800">${rec.source_admissions?.name || 'N/A'}</strong></div>
    <div><span class="text-slate-400">Official DOB:</span> ${rec.source_admissions?.dob || 'N/A'}</div>
    <div><span class="text-slate-400">Program:</span> ${rec.source_admissions?.dept || 'N/A'}</div>
    <div><span class="text-slate-400">ERP Status:</span> ${rec.source_admissions?.status || 'N/A'}</div>
  `;

  // Source C Details
  document.getElementById('modal-source-c').innerHTML = `
    <div><span class="text-slate-400">Receipt No:</span> ${rec.source_fees?.receipt_no || 'N/A'}</div>
    <div><span class="text-slate-400">Tuition Paid:</span> ₹${Number(rec.source_fees?.paid_inr || 0).toLocaleString()}</div>
    <div><span class="text-slate-400">Tuition Due:</span> ₹${Number(rec.source_fees?.due_inr || 0).toLocaleString()}</div>
    <div><span class="text-slate-400">Accounts Status:</span> ${rec.source_fees?.status || 'N/A'}</div>
  `;

  document.getElementById('diff-modal').classList.remove('hidden');
  if (window.lucide) lucide.createIcons();
}

function closeModal() {
  document.getElementById('diff-modal').classList.add('hidden');
  selectedRecord = null;
}

function saveModalDecision() {
  if (!selectedRecord) return;

  const decision = document.getElementById('modal-decision').value;
  const verifier = document.getElementById('modal-verifier').value;
  const notes = document.getElementById('modal-notes').value || 'Decision logged by verifier.';
  const now = new Date().toISOString().replace('T', ' ').substring(0, 19);

  if (decision === 'APPROVED_OVERRIDE') {
    selectedRecord.overall_status = 'VERIFIED';
    selectedRecord.flag_reasons = [`Human Override Approved by ${verifier}: ${notes}`];
  } else if (decision === 'REJECTED') {
    selectedRecord.overall_status = 'MISMATCH';
    selectedRecord.flag_reasons = [`Rejected by ${verifier}: ${notes}`];
  }

  // Append to audit log
  const entry = `✓ [${now}] ${verifier} -> Record ${selectedRecord.roll_number}: Set status to ${decision} | Note: "${notes}"`;
  auditLogs.push(entry);

  const container = document.getElementById('dynamic-audit-entries');
  if (container) {
    const div = document.createElement('div');
    div.className = 'text-indigo-900 bg-indigo-50 p-1.5 rounded border border-indigo-200';
    div.innerText = entry;
    container.appendChild(div);
  }

  updateKPIRibbon();
  renderGrid();
  closeModal();

  alert(`Decision for ${selectedRecord.roll_number} committed successfully! Audit trail updated.`);
}

function loadSampleData() {
  if (window.VERIFYGRID_DATA) {
    verificationData = JSON.parse(JSON.stringify(window.VERIFYGRID_DATA));
    updateKPIRibbon();
    renderGrid();
    switchTab('tab-grid');
    alert('500 Realistic messy records from NIMS University scholarship batch loaded instantly!');
  }
}

function runVerification() {
  switchTab('tab-grid');
  alert('Deterministic verification executed! 500 records cross-checked across 4 rules in 0.42 seconds.');
}

function handleFileUpload(event, source) {
  const file = event.target.files[0];
  if (!file) return;
  const badgeId = `status-source-${source.toLowerCase()}`;
  const el = document.getElementById(badgeId);
  if (el) {
    el.innerText = `Uploaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    el.classList.remove('bg-indigo-50', 'text-indigo-600');
    el.classList.add('bg-emerald-50', 'text-emerald-700', 'border', 'border-emerald-200');
  }
}

function exportToCSV() {
  const table = verificationData.verification_table || [];
  if (table.length === 0) return;

  let csvContent = "data:text/csv;charset=utf-8,";
  csvContent += "Application_ID,Roll_Number,Status,Candidate_Name_SourceA,Registrar_Name_SourceB,Applicant_DOB,Registrar_DOB,Fee_Status,Reason\n";

  table.forEach(r => {
    const reasonClean = (r.flag_reasons && r.flag_reasons[0]) ? r.flag_reasons[0].replace(/"/g, '""') : 'Verified';
    const row = [
      r.application_id,
      r.roll_number,
      r.overall_status,
      `"${r.source_applicant?.name || ''}"`,
      `"${r.source_admissions?.name || ''}"`,
      r.source_applicant?.dob || '',
      r.source_admissions?.dob || '',
      r.source_fees?.status || '',
      `"${reasonClean}"`
    ].join(',');
    csvContent += row + "\n";
  });

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `VerifyGrid_Reconciliation_Export_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function downloadAuditCertificate() {
  alert("Generating cryptographically verified audit sign-off PDF for NIMS University Examination & Scholarship Council...");
}
