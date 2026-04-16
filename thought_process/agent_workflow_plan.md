## Step 1: Characterization Agent (The "Style Extractor")

Before writing, the AI must "study" the dataset. Since you are using a BBC and a Taylor Swift dataset, this agent's job is to create a **Style Guide** for each.

* **Input:** 10–20 sample rows from each dataset.
* **Prompting Technique:** **"Few-Shot Extraction."** You ask the LLM to identify specific linguistic patterns.
* **What it extracts:**
* **BBC:** Structural rules (e.g., "The Inverted Pyramid"—most important info first), tone (impartial, formal), and specific grammar (use of "said" instead of descriptive verbs).
* **Taylor Swift:** Use of lowercase, "Easter eggs" (hidden meanings), emotional keywords, and fan-centric language (e.g., calling them "Swifties" or mentioning "Eras").



---

## Step 2: Generation Agent (The "Writer")

This agent takes the **User's Topic** (e.g., "A new cat café opening") and the **Style Guide** from Step 1 to produce the content.

* **Prompting Technique:** **"Persona-Based Prompting"** + **"Constraint Satisfaction."**
* **The Workflow:**
1. **For BBC:** It writes a headline + a lead paragraph answering the 5 W’s (Who, What, When, Where, Why).
2. **For Taylor Swift:** It writes a short, punchy tweet using her specific "voice" (e.g., breathless excitement or lyrical metaphors).


* **Key Instruction:** "Write the BBC article first, then summarize the same news into a Taylor Swift-style tweet."

---

## Step 3: Review & QA Agent (The "Critic")

This is the "Agentic" part. Instead of just giving you the first draft, the system checks its own work.

* **The Logic:**
* **Check 1 (Length):** Is the tweet under 280 characters?
* **Check 2 (Style Check):** Did the BBC article use "I" or "Me"? (If yes, rewrite it to be objective). Did the Taylor Swift tweet sound too formal? (If yes, add emojis or lowercase it).


* **Final Output:** The refined, QA-approved version.

---

## Summary Table for your Assignment Documentation

If you need to present this in a diagram or table, use this structure:

| Agent | Task | Key Strategy |
| --- | --- | --- |
| **The Analyst** | Extract Style DNA | **Pattern Recognition**: Identify sentence length, tone, and vocabulary. |
| **The Writer** | Draft Content | **Few-Shot Prompting**: Use 3 examples of real text to guide the new draft. |
| **The Editor** | QA & Refinement | **Self-Correction**: Check against constraints (word count, brand voice). |

---

### Pro-Tip for your Prompt Engineering:

When writing the prompt for the "Taylor Swift" agent, tell the AI: *"Use lowercase for aesthetic effect and reference a 'glitch' or an 'era' if the topic allows."* This shows the instructor you’ve actually analyzed the nuances of her specific Twitter (X) presence.