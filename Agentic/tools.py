import inspect
import json


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
    args = json.load(tool_call.function.arguments)
    print(f"Call function {name} with arguments {args}")
    return tools_map[name](**args)
