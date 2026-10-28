# LangGraph Agent API

A FastAPI service backed by a LangGraph `StateGraph`. The graph uses LangChain's MCP integration to connect to a local MCP server for arithmetic, project knowledge lookup, and timezone-aware current time. API calls can continue a conversation by sending the same `thread_id`.

## Run locally (PowerShell)

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. `OPENAI_MODEL` defaults to `gpt-4.1-mini`; `APP_NAME` controls the API title. Start the service:

```powershell
uvicorn app.main:app --reload
```

The API starts without an API key so its health and documentation routes remain available. The first `POST /agent` request launches the local MCP tool server and initializes the graph. Open `http://127.0.0.1:8000/docs` for the interactive API reference.

## API

`GET /health` reports service health and whether an API key is configured.

`POST /agent` accepts:

```json
{
  "message": "What is 12 * 8?",
  "thread_id": "optional-conversation-id"
}
```

The response includes a `thread_id`, the assistant's reply, and the number of messages in the current conversation state. Reuse the returned `thread_id` to continue the conversation; omit it to start a new one. The MCP server is launched over stdio by the API and does not need a separate terminal.

## Runtime notes

- Thread state is held in an in-memory LangGraph checkpointer and is lost when the API process restarts. Run one API worker for this local setup.
- The calculator accepts numeric arithmetic expressions only; it does not evaluate Python code.
- The included knowledge lookup is a small example in `mcp_server/server.py` that you can replace with project-specific data.
- Before deploying publicly, add authentication and rate limiting, and use persistent shared checkpoint storage for multi-worker deployments.
