# Gemini model fallback (`FallbackGeminiLlm`)

This project can use **several Gemini model IDs in priority order**. If the **primary** model fails with a **quota or rate-limit style** error (for example HTTP **429** / **RESOURCE_EXHAUSTED**), the same request is retried with the **next** model in the list—without changing agent code.

## Where it is configured

Edit **`config.yaml`**. Use **`model_candidates`** (ordered list) per agent:

```yaml
agents:
  coordinator:
    model_candidates:
      - gemini-3.1-flash-lite-preview
      - gemini-3-flash-preview
      - gemini-2.5-flash
  workspace:
    model_candidates:
      - gemini-3.1-flash-lite-preview
      - gemini-3-flash-preview
      - gemini-2.5-flash
```

**Single model (no fallback wrapper):** use `model: some-model-id` or **`model_candidates`** with **one** entry. Then ADK receives a plain **string** model name.

## How it is wired

1. **`app/config.py`** — `resolve_agent_model("coordinator")` or `"workspace"` reads the matching YAML block under **`agents`**.
2. If there are **multiple** candidates, it returns **`FallbackGeminiLlm(model=first, fallbacks=rest)`**.
3. **`app/agents/*/agent.py`** passes that value to **`Agent(..., model=...)`**.

| Piece | Path |
|--------|------|
| YAML | `config.yaml` |
| Resolution | `app/config.py` |
| Fallback logic | `app/llm/fallback_gemini.py` |
| Agents | `app/agents/coordinator/agent.py`, `app/agents/coordinator/workspace_agent.py` |

## Live / `connect()`

**`connect()`** delegates only to the **first** model in the chain; normal text generation uses the full fallback loop.
