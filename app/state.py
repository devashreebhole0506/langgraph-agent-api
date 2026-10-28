from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """Conversation state shared by the model and MCP tool nodes."""
