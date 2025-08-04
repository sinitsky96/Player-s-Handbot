#!/usr/bin/env python3
"""
D&D MCP Server
Provides access to D&D data from 5e.tools for AI agents, excluding 2014 PHB content
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.server.stdio
import mcp.types as types

from dnd_5etools_fetcher import FiveEToolsClient
from msrp_loader import load_msrp_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dnd-mcp-server")

server = Server("dnd-server")

# Load MSRP data and initialize the 5e.tools client
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "Merchant's Sorcerous Rarities Pricelist (MSRP) - Full.csv")

logger.info(f"Loading MSRP pricing data from: {csv_path}")
try:
    msrp_data = load_msrp_data(csv_path)
    logger.info(f"SUCCESS: Loaded MSRP data for {len(msrp_data)} items")
    # Test for specific items to confirm data is loaded
    if "bag of holding" in msrp_data:
        logger.info(f"SUCCESS: Bag of Holding found in MSRP: {msrp_data['bag of holding']['msrp_common']} gp")
    else:
        logger.warning("WARNING: Bag of Holding NOT found in MSRP data")
except Exception as e:
    logger.error(f"FAILED to load MSRP data from {csv_path}: {e}")
    logger.error(f"Current working directory: {os.getcwd()}")
    logger.error(f"Script directory: {script_dir}")
    msrp_data = {}

# Initialize the 5e.tools client with MSRP data
dnd_client = FiveEToolsClient(msrp_data=msrp_data)

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="dnd://assistant-prompt",
            name="D&D Assistant System Prompt",
            description="Suggested system prompt for using this D&D MCP server",
            mimeType="text/plain"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a resource"""
    if uri == "dnd://assistant-prompt":
        return """You are a D&D 5e assistant with access to comprehensive game data through MCP tools. You can help with:

- Character creation (races, classes, backgrounds, feats)
- Spell information and spell lists
- Monster statistics and encounter planning  
- Equipment and magic items with MSRP pricing from the Merchant's Sorcerous Rarities Pricelist (MSRP)
- Rules and conditions reference

All content excludes outdated 2014 PHB material and focuses on current D&D rules. Magic items include community-maintained pricing from the separate MSRP manual when available."""
    
    raise ValueError(f"Unknown resource: {uri}")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools for D&D content (excludes 2014 PHB)"""
    return [
        # SPELL TOOLS
        Tool(
            name="get_spell_list_2024",
            description="Get a list of D&D spells from all sources except 2014 PHB",
            inputSchema={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 9,
                        "description": "Spell level to filter by (0-9)"
                    },
                    "school": {
                        "type": "string",
                        "description": "Spell school to filter by (e.g., 'evocation', 'enchantment')"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of results to return"
                    }
                }
            }
        ),
        Tool(
            name="get_spell_details_2024",
            description="Get detailed information about a specific spell from any source except 2014 PHB",
            inputSchema={
                "type": "object",
                "properties": {
                    "spell_name": {
                        "type": "string",
                        "description": "The spell name (e.g., 'Fireball', 'Magic Missile')"
                    }
                },
                "required": ["spell_name"]
            }
        ),
        Tool(
            name="search_spells_2024",
            description="Search for spells by name or description across all sources except 2014 PHB",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Maximum number of results to return"
                    }
                },
                "required": ["query"]
            }
        ),
        
        # MONSTER TOOLS
        Tool(
            name="get_monster_list_5etools",
            description="Get a list of D&D monsters from 5e.tools",
            inputSchema={
                "type": "object",
                "properties": {
                    "cr_range": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                        "description": "Challenge rating range [min, max] (e.g., [1, 5])"
                    },
                    "monster_type": {
                        "type": "string",
                        "description": "Monster type to filter by (e.g., 'dragon', 'humanoid')"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of results to return"
                    }
                }
            }
        ),
        Tool(
            name="get_monster_details_5etools",
            description="Get detailed information about a specific monster",
            inputSchema={
                "type": "object",
                "properties": {
                    "monster_name": {
                        "type": "string",
                        "description": "The monster name (e.g., 'Ancient Red Dragon', 'Goblin')"
                    }
                },
                "required": ["monster_name"]
            }
        ),
        Tool(
            name="search_monsters_5etools",
            description="Search for monsters by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Maximum number of results to return"
                    }
                },
                "required": ["query"]
            }
        ),
        
        # RACE TOOLS
        Tool(
            name="get_race_list",
            description="Get a list of playable and non-playable races from all sources except 2014 PHB",
            inputSchema={
                "type": "object",
                "properties": {
                    "size": {
                        "type": "string",
                        "description": "Race size to filter by (e.g., 'Medium', 'Small')"
                    },
                    "source_filter": {
                        "type": "string",
                        "description": "Source book to filter by (e.g., 'XPHB', 'MPMM')"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of results to return"
                    }
                }
            }
        ),
        Tool(
            name="get_race_details",
            description="Get detailed information about a specific race",
            inputSchema={
                "type": "object",
                "properties": {
                    "race_name": {
                        "type": "string",
                        "description": "The race name (e.g., 'Human', 'Elf')"
                    }
                },
                "required": ["race_name"]
            }
        ),
        Tool(
            name="search_races",
            description="Search for races by name or features",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Maximum number of results to return"
                    }
                },
                "required": ["query"]
            }
        ),
        
        # CLASS TOOLS
        Tool(
            name="get_class_list",
            description="Get a list of D&D classes from all sources except 2014 PHB",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_filter": {
                        "type": "string",
                        "description": "Source book to filter by (e.g., 'XPHB', 'TCE')"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of results to return"
                    }
                }
            }
        ),
        Tool(
            name="get_class_details",
            description="Get detailed information about a specific class including subclasses",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "The class name (e.g., 'Fighter', 'Wizard')"
                    }
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="get_subclass_list",
            description="Get a list of subclasses, optionally filtered by class",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "The class name to filter subclasses by"
                    },
                    "source_filter": {
                        "type": "string",
                        "description": "Source book to filter by"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of results to return"
                    }
                }
            }
        ),
        Tool(
            name="search_classes",
            description="Search for classes by name or features",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Maximum number of results to return"
                    }
                },
                "required": ["query"]
            }
        ),
        
        # BACKGROUND TOOLS
        Tool(
            name="get_background_list",
            description="Get a list of D&D backgrounds from all sources except 2014 PHB",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_filter": {
                        "type": "string",
                        "description": "Source book to filter by"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of results to return"
                    }
                }
            }
        ),
        Tool(
            name="get_background_details",
            description="Get detailed information about a specific background",
            inputSchema={
                "type": "object",
                "properties": {
                    "background_name": {
                        "type": "string",
                        "description": "The background name (e.g., 'Acolyte', 'Criminal')"
                    }
                },
                "required": ["background_name"]
            }
        ),
        Tool(
            name="search_backgrounds",
            description="Search for backgrounds by name or features",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Maximum number of results to return"
                    }
                },
                "required": ["query"]
            }
        ),
        
        # FEAT TOOLS
        Tool(
            name="get_feat_list",
            description="Get a list of D&D feats from all sources except 2014 PHB",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_filter": {
                        "type": "string",
                        "description": "Source book to filter by"
                    },
                    "category": {
                        "type": "string",
                        "description": "Feat category to filter by (G=General, FS=Fighting Style)"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of results to return"
                    }
                }
            }
        ),
        Tool(
            name="get_feat_details",
            description="Get detailed information about a specific feat",
            inputSchema={
                "type": "object",
                "properties": {
                    "feat_name": {
                        "type": "string",
                        "description": "The feat name (e.g., 'Alert', 'Lucky')"
                    }
                },
                "required": ["feat_name"]
            }
        ),
        Tool(
            name="search_feats",
            description="Search for feats by name or description",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Maximum number of results to return"
                    }
                },
                "required": ["query"]
            }
        ),
        
        # EQUIPMENT TOOLS
        Tool(
            name="get_equipment_list",
            description="Get a list of non-magical equipment from all sources except 2014 PHB with MSRP pricing when available",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_type": {
                        "type": "string",
                        "description": "Equipment type to filter by (e.g., 'weapon', 'armor')"
                    },
                    "source_filter": {
                        "type": "string",
                        "description": "Source book to filter by"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of results to return"
                    }
                }
            }
        ),
        Tool(
            name="get_equipment_details",
            description="Get detailed information about a specific equipment item with MSRP pricing when available",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "The equipment item name (e.g., 'Longsword', 'Chain Mail')"
                    }
                },
                "required": ["item_name"]
            }
        ),
        
        # MAGIC ITEMS TOOLS
        Tool(
            name="get_magic_item_list",
            description="Get a list of magic items with MSRP pricing when available",
            inputSchema={
                "type": "object",
                "properties": {
                    "rarity": {
                        "type": "string",
                        "enum": ["common", "uncommon", "rare", "very rare", "legendary", "artifact"],
                        "description": "Item rarity to filter by"
                    },
                    "item_type": {
                        "type": "string",
                        "description": "Item type to filter by (e.g., 'weapon', 'armor', 'wondrous item')"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum number of results to return"
                    }
                }
            }
        ),
        Tool(
            name="get_magic_item_details",
            description="Get detailed information about a specific magic item with MSRP pricing when available",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "The magic item name (e.g., 'Bag of Holding', 'Flametongue')"
                    }
                },
                "required": ["item_name"]
            }
        ),
        
        # RULES AND CONDITIONS TOOLS
        Tool(
            name="get_conditions_list",
            description="Get a list of all D&D conditions and status effects",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_condition_details",
            description="Get detailed information about a specific condition",
            inputSchema={
                "type": "object",
                "properties": {
                    "condition_name": {
                        "type": "string",
                        "description": "The condition name (e.g., 'Charmed', 'Paralyzed')"
                    }
                },
                "required": ["condition_name"]
            }
        ),
        Tool(
            name="search_rules",
            description="Search across D&D rules and conditions",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for rules content"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Maximum number of results to return"
                    }
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls"""
    try:
        # SPELL FUNCTIONS
        if name == "get_spell_list_2024":
            result = await dnd_client.get_spell_list_2024(
                level=arguments.get("level"),
                school=arguments.get("school"),
                limit=arguments.get("limit", 50)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_spell_details_2024":
            result = await dnd_client.get_spell_details_2024(
                spell_name=arguments["spell_name"]
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "search_spells_2024":
            result = await dnd_client.search_spells_2024(
                query=arguments["query"],
                limit=arguments.get("limit", 20)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # RACE FUNCTIONS
        elif name == "get_race_list":
            result = await dnd_client.get_race_list(
                size=arguments.get("size"),
                source_filter=arguments.get("source_filter"),
                limit=arguments.get("limit", 50)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_race_details":
            result = await dnd_client.get_race_details(
                race_name=arguments["race_name"]
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "search_races":
            result = await dnd_client.search_races(
                query=arguments["query"],
                limit=arguments.get("limit", 20)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # CLASS FUNCTIONS
        elif name == "get_class_list":
            result = await dnd_client.get_class_list(
                source_filter=arguments.get("source_filter"),
                limit=arguments.get("limit", 50)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_class_details":
            result = await dnd_client.get_class_details(
                class_name=arguments["class_name"]
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_subclass_list":
            result = await dnd_client.get_subclass_list(
                class_name=arguments.get("class_name"),
                source_filter=arguments.get("source_filter"),
                limit=arguments.get("limit", 50)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "search_classes":
            result = await dnd_client.search_classes(
                query=arguments["query"],
                limit=arguments.get("limit", 20)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # BACKGROUND FUNCTIONS
        elif name == "get_background_list":
            result = await dnd_client.get_background_list(
                source_filter=arguments.get("source_filter"),
                limit=arguments.get("limit", 50)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_background_details":
            result = await dnd_client.get_background_details(
                background_name=arguments["background_name"]
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "search_backgrounds":
            result = await dnd_client.search_backgrounds(
                query=arguments["query"],
                limit=arguments.get("limit", 20)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # FEAT FUNCTIONS
        elif name == "get_feat_list":
            result = await dnd_client.get_feat_list(
                source_filter=arguments.get("source_filter"),
                category=arguments.get("category"),
                limit=arguments.get("limit", 50)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_feat_details":
            result = await dnd_client.get_feat_details(
                feat_name=arguments["feat_name"]
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "search_feats":
            result = await dnd_client.search_feats(
                query=arguments["query"],
                limit=arguments.get("limit", 20)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # EQUIPMENT FUNCTIONS
        elif name == "get_equipment_list":
            result = await dnd_client.get_equipment_list(
                item_type=arguments.get("item_type"),
                source_filter=arguments.get("source_filter"),
                limit=arguments.get("limit", 50)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_equipment_details":
            result = await dnd_client.get_equipment_details(
                item_name=arguments["item_name"]
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # MONSTER FUNCTIONS
        elif name == "get_monster_list_5etools":
            result = await dnd_client.get_monster_list_5etools(
                cr_range=arguments.get("cr_range"),
                monster_type=arguments.get("monster_type"),
                limit=arguments.get("limit", 50)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_monster_details_5etools":
            result = await dnd_client.get_monster_details_5etools(
                monster_name=arguments["monster_name"]
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "search_monsters_5etools":
            result = await dnd_client.search_monsters_5etools(
                query=arguments["query"],
                limit=arguments.get("limit", 20)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # MAGIC ITEM FUNCTIONS
        elif name == "get_magic_item_list":
            result = await dnd_client.get_magic_item_list(
                rarity=arguments.get("rarity"),
                item_type=arguments.get("item_type"),
                limit=arguments.get("limit", 50)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_magic_item_details":
            item_name = arguments["item_name"]
            logger.info(f"DEBUG: get_magic_item_details called for '{item_name}'")
            logger.info(f"DEBUG: dnd_client has MSRP data: {len(dnd_client.msrp_data)} items")
            result = await dnd_client.get_magic_item_details(item_name=item_name)
            logger.info(f"DEBUG: Result data_completeness: {result.get('data_completeness', 'N/A')}")
            logger.info(f"DEBUG: Result sources_used: {result.get('sources_used', 'N/A')}")
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        # RULES AND CONDITIONS FUNCTIONS
        elif name == "get_conditions_list":
            result = await dnd_client.get_conditions_list()
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "get_condition_details":
            result = await dnd_client.get_condition_details(
                condition_name=arguments["condition_name"]
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "search_rules":
            result = await dnd_client.search_rules(
                query=arguments["query"],
                limit=arguments.get("limit", 20)
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Run the MCP server"""
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    finally:
        # Clean up the client when server shuts down
        await dnd_client.close()

if __name__ == "__main__":
    asyncio.run(main())