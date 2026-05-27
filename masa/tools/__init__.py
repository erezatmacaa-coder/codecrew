from . import file_ops, shell
import json

def get_all_tools():
    tools = []
    tools.extend(file_ops.TOOLS)
    tools.append(shell.TOOL)
    return tools

def execute_tool(tool_call):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    if name in ("read_file", "write_file", "edit_file", "list_files"):
        return file_ops.execute(name, args)
    elif name == "execute_command":
        return shell.execute(args)
    else:
        return f"Error: Unknown tool: {name}"
