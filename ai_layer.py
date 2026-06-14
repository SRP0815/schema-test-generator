import os
import json
import urllib.request
import urllib.parse
from typing import Dict, Any, List

from schema_parser import summarize_schema, SchemaMetadata


def _choose_provider() -> str:
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    return "none"


def is_enabled() -> bool:
    return _choose_provider() != "none"


def _call_openai(prompt: str, model: str = None, max_tokens: int = 300) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return ""
    model = model or os.environ.get("OPENAI_MODEL") or "gpt-3.5-turbo"
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8")
            j = json.loads(text)
            # best-effort extraction
            return j.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception:
        return ""

def _call_gemini(prompt: str, model: str = None, max_tokens: int = 300) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return ""
    model = model or os.environ.get("GEMINI_MODEL") or "gemini-1.5-flash"  # ✅ New model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"  # ✅ New URL
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.0},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8")
            j = json.loads(text)
            candidates = j.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
        return ""
    except Exception:
        return ""



def call_llm(prompt: str, max_tokens: int = 300) -> str:
    provider = _choose_provider()
    if provider == "openai":
        return _call_openai(prompt, max_tokens=max_tokens)
    if provider == "gemini":
        return _call_gemini(prompt, max_tokens=max_tokens)
    return ""


def analyze_schema(metadata: SchemaMetadata) -> Dict[str, Any]:
    summary = summarize_schema(metadata)
    result: Dict[str, Any] = {
        "business_domain": "Unknown",
        "schema_description": "",
        "system_type": "",
        "complexity_score": 0,
        "semantic_mapping": {},
        "recommendations": [],
    }

    # Heuristic baseline
    tables = summary.get("tables", [])
    joined = " ".join(tables).lower()
    if any(k in joined for k in ["order", "product", "customer", "cart", "inventory"]):
        result["business_domain"] = "E-commerce Management System"
        result["system_type"] = "Transactional / Order Management"
    elif any(k in joined for k in ["employee", "hr", "payroll", "department"]):
        result["business_domain"] = "HR Management System"
        result["system_type"] = "HR / Payroll"
    elif any(k in joined for k in ["account", "transaction", "client", "balance"]):
        result["business_domain"] = "Banking / Finance System"
        result["system_type"] = "Financial Ledger"
    else:
        result["business_domain"] = "General Data Management"

    # Complexity score: simple heuristic
    total_tables = summary.get("total_tables", 0)
    total_fks = summary.get("total_foreign_keys", 0)
    result["complexity_score"] = min(100, total_tables * 10 + total_fks * 5)

    # Build a short prompt for improved results if LLM available
    if is_enabled():
        prompt_lines: List[str] = []
        prompt_lines.append("You are an assistant that summarizes SQL schema metadata. Provide JSON output with keys: business_domain, schema_description, system_type, semantic_mapping, recommendations. Keep output concise.")
        prompt_lines.append("Tables and columns:")
        for tname, table in metadata.tables.items():
            cols = ", ".join(c.name for c in table.columns)
            prompt_lines.append(f"{tname}: {cols}")
        prompt = "\n".join(prompt_lines)
        raw = call_llm(prompt, max_tokens=400)
        try:
            # attempt to extract json blob from response
            start = raw.find("{")
            if start != -1:
                j = json.loads(raw[start:])
                result.update({k: v for k, v in j.items() if k in result})
            else:
                # fallback: use the text as schema_description
                result["schema_description"] = raw.strip()[:800]
        except Exception:
            result["schema_description"] = raw.strip()[:800]

    # Populate semantic mapping with simple normalization as guidance
    for tname, table in metadata.tables.items():
        for col in table.columns:
            key = f"{tname}.{col.name}"
            label = col.name.lower()
            label = label.replace("usr_", "user_").replace("cust_", "customer_").replace("nm", "name").replace("_nm", "_name").replace("ph_", "phone_")
            result["semantic_mapping"][key] = label

    return result


def review_generated_data(metadata: SchemaMetadata, sample_rows: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Accepts a small sample per table and returns a quality summary."""
    result: Dict[str, Any] = {
        "data_quality_score": None,
        "validation_summary": {},
        "recommendations": [],
    }
    if not is_enabled():
        # When disabled, return empty so UI can skip LLM checks
        return result

    # Build prompt with a tiny sample
    lines: List[str] = ["Review the following sample of generated rows for each table. For each column, state if the values match the column intent (yes/no) and brief reason. Then provide an overall score (0-100) and short recommendations."]
    for tname, rows in sample_rows.items():
        lines.append(f"Table: {tname}")
        for r in rows[:10]:
            lines.append(str(r))

    prompt = "\n".join(lines)
    raw = call_llm(prompt, max_tokens=500)
    result["validation_summary"] = raw.strip()
    # Heuristic: attempt to parse a score
    try:
        import re
        m = re.search(r"(score|overall score)[:\s]+(\d{1,3})", raw, flags=re.I)
        if m:
            s = int(m.group(2))
            result["data_quality_score"] = max(0, min(100, s))
    except Exception:
        pass
    return result
