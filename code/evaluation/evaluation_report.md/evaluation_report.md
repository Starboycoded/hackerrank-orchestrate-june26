# Evaluation Report — Multi-Modal Evidence Review

## Setup
- **Model**: Claude 3.5 Sonnet (primary), GPT-4o / Gemini 2.5 Flash (alternatives)
- **Strategy**: Single-pass VLM with structured JSON output + 7 few-shot examples
- **Temperature**: 0.1 (deterministic, reproducible)

## Strategy Comparison

| Strategy | Calls/Claim | Accuracy | Cost/Claim | Latency |
|----------|-------------|----------|------------|---------|
| **A: Single-pass VLM** (chosen) | 1 | High | ~\$0.011 | 4-8s |
| B: Multi-step (parse + per-image + synthesize) | 2-4 | Marginally higher | ~\$0.030 | 12-20s |
| C: Text-only (no vision) | 1 | Low | ~\$0.003 | 2s |

Strategy A chosen for best balance of accuracy, cost, and simplicity.

## Operational Analysis — Full Test Set (40 claims)

### API Usage
- Model calls: ~40-50 (one per claim + potential retries for JSON parse failures)
- Input tokens: ~60,000-100,000 (text prompts + image encoding)
- Output tokens: ~15,000-25,000 (JSON responses)
- Images processed: ~75 images across 40 claims

### Cost (Claude 3.5 Sonnet)
- Input: \$3.00 / 1M tokens → ~\$0.24
- Output: \$15.00 / 1M tokens → ~\$0.30
- **Total per run**: ~\$0.54

### Runtime
- Sequential: ~5-7 minutes (40 claims × 7-10s each)
- Could parallelize to ~1-2 minutes with concurrent API calls

### Rate Limits
- Anthropic Tier 1: 50 RPM / 20,000 TPM — no issues at this scale

## Key Design Decisions

1. **valid_image gate**: Assessed first and independently from evidence_standard_met
2. **Verbatim evidence requirements**: All 11 rows preserved with requirement IDs, dynamically matched per claim
3. **Per-family matching**: Claims matched to specific requirement by object + issue family
4. **manual_review_required triggers**: 4 explicit conditions
5. **Consistency enforcement**: valid_image=false forces evidence_standard_met=false
6. **Claim/visible separation**: claim_summary + visible_findings fields prevent reasoning drift

## Few-shot Examples Included

7 examples from sample_claims.csv covering:
- Clear support (dent on bumper)
- Claim mismatch (minor scratch vs claimed severe damage)
- Not enough information (wrong part shown)
- Wrong object + manipulation
- Text instruction in image
- Missing contents + invalid image
- Blurry image with one clear supporting image

## Fields Evaluated

| Field | Type | Notes |
|-------|------|-------|
| evidence_standard_met | boolean | Per-requirement matching |
| claim_status | categorical | supported / contradicted / not_enough_information |
| issue_type | categorical | 12 allowed values |
| object_part | categorical | Per-object allowed lists |
| valid_image | boolean | Independent gate |
| severity | categorical | 5 levels |
| risk_flags | multi-label | 14 flags with overlap scoring |
| supporting_image_ids | multi-value | Surgical precision required |
