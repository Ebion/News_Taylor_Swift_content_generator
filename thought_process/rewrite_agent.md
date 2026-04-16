# Rewrite Agent Plan

## Overview
The Rewrite Agent applies user modifications and style fixes to rewrite the AI draft.

## Input
- `suggested_changes_bbc.json` or `suggested_changes_taylor_swift.json`
- User has filled in `user_modified_content` with their edits

## Process

### Pass 1: Load Data
- Load the JSON with user's modifications
- Get `ai_draft`, `user_modified_content`, `reviewer_notes`, `style_dna`

### Pass 2: Multi-Pass Rewrite
- **Structure Fix:** Headline/lead violations first
- **Punctuation Fix:** Remove Markdown links, fix spacing
- **Tone/Key Phrases:** Apply remaining changes

### Pass 3: Safety Guardrail
- Fact check: Ensure no data changed (e.g., "128-qubit" preserved)
- Markdown check: Ensure no leftover `[` or `]` characters

## Output
```json
{
  "run_id": "...",
  "original_draft": "...",
  "user_modifications": "...",
  "rewritten_content": "...",
  "fact_check_passed": true,
  "markdown_check_passed": true
}
```

## Implementation
1. `utils/rewrite_models.py` - Pydantic models
2. `notebooks/rewrite_agent_test.ipynb` - Rewrite agent

## Rewrite Prompt
```
You are a Senior Copy Editor. Your task is to rewrite the draft based on user modifications and reviewer feedback.

BASE DRAFT:
{ai_draft}

USER MODIFICATIONS (MANDATORY):
{user_modified_content}

REVIEWER FEEDBACK:
{reviewer_notes}

STYLE DNA:
{style_dna}

INSTRUCTIONS:
1. Apply USER MODIFICATIONS exactly as requested
2. Address the REVIEWER FEEDBACK violations
3. Maintain the original facts (e.g., numbers, names, dates)
4. Follow the STYLE DNA constraints

OUTPUT:
