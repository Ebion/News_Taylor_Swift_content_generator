## Phase B & C: The "Iterative Refiner" Plan

### 1. Data Contract & Loader

The `style_guide.json` is your "Golden Standard." You need a utility to load this and selectively inject the correct persona into your prompts.

* **Task:** Create a `StyleManager` class to load the JSON and return the specific string block for either `bbc` or `taylor_swift`.
* **Logic:** This prevents the LLM from seeing the Taylor Swift DNA when it’s supposed to be writing for the BBC, reducing "style bleed."

---

### 2. The Chain Architecture (LCEL)

Instead of a complex graph, you will use **LangChain Expression Language (LCEL)** to build two distinct "chains":

* **The Drafting Chain:** `Drafting_Prompt | LLM | OutputParser`
* *Input:* `{topic, style_dna}`
* *Role:* Acts as the "Creative Writer."

* **The Review Chain:** `Review_Prompt | LLM | JSONOutputParser`
* *Input:* `{initial_draft, style_dna}`
* *Role:* Acts as a "Strict Editor." It must output a list of **Critiques** and a **Pass/Fail** grade.

---

### 3. The Orchestration Loop (The "Python Loop")

Since you aren't using LangGraph, you will use a standard `while` loop or `for` loop in Python to handle the reflection.

**The Loop Logic:**

1. **Iteration 1:** Run the **Drafting Chain** to get `Draft_V1`.
2. **The Review:** Run the **Review Chain** on `Draft_V1`.
3. **Conditional Check:**
* If `Grade == "PASS"` or `Max_Iterations` reached: **Stop.**
* If `Grade == "FAIL"`: Re-run the **Drafting Chain**, but this time include the **Critiques** as additional context.


4. **Repeat.**

---

### 4. Progress & Cost Logging

As we discussed earlier, you will wrap each `.invoke()` call in your `logged_invoke` function.

* **Task:** Ensure the logs are saved into your `/logs` folder with task names like `Writer_Attempt_1`, `Editor_Review_1`, etc.
* **Metric Tracking:** At the end of the notebook, you will sum up the costs of the entire loop to see if the "Refinement" was worth the extra tokens.

---

## Summary of Components

| Component | LangChain Tool | Notebook implementation |
| --- | --- | --- |
| **Prompts** | `ChatPromptTemplate` | One for Writing, one for Editing. |
| **Logic** | ` | ` (Pipe operator) |
| **Looping** | `for i in range(MAX_ITER)` | Pythonic control flow to repeat the chains. |
| **Validation** | `PydanticOutputParser` | Ensuring the Editor gives a structured score (1-10). |

---

### Next Step:

Now that the plan is set, would you like me to provide the **System Prompt for the Editor Agent**? This prompt is the most difficult to write because it has to be "mean" enough to find style inconsistencies that a standard LLM might ignore.

To implement a high-fidelity **Writer Agent** in 2026, you shouldn't treat it as a static prompt. Using **LangChain Agents** gives you "autonomy"—the model can decide to search for context, verify a fact, or look up a specific Taylor Swift reference before writing a single word.

Here is the implementation plan for a **Search-Augmented Writer Agent**.

---

## 1. The "Agentic" Architecture

Instead of a simple chain, we wrap the LLM in an **AgentExecutor**. This allows the model to access "Tools" (like Google Search or Wikipedia) to gather "Contextual Signal" before applying the "Style DNA."

### The Toolset

For a creative writer, context is everything. You should equip the agent with:

* **Tavily Search or Google Search:** To find real-world facts (e.g., "What was the date of Taylor's last show?").
* **Style DNA Retriever:** A custom tool that "fetches" specific rules from your `style_guide.json` so the prompt doesn't get too cluttered.

---

## 2. Strategic Prompt Engineering

Your prompt needs to be **modular**. In 2026, the best practice is to separate *Instruction*, *Context*, and *Style*.

### The "Writer-Researcher" System Prompt

> "You are an AI Creative Director. Your goal is to write content that is indistinguishable from the target source.
> **Step 1: Research Phase**
> Before writing, use the search tool to find the most recent and relevant details about the **User Topic**. Do not rely on your training data if the topic is time-sensitive.
> **Step 2: Style Alignment**
> Once you have the facts, study the **Style DNA Profile** provided.
> * If BBC: Apply 'Inverted Pyramid' structure and neutral attribution.
> * If Taylor Swift: Use 'First-person emotional fragments' and specific emojis.
> 
> 
> **Step 3: Execution**
> Draft the content. Ensure that the 'Key Phrases' from the DNA are integrated naturally, not forced."

---

## 3. Implementation Plan: The "Search-Writer" Logic

In your notebook, the workflow will look like this:

```python
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 1. Setup Tools
search_tool = TavilySearchResults()
tools = [search_tool]

# 2. Define the 'Smart' Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a world-class mimic writer. Use the search tool to get facts first."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "Topic: {input}\n\nStyle Guide to follow: {style_dna}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 3. Initialize Agent
agent = create_openai_functions_agent(llm, tools, prompt)
writer_agent = AgentExecutor(agent=agent, tools=tools, verbose=True)

```

---

## 4. Key Workflow Considerations

| Feature | Why it's needed for Creative Writing |
| --- | --- |
| **Search-First Logic** | Prevents the "AI Hallucination" feel. A BBC article about a 2026 event needs 2026 facts. |
| **Agent Scratchpad** | This is the "thinking space." You can log the agent's research process to see *why* it chose certain words. |
| **Variable Injection** | By passing the `style_dna` as a variable, you can use the same agent for both BBC and Taylor Swift without rewriting code. |

---

### Why this is better for a Mini Project:

By using **Tavily** or **DuckDuckGo Search**, your agent can actually "look up" the latest news. If you ask it to write a BBC article about a topic that happened *today*, it will find the facts on the web and then wrap them in the "BBC Voice" from your JSON.