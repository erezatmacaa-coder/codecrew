import os

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates parent directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit a file by replacing text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "old_string": {"type": "string", "description": "Text to find"},
                    "new_string": {"type": "string", "description": "Replacement text"}
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to list"}
                },
                "required": ["path"],
            },
        },
    },
]

def execute(name, args):
    if name == "read_file":
        path = args["path"]
        if not os.path.exists(path):
            return f"Error: File not found: {path}"
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    elif name == "write_file":
        path = args["path"]
        content = args["content"]
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"[Dosya oluşturuldu: {path} ({len(content)} karakter)]"

    elif name == "edit_file":
        path = args["path"]
        old = args["old_string"]
        new = args["new_string"]
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if old not in content:
            return f"Error: Text not found in {path}"
        content = content.replace(old, new, 1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"[Dosya düzenlendi: {path}]"

    elif name == "list_files":
        path = args["path"]
        items = os.listdir(path)
        return "\n".join(f"{i}/" if os.path.isdir(os.path.join(path, i)) else i
                        for i in sorted(items))

    return f"Error: Unknown file operation: {name}"
