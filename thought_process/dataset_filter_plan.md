## 1. The Pre-Processing Step (The "Data Sieve")

Instead of feeding the whole file to the AI, use a script (like Python/Pandas) to clean and sample the data.

* **Filter for Quality:** Remove retweets, very short tweets (under 5 words), or news articles that are just "Headline + Link."
* **Stratified Sampling:** Randomly pick **20–30 high-quality rows** from each dataset. This is usually enough for an LLM to "get" the vibe without getting overwhelmed.
* **Concatenation:** Join these 30 rows into a single text block separated by "---".

---

## 2. The Batch "Style Extractor" Prompt

Once you have your 30-row sample, you send it to your first agent. This is where you use **Batch Prompting**.

**The Prompt Structure:**

> "I am providing you with 30 sample texts from [BBC/Taylor Swift]. Your goal is to act as a **Linguistic Pattern Analyst**.
> 1. Analyze these samples for **common vocabulary** (e.g., words used 3+ times).
> 2. Identify the **average sentence structure** (short/punchy vs. long/complex).
> 3. List the **top 5 punctuation or formatting quirks** (e.g., use of '...' or all-lowercase).
> **Output:** A concise 'Style Cheat Sheet' to be used for future writing."
> 
> 

---

## 3. Creating a "Golden Reference" (Optional but Smart)

If you want to impress your instructor, don't just pick random rows. Use **Clustering**:

* Identify 3 "types" of Taylor Swift tweets (e.g., *Album Promo*, *Personal Reflection*, *Fan Interaction*).
* Pick 2 examples of each.
* Feed this "Diverse Sample" to the Style Extractor. This ensures the AI understands her *range*, not just one specific mood.

---

## The Workflow in a Nutshell

| Data Source | Action | Output |
| --- | --- | --- |
| **Raw CSV** | Filter & Sample (20-30 rows) | **Clean Sample Set** |
| **Clean Sample Set** | Send to Analyst Agent | **Style DNA (JSON/Markdown)** |
| **Style DNA + User Input** | Send to Writer Agent | **Final News/Tweet** |

---

### Why this works:

1. **Efficiency:** You aren't wasting tokens on 5,000 rows of repetitive data.
2. **Accuracy:** By pre-filtering for "good" examples, you prevent the AI from mimicking typos or irrelevant data points.
3. **Scalability:** If the dataset grows to 1 million rows, your "sample 30" logic still works perfectly.