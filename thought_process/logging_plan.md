### 1. The Most Efficient Logging Strategy

The industry standard for "mini" projects is to create a list of dictionaries where each entry represents one LLM lifecycle. You can then easily convert this list into a **Pandas DataFrame** for instant display or export it to a `.json` file.

**What to include in each log entry:**

* **Timestamp:** When the call happened.
* **Model:** Which model you used (e.g., `gpt-4o-mini`).
* **Prompt (Input):** The exact string sent.
* **Completion (Output):** The exact string received.
* **Metadata:** Token counts (Prompt + Completion) and the calculated cost in USD.

---

### 2. How Cost Calculation is Handled

Cost is calculated using the formula:


*Note: Most modern APIs (OpenAI/Anthropic/Google) now quote prices per 1 million tokens.*

---

### 3. Notebook Implementation: The "Logged Invoke"

Here is a clean way to implement this in your notebook using a simple wrapper function.

```python
import time
import json
from datetime import datetime

# 1. Define your current pricing (2026 Sample Rates for gpt-4o-mini)
PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60}, # Price per 1M tokens in USD
}

# Global list to store logs
llm_logs = []

def logged_invoke(llm, prompt, task_name="general"):
    # Execute the call
    start_time = time.time()
    response = llm.invoke(prompt)
    latency = round(time.time() - start_time, 2)
    
    # Extract Metadata (LangChain structure)
    usage = response.usage_metadata
    model_name = llm.model_name
    
    # 2. Calculate Cost
    input_cost = (usage['input_tokens'] / 1_000_000) * PRICING[model_name]['input']
    output_cost = (usage['output_tokens'] / 1_000_000) * PRICING[model_name]['output']
    total_cost = input_cost + output_cost

    # 3. Create the Log Entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "task": task_name,
        "model": model_name,
        "input": prompt,
        "output": response.content,
        "tokens": usage,
        "cost_usd": f"${total_cost:.6f}",
        "latency_sec": latency
    }
    
    llm_logs.append(log_entry)
    return response.content

# Example usage in your notebook:
# result = logged_invoke(character_agent, bbc_corpus, task_name="BBC_Style_Extraction")

```

---

### 4. Visualizing the Logs

After you've run your agents, you can display your "bill" and your history beautifully using Pandas:

```python
import pandas as pd

# Convert logs to DataFrame
df_logs = pd.DataFrame(llm_logs)

# Display specific columns to save space
print(f"Total Project Cost: ${df_logs['cost_usd'].str.replace('$', '').astype(float).sum():.4f}")
df_logs[['timestamp', 'task', 'tokens', 'cost_usd', 'latency_sec']]

```

---

### Summary of the Logging Workflow

| Step | Method | Why? |
| --- | --- | --- |
| **Storage** | List of Dicts | Flexible and easy to append to during a notebook session. |
| **Formatting** | JSON | Standard data contract; easy to save to a file for your assignment submission. |
| **Costing** | Per-1M Token Math | Accurate reflection of how you are billed by providers. |
| **Display** | Pandas DataFrame | Best for human-readable "Audit Trails" in a report. |