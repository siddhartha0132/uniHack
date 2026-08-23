const API_BASE = window.VERITAS_API_BASE || "http://127.0.0.1:8000";

const el = (sel) => document.querySelector(sel);

function escapeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
const productList = el("#product-list");
const detailPanel = el("#detail-panel");
const apiStatus = el("#api-status");
const runDemoBtn = el("#run-demo-btn");

let currentProductId = null;
let authToken = localStorage.getItem("veritas_token") || null;

function authHeaders() {
  return authToken ? { "Authorization": `Bearer ${authToken}`, "Content-Type": "application/json" } : { "Content-Type": "application/json" };
}

async function checkApi() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (res.ok) {
      apiStatus.textContent = "API connected";
      apiStatus.className = "api-status ok";
      return true;
    }
    throw new Error("bad status");
  } catch (e) {
    apiStatus.textContent = "API not reachable — start the backend (see README)";
    apiStatus.className = "api-status err";
    return false;
  }
}

async function login(username, password) {
  console.log("login() called with:", username);
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);
  
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData.toString()
  });
  
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Login failed");
  }
  
  const data = await res.json();
  authToken = data.access_token;
  localStorage.setItem("veritas_token", authToken);
  console.log("login() succeeded, token stored");
  return true;
}

function showLoginForm() {
  console.log("showLoginForm called, detailPanel:", detailPanel);
  
  // Hide top action buttons when not logged in
  const topUploadBtn = el("#upload-btn");
  const topRunDemoBtn = el("#run-demo-btn");
  if (topUploadBtn) topUploadBtn.style.display = "none";
  if (topRunDemoBtn) topRunDemoBtn.style.display = "none";

  // Clear sidebar controls when logged out
  const sidebarHeader = el(".sidebar-head");
  if (sidebarHeader) {
    sidebarHeader.innerHTML = `
      <h2>Products</h2>
      <span class="hint">Processed through the arbitration engine</span>
    `;
  }
  if (productList) {
    productList.innerHTML = `<li class="empty-state">Please sign in.</li>`;
  }

  detailPanel.innerHTML = `
    <p class="eyebrow">01 — authentication required</p>
    <h1>Sign in to Veritas</h1>
    <p class="muted">Any username creates a new tenant. Use <b>demo</b>/<b>demo</b> for the demo tenant.</p>
    <form id="login-form" style="max-width: 360px; margin: 32px auto; padding: 24px; border: 2px solid var(--accent-verified); border-radius: 8px; background: var(--panel);">
      <div style="margin-bottom: 20px;">
        <label style="display:block; margin-bottom: 8px; font-size: 14px; color: var(--text-secondary); font-weight: 600;">Username</label>
        <input name="username" type="text" value="demo" required style="width:100%; padding: 14px 16px; background: var(--bg); border: 2px solid var(--border); border-radius: 6px; color: var(--text-primary); font-family: var(--font-body); font-size: 16px; box-sizing: border-box;" />
      </div>
      <div style="margin-bottom: 24px;">
        <label style="display:block; margin-bottom: 8px; font-size: 14px; color: var(--text-secondary); font-weight: 600;">Password</label>
        <input name="password" type="password" value="demo" required style="width:100%; padding: 14px 16px; background: var(--bg); border: 2px solid var(--border); border-radius: 6px; color: var(--text-primary); font-family: var(--font-body); font-size: 16px; box-sizing: border-box;" />
      </div>
      <button type="submit" class="btn btn-primary" style="width:100%; padding: 14px; font-size: 16px; font-weight: 700;">Sign in</button>
      <p id="login-error" class="err" style="margin-top:16px; color: var(--accent-conflict); font-weight: 600; text-align: center; display:none;"></p>
    </form>
  `;
  console.log("Login form HTML set, form element:", el("#login-form"));
  
  el("#login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    console.log("Login form submitted");
    const form = e.target;
    const username = form.username.value;
    const password = form.password.value;
    const errorEl = el("#login-error");
    errorEl.style.display = "none";
    
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.textContent = "Signing in…";
    submitBtn.disabled = true;
    
    try {
      console.log("Calling login...");
      await login(username, password);
      console.log("Login succeeded, loading workspace...");
      errorEl.style.display = "none";
      detailPanel.innerHTML = `
        <div class="empty-detail">
          <p class="eyebrow">01 — loading workspace</p>
          <h1>Loading Veritas…</h1>
        </div>
      `;
      await initApp();
    } catch (err) {
      console.error("Login failed:", err);
      errorEl.textContent = err.message;
      errorEl.style.display = "block";
      submitBtn.textContent = "Sign in";
      submitBtn.disabled = false;
    }
  });
}

async function loadProducts() {
  // Show top action buttons when authenticated
  const topUploadBtn = el("#upload-btn");
  const topRunDemoBtn = el("#run-demo-btn");
  if (topUploadBtn) topUploadBtn.style.display = "";
  if (topRunDemoBtn) topRunDemoBtn.style.display = "";

  // Sidebar header with controls (only when authenticated)
  const sidebarHeader = el(".sidebar-head");
  if (sidebarHeader) {
    sidebarHeader.innerHTML = `
      <h2>Products</h2>
      <span class="hint">Processed through the arbitration engine</span>
      <div class="sidebar-controls">
        <button class="btn btn-small btn-secondary" id="logout-btn">Logout</button>
        <button class="btn btn-small btn-danger" id="clear-data-btn">Clear All Data</button>
      </div>
    `;
    const logoutBtn = el("#logout-btn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("veritas_token");
        authToken = null;
        currentProductId = null;
        showLoginForm();
      });
    }
    const clearBtn = el("#clear-data-btn");
    if (clearBtn) {
      clearBtn.addEventListener("click", async () => {
        if (!confirm("Delete ALL products for this tenant? This cannot be undone.")) return;
        try {
          const res = await fetch(`${API_BASE}/api/products/clear`, {
            method: "DELETE",
            headers: authHeaders()
          });
          if (res.ok) {
            currentProductId = null;
            loadProducts();
            detailPanel.innerHTML = `<div class="empty-detail"><p class="eyebrow">01 — select a record</p><h1>No product selected</h1><p class="muted">Run the demo pipeline or upload sources to begin.</p></div>`;
          } else {
            alert("Failed to clear data");
          }
        } catch (e) {
          alert("Error: " + e.message);
        }
      });
    }
  }

  const res = await fetch(`${API_BASE}/api/products`, { headers: authHeaders() });
  
  if (res.status === 401) {
    localStorage.removeItem("veritas_token");
    authToken = null;
    showLoginForm();
    return;
  }
  
  const products = await res.json();

  if (products.length === 0) {
    productList.innerHTML = `<li class="empty-state">No products yet — run the demo pipeline.</li>`;
    if (!currentProductId) {
      detailPanel.innerHTML = `
        <div class="empty-detail">
          <p class="eyebrow">01 — no product selected</p>
          <h1>Select a product, or run the sample pipeline</h1>
          <p class="muted">The demo dataset is one Siemens PLC SKU pulled from three genuinely disagreeing sources — a technical datasheet, a manufacturer product page, and a distributor's legacy ERP export. Watch the arbitration engine resolve it with evidence.</p>
        </div>
      `;
    }
    return;
  }

  productList.innerHTML = products.map(p => `
    <li class="product-item ${p.product_id === currentProductId ? 'active' : ''}" data-id="${p.product_id}">
      <span class="p-name">${escapeHtml(p.product_name)}</span>
      <span class="p-meta">
        <span>score ${p.overall_score}</span>
        <span>${p.needs_review} to review</span>
      </span>
    </li>
  `).join("");

  productList.querySelectorAll(".product-item").forEach(node => {
    node.addEventListener("click", () => loadProductDetail(node.dataset.id));
  });

  // If no product is currently active, automatically open the first one
  if (!currentProductId && products.length > 0) {
    loadProductDetail(products[0].product_id);
  }
}

function confColor(conf) {
  if (conf >= 0.85) return "var(--accent-verified)";
  if (conf >= 0.6) return "var(--accent-review)";
  return "var(--accent-conflict)";
}

function formatValue(attr) {
  const v = attr.resolved_value;
  const unit = attr.unit ? ` ${attr.unit}` : "";
  if (Array.isArray(v)) return `${v[0]} – ${v[1]}${unit}`;
  const strV = String(v);
  if (unit && strV.endsWith(attr.unit)) {
    return strV;
  }
  return `${v}${unit}`;
}

function renderAttributeRow(name, attr) {
  const confPct = Math.round(attr.confidence * 100);
  const color = confColor(attr.confidence);
  const rawVal = Array.isArray(attr.resolved_value) ? attr.resolved_value.join(" – ") : (attr.resolved_value ?? "");

  const evidenceHtml = attr.evidence.map(ev => `
    <div class="evidence-item">
      <div class="ev-head">
        <span>${ev.source_type} · ${ev.location}</span>
        <span class="${ev.agrees_with_resolution ? 'agree' : 'disagree'}">
          ${ev.agrees_with_resolution ? '✓ agrees' : '✗ disagrees'} — ${Array.isArray(ev.value) ? ev.value.join('–') : ev.value}${ev.unit ? ' ' + ev.unit : ''}
        </span>
      </div>
      <div class="ev-snippet">"${ev.raw_snippet}"</div>
    </div>
  `).join("");

  return `
    <div class="attr-row status-${attr.status}" data-attr="${name}">
      <div class="attr-summary">
        <span class="attr-name">${name.replace(/_/g, " ")}</span>
        <span class="attr-value" data-raw-val="${escapeHtml(rawVal)}">${formatValue(attr)}</span>
        <span class="attr-confidence">
          ${confPct}%
          <div class="conf-bar"><div class="conf-bar-fill" style="width:${confPct}%; background:${color};"></div></div>
        </span>
        <span class="attr-status-badge status-${attr.status}">${attr.status.replace(/_/g, " ")}</span>
      </div>
      <div class="attr-detail">
        <p class="reasoning">${attr.reasoning}</p>
        ${evidenceHtml}
        <div class="review-actions">
          <button class="btn btn-small" data-action="approve" data-attr="${name}">Approve</button>
          <button class="btn btn-small" data-action="edit" data-attr="${name}">Edit</button>
          <button class="btn btn-small" data-action="reject" data-attr="${name}">Reject</button>
        </div>
      </div>
    </div>
  `;
}

async function loadProductDetail(productId) {
  currentProductId = productId;
  const res = await fetch(`${API_BASE}/api/products/${productId}`, { headers: authHeaders() });
  
  if (res.status === 401) {
    localStorage.removeItem("veritas_token");
    authToken = null;
    showLoginForm();
    return;
  }
  
  const product = await res.json();
  renderDetail(product);
  loadProducts(); // refresh active state in sidebar
}

function renderDetail(product) {
  const q = product.quality;
  const cls = product.classification;
  const related = product.related;

  const attrRows = Object.entries(product.attributes)
    .sort((a, b) => a[1].confidence - b[1].confidence) // lowest confidence first — needs attention first
    .map(([name, attr]) => renderAttributeRow(name, attr))
    .join("");

  detailPanel.innerHTML = `
    <p class="eyebrow">Product record — ${product.product_id}</p>
    <h1>${product.product_name}</h1>

    <div class="score-header">
      <div class="score-ring">${q.overall_score}<span class="unit">/100</span></div>
      <div class="score-stats">
        <div class="score-stat"><b>${q.completeness}%</b>complete</div>
        <div class="score-stat"><b>${q.avg_confidence}%</b>avg. confidence</div>
        <div class="score-stat"><b>${q.conflicts_detected}</b>conflicts resolved</div>
        <div class="score-stat"><b>${q.needs_review.length}</b>need review</div>
      </div>
      <div class="score-explanation">${q.explanation}</div>
    </div>

    <div class="ledger-head">
      <h2>Evidence ledger</h2>
      <span class="hint">click a row to see sources · lowest confidence first</span>
    </div>
    <div id="attr-rows">${attrRows}</div>

    <div class="meta-grid">
      <div class="meta-card">
        <h3>Classification</h3>
        ${cls ? `
          <p class="code">ETIM ${cls.etim_class} — ${cls.etim_class_name}</p>
          <p class="code">ECLASS ${cls.eclass_code} — ${cls.eclass_name}</p>
          <p class="code">UNSPSC ${cls.unspsc}</p>
        ` : `<p class="muted">No classification match for this product category yet.</p>`}
      </div>
      <div class="meta-card">
        <h3>Related products (graph)</h3>
        <ul>
          ${related.replacement_products.length ? related.replacement_products.map(r => `<li>Replacement: ${r.name}</li>`).join("") : ""}
          ${related.related_family_members.map(r => `<li>Family: ${r.name}</li>`).join("")}
          ${related.compatible_accessories.map(r => `<li>Compatible: ${r.name}</li>`).join("")}
        </ul>
      </div>
    </div>

    <div class="ask-box">
      <h3>Ask about this product</h3>
      <div class="ask-row">
        <input id="ask-input" type="text" placeholder="e.g. what is the operating temperature range?" />
        <button class="btn btn-primary btn-small" id="ask-btn">Ask</button>
      </div>
      <div id="ask-answer"></div>
    </div>

    <div class="export-box">
      <h3>Export</h3>
      <div class="export-row">
        <button class="btn btn-secondary btn-small" id="export-json">Download JSON</button>
        <button class="btn btn-secondary btn-small" id="export-csv">Download CSV</button>
      </div>
      <div id="export-status" class="muted" style="margin-top: 8px;"></div>
    </div>
  `;

  // toggle evidence detail
  document.querySelectorAll(".attr-row").forEach(row => {
    row.querySelector(".attr-summary").addEventListener("click", () => {
      row.querySelector(".attr-detail").classList.toggle("open");
    });
  });

  // review actions
  document.querySelectorAll("[data-action]").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const attribute = btn.dataset.attr;
      const action = btn.dataset.action;
      
      if (action === "edit") {
        const detailEl = btn.closest(".attr-detail");
        if (!detailEl) {
          console.error("Could not find .attr-detail parent");
          return;
        }
        
        // Find value element - try multiple selectors
        let valueEl = detailEl.querySelector(".attr-value");
        if (!valueEl) {
          // Fallback: find the span with the value in the summary
          valueEl = detailEl.closest(".attr-row").querySelector(".attr-value");
        }
        if (!valueEl) {
          console.error("Could not find .attr-value element", detailEl);
          return;
        }
        
        const currentValue = valueEl.dataset.rawVal !== undefined ? valueEl.dataset.rawVal : valueEl.textContent.trim();
        
        // Replace value with inline editor
        valueEl.innerHTML = `
          <input type="text" class="edit-input" value="${escapeHtml(currentValue)}" 
                 style="width:140px; padding:4px 8px; background:var(--bg); border:1px solid var(--accent-verified); border-radius:3px; color:var(--text-primary); font-family:var(--font-mono); font-size:12px;">
          <button class="btn btn-small save-edit" style="margin-left:8px;">Save</button>
          <button class="btn btn-small cancel-edit" style="margin-left:4px;">Cancel</button>
        `;
        
        const inputEl = valueEl.querySelector(".edit-input");
        inputEl.focus();
        inputEl.select();
        
        // Save handler
        const save = async () => {
          const corrected = inputEl.value;
          inputEl.disabled = true;
          const saveBtn = valueEl.querySelector(".save-edit");
          if (saveBtn) {
            saveBtn.textContent = "Saving…";
            saveBtn.disabled = true;
          }
          
          await fetch(`${API_BASE}/api/products/${product.product_id}/review`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ attribute, action: "edit", corrected_value: corrected }),
          });
          loadProductDetail(product.product_id);
        };
        
        // Cancel handler
        const cancel = () => loadProductDetail(product.product_id);
        
        // Event listeners
        const saveBtn = valueEl.querySelector(".save-edit");
        const cancelBtn = valueEl.querySelector(".cancel-edit");
        if (saveBtn) saveBtn.addEventListener("click", save);
        if (cancelBtn) cancelBtn.addEventListener("click", cancel);
        
        // Keyboard: Enter = save, Escape = cancel
        inputEl.addEventListener("keydown", (e) => {
          if (e.key === "Enter") { e.preventDefault(); save(); }
          if (e.key === "Escape") { e.preventDefault(); cancel(); }
        });
        
        return;
      }
      
      // Approve/Reject
      await fetch(`${API_BASE}/api/products/${product.product_id}/review`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ attribute, action }),
      });
      loadProductDetail(product.product_id);
    });
  });

  el("#ask-btn").addEventListener("click", async () => {
    const q = el("#ask-input").value.trim();
    if (!q) return;
    const res = await fetch(`${API_BASE}/api/products/${product.product_id}/ask?q=${encodeURIComponent(q)}`, { headers: authHeaders() });
    const data = await res.json();
    el("#ask-answer").innerHTML = `
      <p><strong>${data.answer}</strong> ${data.confidence !== undefined ? `(${Math.round(data.confidence * 100)}% confidence)` : ""}</p>
      <p class="muted">${data.reasoning || ""}</p>
    `;
  });

  // export buttons
  el("#export-json").addEventListener("click", async () => {
    el("#export-status").textContent = "Downloading JSON...";
    const res = await fetch(`${API_BASE}/api/products/${product.product_id}/export?format=json`, { headers: authHeaders() });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${product.product_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
    el("#export-status").textContent = "JSON downloaded";
  });

  el("#export-csv").addEventListener("click", async () => {
    el("#export-status").textContent = "Downloading CSV...";
    const res = await fetch(`${API_BASE}/api/products/${product.product_id}/export?format=akeneo_csv`, { headers: authHeaders() });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${product.product_id}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    el("#export-status").textContent = "CSV downloaded";
  });
}

runDemoBtn.addEventListener("click", async () => {
  runDemoBtn.textContent = "Running…";
  runDemoBtn.disabled = true;
  const res = await fetch(`${API_BASE}/api/demo/run`, { headers: authHeaders() });
  
  if (res.status === 401) {
    localStorage.removeItem("veritas_token");
    authToken = null;
    showLoginForm();
    runDemoBtn.textContent = "Run demo pipeline";
    runDemoBtn.disabled = false;
    return;
  }
  
  const product = await res.json();
  runDemoBtn.textContent = "Run demo pipeline";
  runDemoBtn.disabled = false;
  await loadProducts();
  loadProductDetail(product.product_id);
});

// ─── Upload Modal Logic ──────────────────────────────────────────────
const uploadBtn = el("#upload-btn");
const uploadModal = el("#upload-modal");
const closeUploadModal = el("#close-upload-modal");
const cancelUpload = el("#cancel-upload");
const addFileRowBtn = el("#add-file-row");
const loadDemoFilesBtn = el("#load-demo-files");
const processUploadBtn = el("#process-upload");
const fileRowsContainer = el("#file-rows");
const uploadProgress = el("#upload-progress");
const uploadProductName = el("#upload-product-name");
const uploadProductId = el("#upload-product-id");

let fileRowCounter = 0;

function openUploadModal() {
  uploadModal.classList.add("open");
  resetUploadForm();
}

function closeUploadModalFn() {
  uploadModal.classList.remove("open");
}

function resetUploadForm() {
  uploadProductName.value = "";
  uploadProductId.value = "";
  fileRowsContainer.innerHTML = "";
  fileRowCounter = 0;
  uploadProgress.style.display = "none";
  uploadProgress.innerHTML = "";
  processUploadBtn.disabled = true;
}

function addFileRow(sourceId, sourceType, file = null) {
  fileRowCounter++;
  const id = sourceId || `upload_${fileRowCounter}`;
  const type = sourceType || "datasheet";
  
  const row = document.createElement("div");
  row.className = "upload-row";
  row.innerHTML = `
    <input type="file" accept=".pdf,.txt,.csv,.jpg,.jpeg,.png" ${file ? "" : "required"} />
    <select class="source-type-select">
      <option value="datasheet" ${type === "datasheet" ? "selected" : ""}>Datasheet</option>
      <option value="manufacturer_website" ${type === "manufacturer_website" ? "selected" : ""}>Manufacturer Website</option>
      <option value="distributor_erp" ${type === "distributor_erp" ? "selected" : ""}>Distributor ERP</option>
      <option value="catalog_pdf" ${type === "catalog_pdf" ? "selected" : ""}>Catalog PDF</option>
      <option value="image_label" ${type === "image_label" ? "selected" : ""}>Image/Nameplate</option>
    </select>
    <span class="source-id">${id}</span>
    <button type="button" class="btn btn-small btn-danger" onclick="removeFileRow(this)">✕</button>
  `;
  
  const fileInput = row.querySelector("input[type=file]");
  if (file) {
    // Create a DataTransfer to set the file on the input
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;
  }
  
  fileInput.addEventListener("change", () => updateProcessButtonState());
  row.querySelector("select").addEventListener("change", () => updateProcessButtonState());
  
  fileRowsContainer.appendChild(row);
  updateProcessButtonState();
}

function removeFileRow(btn) {
  btn.closest(".upload-row").remove();
  updateProcessButtonState();
}

function updateProcessButtonState() {
  const rows = fileRowsContainer.querySelectorAll(".upload-row");
  let hasFiles = false;
  rows.forEach(row => {
    const input = row.querySelector("input[type=file]");
    if (input.files && input.files.length > 0) hasFiles = true;
  });
  processUploadBtn.disabled = rows.length === 0 || !hasFiles;
}

async function loadDemoFiles() {
  loadDemoFilesBtn.textContent = "Loading…";
  loadDemoFilesBtn.disabled = true;
  
  const demoFiles = [
    { name: "source_a_datasheet.txt", type: "datasheet" },
    { name: "source_b_website.txt", type: "manufacturer_website" },
    { name: "source_c_distributor_erp.csv", type: "distributor_erp" },
  ];
  
  fileRowsContainer.innerHTML = "";
  fileRowCounter = 0;
  
  for (let i = 0; i < demoFiles.length; i++) {
    try {
      const res = await fetch(`${API_BASE}/api/demo/files/${demoFiles[i].name}`);
      if (res.ok) {
        const blob = await res.blob();
        const file = new File([blob], demoFiles[i].name, { type: blob.type });
        addFileRow(`upload_${i+1}`, demoFiles[i].type, file);
      }
    } catch (err) {
      console.error("Failed to load demo file:", demoFiles[i].name, err);
    }
  }
  
  uploadProductName.value = "SIMATIC S7-1200 CPU 1214C";
  uploadProductId.value = "6ES7214-1AG40-0XB0";
  updateProcessButtonState();
  
  loadDemoFilesBtn.textContent = "Use Demo Data";
  loadDemoFilesBtn.disabled = false;
}

function showUploadProgress(steps) {
  uploadProgress.style.display = "block";
  uploadProgress.innerHTML = steps.map((step, i) => `
    <div class="progress-step ${i === 0 ? "active" : ""}" data-step="${i}">
      ${step}
    </div>
  `).join("");
}

function updateProgressStep(stepIndex) {
  const steps = uploadProgress.querySelectorAll(".progress-step");
  steps.forEach((step, i) => {
    step.classList.remove("active");
    step.classList.remove("done");
    if (i < stepIndex) step.classList.add("done");
    else if (i === stepIndex) step.classList.add("active");
  });
}

async function handleUpload() {
  const productName = uploadProductName.value.trim();
  const productId = uploadProductId.value.trim();
  
  if (!productName || !productId) {
    alert("Please enter product name and SKU");
    return;
  }
  
  const rows = fileRowsContainer.querySelectorAll(".upload-row");
  const files = [];
  const sourceIds = [];
  const sourceTypes = [];
  
  rows.forEach((row, i) => {
    const input = row.querySelector("input[type=file]");
    const select = row.querySelector("select");
    const sourceIdEl = row.querySelector(".source-id");
    
    if (input.files && input.files[0]) {
      files.push(input.files[0]);
      sourceIds.push(sourceIdEl.textContent);
      sourceTypes.push(select.value);
    }
  });
  
  if (files.length === 0) {
    alert("Please add at least one file");
    return;
  }
  
  processUploadBtn.disabled = true;
  processUploadBtn.textContent = "Processing…";
  
  showUploadProgress([
    "Uploading files…",
    "Extracting content…",
    "Running arbitration…",
    "Complete"
  ]);
  
  const formData = new FormData();
  formData.append("product_name", productName);
  formData.append("product_id", productId);
  sourceIds.forEach(id => formData.append("source_ids", id));
  sourceTypes.forEach(t => formData.append("source_types", t));
  files.forEach(f => formData.append("files", f));
  
  try {
    updateProgressStep(1);
    const res = await fetch(`${API_BASE}/api/ingest/upload`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${authToken}` },
      body: formData
    });
    
    updateProgressStep(2);
    
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Upload failed");
    }
    
    updateProgressStep(3);
    const product = await res.json();
    
    closeUploadModalFn();
    await loadProducts();
    loadProductDetail(product.product_id);
    
  } catch (err) {
    console.error("Upload failed:", err);
    uploadProgress.innerHTML = `<div class="progress-step" style="color: var(--accent-conflict);">Error: ${err.message}</div>`;
    processUploadBtn.disabled = false;
    processUploadBtn.textContent = "Process";
  }
}

// Event listeners for upload modal
uploadBtn.addEventListener("click", openUploadModal);
closeUploadModal.addEventListener("click", closeUploadModalFn);
cancelUpload.addEventListener("click", closeUploadModalFn);
addFileRowBtn.addEventListener("click", () => addFileRow());
loadDemoFilesBtn.addEventListener("click", loadDemoFiles);
processUploadBtn.addEventListener("click", handleUpload);

// Close modal on overlay click
uploadModal.addEventListener("click", (e) => {
  if (e.target === uploadModal) closeUploadModalFn();
});

// Close modal on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && uploadModal.classList.contains("open")) {
    closeUploadModalFn();
  }
});

// Make removeFileRow globally accessible for inline onclick
window.removeFileRow = removeFileRow;

async function initApp() {
  console.log("initApp called");
  const ok = await checkApi();
  console.log("checkApi result:", ok);
  if (ok) {
    console.log("authToken:", authToken);
    if (authToken) {
      // Verify token still works
      const res = await fetch(`${API_BASE}/api/products`, { headers: authHeaders() });
      if (res.status === 401) {
        localStorage.removeItem("veritas_token");
        authToken = null;
        showLoginForm();
      } else {
        loadProducts();
      }
    } else {
      showLoginForm();
    }
  }
}

console.log("App.js loaded, starting init...");
(async function init() {
  console.log("Init called");
  await initApp();
  console.log("Init complete");
})();