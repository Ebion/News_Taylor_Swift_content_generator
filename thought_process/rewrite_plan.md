Refinement Agent

### 1. The "Filtered Context" Workflow

Instead of just passing the whole JSON, the agent should first **reconcile** the user's choices.

* **Step A: Intersection Logic.** The agent should only ingest "Violations" where the user has not unchecked them.
* **Step B: Priority Ranking.** User-added comments (from `user_modified_content`) must be treated as "Level 0" instructions that can override the Style DNA or the Reviewer Notes.
* **Step C: State Management.** The agent should receive the `ai_draft` as the "Base" and the filtered suggestions as "Deltas."

---

### 2. The Agent’s Internal Instructions (System Prompting)

Your agent shouldn't just "rewrite the story." It should follow a **Multi-Pass Edit** strategy to ensure it doesn't lose the facts while fixing the style:

#### **Pass 1: Structural Repair**

Address the "Headline" and "Lede" violations first. These are the most visible BBC-style markers.

* *Action:* Move the sub-clause out of the headline.
* *Action:* Inject the "Where" (Location) into the first sentence.

#### **Pass 2: Punctuation & Formatting (The "Grit")**

This is where the agent applies the "Punctuation Quirks" from your DNA.

* *Action:* Replace all `[link](url)` with plain text or attributions.
* *Action:* Regex-check for double spaces after periods if that rule was accepted.

#### **Pass 3: Tone & Vocabulary Check**

* *Action:* Scan for "Key Phrases." If the user agreed to the violation regarding "Key Phrases," the agent should look for natural places to swap generic verbs for corpus-specific ones (e.g., changing "reached a high" to "has hit its highest level").

---

### 3. Recommended Technical Implementation

If you are using LangChain, you can structure the rewrite prompt like this:

```python
REWRITE_PROMPT = """
You are a Senior BBC News Copyeditor. 
Your task is to rewrite a draft to strictly adhere to a specific "Style DNA" and "Reviewer Feedback".

BASE DRAFT: {ai_draft}

APPROVED STYLE REVISIONS:
{violations}

USER COMMENTS (MANDATORY):
{user_modified_content}

STYLE DNA CONSTRAINTS:
- Tone: {style_dna.tone}
- Punctuation: {style_dna.punctuation_quirks}

INSTRUCTIONS:
1. Apply the APPROVED STYLE REVISIONS surgically. 
2. Ensure USER COMMENTS are integrated exactly as requested.
3. Maintain the inverted-pyramid structure.
4. Output ONLY the final news story text.
"""

```

### 4. Safety/Quality Guardrail

Before returning the final text, the agent should perform a **Self-Correction** check:

* **Fact Check:** Did I accidentally change "128-qubit" to something else while rewriting?
* **Markdown Check:** Are there any leftover `[` or `]` characters?

---

### Next Step

Would you like me to help you write the **Pydantic schema** for this refined "Correction Object" so your LangChain agent can handle the user's accepted/rejected violations cleanly?