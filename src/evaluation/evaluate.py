"""
Evaluation Module — Compare pipeline output against ground truth (Delivery Format).
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple
from rapidfuzz import fuzz
import json

PROJECT_ROOT = Path(r"C:\Users\goels\uniHack")
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
GROUND_TRUTH_DIR = PROJECT_ROOT / "data" / "ground_truth"


def load_ground_truth() -> pd.DataFrame:
    """Load ground truth delivery format."""
    path = GROUND_TRUTH_DIR / "delivery_format_2rows.csv"
    if not path.exists():
        raise FileNotFoundError(f"Ground truth not found: {path}")
    return pd.read_csv(path)


def load_pipeline_output(path: str) -> pd.DataFrame:
    """Load pipeline output CSV."""
    return pd.read_csv(path)


def compare_fields(gt_row: pd.Series, pred_row: pd.Series, field: str) -> Dict[str, Any]:
    """Compare a single field between ground truth and prediction."""
    gt_val = gt_row.get(field, "")
    pred_val = pred_row.get(field, "")
    
    # Handle NaN
    if pd.isna(gt_val):
        gt_val = ""
    if pd.isna(pred_val):
        pred_val = ""
    
    gt_str = str(gt_val).strip()
    pred_str = str(pred_val).strip()
    
    if not gt_str and not pred_str:
        return {"match": True, "score": 1.0, "gt": "", "pred": "", "note": "Both empty"}
    
    if not gt_str:
        return {"match": False, "score": 0.0, "gt": "", "pred": pred_str, "note": "GT empty"}
    
    if not pred_str:
        return {"match": False, "score": 0.0, "gt": gt_str, "pred": "", "note": "Pred empty"}
    
    # Normalize for comparison
    gt_norm = normalize_value(gt_str)
    pred_norm = normalize_value(pred_str)
    
    # Exact match after normalization
    if gt_norm == pred_norm:
        return {"match": True, "score": 1.0, "gt": gt_str, "pred": pred_str, "note": "Exact match (normalized)"}
    
    # Fuzzy match
    score = fuzz.ratio(gt_norm, pred_norm) / 100.0
    is_match = score >= 0.85
    
    return {
        "match": is_match,
        "score": score,
        "gt": gt_str,
        "pred": pred_str,
        "note": "Fuzzy match" if is_match else "Mismatch"
    }


def normalize_value(val: str) -> str:
    """Normalize value for comparison: strip units, handle numeric equivalence."""
    val = val.strip()
    if not val:
        return ""
    
    # Remove common units
    units_to_strip = [' V', ' A', ' dBA', ' in', ' ft', ' mm', ' cm', ' m', ' lb', ' kg', ' Hz', ' W', ' RPM', ' psi', ' bar', ' °F', ' °C']
    for unit in units_to_strip:
        if val.endswith(unit):
            val = val[:-len(unit)].strip()
            break
    
    # Handle numeric equivalence (5.0 == 5, 120 == 120.0)
    try:
        # Check if both are numeric
        float(val)
        # If we can parse as float, normalize to remove trailing .0
        if '.' in val:
            val = str(float(val)).rstrip('0').rstrip('.')
    except ValueError:
        pass
    
    return val.lower()


def compare_char_limit(field: str, pred_val: str, max_len: int) -> Dict[str, Any]:
    """Check if prediction respects character limit."""
    pred_str = pred_val.strip() if not pd.isna(pred_val) else ""
    return {
        "field": field,
        "length": len(pred_str),
        "limit": max_len,
        "compliant": len(pred_str) <= max_len,
        "value": pred_str[:100],
    }


def evaluate_descriptions(gt_row: pd.Series, pred_row: pd.Series) -> Dict[str, Any]:
    """Evaluate the 5 description formats."""
    desc_fields = {
        "INVOICE_DESC": 40,
        "MOBILE_DESC": 80,  # min 60, max 80
        "SHORT_DESC": 200,  # approximate
        "LONG_DESC1": 2000,  # approximate
    }
    
    results = {}
    for field, max_len in desc_fields.items():
        gt_val = gt_row.get(field, "")
        pred_val = pred_row.get(field, "")
        
        comp = compare_fields(gt_row, pred_row, field)
        limit_check = compare_char_limit(field, pred_val, max_len)
        
        results[field] = {
            "accuracy": comp,
            "char_limit": limit_check,
        }
    
    return results


def evaluate_attributes(gt_row: pd.Series, pred_row: pd.Series) -> Dict[str, Any]:
    """Evaluate attribute columns (ATTRIBUTE_LABEL/VALUE/UOM 1-23)."""
    results = {}
    matched = 0
    total_gt = 0
    total_pred = 0
    
    # Try both underscore and space formats for ground truth
    def get_gt_field(row, base, i):
        # Try space format first (ground truth), then underscore (pipeline output)
        space_key = f"{base} {i}"
        underscore_key = f"{base}_{i}"
        if space_key in row.index:
            return row.get(space_key, "")
        return row.get(underscore_key, "")
    
    for i in range(1, 24):
        label_field = f"ATTRIBUTE_LABEL_{i}"
        value_field = f"ATTRIBUTE_VALUE_{i}"
        uom_field = f"ATTRIBUTE_UOM_{i}"
        
        gt_label = str(get_gt_field(gt_row, "ATTRIBUTE_LABEL", i)).strip()
        gt_value = str(get_gt_field(gt_row, "ATTRIBUTE_VALUE", i)).strip()
        gt_uom = str(get_gt_field(gt_row, "ATTRIBUTE_UOM", i)).strip()
        
        pred_label = str(pred_row.get(label_field, "")).strip()
        pred_value = str(pred_row.get(value_field, "")).strip()
        pred_uom = str(pred_row.get(uom_field, "")).strip()
        
        if gt_label:
            total_gt += 1
            # Find matching attribute in prediction
            best_match = None
            best_score = 0
            for j in range(1, 24):
                p_label = str(pred_row.get(f"ATTRIBUTE_LABEL_{j}", "")).strip()
                if p_label:
                    score = fuzz.ratio(gt_label.lower(), p_label.lower()) / 100.0
                    if score > best_score:
                        best_score = score
                        best_match = j
            
            if best_match and best_score >= 0.8:
                p_value = str(pred_row.get(f"ATTRIBUTE_VALUE_{best_match}", "")).strip()
                p_uom = str(pred_row.get(f"ATTRIBUTE_UOM_{best_match}", "")).strip()
                
                value_match = fuzz.ratio(normalize_value(gt_value), normalize_value(p_value)) / 100.0 if gt_value and p_value else 0
                uom_match = fuzz.ratio(normalize_value(gt_uom), normalize_value(p_uom)) / 100.0 if gt_uom and p_uom else 0
                
                attr_match = value_match >= 0.8 and (not gt_uom or uom_match >= 0.8)
                if attr_match:
                    matched += 1
                
                results[gt_label] = {
                    "gt_value": gt_value,
                    "gt_uom": gt_uom,
                    "pred_label": pred_label,
                    "pred_value": p_value,
                    "pred_uom": p_uom,
                    "label_match": best_score,
                    "value_match": value_match,
                    "uom_match": uom_match,
                    "matched": attr_match,
                }
            else:
                results[gt_label] = {
                    "gt_value": gt_value,
                    "gt_uom": gt_uom,
                    "matched": False,
                    "note": "Label not found in prediction",
                }
        
        if pred_label:
            total_pred += 1
    
    precision = matched / total_pred if total_pred > 0 else 0
    recall = matched / total_gt if total_gt > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "per_attribute": results,
        "summary": {
            "matched": matched,
            "total_gt_attributes": total_gt,
            "total_pred_attributes": total_pred,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    }


def evaluate_key_fields(gt_row: pd.Series, pred_row: pd.Series) -> Dict[str, Any]:
    """Evaluate key identity fields."""
    key_fields = [
        "MANUFACTURER_NAME",
        "BRAND_NAME",
        "MANUFACTURER_PART_NUMBER",
        "Classpath",
        "Product_Name",
    ]
    
    results = {}
    for field in key_fields:
        results[field] = compare_fields(gt_row, pred_row, field)
    
    return results


def run_evaluation(pipeline_output_path: str) -> Dict[str, Any]:
    """Run full evaluation against ground truth."""
    gt_df = load_ground_truth()
    pred_df = load_pipeline_output(pipeline_output_path)
    
    # Match by Mfg_Part_Num
    gt_df = gt_df.set_index("Mfg_Part_Num")
    pred_df = pred_df.set_index("Mfg_Part_Num")
    
    all_results: Dict[str, Any] = {
        "per_item": {},
        "aggregate": {
            "descriptions": {},
            "attributes": {"matched": 0.0, "total_gt": 0.0, "total_pred": 0.0},
            "key_fields": {},
        }
    }
    
    for mpn in gt_df.index:
        if mpn not in pred_df.index:
            all_results["per_item"][mpn] = {"error": "Not in predictions"}
            continue
        
        gt_row = gt_df.loc[mpn]
        pred_row = pred_df.loc[mpn]
        
        # Handle potential multi-index
        if isinstance(gt_row, pd.DataFrame):
            gt_row = gt_row.iloc[0]
        if isinstance(pred_row, pd.DataFrame):
            pred_row = pred_row.iloc[0]
        
        item_result = {
            "key_fields": evaluate_key_fields(gt_row, pred_row),
            "descriptions": evaluate_descriptions(gt_row, pred_row),
            "attributes": evaluate_attributes(gt_row, pred_row),
        }
        
        all_results["per_item"][mpn] = item_result
        
        # Aggregate
        attr_sum = item_result["attributes"]["summary"]
        all_results["aggregate"]["attributes"]["matched"] += attr_sum["matched"]
        all_results["aggregate"]["attributes"]["total_gt"] += attr_sum["total_gt_attributes"]
        all_results["aggregate"]["attributes"]["total_pred"] += attr_sum["total_pred_attributes"]
    
    # Compute aggregate metrics
    agg: Dict[str, Any] = all_results["aggregate"]["attributes"]
    if agg["total_pred"] > 0:
        agg["precision"] = agg["matched"] / agg["total_pred"]
    if agg["total_gt"] > 0:
        agg["recall"] = agg["matched"] / agg["total_gt"]
    if agg.get("precision", 0) + agg.get("recall", 0) > 0:
        agg["f1"] = 2 * agg["precision"] * agg["recall"] / (agg["precision"] + agg["recall"])
    
    # Description aggregate
    desc_fields = ["INVOICE_DESC", "MOBILE_DESC", "SHORT_DESC", "LONG_DESC1"]
    for field in desc_fields:
        scores = []
        for item in all_results["per_item"].values():
            if isinstance(item, dict) and "descriptions" in item and isinstance(item["descriptions"], dict):
                field_eval = item["descriptions"].get(field)
                if isinstance(field_eval, dict) and "accuracy" in field_eval and isinstance(field_eval["accuracy"], dict):
                    scores.append(field_eval["accuracy"].get("score", 0.0))
        if scores:
            all_results["aggregate"]["descriptions"][field] = {
                "avg_score": sum(scores) / len(scores),
                "exact_matches": sum(1 for s in scores if s == 1.0),
                "total": len(scores),
            }
    
    return all_results


def print_evaluation_report(results: Dict[str, Any]):
    """Print human-readable evaluation report."""
    print("\n" + "="*60)
    print("EVALUATION REPORT")
    print("="*60)
    
    # Key fields
    print("\nKEY FIELDS:")
    for mpn, item in results["per_item"].items():
        if "key_fields" in item:
            print(f"  {mpn}:")
            for field, comp in item["key_fields"].items():
                status = "[OK]" if comp["match"] else "[FAIL]"
                print(f"    {status} {field}: {comp['score']:.2f} ({comp['note']})")
    
    # Descriptions
    print("\nDESCRIPTIONS:")
    for field, stats in results["aggregate"]["descriptions"].items():
        print(f"  {field}: avg={stats['avg_score']:.2f}, exact={stats['exact_matches']}/{stats['total']}")
    
    # Attributes
    agg = results["aggregate"]["attributes"]
    print(f"\nATTRIBUTES: P={agg.get('precision', 0):.2f} R={agg.get('recall', 0):.2f} F1={agg.get('f1', 0):.2f}")
    print(f"    Matched: {agg['matched']}/{agg['total_gt']} GT attrs, {agg['total_pred']} predicted")
    
    # Per-item attribute details
    for mpn, item in results["per_item"].items():
        if "attributes" in item:
            print(f"\n  {mpn} attributes:")
            for attr, detail in item["attributes"]["per_attribute"].items():
                status = "[OK]" if detail.get("matched") else "[FAIL]"
                print(f"    {status} {attr}: label={detail.get('label_match', 0):.2f} val={detail.get('value_match', 0):.2f} uom={detail.get('uom_match', 0):.2f}")


if __name__ == "__main__":
    import sys
    output_path = sys.argv[1] if len(sys.argv) > 1 else "data/processed/output_test.csv"
    
    results = run_evaluation(output_path)
    print_evaluation_report(results)
    
    # Save detailed results
    report_path = output_path.replace(".csv", "_eval.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📊 Detailed report saved to {report_path}")