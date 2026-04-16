### Phase 1: Data Strategy (The "Data Sieve")

You cannot feed an entire CSV to an LLM. Industry standard is to provide **diverse high-signal samples**.

1. **For BBC:** Group by the `category` column and pick 3 samples from each (Business, Tech, etc.). This ensures the agent learns "Journalism" generally, not just "Business talk."
2. **For Taylor Swift:** Sort by `likeCount` or `retweetCount` and pick the top 20. High-engagement tweets usually represent the "purest" version of her public voice.

---

### Phase 2: Python Notebook Implementation

In your notebook, use the following logic to prepare your data for the Characterization Agent.

```python
import pandas as pd

def prepare_style_samples(bbc_path, ts_path):
    # Load Datasets
    bbc_df = pd.read_csv(bbc_path)
    ts_df = pd.read_csv(ts_path)

    # 1. BBC Sampling: Get 2 samples from each category for diversity
    bbc_samples = bbc_df.groupby('category').head(2)
    bbc_text = "\n---\n".join(bbc_samples['title'] + ": " + bbc_samples['content'])

    # 2. Taylor Swift Sampling: Get top 20 tweets by engagement
    ts_samples = ts_df.sort_values(by='likeCount', ascending=False).head(20)
    ts_text = "\n---\n".join(ts_samples['content'])

    return bbc_text, ts_text

# Execute and store for the prompt
bbc_corpus, ts_corpus = prepare_style_samples('bbc_news.csv', 'taylor_swift_tweets.csv')

```

---

### Phase 3: The Characterization Agent (The "Style Extractor")

This is the "Agentic" heart of your first step. You will pass the `bbc_corpus` and `ts_corpus` into a specialized prompt.

**The Prompt Strategy: "Linguistic Reverse-Engineering"**
Instead of asking for a summary, ask for **rules**. Use a prompt like this for each corpus:

> "I am providing you with a corpus of [BBC News / Taylor Swift Tweets].
> Your task is to act as a **Linguistic Pattern Analyst**.
> Analyze the text and output a **Style Guide** in JSON format covering:
> 1. **Tone:** (e.g., Objective vs. Intimate)
> 2. **Structure:** (e.g., Inverted pyramid vs. stream-of-consciousness)
> 3. **Punctuation Quirk:** (e.g., Oxford commas vs. excessive '!!')
> 4. **Vocabulary Level:** (e.g., Grade 12 level vs. Metaphorical/Lyrical)
> 5. **Formatting:** (e.g., Standard Case vs. All Lowercase)"
> 
> 

---

### Summary of the Workflow for your Assignment

If you are documenting this for your backend design, here is the technical flow:

| Component | Technical Implementation | Goal |
| --- | --- | --- |
| **Data Loader** | Pandas `read_csv` + `groupby` | Reduce noise and token costs by selecting representative samples. |
| **Extraction Agent** | LLM with **Few-Shot Analysis** prompt | Convert raw text into a machine-readable "Style Guide" (JSON). |
| **Output** | Structured Metadata (JSON) | Provide the "DNA" that the Writing Agent will use in Step 2. |

---

### Next Step for You

Now that you have the sampling logic and the prompt strategy, would you like me to provide the **Exact Python code to call the LLM API** (like OpenAI or Gemini) to run this "Style Extractor" prompt in your notebook?