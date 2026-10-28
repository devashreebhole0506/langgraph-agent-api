import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request

from app.config import settings
from app.graph import build_graph
from app.schemas import AgentRequest, AgentResponse, HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = None
    app.state.graph_lock = asyncio.Lock()
    app.state.thread_locks = {}
    app.state.thread_locks_guard = asyncio.Lock()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="A LangGraph agent that uses tools from a local MCP server.",
    lifespan=lifespan,
)


async def get_graph(request: Request):
    if request.app.state.graph is None:
        async with request.app.state.graph_lock:
            if request.app.state.graph is None:
                request.app.state.graph = await build_graph()
    return request.app.state.graph


async def get_thread_lock(request: Request, thread_id: str):
    async with request.app.state.thread_locks_guard:
        return request.app.state.thread_locks.setdefault(thread_id, asyncio.Lock())


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        api_key_configured=bool(settings.openai_api_key),
    )


@app.post("/agent", response_model=AgentResponse)
async def run_agent(body: AgentRequest, request: Request):
    thread_id = body.thread_id or str(uuid4())
    try:
        graph = await get_graph(request)
        thread_lock = await get_thread_lock(request, thread_id)
        async with thread_lock:
            result = await graph.ainvoke(
                {"messages": [{"role": "user", "content": body.message}]},
                config={"configurable": {"thread_id": thread_id}},
            )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Agent execution failed. Check the model and MCP server configuration.",
        ) from exc

    messages = result.get("messages", [])
    if not messages:
        raise HTTPException(status_code=502, detail="Agent returned no messages.")

    content = messages[-1].content
    if isinstance(content, str):
        reply = content.strip()
    elif isinstance(content, list):
        reply = "\n".join(
            str(block.get("text", ""))
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()
    else:
        reply = str(content).strip()
    if not reply:
        raise HTTPException(status_code=502, detail="Agent returned an empty reply.")

    return AgentResponse(
        thread_id=thread_id,
        reply=reply,
        message_count=len(messages),
    )
