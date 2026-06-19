#!/usr/bin/env python3
"""Evaluation: compare predictions vs labeled ground truth from sample_claims.csv."""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent.parent))

def evaluate(pred_csv, gt_csv):
    pred = pd.read_csv(pred_csv)
    gt = pd.read_csv(gt_csv)
    merged = pred.merge(gt, on="user_id", suffixes=("_pred","_gt"))
    print(f"\n{'='*60}\nEVALUATION: {len(merged)} rows\n{'='*60}\n")
    fields = ["evidence_standard_met","claim_status","issue_type","object_part","valid_image","severity"]
    total_correct = 0; total_checks = 0
    for f in fields:
        pc, gc = f"{f}_pred", f"{f}_gt"
        if pc in merged.columns and gc in merged.columns:
            correct = (merged[pc].astype(str).str.strip().str.lower()==merged[gc].astype(str).str.strip().str.lower()).sum()
            acc = correct/len(merged)*100
            bar = chr(9608)*int(acc/5) + chr(9617)*(20-int(acc/5))
            print(f"  {f:<28} {correct:>2}/{len(merged)}  {bar}  {acc:.1f}%")
            total_correct += correct; total_checks += len(merged)
    if total_checks > 0: print(f"\n  {'OVERALL':<28} {total_correct:>2}/{total_checks}  -> {total_correct/total_checks*100:.1f}%")
    if "risk_flags_pred" in merged.columns:
        exact = any_overlap = 0
        for _, row in merged.iterrows():
            pf = set(f.strip() for f in str(row["risk_flags_pred"]).split(";") if f.strip()!="none")
            gf = set(f.strip() for f in str(row["risk_flags_gt"]).split(";") if f.strip()!="none")
            if pf==gf: exact+=1
            if pf&gf: any_overlap+=1
        print(f"\n  risk_flags exact:      {exact}/{len(merged)} -> {exact/len(merged)*100:.1f}%")
        print(f"  risk_flags any overlap: {any_overlap}/{len(merged)} -> {any_overlap/len(merged)*100:.1f}%")
    mismatches = merged[merged["claim_status_pred"].astype(str).str.strip().str.lower()!=merged["claim_status_gt"].astype(str).str.strip().str.lower()]
    print(f"\n{'='*60}\nMISMATCHED claim_status ({len(mismatches)}):\n{'='*60}")
    for _, row in mismatches.iterrows():
        print(f"  {row['user_id']}: pred={row['claim_status_pred']} actual={row['claim_status_gt']}")
        print(f"    obj={row.get('claim_object_gt','?')} issue={row.get('issue_type_gt','?')}")
    return merged

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--predictions", default="output.csv")
    ap.add_argument("--ground-truth", default="dataset/sample_claims.csv")
    ap.add_argument("--run-first", action="store_true")
    args = ap.parse_args()
    if args.run_first:
        from pipeline import run_pipeline
        run_pipeline(claims_csv="dataset/sample_claims.csv", user_history_csv="dataset/user_history.csv",
                     image_base_dir=".", output_csv=args.predictions)
    evaluate(args.predictions, args.ground_truth)

if __name__ == "__main__": main()
