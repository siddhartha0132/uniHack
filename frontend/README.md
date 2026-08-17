# Frontend Dashboard — Veritas

## Overview

Vanilla JavaScript (ES6 modules), no build step, no framework dependencies. Communicates with backend via REST API.

## Files

```
frontend/
├── index.html      # Main HTML structure
├── styles.css      # All styling (CSS custom properties, responsive)
└── app.js          # Application logic (ES6 class-based)
```

## Architecture

```
app.js (VeritasApp class)
├── init()                    # Boot: check auth, load products
├── Auth
│   ├── login()               # POST /api/auth/login → store JWT
│   ├── register()            # POST /api/auth/register
│   └── logout()              # Clear token, reset UI
├── API Client
│   ├── apiRequest()          # Wrapper with auth header, error handling
│   └── endpoints...          # All REST calls
├── Product List
│   ├── loadProducts()        # GET /api/products → render table
│   └── renderProductRow()    # Click → loadProductDetail()
├── Product Detail
│   ├── loadProductDetail()   # GET /api/products/{id}
│   ├── renderAttributes()    # Expandable evidence cards
│   ├── renderQuality()       # Score badges, needs_review list
│   ├── renderClassification()# ETIM/ECLASS/UNSPSC codes
│   └── renderRelated()       # Family/Compatible/Replacements
├── Actions
│   ├── reviewAttribute()     # POST /api/products/{id}/review
│   ├── askQuestion()         # GET /api/products/{id}/ask
│   └── exportProduct()       # GET /api/products/{id}/export
└── Demo
    └── runDemo()             # GET /api/demo/run
```

## Key Features

### Evidence Ledger
- Each attribute shows expandable evidence cards
- Sorted lowest-confidence-first (reviewers see problems first)
- Color-coded: green=agreed, yellow=resolved_conflict, red=unresolved_conflict
- Shows source badge, location, raw snippet, agrees/disagrees indicator

### Human Review Actions
- **Approve** — accepts resolved value, boosts confidence to 95%
- **Edit** — enters corrected value, sets confidence to 98%, status=human_corrected
- **Reject** — marks rejected, confidence=0
- All actions: recompute quality score, update learned reliability, optimistic locking

### Q&A Box
- Natural language questions → alias expansion → keyword match
- Returns answer + confidence + reasoning + evidence
- Stand-in for full RAG implementation

### Export
- JSON or Akeneo CSV download
- Triggered from product detail view

## Configuration

Edit `VERITAS_API_BASE` in `app.js`:
```javascript
const VERITAS_API_BASE = 'http://localhost:8000';  // or your deployed URL
```

## Running

### Option 1: Direct file open
```bash
cd frontend
# Double-click index.html or:
open index.html  # macOS
start index.html  # Windows
```

### Option 2: Static server (recommended for CORS)
```bash
cd frontend
python -m http.server 5500
# Open http://localhost:5500
```

### Option 3: VS Code Live Server
Right-click `index.html` → "Open with Live Server"

## API Integration

All calls go through `apiRequest()` which:
1. Adds `Authorization: Bearer <token>` header
2. Handles 401 → redirect to login
3. Parses JSON, throws on non-2xx
4. Shows toast notifications for errors

## State Management

Simple in-memory state in `VeritasApp`:
```javascript
this.token = null;           // JWT
this.currentProduct = null;  // Full product record
this.products = [];          // List from GET /api/products
```

No global state library needed for this scope.

## Styling

CSS Custom Properties (in `styles.css`):
```css
:root {
  --primary: #2563eb;
  --primary-hover: #1d4ed8;
  --success: #16a34a;
  --warning: #f59e0b;
  --danger: #dc2626;
  --bg: #f8fafc;
  --card: #ffffff;
  --text: #1e293b;
  --text-muted: #64748b;
  --border: #e2e8f0;
  --radius: 8px;
  --shadow: 0 1px 3px rgba(0,0,0,0.1);
  --font: system-ui, -apple-system, sans-serif;
}
```

Responsive breakpoints:
- Mobile: < 640px
- Tablet: 640–1024px
- Desktop: > 1024px

## Extending the Frontend

### Add New Tab/Section
1. Add HTML in `index.html`
2. Add render method in `app.js`
3. Call from `loadProductDetail()`

### Add New Action Button
1. Add button in render method
2. Add handler method
3. Call `apiRequest()` with appropriate endpoint

### Custom Styling
Override CSS custom properties or add new classes in `styles.css`.

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 15+
- Edge 90+

Uses: `fetch`, `async/await`, `class`, `const/let`, `arrow functions`, `template literals`, CSS custom properties.

## Debugging

Open DevTools Console:
```javascript
// Access app instance
window.app  // VeritasApp instance

// Inspect current product
window.app.currentProduct

// Manual API call
fetch('http://localhost:8000/api/products', {
  headers: { 'Authorization': `Bearer ${window.app.token}` }
}).then(r => r.json()).then(console.log)
```

## Production Build (Optional)

If you want to bundle/minify:
```bash
# Install esbuild
npm install -g esbuild

# Bundle
esbuild app.js --bundle --outfile=app.bundle.js --minify --target=es2020

# Update index.html to use app.bundle.js
```

But not required — vanilla JS loads fast enough.

## Accessibility

- Semantic HTML5
- Focus indicators on all interactive elements
- ARIA labels on icon-only buttons
- Color contrast meets WCAG AA
- Keyboard navigable

## Performance

- No framework overhead (~15KB JS gzipped)
- Single API call per view
- Evidence lazy-rendered on expand
- Images: none (icons are inline SVG)

---

## Future Enhancements

- [ ] Virtualized product list for 10k+ SKUs
- [ ] Real-time updates via WebSocket
- [ ] Bulk review actions
- [ ] Advanced filtering/search
- [ ] Dark mode toggle
- [ ] PWA support (offline)
- [ ] Unit tests (Vitest + JSDOM)