import subprocess

TOOL = {
    "type": "function",
    "function": {
        "name": "execute_command",
        "description": "Execute a shell command and return output.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds",
                    "default": 30,
                },
            },
            "required": ["command"],
        },
    },
}

def execute(args):
    command = args["command"]
    timeout = args.get("timeout", 8)
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n--- STDERR ---\n"
            output += result.stderr
        if result.returncode != 0:
            output += f"\n(Exit code: {result.returncode})"
        return output.strip() or "(No output)"
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"
