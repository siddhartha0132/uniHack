#!/usr/bin/env python3
"""
UniHack Product Enrichment Pipeline - Main Entry Point
Run: python run_pipeline.py [--max-rows N] [--output PATH]
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pipeline import UniHackPipeline
from ingestion.load_reference_files import load_input_csv
from evaluation.evaluate import run_evaluation, print_evaluation_report


def main():
    parser = argparse.ArgumentParser(description="UniHack Product Enrichment Pipeline")
    parser.add_argument("--max-rows", type=int, default=None, help="Max rows to process (default: all)")
    parser.add_argument("--output", type=str, default="data/processed/output.csv", help="Output CSV path")
    parser.add_argument("--eval", action="store_true", help="Run evaluation against ground truth")
    parser.add_argument("--test", action="store_true", help="Run on first 10 rows only")
    args = parser.parse_args()
    
    if args.test:
        args.max_rows = 10
        args.output = "data/processed/output_test.csv"
    
    print("="*60)
    print("UNIHACK PRODUCT ENRICHMENT PIPELINE")
    print("="*60)
    
    # Load input
    print("\n[1/4] Loading input data...")
    input_df = load_input_csv()
    print(f"   Loaded {len(input_df)} rows")
    
    # Initialize pipeline
    print("\n[2/4] Initializing pipeline...")
    pipeline = UniHackPipeline()
    
    # Process
    print(f"\n[3/4] Processing {args.max_rows or 'all'} rows...")
    results = pipeline.process_batch(input_df, max_rows=args.max_rows)
    
    # Save output
    print(f"\n[4/4] Saving output to {args.output}...")
    pipeline.save_output(results, args.output)
    
    # Evaluate if requested
    if args.eval or args.test:
        print("\nRunning evaluation...")
        eval_results = run_evaluation(args.output)
        print_evaluation_report(eval_results)
    
    print("\nDone!")


if __name__ == "__main__":
    main()