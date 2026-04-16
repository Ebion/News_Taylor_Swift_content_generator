# Review Agent Plan

## Overview
The Review Agent evaluates AI-generated content against the Style DNA and outputs structured review notes for human editing.

## JSON Output Structure

```json
{
  "run_id": "TS-Album-Launch-001",
  "ai_draft": "...",
  "style_dna": "{...}",
  "reviewer_notes": {
    "overall_fidelity_score": 6,
    "violations": [
      {
        "aspect": "Tone",
        "issue": "The opening is too formal...",
        "suggestion": "Use 'enchanted' to match..."
      }
    ],
    "critique_summary": "The draft is factually correct but sounds generic..."
  },
  "user_modified_content": "",
  "status": "AWAITING_HUMAN_EDIT"
}
```

## Key Components

### 1. Pydantic Models (utils/review_models.py)
- `StyleViolation` - aspect, issue, suggestion
- `ReviewOutput` - overall_fidelity_score, violations (list), critique_summary

### 2. Separate Prompts for BBC and Taylor Swift

**BBC Reviewer Prompt:**
```
You are a Professional BBC Copy Editor.

OBJECTIVE:
Cross-reference the [DRAFT] against the provided [BBC STYLE DNA].

INSTRUCTIONS:
1. Check 'Tone' - Should be neutral, factual, impartial
2. Check 'Structure' - Should use Inverted Pyramid (most important first), headline + lead paragraph
3. Check 'Punctuation' - Headlines use "Verb + Object + Colon" pattern, proper quotation marks
4. Check 'Vocabulary' - Plain-language journalism, accessible register
5. Check 'Key Phrases' - Look for: "has hit", "Quarterly profits", "said", "on Friday"

OUTPUT:
- overall_fidelity_score (1-10)
- violations (aspect, issue, suggestion)
- critique_summary
```

**Taylor Swift Reviewer Prompt:**
```
You are a Professional Copy Editor for Taylor Swift's PR team.

OBJECTIVE:
Cross-reference the [DRAFT] against the provided [TAYLOR SWIFT STYLE DNA].

INSTRUCTIONS:
1. Check 'Tone' - Should be conversational, intimate, first-person, emotional
2. Check 'Structure' - Short fragments, rhetorical questions, line breaks for pacing
3. Check 'Punctuation' - Lowercase for aesthetic, emojis, repeated punctuation (!!!)
4. Check 'Formatting' - Multi-line tweets, parenthesized dates, @mentions
5. Check 'Key Phrases' - Look for: "Pre-order now", "Meet me at midnight", "I AM IN SHAMBLES"

OUTPUT:
- overall_fidelity_score (1-10)
- violations (aspect, issue, suggestion)
- critique_summary
```

### 3. Implementation
- Use `llm.with_structured_output(ReviewOutput)` for structured output
- `run_id` comes from environment variable
- Save to `artifact/suggested_changes.json`
