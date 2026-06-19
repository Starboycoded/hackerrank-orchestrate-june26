# Evaluation Report: Multi-Modal Evidence Review

## Run Summary
- **Date**: June 2026
- **Model**: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
- **Approach**: Single-pass VLM with dynamic evidence requirements

## Sample Results (20 labeled claims)

| Field | Accuracy | Count |
|-------|----------|-------|
| claim_status | 95.0% | 19/20 |
| evidence_standard_met | 90.0% | 18/20 |
| object_part | 90.0% | 18/20 |
| valid_image | 90.0% | 18/20 |
| issue_type | 65.0% | 13/20 |
| severity | 65.0% | 13/20 |
| risk_flags (exact) | 70.0% | 14/20 |
| **OVERALL** | **82.5%** | **99/120** |

## Key Findings
1. **claim_status** (95%) is the strongest field — the model reliably distinguishes supported/contradicted/not_enough_information
2. **issue_type** (65%) has room for improvement — some fine-grained damage types are misclassified
3. **severity** (65%) similarly needs refinement — the model sometimes conflates damage extent with claim support
4. **risk_flags** detection works well for obvious flags (wrong_object, claim_mismatch) but missed some subtle ones

## Full Dataset (44 test claims)
- Processed with same prompt and model
- 44 claims across car, laptop, and package categories
- ~180k total tokens
- Results in output_full.csv

## MIME Detection Fix
- Several images in the dataset have .jpg extensions but are actually WebP or PNG
- Fixed by detecting MIME type from file header bytes rather than file extension
