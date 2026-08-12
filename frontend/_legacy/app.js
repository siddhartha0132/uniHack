const API_BASE = window.VERITAS_API_BASE || "http://127.0.0.1:8000";

const el = (sel) => document.querySelector(sel);
const productList = el("#product-list");
const detailPanel = el("#detail-panel");
const apiStatus = el("#api-status");
const runDemoBtn = el("#run-demo-btn");

let currentProductId = null;

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

async function loadProducts() {
  const res = await fetch(`${API_BASE}/api/products`);
  const products = await res.json();

  if (products.length === 0) {
    productList.innerHTML = `<li class="empty-state">No products yet — run the demo pipeline.</li>`;
    return;
  }

  productList.innerHTML = products.map(p => `
    <li class="product-item ${p.product_id === currentProductId ? 'active' : ''}" data-id="${p.product_id}">
      <span class="p-name">${p.product_name}</span>
      <span class="p-meta">
        <span>score ${p.overall_score}</span>
        <span>${p.needs_review} to review</span>
      </span>
    </li>
  `).join("");

  productList.querySelectorAll(".product-item").forEach(node => {
    node.addEventListener("click", () => loadProductDetail(node.dataset.id));
  });
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
  return `${v}${unit}`;
}

function renderAttributeRow(name, attr) {
  const confPct = Math.round(attr.confidence * 100);
  const color = confColor(attr.confidence);

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
        <span class="attr-value">${formatValue(attr)}</span>
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
          <button class="btn btn-small" data-action="reject" data-attr="${name}">Reject</button>
        </div>
      </div>
    </div>
  `;
}

async function loadProductDetail(productId) {
  currentProductId = productId;
  const res = await fetch(`${API_BASE}/api/products/${productId}`);
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
      await fetch(`${API_BASE}/api/products/${product.product_id}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ attribute, action }),
      });
      loadProductDetail(product.product_id);
    });
  });

  el("#ask-btn").addEventListener("click", async () => {
    const q = el("#ask-input").value.trim();
    if (!q) return;
    const res = await fetch(`${API_BASE}/api/products/${product.product_id}/ask?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    el("#ask-answer").innerHTML = `
      <p><strong>${data.answer}</strong> ${data.confidence !== undefined ? `(${Math.round(data.confidence * 100)}% confidence)` : ""}</p>
      <p class="muted">${data.reasoning || ""}</p>
    `;
  });
}

runDemoBtn.addEventListener("click", async () => {
  runDemoBtn.textContent = "Running…";
  runDemoBtn.disabled = true;
  const res = await fetch(`${API_BASE}/api/demo/run`);
  const product = await res.json();
  runDemoBtn.textContent = "Run demo pipeline";
  runDemoBtn.disabled = false;
  await loadProducts();
  loadProductDetail(product.product_id);
});

(async function init() {
  const ok = await checkApi();
  if (ok) loadProducts();
})();
