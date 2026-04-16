"""
Logging utilities for LLM calls.
Stores logs in JSON format to the logging folder.
Files are split by day (YYYY-MM-DD) and optionally by run_id.
"""

import time
import json
import os
from datetime import datetime
from pathlib import Path
import re

# Updated OpenAI Pricing (February 2026)
# Prices are in USD per 1M tokens
PRICING = {
    # GPT-5 Series (Latest Frontier Models)
    "gpt-5.2": {"input": 1.75, "output": 14.00},       # Flagship: Agentic & Coding
    "gpt-5.1": {"input": 1.25, "output": 10.00},       # Flagship: General
    "gpt-5": {"input": 1.25, "output": 10.00},         # Flagship: Standard
    "gpt-5-mini": {"input": 0.25, "output": 2.00},     # Fast, balanced performance
    "gpt-5-nano": {"input": 0.05, "output": 0.40},     # Optimized for massive scale
    "gpt-5-pro": {"input": 15.00, "output": 120.00},   # Ultimate Reasoning / Enterprise

    # GPT-4.1 & o3 Series (Reasoning & Intelligence)
    "gpt-4.1": {"input": 2.00, "output": 8.00},        # Succeeded "GPT-4 Turbo"
    "o3": {"input": 2.00, "output": 8.00},             # Advanced Reasoning
    "o3-pro": {"input": 20.00, "output": 80.00},       # Elite Reasoning
    "o4-mini": {"input": 1.10, "output": 4.40},        # Cost-efficient Reasoning

    # Legacy & Omni Models (Still supported, but often higher cost than 5.1)
    "gpt-4o": {"input": 2.50, "output": 10.00},        
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},    
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},  # Deep Legacy
}

# Default pricing if model not found
DEFAULT_PRICING = {"input": 0.50, "output": 1.50}

# Global list to store logs in memory
llm_logs = []

# Logging directory
LOG_DIR = Path("logging")

# Directory for full prompt persistence (additive; does not change existing JSON logs)
FULL_PROMPT_DIR = LOG_DIR / "prompts"


def _safe_filename(value: str) -> str:
    """Make a string safe for use in filenames on Windows/macOS/Linux."""
    # Replace path separators and illegal characters.
    value = re.sub(r"[\\/:*?\"<>|]", "_", value)
    value = value.replace("\n", " ").replace("\r", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value[:120] if len(value) > 120 else value


def persist_full_prompt(prompt: str, *, task_name: str, run_id: str = None, timestamp: str = None) -> str | None:
    """Persist the full prompt to disk and return a relative path.

    This is best-effort and additive: existing JSON logs remain unchanged.
    """
    try:
        ts = timestamp or datetime.now().isoformat()
        # Use a filename-safe timestamp for Windows.
        ts_safe = ts.replace(":", "-")
        rid = run_id or "no_run_id"

        folder = FULL_PROMPT_DIR / rid
        folder.mkdir(parents=True, exist_ok=True)

        task_safe = _safe_filename(task_name or "general")
        filename = f"{ts_safe}__{task_safe}__input.txt"
        path = folder / filename

        # Always write UTF-8.
        with open(path, "w", encoding="utf-8") as f:
            f.write(prompt or "")

        # Return relative path for portability.
        return str(path.as_posix())
    except Exception:
        return None


def get_log_filename(run_id: str = None) -> Path:
    """
    Get the log filename based on date and optional run_id.
    
    Args:
        run_id: Optional run identifier. If provided, logs will be saved to run_id.json
        
    Returns:
        Path to the log file
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    if run_id:
        # Use run_id as filename
        return LOG_DIR / f"{run_id}.json"
    else:
        # Use today's date as filename
        return LOG_DIR / f"{today}.json"


def get_pricing(model_name: str) -> dict:
    """Get pricing for a given model."""
    return PRICING.get(model_name, DEFAULT_PRICING)


def load_logs(run_id: str = None) -> list:
    """Load existing logs from JSON file."""
    log_file = get_log_filename(run_id)
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def save_logs(logs: list, run_id: str = None):
    """Save logs to JSON file."""
    LOG_DIR.mkdir(exist_ok=True)
    log_file = get_log_filename(run_id)
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)


def init_logs(run_id: str = None):
    """Initialize logs - load existing and prepare global list."""
    global llm_logs
    llm_logs = load_logs(run_id)
    return llm_logs


def get_model_name(llm) -> str:
    """Get model name from LangChain LLM instance."""
    # Try different attributes that LangChain might use
    if hasattr(llm, 'model_name'):
        return llm.model_name
    elif hasattr(llm, 'model'):
        return llm.model
    elif hasattr(llm, 'model_kwargs') and 'model' in llm.model_kwargs:
        return llm.model_kwargs['model']
    else:
        return "unknown"


def get_usage_metadata(response) -> dict:
    """Extract usage metadata from LLM response."""
    usage = {}
    
    # Try different ways to get usage
    if hasattr(response, 'usage_metadata'):
        usage = response.usage_metadata
    elif hasattr(response, 'usage'):
        usage_obj = response.usage
        usage = {
            'input_tokens': getattr(usage_obj, 'prompt_tokens', 0),
            'output_tokens': getattr(usage_obj, 'completion_tokens', 0),
            'total_tokens': getattr(usage_obj, 'total_tokens', 0)
        }
    else:
        usage = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
    
    return usage


def logged_invoke(llm, prompt: str, task_name: str = "general", run_id: str = None) -> str:
    """
    Execute an LLM call with logging.
    
    Args:
        llm: LangChain LLM instance
        prompt: The prompt to send
        task_name: Name for this task (e.g., "BBC_Style_Extraction")
        run_id: Optional run identifier for log file naming
        
    Returns:
        The LLM response content
    """
    global llm_logs
    
    # Execute the call
    start_time = time.time()
    response = llm.invoke(prompt)
    latency = round(time.time() - start_time, 2)
    
    # Extract metadata
    usage = get_usage_metadata(response)
    model_name = get_model_name(llm)
    
    # Get pricing for model
    pricing = get_pricing(model_name)
    
    # Calculate cost
    input_cost = (usage.get('input_tokens', 0) / 1_000_000) * pricing['input']
    output_cost = (usage.get('output_tokens', 0) / 1_000_000) * pricing['output']
    total_cost = input_cost + output_cost
    
    timestamp = datetime.now().isoformat()
    full_prompt_path = persist_full_prompt(prompt, task_name=task_name, run_id=run_id, timestamp=timestamp)

    # Create log entry
    log_entry = {
        "timestamp": timestamp,
        "task": task_name,
        "model": model_name,
        "input": prompt[:500] if len(prompt) > 500 else prompt,  # Truncate for storage
        "input_full_path": full_prompt_path,
        "input_full_chars": len(prompt or ""),
        "output": response.content[:500] if len(response.content) > 500 else response.content,
        "tokens": {
            "input_tokens": usage.get('input_tokens', 0),
            "output_tokens": usage.get('output_tokens', 0),
            "total_tokens": usage.get('total_tokens', 0)
        },
        "cost_usd": round(total_cost, 6),
        "latency_sec": latency
    }
    
    # Add to global logs
    llm_logs.append(log_entry)
    
    # Save to file (with optional run_id)
    save_logs(llm_logs, run_id)
    
    return response.content


def get_logs_dataframe(run_id: str = None):
    """Get logs as a Pandas DataFrame for visualization."""
    import pandas as pd
    
    # Load logs (either from memory or from file)
    logs_to_display = llm_logs if llm_logs else load_logs(run_id)
    
    if not logs_to_display:
        return pd.DataFrame()
    
    df = pd.DataFrame(logs_to_display)
    
    # Add readable cost column
    df['cost_display'] = df['cost_usd'].apply(lambda x: f"${x:.6f}")
    
    return df


def get_summary(run_id: str = None) -> dict:
    """Get summary statistics of logged calls."""
    logs_to_summarize = llm_logs if llm_logs else load_logs(run_id)
    
    if not logs_to_summarize:
        return {"total_calls": 0, "total_cost": 0, "total_tokens": 0}
    
    total_cost = sum(log['cost_usd'] for log in logs_to_summarize)
    total_tokens = sum(log['tokens']['total_tokens'] for log in logs_to_summarize)
    
    return {
        "total_calls": len(logs_to_summarize),
        "total_cost_usd": round(total_cost, 6),
        "total_tokens": total_tokens,
        "tasks": list(set(log['task'] for log in logs_to_summarize))
    }


def clear_logs(run_id: str = None):
    """Clear all logs (use with caution)."""
    global llm_logs
    llm_logs = []
    save_logs([], run_id)
    return "Logs cleared successfully"


def list_log_files() -> list:
    """List all log files in the logging directory."""
    if not LOG_DIR.exists():
        return []
    return [f.name for f in LOG_DIR.glob("*.json")]


def log_langchain_response(response, prompt: str, task_name: str = "general", run_id: str = None) -> dict:
    """
    Log a LangChain LLM response (including structured output).
    
    Args:
        response: LangChain response object
        prompt: The prompt that was sent
        task_name: Name for this task
        run_id: Optional run identifier
        
    Returns:
        The response as dict
    """
    global llm_logs
    
    # Get output - for structured output, response is the Pydantic model
    output_text = ""
    if hasattr(response, 'model_dump_json'):
        output_text = response.model_dump_json()
    elif hasattr(response, 'dict'):
        output_text = str(response.dict())
    elif hasattr(response, 'content'):
        output_text = response.content
    
    # Get usage metadata
    usage = get_usage_metadata(response)
    model_name = get_model_name(getattr(response, 'lc_kwargs', {}).get('llm', None) or "unknown")
    
    # Get pricing
    pricing = get_pricing(model_name)
    
    # Calculate cost
    input_cost = (usage.get('input_tokens', 0) / 1_000_000) * pricing['input']
    output_cost = (usage.get('output_tokens', 0) / 1_000_000) * pricing['output']
    total_cost = input_cost + output_cost
    
    timestamp = datetime.now().isoformat()
    full_prompt_path = persist_full_prompt(prompt, task_name=task_name, run_id=run_id, timestamp=timestamp)

    # Create log entry
    log_entry = {
        "timestamp": timestamp,
        "task": task_name,
        "model": model_name,
        "input": prompt[:500] if len(prompt) > 500 else prompt,
        "input_full_path": full_prompt_path,
        "input_full_chars": len(prompt or ""),
        "output": output_text[:500] if len(output_text) > 500 else output_text,
        "tokens": usage,
        "cost_usd": round(total_cost, 6),
        "latency_sec": None
    }
    
    llm_logs.append(log_entry)
    save_logs(llm_logs, run_id)
    
    # Return as dict
    if hasattr(response, 'model_dump'):
        return response.model_dump()
    elif hasattr(response, 'dict'):
        return response.dict()
    return {"output": output_text}


def log_openai_response(response, prompt: str, task_name: str = "general", run_id: str = None) -> str:
    """
    Log an OpenAI SDK response (from client.responses.create).
    
    Args:
        response: OpenAI SDK response object
        prompt: The prompt that was sent
        task_name: Name for this task (e.g., "BBC_Article_Write")
        run_id: Optional run identifier for log file naming
        
    Returns:
        The response output text
    """
    global llm_logs
    
    # Get output text from response
    output_text = ""
    if hasattr(response, 'output_text'):
        output_text = response.output_text
    elif hasattr(response, 'choices') and response.choices:
        output_text = response.choices[0].message.content
    
    # Get usage from response
    usage = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
    if hasattr(response, 'usage') and response.usage:
        usage = {
            'input_tokens': getattr(response.usage, 'input_tokens', 0) or 0,
            'output_tokens': getattr(response.usage, 'output_tokens', 0) or 0,
            'total_tokens': getattr(response.usage, 'total_tokens', 0) or 0
        }
    elif hasattr(response, 'usage_metadata'):
        usage = response.usage_metadata
    
    # Get model name
    model_name = "unknown"
    if hasattr(response, 'model'):
        model_name = response.model
    elif hasattr(response, 'request') and hasattr(response.request, 'model'):
        model_name = response.request.model
    
    # Get pricing for model
    pricing = get_pricing(model_name)
    
    # Calculate cost
    input_cost = (usage.get('input_tokens', 0) / 1_000_000) * pricing['input']
    output_cost = (usage.get('output_tokens', 0) / 1_000_000) * pricing['output']
    total_cost = input_cost + output_cost
    
    timestamp = datetime.now().isoformat()
    full_prompt_path = persist_full_prompt(prompt, task_name=task_name, run_id=run_id, timestamp=timestamp)

    # Create log entry
    log_entry = {
        "timestamp": timestamp,
        "task": task_name,
        "model": model_name,
        "input": prompt[:500] if len(prompt) > 500 else prompt,
        "input_full_path": full_prompt_path,
        "input_full_chars": len(prompt or ""),
        "output": output_text[:500] if len(output_text) > 500 else output_text,
        "tokens": {
            "input_tokens": usage.get('input_tokens', 0),
            "output_tokens": usage.get('output_tokens', 0),
            "total_tokens": usage.get('total_tokens', 0)
        },
        "cost_usd": round(total_cost, 6),
        "latency_sec": None  # OpenAI SDK doesn't provide latency directly
    }
    
    # Add to global logs
    llm_logs.append(log_entry)
    
    # Save to file
    save_logs(llm_logs, run_id)
    
    return output_text
