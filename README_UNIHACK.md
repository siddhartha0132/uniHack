# UniHack Product Enrichment Pipeline

AI-powered product intelligence pipeline for industrial commerce — UniHack 2024 submission.

## Overview

Transforms messy distributor catalog rows (1,000 items) into structured, commerce-ready product records matching Unilog's 252-column Delivery Format.

**Input:** `Part_Desc` (e.g., `"49-94-0013 Milw 5\"x.045\"x7/8\" Metal Cut Off Disc"`)
**Output:** 252 standardized fields — manufacturer/brand normalization, LOV-constrained attributes, UOM standards, decimal→fraction conversion, 5 description formats

## Architecture

```
Input CSV (1000 rows)
       │
       ▼
┌──────────────────┐
│ Manufacturer/    │  ← Fuzzy match against 27k UniCat list
│ Brand Resolver   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Classpath        │  ← Keyword/ML classification to UniCat LOV classpath
│ Classifier       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ LOV-Constrained  │  ← Regex extraction → LOV validation → UOM/fraction normalize
│ Attribute Extract│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Description      │  ← Jinja2 templates for 5 UniHack formats
│ Generator        │
└────────┬─────────┘
         │
         ▼
Delivery Format CSV (252 columns)
```

## Key Features

| Feature | Implementation |
|---------|----------------|
| **Manufacturer/Brand Resolution** | RapidFuzz WRatio against 27k approved list (with ®/™/Inc/LLC handling) |
| **LOV Compliance** | All attribute values validated against UniCat `Normalized Values` |
| **UOM Standards** | 500 approved abbreviations, enforced spacing (`24 in` not `24in`) |
| **Decimal→Fraction** | 64th-inch conversion (`50.25` → `50-1/4`) |
| **5 Description Formats** | Invoice (≤40 caps), Mobile (60-80), Title, Short, Long — Jinja2 templates |
| **Category Specialization** | Dishwashers, Abrasives — extensible per-category templates |
| **Traceability** | Per-field confidence scores, extraction method, LOV validation status |

## Quick Start

```bash
# 1. Install Python 3.11+ and dependencies
pip install -r requirements.txt

# 2. Download 7 reference files from UniHack portal to data/raw/:
#    - Reference_Documents_Summary.xlsx
#    - UniCat_Manufacturer_and_Brand_List.xlsx
#    - Unicat_Lov_v1_0_Updated_With_Remarks.xlsx
#    - Unilog_Master_UOM_Standards_Abbreviations_and_Terms.xlsx
#    - Decimal_Fraction.xlsx
#    - UNILOG_INTERNAL_CONTENT_GUIDELINES.docx
#    - FAUCETS_LOV.xlsx (or Fittings_LOV.xlsx)

# 3. Ingest reference files
python src/ingestion/load_reference_files.py

# 4. Run pipeline (test on 10 rows)
python run_pipeline.py --test --eval

# 5. Run full pipeline
python run_pipeline.py --max-rows 1000 --eval
```

## Output

- `data/processed/output.csv` — 252-column Delivery Format
- `data/processed/output_meta.json` — Per-row confidence metadata
- `data/processed/output_eval.json` — Detailed evaluation vs ground truth

## Evaluation Metrics

| Metric | Target |
|--------|--------|
| Invoice Desc ≤40 chars | 100% compliant |
| Mobile Desc 60-80 chars | 100% compliant |
| Manufacturer exact match | >90% |
| Brand exact match | >85% |
| Attribute value LOV match | >95% |
| Attribute F1 (vs GT) | >0.80 |

## Project Structure

```
unihack/
├── data/
│   ├── raw/              # 7 reference files + input CSVs (gitignored)
│   ├── processed/        # Parquet lookups + outputs
│   └── ground_truth/     # 2-row Delivery Format sample
├── src/
│   ├── ingestion/        # Reference file loaders
│   ├── normalization/    # Mfr/brand, UOM, decimal→fraction
│   ├── classification/   # Classpath classifier
│   ├── extraction/       # LOV-constrained attribute extraction
│   ├── generation/       # 5-format description templates
│   ├── evaluation/       # Ground truth comparison
│   └── pipeline.py       # Main orchestrator
├── templates/            # Jinja2 description templates (per category)
├── run_pipeline.py       # CLI entry point
└── requirements.txt
```

## Extending Categories

1. Add category-specific templates to `templates/{category}_{format}.j2`
2. Register in `src/generation/description_generator.py` → `CATEGORY_TEMPLATES`
3. Add extraction patterns in `pipeline.py` → `_extract_{category}_attrs()`

## License

UniHack 2024 Competition Submission