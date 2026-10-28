import ast
import operator
from datetime import datetime
from zoneinfo import ZoneInfo

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("LangGraph Project Tools")


@mcp.tool()
def calculator(expression: str) -> str:
    """Safely evaluate a numeric arithmetic expression."""
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }
    unary_operators = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    def evaluate(node):
        if isinstance(node, ast.Constant) and not isinstance(node.value, bool):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numeric constants are allowed.")
        if isinstance(node, ast.BinOp) and type(node.op) in operators:
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("Exponent is too large.")
            return operators[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in unary_operators:
            return unary_operators[type(node.op)](evaluate(node.operand))
        raise ValueError("Unsupported expression.")

    try:
        if not expression.strip() or len(expression) > 256:
            raise ValueError("Expression must contain 1 to 256 characters.")
        result = evaluate(ast.parse(expression, mode="eval").body)
        if isinstance(result, (int, float)) and abs(result) > 1e100:
            raise ValueError("Result is too large.")
        return str(result)
    except Exception as exc:
        return f"Calculator error: {exc}"


@mcp.tool()
def project_lookup(topic: str) -> str:
    """Look up facts about this LangGraph agent API."""
    knowledge = {
        "framework": "The API uses LangGraph StateGraph and FastAPI.",
        "mcp": "The tools are exposed through a local Model Context Protocol server.",
        "tools": "Available tools are calculator, project lookup, and current time.",
        "api": "The API exposes POST /agent and GET /health.",
    }
    query = topic.lower()
    for key, value in knowledge.items():
        if key in query:
            return value
    return "No matching information was found in the project knowledge base."


@mcp.tool()
def current_time(timezone_name: str = "Asia/Kolkata") -> str:
    """Return the current date and time in an IANA timezone."""
    try:
        return datetime.now(ZoneInfo(timezone_name)).isoformat()
    except Exception:
        return "Time lookup error: invalid or unavailable timezone."


if __name__ == "__main__":
    mcp.run(transport="stdio")
