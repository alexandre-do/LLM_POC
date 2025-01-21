import inspect
import json

from agent import issues_and_repairs_agent, refund_agent, sales_agent, triage_agent


def function_to_schema(func) -> dict:
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }
    try:
        signature = inspect.signature(func)
    except Exception as e:
        raise ValueError(f"Failed to get signature for func {func.__name__}, error={e}")
    params = {}
    for param in signature.parameters.values():
        try:
            param_type = type_map.get(param.annotation, "string")
            params[param.name] = {"type": param_type}
        except KeyError as e:
            raise f"Unknow type annotation {param.annotation} for param {param.name}, error = {e}"
    required = [
        param.name
        for param in signature.parameters.values()
        if param.default == inspect._empty
    ]
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": (func.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": params,
                "required": required,
            },
        },
    }


def execute_tool_call(tool_call, tools_map):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    print(f"Call function {name} with arguments {args}")
    return tools_map[name](**args)


def execute_tool_call_handoff(tool_call, tools_map, agent_name):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    print(f"{agent_name}:", f"{name}({args})")
    return tools_map[name](**args)


def transfer_back_to_triage():
    """Call this if the user brings up a topic outside of your purview,
    including escalating to human."""
    return triage_agent


def transfer_to_refund():
    return refund_agent


def transfer_to_sales_agent():
    return sales_agent


def transfer_to_issues_and_repairs():
    """User for issues, repairs, or refunds."""
    return issues_and_repairs_agent
