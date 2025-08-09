# CLAUDE.md

This file provides guidance for Claude Code when working with the Player's Handbot codebase.

## Project Overview

Player's Handbot is a Model Context Protocol (MCP) server that provides AI agents with comprehensive D&D 5e data access. It integrates 5e.tools content with MSRP (Merchant's Sorcerous Rarities Pricelist) pricing data while explicitly excluding 2014 PHB content to focus on current game rules.

## Development Commands

### Server Operations
```bash
# Run the MCP server
python dnd_mcp_server.py

# Install all dependencies
pip install -r requirements.txt
```

### Component Testing
```bash
# Test MSRP pricing data loader
python msrp_loader.py

# Test 5e.tools data fetcher
python dnd_5etools_fetcher.py
```

## Core Architecture

### Primary Components

**`dnd_mcp_server.py`** - Main MCP server implementation
- Implements MCP protocol with 20+ D&D content tools
- Orchestrates data flow between components
- Handles tool routing and response formatting
- Integrates MSRP pricing with game content

**`dnd_5etools_fetcher.py`** - 5e.tools data client
- Fetches D&D content from 5e.tools-mirror-3 GitHub repository
- Implements session-duration HTTP caching
- Filters out 2014 PHB content across all data types
- Normalizes and structures raw JSON data

**`msrp_loader.py`** - MSRP pricing integration
- Parses CSV pricing data with pandas/openpyxl
- Implements fuzzy string matching for item names
- Normalizes item names for consistent lookups
- Provides pricing fallbacks and error handling

### Data Flow Architecture

1. **Initialization**: Server loads MSRP pricing data from CSV file
2. **Client Setup**: FiveEToolsClient instantiated with MSRP cross-reference data
3. **Request Routing**: MCP tool calls route through server to appropriate data sources
4. **Response Assembly**: Results combine 5e.tools content with MSRP pricing when available
5. **Caching**: HTTP responses cached for session duration to improve performance

## Tool Categories

### Character Creation Tools
- **Spells**: `get_spell_list_2024`, `get_spell_details_2024`, `search_spells_2024`
- **Races**: `get_race_list`, `get_race_details`, `search_races`
- **Classes**: `get_class_list`, `get_class_details`, `get_subclass_list`, `search_classes`
- **Backgrounds**: `get_background_list`, `get_background_details`, `search_backgrounds`
- **Feats**: `get_feat_list`, `get_feat_details`, `search_feats`

### Equipment Tools
- **Equipment**: `get_equipment_list`, `get_equipment_details`
- **Magic Items**: `get_magic_item_list`, `get_magic_item_details`

### Game Master Tools
- **Monsters**: `get_monster_list_5etools`, `get_monster_details_5etools`, `search_monsters_5etools`
- **Rules**: `get_conditions_list`, `get_condition_details`, `search_rules`

## Key Implementation Features

### Content Filtering Strategy
- All tools automatically exclude 2014 PHB content by design
- Filter applied at data source level, not post-processing
- Ensures consistency across all tool responses

### MSRP Pricing Integration
- Magic items automatically include MSRP pricing when available
- Fuzzy matching handles variations in item naming conventions
- Pricing data gracefully degrades when matches aren't found

### Performance Optimizations
- HTTP response caching for 5e.tools API calls
- Lazy loading of large datasets
- Efficient fuzzy matching algorithms

### Error Handling
- Graceful degradation when external APIs are unavailable
- Comprehensive logging for debugging
- User-friendly error messages through MCP protocol

## Dependencies Management

### Core Dependencies
```python
mcp>=1.0.0              # Model Context Protocol implementation
httpx>=0.25.0            # Async HTTP client for API requests
pandas>=1.5.0            # Data manipulation and CSV processing
openpyxl>=3.1.0          # Excel file parsing support
```

### Utility Dependencies
```python
aiofiles>=23.0.0         # Async file operations
pydantic>=2.0.0          # Data validation and serialization
typing-extensions>=4.5.0 # Type hints for older Python versions
fuzzywuzzy>=0.18.0       # Fuzzy string matching
python-levenshtein>=0.21.0 # String distance calculations
```

## File Structure & Data Sources

### Required Files
- `"Merchant's Sorcerous Rarities Pricelist (MSRP) - Full.csv"` - Community pricing data
- `requirements.txt` - Python package dependencies
- `README.md` - User-facing documentation
- `CLAUDE.md` - This development guide

### External Data Sources
- **5e.tools-mirror-3 GitHub**: Live D&D content repository
- **MSRP CSV**: Community-maintained magic item pricing

## Development Guidelines

### Code Style
- Follow async/await patterns for HTTP operations
- Use type hints for better code maintainability
- Implement proper error handling for all external API calls

### Testing Strategy
- Test individual components in isolation
- Verify MCP protocol compliance
- Validate data filtering (2014 PHB exclusion)
- Test MSRP pricing integration accuracy

### Performance Considerations
- Minimize API calls through effective caching
- Use efficient data structures for lookups
- Implement lazy loading for large datasets