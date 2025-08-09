# Player's Handbot

A D&D 5e MCP (Model Context Protocol) server that provides AI agents with comprehensive access to D&D data through integration with 5e.tools and MSRP pricing information. Specifically excludes 2014 PHB content to focus on current game rules.

## Features

- **Comprehensive D&D Data**: Access to spells, monsters, races, classes, backgrounds, feats, equipment, and rules
- **MSRP Pricing Integration**: Magic items include pricing from Merchant's Sorcerous Rarities Pricelist when available
- **Current Content Focus**: Excludes 2014 PHB content across all data types
- **MCP Protocol**: 20+ tools accessible through the Model Context Protocol
- **Fuzzy Matching**: Intelligent item name matching for better user experience

## Requirements

- Python 3.8+
- MCP-compatible client (Claude Desktop, Cursor, etc.)
- Internet connection for 5e.tools data fetching

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify MSRP data file:**
   Ensure `"Merchant's Sorcerous Rarities Pricelist (MSRP) - Full.csv"` is in the project directory

## Usage

### Running the Server

```bash
python dnd_mcp_server.py
```

### MCP Client Configuration

Configure your MCP client to connect to the server. For Claude Desktop, add this to your configuration file:

```json
{
  "mcpServers": {
    "dnd-2024-server": {
      "command": "python",
      "args": ["/absolute/path/to/your/dnd_mcp_server.py"],
      "env": {}
    }
  }
}
```

**Important:** Use the absolute path to your `dnd_mcp_server.py` file.

## Available Tools

### Character Creation
- **Races**: Get race details, search by features, filter by size
- **Classes**: Access class information including subclasses
- **Backgrounds**: Character background options with mechanical benefits
- **Feats**: General and fighting style feats
- **Spells**: Complete spell database with filtering by level and school

### Equipment & Items
- **Equipment**: Mundane gear with pricing
- **Magic Items**: Magical equipment with MSRP pricing integration
- **Comprehensive Pricing**: Real market values for campaign economics

### Game Master Tools
- **Monsters**: Bestiary data with CR filtering and detailed statistics
- **Conditions**: Status effects and their mechanical impact
- **Rules Search**: Quick reference for game mechanics

## Data Sources

- **5e.tools**: Core game content from official D&D sources
- **MSRP**: Community-maintained pricing for magic items
- **Content Filtering**: Automatically excludes outdated 2014 PHB material

## Architecture

The server consists of three main components:

- **MCP Server** (`dnd_mcp_server.py`): Handles MCP protocol and tool routing
- **5e.tools Client** (`dnd_5etools_fetcher.py`): Fetches and caches game data from GitHub
- **MSRP Loader** (`msrp_loader.py`): Processes pricing information from CSV files

## Testing

Test individual components:

```bash
# Test MSRP data loading
python msrp_loader.py

# Test 5e.tools client functionality  
python dnd_5etools_fetcher.py
```

## Troubleshooting

- **Connection Issues**: Ensure internet connectivity for 5e.tools data fetching
- **Missing Data**: Check that MSRP CSV file is present and accessible
- **MCP Client**: Verify your client supports MCP and is properly configured

## Contributing

This project integrates community resources. When contributing:
- Maintain 2014 PHB content exclusion
- Ensure MSRP pricing integration works correctly
- Test with actual MCP clients before submitting changes