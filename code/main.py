#!/usr/bin/env python3
"""Multi-Modal Evidence Review - Entry Point.
Usage: python main.py [--sample] [--dry-run] [--limit N] [--provider anthropic|openai|google]
Requires: export ANTHROPIC_API_KEY="sk-ant-..." ; pip install anthropic Pillow pandas python-dotenv"""
import argparse, sys
from config import model_config
from pipeline import run_pipeline

def main():
    p = argparse.ArgumentParser(description="Multi-Modal Evidence Review")
    p.add_argument("--sample", action="store_true", help="Process labeled sample claims")
    p.add_argument("--dry-run", action="store_true", help="Inspect prompts without API calls")
    p.add_argument("--limit", type=int, default=0, help="Process only first N claims")
    p.add_argument("--claims", type=str, help="Path to claims CSV")
    p.add_argument("--history", type=str, default="dataset/user_history.csv")
    p.add_argument("--images", type=str, default=".", help="Base dir for image paths")
    p.add_argument("--output", type=str, default="output.csv")
    p.add_argument("--provider", type=str, choices=["anthropic","openai","google"])
    args = p.parse_args()
    if args.provider: model_config.provider = args.provider
    if args.claims: claims_csv = args.claims
    elif args.sample: claims_csv = "dataset/sample_claims.csv"
    else: claims_csv = "dataset/claims.csv"
    if not args.dry_run:
        try: provider = model_config.get_provider()
        except ValueError as e:
            print(f"ERROR: {e}\nSet ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY.\nOr use --dry-run.")
            sys.exit(1)
        print(f"Provider: {provider}")
    print(f"Claims: {claims_csv}")
    run_pipeline(claims_csv=claims_csv, user_history_csv=args.history,
                 image_base_dir=args.images, output_csv=args.output,
                 dry_run=args.dry_run, limit=args.limit)

if __name__ == "__main__": main()
