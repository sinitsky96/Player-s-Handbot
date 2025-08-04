# Player's Handbot

A D&D 5e MCP (Model Context Protocol) server that provides AI agents with comprehensive access to D&D data through integration with 5e.tools and MSRP pricing information. Specifically excludes 2014 PHB content to focus on current game rules.

## Features

- **Comprehensive D&D Data**: Access to spells, monsters, races, classes, backgrounds, feats, equipment, and rules
- **MSRP Pricing Integration**: Magic items include pricing from Merchant's Sorcerous Rarities Pricelist when available
- **Current Content Focus**: Excludes 2014 PHB content across all data types
- **MCP Protocol**: 20+ tools accessible through the Model Context Protocol
- **Fuzzy Matching**: Intelligent item name matching for better user experience

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the MCP server:
   ```bash
   python dnd_mcp_server.py
   ```

3. Configure your MCP client (Claude Desktop, Cursor, etc.) to connect to the server by adding this configuration:
   ```json
   "dnd-2024-server": {
     "command": "python",
     "args": ["/path/to/your/dnd_mcp_server.py"],
     "env": {}
   }
   ```

4. The server will load MSRP pricing data and be ready to serve D&D content through MCP tools.

## Available Tools

### Character Creation
- Races, classes, subclasses, backgrounds, and feats
- Spell lists and detailed spell information
- Equipment with pricing data

### Game Master Tools
- Monster statistics and encounter data
- Magic item details with MSRP pricing
- Rules and conditions reference

### Content Sources
- **5e.tools**: Core game content from multiple official sources
- **MSRP**: Community-maintained pricing for magic items
- **Filtered Content**: Automatically excludes outdated 2014 PHB material

## Architecture

The server consists of three main components:
- **MCP Server** (`dnd_mcp_server.py`): Handles protocol and tool routing
- **5e.tools Client** (`dnd_5etools_fetcher.py`): Fetches and caches game data
- **MSRP Loader** (`msrp_loader.py`): Processes pricing information from CSV

## Requirements

- Python 3.8+
- MCP library for protocol handling
- httpx for async HTTP requests
- pandas/openpyxl for data processing
- **MCP Client**: Claude Desktop, Cursor, or other MCP-compatible application to interact with the server
