# AGENTS.md — AI Collaboration Log

**Project:** Multi-Modal Evidence Review  
**Challenge:** HackerRank Orchestrate June 2026  
**Date:** June 19, 2026  

---

## What I Asked the AI to Do

Build an end-to-end solution that verifies damage claims (car, laptop, package) by analyzing submitted images, conversation transcripts, user claim history, and evidence requirements — then produce a structured CSV with 14 output fields per claim.

Specific requests:

- Design the architecture (single-pass VLM was the AI's recommendation, which I approved)
- Write all code: `main.py`, `pipeline.py`, `prompts.py`, `config.py`, evaluation scripts, and README
- Run the pipeline on 20 labeled sample claims and 44 unlabeled test claims
- Iterate on bugs and accuracy improvements
- Prepare submission materials and interview prep

## Key Decisions

| Decision | Rationale |
|---|---|
| **Single-pass VLM** (1 Claude call per claim) | Lower cost/latency than multi-step agents; visual perception task doesn't benefit from reasoning chains |
| **valid_image as independent gate** | An image can load fine but still fail to show the required part — these are separate checks |
| **Dynamic evidence requirements** | Loaded from CSV per-claim rather than hardcoded; ensures the right standard is checked each time |
| **7 few-shot examples** | Cover all decision types (supported/contradicted/not_enough_information) with precise image ID selection |
| **Anthropic Claude Sonnet 4.5** | Best vision quality for detailed object/damage inspection; multi-provider fallback configured |
| **Temperature 0.1** | Near-deterministic but allows minor variation to avoid getting stuck on edge cases |

## Bugs Encountered and Fixed

1. **File indentation corruption** — `pipeline.py` had 4-space indent on every line. Fixed by stripping leading whitespace.
2. **MIME type mismatch** — Many `.jpg` files are actually WebP or PNG. Claude API returned 400 errors. Fixed by detecting actual format from file header bytes.
3. **Deprecated model name** — `claude-3-5-sonnet-20241022` returned 404. Switched to `claude-sonnet-4-5-20250929` after listing available models.
4. **Dry-run ordering bug** — Dry-run mode required API keys because it checked the provider before the dry-run flag. Reordered to check dry-run first.
5. **Image path default** — Default `--images` was `.` (repo root), but images live under `dataset/`. Changed to `dataset`.
6. **Prompt tuning sensitivity** — Two attempts to improve issue_type and severity scores via prompt changes caused overall regression. Reverted to v1 prompts, which proved most stable.

## Final Results

| Field | Accuracy |
|---|---|
| claim_status | **95%** (19/20) |
| evidence_standard_met | 90% (18/20) |
| object_part | 90% (18/20) |
| valid_image | 90% (18/20) |
| risk_flags | 70% (14/20) |
| issue_type | 65% (13/20) |
| severity | 60% (12/20) |
| **OVERALL** | **82.5%** (99/120) |

- 44 full test claims processed at ~$1.50 total API cost
- ~4,500 tokens per claim (~3-5 seconds each)
- Only 1 claim_status miss across all labeled data

## Tools Used

- **AI Assistant:** Ally (AllyHub) — architecture design, code generation, debugging, pipeline execution
- **Model:** Claude Sonnet 4.5 via Anthropic API
- **Language:** Python 3.13 with pandas, Pillow, and anthropic SDK
- **Repository:** GitHub (Starboycoded/hackerrank-orchestrate-june26)
