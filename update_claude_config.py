import json
import os

def update_claude_config():
    appdata = os.getenv('APPDATA')
    config_dir = os.path.join(appdata, "Claude")
    config_file = os.path.join(config_dir, "claude_desktop_config.json")

    if not os.path.exists(config_dir):
        print("Creating Claude Desktop config directory...")
        os.makedirs(config_dir)

    if not os.path.exists(config_file):
        print("Creating new Claude Desktop configuration file...")
        initial_config = {"mcpServers": {}}
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(initial_config, f, indent=4)

    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    project_path = os.path.abspath(os.path.dirname(__file__))
    mcp_server_path = os.path.join(project_path, "dnd_mcp_server.py")

    server_config = {
        "dnd-2024-server": {
            "args": [mcp_server_path],
            "env": {},
            "command": "python"
        }
    }

    if "mcpServers" not in config:
        config["mcpServers"] = {}

    existing_server = config["mcpServers"].get("dnd-2024-server")

    if existing_server and existing_server.get("args", []):
        existing_path = existing_server["args"][0]
        if existing_path != mcp_server_path:
            print(f"Updating MCP server path:\nOld: {existing_path}\nNew: {mcp_server_path}")
            config["mcpServers"]["dnd-2024-server"]["args"] = [mcp_server_path]
        else:
            print("D&D MCP server already configured with correct path.")
    else:
        print("Adding new D&D MCP server configuration...")
        config["mcpServers"]["dnd-2024-server"] = server_config["dnd-2024-server"]

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

    print("Claude Desktop configuration updated successfully!")

if __name__ == "__main__":
    update_claude_config()
