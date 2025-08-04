# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Player's Handbot is a D&D 5e MCP (Model Context Protocol) server that provides AI agents access to comprehensive D&D data through integration with 5e.tools and the MSRP (Merchant's Sorcerous Rarities Pricelist). The server specifically excludes 2014 PHB content to focus on current game rules.

## Key Commands

### Running the MCP Server
```bash
python dnd_mcp_server.py
```

### Testing individual components
```bash
# Test MSRP data loading
python msrp_loader.py

# Test 5e.tools client functionality  
python dnd_5etools_fetcher.py
```

### Installing dependencies
```bash
pip install -r requirements.txt
```

## Architecture

### Core Components

1. **dnd_mcp_server.py** - Main MCP server that orchestrates all D&D data access
   - Implements MCP protocol with 20+ tools for D&D content
   - Handles tool routing and response formatting
   - Integrates pricing data with game content

2. **dnd_5etools_fetcher.py** - Client for 5e.tools GitHub data
   - Fetches D&D content from 5e.tools-mirror-3 repository
   - Handles caching, filtering, and data normalization
   - Excludes 2014 PHB content across all data types

3. **msrp_loader.py** - MSRP pricing data loader
   - Parses CSV file with magic item pricing
   - Provides fuzzy matching for item names
   - Normalizes item names for consistent lookups

### Data Flow

1. Server initialization loads MSRP pricing data from CSV
2. FiveEToolsClient is instantiated with MSRP data for cross-referencing
3. Tool calls route through the server to appropriate data sources
4. Results combine 5e.tools content with MSRP pricing when available

### Tool Categories

- **Spells** - Search, list, and get details for spells (excluding 2014 PHB)
- **Monsters** - Monster Manual bestiary data with CR and type filtering  
- **Character Options** - Races, classes, subclasses, backgrounds, feats
- **Equipment** - Magic items and mundane equipment with MSRP pricing
- **Rules** - Conditions, diseases, and rule references

### Key Features

- **Content Filtering**: All tools exclude 2014 PHB content by design
- **Pricing Integration**: Magic items include MSRP pricing when available
- **Fuzzy Matching**: Item lookups handle variations in naming
- **Data Completeness Tracking**: Results indicate which data sources were used
- **Caching**: HTTP responses cached for session duration

### Dependencies

- `mcp>=1.0.0` - Model Context Protocol implementation
- `httpx>=0.25.0` - Async HTTP client for 5e.tools data fetching
- `asyncio` - Async programming support
- `openpyxl` - Excel file parsing (for MSRP data)
- `pandas` - Data manipulation for CSV processing

### File Structure

- `"Merchant's Sorcerous Rarities Pricelist (MSRP) - Full.csv"` - Pricing data source
- `requirements.txt` - Python dependencies
- `README.md` - Basic project information