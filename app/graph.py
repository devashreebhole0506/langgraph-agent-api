from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.config import settings
from app.mcp_client import load_tools
from app.state import AgentState


SYSTEM_PROMPT = (
    "You are a helpful assistant. Use the available MCP tools for arithmetic, "
    "project information, and time lookups. Explain results clearly. "
    "If a tool reports an error or no matching information, say so accurately."
)


async def build_graph():
    """Load MCP tools and compile the async LangGraph agent."""
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    tools = await load_tools()
    model = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )
    model_with_tools = model.bind_tools(tools)

    async def call_model(state: AgentState):
        response = await model_with_tools.ainvoke(
            [{"role": "system", "content": SYSTEM_PROMPT}, *state["messages"]]
        )
        return {"messages": [response]}

    builder = StateGraph(AgentState)
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=InMemorySaver())
