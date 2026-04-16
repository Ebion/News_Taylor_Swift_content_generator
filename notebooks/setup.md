# Setup Instructions for OpenAI API Key

## Prerequisites

1. **Python Environment**: Ensure you have Python 3.8+ installed
2. **OpenAI Account**: Get your API key from https://platform.openai.com/api-keys

## Installation

Install the required packages:

```bash
pip install langchain langchain-openai python-dotenv pandas
```

## How to Inject Your OpenAI API Key

### Option A: Environment Variable (Recommended)

**For Mac/Linux (Terminal):**
```bash
export OPENAI_API_KEY="sk-your-openai-key-here"
```

**For Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=sk-your-openai-key-here
```

**For Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-your-openai-key-here"
```

Then run your notebook - the environment variable will be automatically read by LangChain.

---

### Option B: .env File (Recommended for Projects)

1. Create a file named `.env` in your project root:
```
OPENAI_API_KEY=sk-your-openai-key-here
```

2. Add this to your notebook code:
```python
from dotenv import load_dotenv
load_dotenv()  # This loads the .env file
```

---

### Option C: Inline in Notebook

Add this to your notebook (less secure, but quick for testing):

```python
import os
os.environ["OPENAI_API_KEY"] = "sk-your-openai-key-here"  # Replace with your actual key
```

---

## Verification

To verify your setup works, run:

```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4")
response = llm.invoke("Say 'Hello, World!'")
print(response.content)
```

If you see "Hello, World!" - your setup is complete!

---

## Model Options

In the notebook, you can use:
- `gpt-4` (recommended for better quality)
- `gpt-3.5-turbo` (faster, cheaper)

To change the model, update the `model` parameter:
```python
llm = ChatOpenAI(model="gpt-3.5-turbo")
```
