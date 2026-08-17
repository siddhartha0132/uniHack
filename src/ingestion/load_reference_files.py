"""
Ingestion module for UniHack reference files.
Loads all 7 reference files into clean lookup tables (parquet).
"""

import pandas as pd
from pathlib import Path
import re
from typing import Dict, Any


# Use absolute path to project root
PROJECT_ROOT = Path(r"C:\Users\goels\uniHack")
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_manufacturer_brand_list() -> pd.DataFrame:
    """Load UniCat_Manufacturer_and_Brand_List.xlsx — 27k+ canonical names."""
    path = RAW_DIR / "UniCat_Manufacturer_and_Brand_List.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}. Download from UniHack portal.")
    df = pd.read_excel(path)
    # Expected columns: MANUFACTURER_NAME, MANUFACTURER_CODE, BRAND_NAME, BRAND_CODE
    df.columns = [c.strip().upper() for c in df.columns]
    return df


def load_lov() -> pd.DataFrame:
    """Load Unicat_Lov_v1_0_Updated_With_Remarks.xlsx — 161k LOV rows."""
    path = RAW_DIR / "Unicat_Lov_v1_0_Updated_With_Remarks.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}. Download from UniHack portal.")
    df = pd.read_excel(path)
    df.columns = [c.strip() for c in df.columns]
    return df


def load_uom_standards() -> pd.DataFrame:
    """Load Unilog_Master_UOM_Standards_Abbreviations_and_Terms.xlsx — 500 UOM."""
    path = RAW_DIR / "Unilog_Master_UOM_Standards_Abbreviations_and_Terms.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}. Download from UniHack portal.")
    # Sheet 1: UOM abbreviations, Sheet 2: 22 house-style rules
    xl = pd.ExcelFile(path)
    uom_df = pd.read_excel(xl, sheet_name=0)
    rules_df = pd.read_excel(xl, sheet_name=1) if len(xl.sheet_names) > 1 else pd.DataFrame()
    uom_df.columns = [c.strip() for c in uom_df.columns]
    return uom_df


def load_decimal_fraction() -> pd.DataFrame:
    """Load Decimal_Fraction.xlsx — 63 inch conversions (4 column blocks)."""
    path = RAW_DIR / "Decimal_Fraction.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}. Download from UniHack portal.")
    df = pd.read_excel(path, header=None)
    # Parse 4 side-by-side Fraction|Decimal blocks
    pairs = []
    for block_start in [0, 2, 4, 6]:
        if block_start + 1 < df.shape[1]:
            frac_col = df.iloc[:, block_start]
            dec_col = df.iloc[:, block_start + 1]
            for f, d in zip(frac_col, dec_col):
                if pd.notna(f) and pd.notna(d):
                    pairs.append({"fraction": str(f).strip(), "decimal": float(d)})
    return pd.DataFrame(pairs).drop_duplicates()


def load_faucets_lov() -> Dict[str, pd.DataFrame]:
    """Load FAUCETS_LOV.xlsx — 4 sheets: Summary, Online Description, Attribute Detail, Visual Guide."""
    path = RAW_DIR / "FAUCETS_LOV.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}. Download from UniHack portal.")
    xl = pd.ExcelFile(path)
    sheets: Dict[str, pd.DataFrame] = {}
    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)
        df.columns = [c.strip() for c in df.columns]
        sheets[str(sheet)] = df
    return sheets


def load_fittings_lov() -> Dict[str, pd.DataFrame]:
    """Load Fittings_LOV.xlsx — Fitting Types, Connection Types, Materials mappings."""
    path = RAW_DIR / "Fittings_LOV.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}. Download from UniHack portal.")
    xl = pd.ExcelFile(path)
    sheets: Dict[str, pd.DataFrame] = {}
    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)
        df.columns = [c.strip() for c in df.columns]
        sheets[str(sheet)] = df
    return sheets


def load_content_guidelines() -> str:
    """Load UNILOG_INTERNAL_CONTENT_GUIDELINES.docx — description formulas, char limits."""
    path = RAW_DIR / "UNILOG_INTERNAL_CONTENT_GUIDELINES.docx"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}. Download from UniHack portal.")
    try:
        import docx
        doc = docx.Document(str(path))
        return "\n".join([p.text for p in doc.paragraphs])
    except ImportError:
        raise ImportError("python-docx required: pip install python-docx")


def load_input_csv() -> pd.DataFrame:
    """Load 1000-item input CSV."""
    path = RAW_DIR / "input_1000.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}")
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    # Clean placeholder values
    placeholder_cols = ["E1_Brand", "Unilog_Brand", "DIB_Brand"]
    for col in placeholder_cols:
        if col in df.columns:
            df[col] = df[col].replace(["-- Unbranded --", "-- No Unilog Brand --", "-- No DIB Brand --"], None)
    return df


def load_ground_truth() -> pd.DataFrame:
    """Load 2-row delivery format ground truth."""
    path = PROJECT_ROOT / "data" / "ground_truth" / "delivery_format_2rows.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing: {path}")
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df


def save_processed(name: str, df: pd.DataFrame) -> None:
    """Save DataFrame as parquet for fast loading."""
    path = PROCESSED_DIR / f"{name}.parquet"
    df.to_parquet(path, index=False)
    print(f"Saved {len(df)} rows to {path}")


def main():
    """Load all reference files and save as processed parquet."""
    print("Loading reference files...")
    
    # Load input data first (always available)
    input_df = load_input_csv()
    save_processed("input_1000", input_df)
    first_words = input_df['Part_Desc'].str.extract(r'^(\w+)').value_counts().head()
    print(f"Input: {len(input_df)} rows, categories: {first_words.to_dict()}")
    
    # Load ground truth
    gt_df = load_ground_truth()
    save_processed("ground_truth_2rows", gt_df)
    print(f"Ground truth: {len(gt_df)} rows")
    
    # Try loading reference files (will fail if not downloaded)
    ref_files = [
        ("manufacturer_brand", load_manufacturer_brand_list),
        ("lov", load_lov),
        ("uom_standards", load_uom_standards),
        ("decimal_fraction", load_decimal_fraction),
        ("faucets_lov", load_faucets_lov),
        ("fittings_lov", load_fittings_lov),
    ]
    
    for name, loader in ref_files:
        try:
            result = loader()
            if isinstance(result, dict):
                for k, v in result.items():
                    save_processed(f"{name}_{k}", v)
            else:
                save_processed(name, result)
            print(f"Loaded {name}")
        except FileNotFoundError as e:
            print(f"SKIP {name}: {e}")
        except Exception as e:
            print(f"ERROR {name}: {e}")
    
    # Content guidelines (text)
    try:
        guidelines = load_content_guidelines()
        (PROCESSED_DIR / "content_guidelines.txt").write_text(guidelines)
        print("Loaded content_guidelines")
    except Exception as e:
        print(f"SKIP content_guidelines: {e}")
    
    print("\nDone. Place missing files in data/raw/ and re-run.")


if __name__ == "__main__":
    main()