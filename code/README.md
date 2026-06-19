# Multi-Modal Evidence Review - Solution

    ## Quick Start
    ```bash
    # Windows CMD:
    set ANTHROPIC_API_KEY=sk-ant-...
    pip install anthropic Pillow pandas python-dotenv
    python code/main.py --sample --dry-run --limit 3   # Inspect prompts first
    python code/main.py --sample                        # Run on 20 labeled claims
    python code/evaluation/main.py --predictions output.csv  # Check accuracy
    python code/main.py                                 # Run on full 40-claim test set
    ```

    ## Provider Options
    - Claude (default): set ANTHROPIC_API_KEY=...
    - GPT-4o: python code/main.py --provider openai
    - Gemini: python code/main.py --provider google

    ## Files
    | File | Purpose |
    |------|---------|
    | main.py | Entry point with --sample, --dry-run, --limit flags |
    | config.py | API keys from environment, defaults to Anthropic |
    | prompts.py | Dynamic evidence requirements, claim/visible separation, few-shot examples |
    | pipeline.py | Load -> analyze (Claude Vision) -> output CSV with dry-run mode |
    | evaluation/main.py | Field-by-field accuracy against ground truth |

    ## Approach
    Single-pass VLM: one Claude call per claim with all context (images, conversation, user history, dynamic evidence requirements, few-shot examples). Dry-run mode for inspecting prompts before spending API credits.
    