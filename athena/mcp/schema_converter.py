"""Convert JSON Schema to Athena ToolParameter."""

from typing import Any
from athena.models.tool import ToolParameter, ToolParameterType


def convert_json_schema_to_tool_parameters(schema: dict[str, Any]) -> list[ToolParameter]:
    """Convert JSON Schema (from MCP inputSchema) to Athena ToolParameters."""
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    parameters = []
    for param_name, param_schema in properties.items():
        param_type = _map_json_type_to_tool_type(param_schema.get("type", "string"))

        parameter = ToolParameter(
            name=param_name,
            type=param_type,
            description=param_schema.get("description", f"Parameter {param_name}"),
            required=param_name in required_fields,
            enum=param_schema.get("enum")
        )
        parameters.append(parameter)

    return parameters


def _map_json_type_to_tool_type(json_type: str) -> ToolParameterType:
    """Map JSON Schema types to ToolParameterType."""
    mapping = {
        "string": ToolParameterType.STRING,
        "number": ToolParameterType.NUMBER,
        "integer": ToolParameterType.NUMBER,
        "boolean": ToolParameterType.BOOLEAN,
        "object": ToolParameterType.OBJECT,
        "array": ToolParameterType.ARRAY,
    }
    return mapping.get(json_type, ToolParameterType.STRING)
