#!/usr/bin/env python3
"""
5e.tools Client
Provides access to D&D 2024 data from 5e.tools GitHub repositories
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
import httpx

logger = logging.getLogger("dnd-5etools-client")

class FiveEToolsClient:
    """Client for accessing 5e.tools data from GitHub raw URLs"""
    
    BASE_URL = "https://raw.githubusercontent.com/5etools-mirror-3/5etools-src/master/data"
    
    # Spell sources to include (excludes 2014 PHB)
    SPELL_SOURCES = [
        "spells-xphb.json",  # 2024 Player's Handbook
        "spells-tce.json",   # Tasha's Cauldron of Everything
        "spells-xge.json",   # Xanathar's Guide to Everything
        "spells-ftd.json",   # Fizban's Treasury of Dragons
        "spells-scc.json",   # Strixhaven: Curriculum of Chaos
        "spells-aag.json",   # Acquisitions Incorporated
        "spells-egw.json",   # Explorer's Guide to Wildemount
        "spells-ggr.json",   # Guildmasters' Guide to Ravnica
        "spells-bmt.json",   # Book of Many Things
        "spells-idrotf.json", # Icewind Dale: Rime of the Frostmaiden
        "spells-llk.json",   # Lost Laboratory of Kwalish
        "spells-sato.json",  # Spelljammer: Adventures in Space
        "spells-tdcsr.json", # Tal'Dorei Campaign Setting Reborn
        "spells-ai.json"     # Adventurers League
    ]
    
    # Class files to include
    CLASS_FILES = [
        "class-artificer.json",
        "class-barbarian.json", 
        "class-bard.json",
        "class-cleric.json",
        "class-druid.json",
        "class-fighter.json",
        "class-monk.json",
        "class-paladin.json",
        "class-ranger.json",
        "class-rogue.json",
        "class-sorcerer.json",
        "class-warlock.json",
        "class-wizard.json"
    ]
    
    def __init__(self, msrp_data: Optional[Dict[str, Dict[str, Any]]] = None):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self._cache = {}  # Simple in-memory cache
        self.msrp_data = msrp_data or {}  # MSRP pricing data
    
    async def _fetch_json(self, url: str) -> Dict[str, Any]:
        """Fetch JSON data from URL with caching"""
        if url in self._cache:
            return self._cache[url]
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            self._cache[url] = data  # Cache for session
            return data
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
    
    # SPELL FUNCTIONS
    async def get_spell_list(self, level: Optional[int] = None, school: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get list of spells from all sources except 2014 PHB"""
        all_spells = []
        for source_file in self.SPELL_SOURCES:
            try:
                url = f"{self.BASE_URL}/spells/{source_file}"
                data = await self._fetch_json(url)
                spells = data.get('spell', [])
                # Filter out 2014 PHB content
                spells = [s for s in spells if s.get('source') != 'PHB']
                all_spells.extend(spells)
            except Exception as e:
                logger.warning(f"Could not load {source_file}: {e}")
                continue
        
        spells = all_spells
        
        # Filter by level if specified
        if level is not None:
            spells = [s for s in spells if s.get('level') == level]
        
        # Filter by school if specified
        if school:
            spells = [s for s in spells if s.get('school', '').lower() == school.lower()]
        
        # Apply limit
        spells = spells[:limit]
        
        # Return in consistent format
        return {
            'count': len(spells),
            'results': [{
                'index': spell.get('name', '').lower().replace(' ', '-').replace("'", ""),
                'name': spell.get('name'),
                'level': spell.get('level'),
                'school': spell.get('school'),
                'source': spell.get('source'),
                'has_2024_rules': spell.get('basicRules2024', False)
            } for spell in spells]
        }
    
    async def get_spell_details(self, spell_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific spell from any source except 2014 PHB"""
        # Search through all spell sources
        for source_file in self.SPELL_SOURCES:
            try:
                url = f"{self.BASE_URL}/spells/{source_file}"
                data = await self._fetch_json(url)
                spells = data.get('spell', [])
                
                # Find spell by name (case-insensitive), exclude 2014 PHB
                for s in spells:
                    if s.get('source') == 'PHB':  # Skip 2014 PHB content
                        continue
                    if (s.get('name', '').lower() == spell_name.lower() or 
                        s.get('name', '').lower().replace(' ', '-').replace("'", "") == spell_name.lower()):
                        return s
            except Exception as e:
                logger.warning(f"Could not search {source_file}: {e}")
                continue
        
        raise ValueError(f"Spell '{spell_name}' not found")
    
    async def search_spells(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for spells by name or description across all sources except 2014 PHB"""
        query_lower = query.lower()
        matching_spells = []
        
        # Search through all spell sources
        for source_file in self.SPELL_SOURCES:
            try:
                url = f"{self.BASE_URL}/spells/{source_file}"
                data = await self._fetch_json(url)
                spells = data.get('spell', [])
                
                # Search in name and description, exclude 2014 PHB
                for spell in spells:
                    if spell.get('source') == 'PHB':  # Skip 2014 PHB content
                        continue
                        
                    name_match = query_lower in spell.get('name', '').lower()
                    
                    # Search in spell description entries
                    desc_match = False
                    entries = spell.get('entries', [])
                    if isinstance(entries, list):
                        for entry in entries:
                            if isinstance(entry, str) and query_lower in entry.lower():
                                desc_match = True
                                break
                    
                    if name_match or desc_match:
                        matching_spells.append(spell)
                        
            except Exception as e:
                logger.warning(f"Could not search {source_file}: {e}")
                continue
        
        matching_spells = matching_spells[:limit]
        
        return {
            'count': len(matching_spells),
            'results': [{
                'index': spell.get('name', '').lower().replace(' ', '-').replace("'", ""),
                'name': spell.get('name'),
                'level': spell.get('level'),
                'school': spell.get('school'),
                'source': spell.get('source')
            } for spell in matching_spells]
        }
    
    # Backward compatibility aliases
    async def get_spell_list_2024(self, level: Optional[int] = None, school: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Deprecated: Use get_spell_list instead"""
        return await self.get_spell_list(level, school, limit)
    
    async def get_spell_details_2024(self, spell_name: str) -> Dict[str, Any]:
        """Deprecated: Use get_spell_details instead"""
        return await self.get_spell_details(spell_name)
    
    async def search_spells_2024(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Deprecated: Use search_spells instead"""
        return await self.search_spells(query, limit)
    
    # RACE FUNCTIONS
    async def get_race_list(self, size: Optional[str] = None, source_filter: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get list of playable and non-playable races from all sources except 2014 PHB"""
        url = f"{self.BASE_URL}/races.json"
        data = await self._fetch_json(url)
        
        races = data.get('race', [])
        
        # Filter out 2014 PHB content
        races = [r for r in races if r.get('source') != 'PHB']
        
        # Filter by size if specified
        if size:
            races = [r for r in races if self._race_size_matches(r.get('size'), size)]
        
        # Filter by source if specified
        if source_filter:
            races = [r for r in races if r.get('source', '').lower() == source_filter.lower()]
        
        # Apply limit
        races = races[:limit]
        
        return {
            'count': len(races),
            'results': [{
                'index': race.get('name', '').lower().replace(' ', '-').replace("'", ""),
                'name': race.get('name'),
                'size': self._format_race_size(race.get('size')),
                'speed': race.get('speed'),
                'source': race.get('source'),
                'lineage': race.get('lineage'),
                'is_legacy': race.get('legacy', False)
            } for race in races]
        }
    
    async def get_race_details(self, race_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific race"""
        url = f"{self.BASE_URL}/races.json"
        data = await self._fetch_json(url)
        
        races = data.get('race', [])
        
        # Find race by name (case-insensitive), exclude 2014 PHB
        race = None
        for r in races:
            if r.get('source') == 'PHB':  # Skip 2014 PHB content
                continue
            if (r.get('name', '').lower() == race_name.lower() or 
                r.get('name', '').lower().replace(' ', '-').replace("'", "") == race_name.lower()):
                race = r
                break
        
        if not race:
            raise ValueError(f"Race '{race_name}' not found")
        
        return race
    
    async def search_races(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for races by name or features"""
        url = f"{self.BASE_URL}/races.json"
        data = await self._fetch_json(url)
        
        races = data.get('race', [])
        query_lower = query.lower()
        
        matching_races = []
        for race in races:
            if race.get('source') == 'PHB':  # Skip 2014 PHB content
                continue
                
            # Search in name
            name_match = query_lower in race.get('name', '').lower()
            
            # Search in race entries/description
            desc_match = False
            entries = race.get('entries', [])
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, str) and query_lower in entry.lower():
                        desc_match = True
                        break
                    elif isinstance(entry, dict):
                        # Check nested entries
                        nested_entries = entry.get('entries', [])
                        if isinstance(nested_entries, list):
                            for nested in nested_entries:
                                if isinstance(nested, str) and query_lower in nested.lower():
                                    desc_match = True
                                    break
            
            # Search in traits
            trait_match = False
            if 'traitTags' in race:
                trait_tags = race.get('traitTags', [])
                if trait_tags:  # Check if trait_tags is not None
                    for tag in trait_tags:
                        if tag and query_lower in str(tag).lower():
                            trait_match = True
                            break
            
            if name_match or desc_match or trait_match:
                matching_races.append(race)
        
        matching_races = matching_races[:limit]
        
        return {
            'count': len(matching_races),
            'results': [{
                'index': race.get('name', '').lower().replace(' ', '-').replace("'", ""),
                'name': race.get('name'),
                'size': self._format_race_size(race.get('size')),
                'speed': race.get('speed'),
                'source': race.get('source'),
                'lineage': race.get('lineage')
            } for race in matching_races]
        }
    
    # CLASS FUNCTIONS
    async def get_class_list(self, source_filter: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get list of D&D classes from all sources except 2014 PHB"""
        all_classes = []
        
        for class_file in self.CLASS_FILES:
            try:
                url = f"{self.BASE_URL}/class/{class_file}"
                data = await self._fetch_json(url)
                classes = data.get('class', [])
                
                # Filter out 2014 PHB content
                classes = [c for c in classes if c.get('source') != 'PHB']
                all_classes.extend(classes)
            except Exception as e:
                logger.warning(f"Could not load {class_file}: {e}")
                continue
        
        # Filter by source if specified
        if source_filter:
            all_classes = [c for c in all_classes if c.get('source', '').lower() == source_filter.lower()]
        
        # Apply limit
        all_classes = all_classes[:limit]
        
        return {
            'count': len(all_classes),
            'results': [{
                'index': cls.get('name', '').lower().replace(' ', '-'),
                'name': cls.get('name'),
                'source': cls.get('source'),
                'hit_die': cls.get('hd', {}).get('faces') if cls.get('hd') else None,
                'primary_ability': cls.get('primaryAbility'),
                'saves': cls.get('proficiency', []),
                'subclass_count': len(cls.get('subclasses', []))
            } for cls in all_classes]
        }
    
    async def get_class_details(self, class_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific class including subclasses"""
        for class_file in self.CLASS_FILES:
            try:
                url = f"{self.BASE_URL}/class/{class_file}"
                data = await self._fetch_json(url)
                classes = data.get('class', [])
                
                # Find class by name (case-insensitive), exclude 2014 PHB
                for cls in classes:
                    if cls.get('source') == 'PHB':  # Skip 2014 PHB content
                        continue
                    if (cls.get('name', '').lower() == class_name.lower() or 
                        cls.get('name', '').lower().replace(' ', '-') == class_name.lower()):
                        return cls
            except Exception as e:
                logger.warning(f"Could not search {class_file}: {e}")
                continue
        
        raise ValueError(f"Class '{class_name}' not found")
    
    async def get_subclass_list(self, class_name: Optional[str] = None, source_filter: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get list of subclasses, optionally filtered by class"""
        all_subclasses = []
        
        for class_file in self.CLASS_FILES:
            try:
                url = f"{self.BASE_URL}/class/{class_file}"
                data = await self._fetch_json(url)
                classes = data.get('class', [])
                
                for cls in classes:
                    if cls.get('source') == 'PHB':  # Skip 2014 PHB content
                        continue
                        
                    # Filter by class name if specified
                    if class_name and cls.get('name', '').lower() != class_name.lower():
                        continue
                    
                    subclasses = cls.get('subclasses', [])
                    for subclass in subclasses:
                        if subclass.get('source') != 'PHB':  # Skip 2014 PHB subclasses
                            subclass_data = subclass.copy()
                            subclass_data['parent_class'] = cls.get('name')
                            all_subclasses.append(subclass_data)
                            
            except Exception as e:
                logger.warning(f"Could not load {class_file}: {e}")
                continue
        
        # Filter by source if specified
        if source_filter:
            all_subclasses = [s for s in all_subclasses if s.get('source', '').lower() == source_filter.lower()]
        
        # Apply limit
        all_subclasses = all_subclasses[:limit]
        
        return {
            'count': len(all_subclasses),
            'results': [{
                'index': f"{subclass['parent_class'].lower()}-{subclass.get('name', '').lower()}".replace(' ', '-'),
                'name': subclass.get('name'),
                'class': subclass['parent_class'],
                'source': subclass.get('source'),
                'short_name': subclass.get('shortName')
            } for subclass in all_subclasses]
        }
    
    async def search_classes(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for classes by name or features"""
        query_lower = query.lower()
        matching_classes = []
        
        for class_file in self.CLASS_FILES:
            try:
                url = f"{self.BASE_URL}/class/{class_file}"
                data = await self._fetch_json(url)
                classes = data.get('class', [])
                
                for cls in classes:
                    if cls.get('source') == 'PHB':  # Skip 2014 PHB content
                        continue
                        
                    # Search in name
                    name_match = query_lower in cls.get('name', '').lower()
                    
                    # Search in class features
                    feature_match = False
                    features = cls.get('classFeatures', [])
                    for feature in features:
                        if isinstance(feature, str) and query_lower in feature.lower():
                            feature_match = True
                            break
                    
                    if name_match or feature_match:
                        matching_classes.append(cls)
                        
            except Exception as e:
                logger.warning(f"Could not search {class_file}: {e}")
                continue
        
        matching_classes = matching_classes[:limit]
        
        return {
            'count': len(matching_classes),
            'results': [{
                'index': cls.get('name', '').lower().replace(' ', '-'),
                'name': cls.get('name'),
                'source': cls.get('source'),
                'hit_die': cls.get('hd', {}).get('faces') if cls.get('hd') else None,
                'primary_ability': cls.get('primaryAbility')
            } for cls in matching_classes]
        }
    
    # BACKGROUND FUNCTIONS
    async def get_background_list(self, source_filter: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get list of D&D backgrounds from all sources except 2014 PHB"""
        url = f"{self.BASE_URL}/backgrounds.json"
        data = await self._fetch_json(url)
        
        backgrounds = data.get('background', [])
        
        # Filter out 2014 PHB content
        backgrounds = [b for b in backgrounds if b.get('source') != 'PHB']
        
        # Filter by source if specified
        if source_filter:
            backgrounds = [b for b in backgrounds if b.get('source', '').lower() == source_filter.lower()]
        
        # Apply limit
        backgrounds = backgrounds[:limit]
        
        return {
            'count': len(backgrounds),
            'results': [{
                'index': bg.get('name', '').lower().replace(' ', '-').replace("'", ""),
                'name': bg.get('name'),
                'source': bg.get('source'),
                'skills': bg.get('skillProficiencies'),
                'languages': bg.get('languageProficiencies'),
                'tool_proficiencies': bg.get('toolProficiencies')
            } for bg in backgrounds]
        }
    
    async def get_background_details(self, background_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific background"""
        url = f"{self.BASE_URL}/backgrounds.json"
        data = await self._fetch_json(url)
        
        backgrounds = data.get('background', [])
        
        # Find background by name (case-insensitive), exclude 2014 PHB
        background = None
        for bg in backgrounds:
            if bg.get('source') == 'PHB':  # Skip 2014 PHB content
                continue
            if (bg.get('name', '').lower() == background_name.lower() or 
                bg.get('name', '').lower().replace(' ', '-').replace("'", "") == background_name.lower()):
                background = bg
                break
        
        if not background:
            raise ValueError(f"Background '{background_name}' not found")
        
        return background
    
    async def search_backgrounds(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for backgrounds by name or features"""
        url = f"{self.BASE_URL}/backgrounds.json"
        data = await self._fetch_json(url)
        
        backgrounds = data.get('background', [])
        query_lower = query.lower()
        
        matching_backgrounds = []
        for bg in backgrounds:
            if bg.get('source') == 'PHB':  # Skip 2014 PHB content
                continue
                
            # Search in name
            name_match = query_lower in bg.get('name', '').lower()
            
            # Search in description
            desc_match = False
            entries = bg.get('entries', [])
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, str) and query_lower in entry.lower():
                        desc_match = True
                        break
            
            if name_match or desc_match:
                matching_backgrounds.append(bg)
        
        matching_backgrounds = matching_backgrounds[:limit]
        
        return {
            'count': len(matching_backgrounds),
            'results': [{
                'index': bg.get('name', '').lower().replace(' ', '-').replace("'", ""),
                'name': bg.get('name'),
                'source': bg.get('source'),
                'skills': bg.get('skillProficiencies')
            } for bg in matching_backgrounds]
        }
    
    # FEAT FUNCTIONS
    async def get_feat_list(self, source_filter: Optional[str] = None, category: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get list of D&D feats from all sources except 2014 PHB"""
        url = f"{self.BASE_URL}/feats.json"
        data = await self._fetch_json(url)
        
        feats = data.get('feat', [])
        
        # Filter out 2014 PHB content
        feats = [f for f in feats if f.get('source') != 'PHB']
        
        # Filter by source if specified
        if source_filter:
            feats = [f for f in feats if f.get('source', '').lower() == source_filter.lower()]
        
        # Filter by category if specified (G = General, FS = Fighting Style, etc.)
        if category:
            feats = [f for f in feats if category.upper() in f.get('category', [])]
        
        # Apply limit
        feats = feats[:limit]
        
        return {
            'count': len(feats),
            'results': [{
                'index': feat.get('name', '').lower().replace(' ', '-').replace("'", ""),
                'name': feat.get('name'),
                'source': feat.get('source'),
                'category': feat.get('category', []),
                'prerequisites': feat.get('prerequisite'),
                'has_2024_rules': feat.get('basicRules2024', False)
            } for feat in feats]
        }
    
    async def get_feat_details(self, feat_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific feat"""
        url = f"{self.BASE_URL}/feats.json"
        data = await self._fetch_json(url)
        
        feats = data.get('feat', [])
        
        # Find feat by name (case-insensitive), exclude 2014 PHB
        feat = None
        for f in feats:
            if f.get('source') == 'PHB':  # Skip 2014 PHB content
                continue
            if (f.get('name', '').lower() == feat_name.lower() or 
                f.get('name', '').lower().replace(' ', '-').replace("'", "") == feat_name.lower()):
                feat = f
                break
        
        if not feat:
            raise ValueError(f"Feat '{feat_name}' not found")
        
        return feat
    
    async def search_feats(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for feats by name or description"""
        url = f"{self.BASE_URL}/feats.json"
        data = await self._fetch_json(url)
        
        feats = data.get('feat', [])
        query_lower = query.lower()
        
        matching_feats = []
        for feat in feats:
            if feat.get('source') == 'PHB':  # Skip 2014 PHB content
                continue
                
            # Search in name
            name_match = query_lower in feat.get('name', '').lower()
            
            # Search in description
            desc_match = False
            entries = feat.get('entries', [])
            if isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, str) and query_lower in entry.lower():
                        desc_match = True
                        break
            
            if name_match or desc_match:
                matching_feats.append(feat)
        
        matching_feats = matching_feats[:limit]
        
        return {
            'count': len(matching_feats),
            'results': [{
                'index': feat.get('name', '').lower().replace(' ', '-').replace("'", ""),
                'name': feat.get('name'),
                'source': feat.get('source'),
                'category': feat.get('category', []),
                'prerequisites': feat.get('prerequisite')
            } for feat in matching_feats]
        }
    
    # EQUIPMENT FUNCTIONS  
    async def get_equipment_list(self, item_type: Optional[str] = None, source_filter: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get list of non-magical equipment from all sources except 2014 PHB"""
        url = f"{self.BASE_URL}/items.json"
        data = await self._fetch_json(url)
        
        items = data.get('item', [])
        
        # Filter for non-magical items only (no rarity = mundane equipment)
        equipment = [item for item in items if not item.get('rarity')]
        
        # Filter out 2014 PHB content
        equipment = [item for item in equipment if item.get('source') != 'PHB']
        
        # Filter by item type if specified (weapon, armor, etc.)
        if item_type:
            equipment = [item for item in equipment if self._item_type_matches(item, item_type)]
        
        # Filter by source if specified
        if source_filter:
            equipment = [item for item in equipment if item.get('source', '').lower() == source_filter.lower()]
        
        # Apply limit
        equipment = equipment[:limit]
        
        # Enhance results with MSRP data if available
        enhanced_results = []
        for item in equipment:
            result = {
                'index': item.get('name', '').lower().replace(' ', '-').replace("'", ""),
                'name': item.get('name'),
                'type': item.get('type'),
                'weight': item.get('weight'),
                'value': item.get('value'),
                'source': item.get('source'),
                'properties': item.get('property', []) if item.get('type') in ['M', 'R'] else None  # Melee/Ranged weapons
            }
            
            # Try to add MSRP pricing
            msrp_data = self._get_msrp_data(item.get('name', ''))
            if msrp_data:
                result.update({
                    'msrp_common': msrp_data.get('msrp_common'),
                    'msrp_rare': msrp_data.get('msrp_rare'),
                    'has_msrp_pricing': True
                })
            else:
                result['has_msrp_pricing'] = False
                
            enhanced_results.append(result)
        
        return {
            'count': len(enhanced_results),
            'results': enhanced_results
        }
    
    async def get_equipment_details(self, item_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific equipment item with MSRP pricing"""
        # Try to get 5etools data
        fivetools_item = None
        try:
            url = f"{self.BASE_URL}/items.json"
            data = await self._fetch_json(url)
            items = data.get('item', [])
            
            # Filter for non-magical items only (no rarity = mundane equipment)
            equipment = [item for item in items if not item.get('rarity')]
            
            # Filter out 2014 PHB content
            equipment = [item for item in equipment if item.get('source') != 'PHB']
            
            # Find item by name (case-insensitive)
            for i in equipment:
                if (i.get('name', '').lower() == item_name.lower() or 
                    i.get('name', '').lower().replace(' ', '-').replace("'", "") == item_name.lower()):
                    fivetools_item = i
                    break
        except Exception as e:
            logger.warning(f"Failed to fetch 5etools data for {item_name}: {e}")
        
        # Try to get MSRP data
        msrp_item = self._get_msrp_data(item_name)
        
        # Combine the data
        if fivetools_item and msrp_item:
            # Both sources available - merge them
            combined_item = fivetools_item.copy()
            combined_item.update({
                'msrp_common': msrp_item.get('msrp_common'),
                'msrp_rare': msrp_item.get('msrp_rare'),
                'msrp_rarity': msrp_item.get('rarity'),
                'msrp_source': msrp_item.get('source'),
                'msrp_type': msrp_item.get('type'),
                'msrp_attunement': msrp_item.get('attunement'),
                'data_completeness': 'full',
                'sources_used': ['5etools', 'MSRP'],
                'data_sources': 'Combined 5etools description with MSRP pricing'
            })
            return combined_item
            
        elif fivetools_item:
            # Only 5etools data available
            combined_item = fivetools_item.copy()
            combined_item.update({
                'data_completeness': 'partial',
                'sources_used': ['5etools'],
                'pricing_note': 'No MSRP pricing available - using 5etools value only'
            })
            return combined_item
            
        elif msrp_item:
            # Only MSRP data available
            combined_item = {
                'name': item_name,
                'msrp_common': msrp_item.get('msrp_common'),
                'msrp_rare': msrp_item.get('msrp_rare'),
                'rarity': msrp_item.get('rarity'),
                'source': msrp_item.get('source'),
                'type': msrp_item.get('type'),
                'attunement': msrp_item.get('attunement'),
                'data_completeness': 'partial',
                'sources_used': ['MSRP'],
                'description_note': 'No 5etools description available - MSRP data only'
            }
            return combined_item
        
        # Neither source has the item
        raise ValueError(f"Equipment item '{item_name}' not found in either 5etools or MSRP data")
    
    # MONSTER FUNCTIONS
    async def get_monster_list_5etools(self, cr_range: Optional[List[Union[int, float]]] = None, 
                                     monster_type: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get list of monsters from 5e.tools bestiary files"""
        # Start with Monster Manual
        url = f"{self.BASE_URL}/bestiary/bestiary-mm.json"
        data = await self._fetch_json(url)
        
        monsters = data.get('monster', [])
        
        # Filter by CR range if specified
        if cr_range and len(cr_range) == 2:
            min_cr, max_cr = cr_range
            monsters = [m for m in monsters if self._cr_in_range(m.get('cr'), min_cr, max_cr)]
        
        # Filter by type if specified
        if monster_type:
            monsters = [m for m in monsters if self._monster_type_matches(m.get('type'), monster_type)]
        
        # Apply limit
        monsters = monsters[:limit]
        
        return {
            'count': len(monsters),
            'results': [{
                'index': monster.get('name', '').lower().replace(' ', '-').replace("'", ""),
                'name': monster.get('name'),
                'size': monster.get('size'),
                'type': self._format_monster_type(monster.get('type')),
                'cr': monster.get('cr'),
                'source': monster.get('source')
            } for monster in monsters]
        }
    
    async def get_monster_details_5etools(self, monster_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific monster"""
        # Try Monster Manual first
        url = f"{self.BASE_URL}/bestiary/bestiary-mm.json"
        data = await self._fetch_json(url)
        
        monsters = data.get('monster', [])
        
        # Find monster by name (case-insensitive)
        monster = None
        for m in monsters:
            if (m.get('name', '').lower() == monster_name.lower() or 
                m.get('name', '').lower().replace(' ', '-').replace("'", "") == monster_name.lower()):
                monster = m
                break
        
        if not monster:
            raise ValueError(f"Monster '{monster_name}' not found")
        
        return monster
    
    async def search_monsters_5etools(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search for monsters by name"""
        url = f"{self.BASE_URL}/bestiary/bestiary-mm.json"
        data = await self._fetch_json(url)
        
        monsters = data.get('monster', [])
        query_lower = query.lower()
        
        # Search by name
        matching_monsters = [
            m for m in monsters 
            if query_lower in m.get('name', '').lower()
        ]
        
        matching_monsters = matching_monsters[:limit]
        
        return {
            'count': len(matching_monsters),
            'results': [{
                'index': monster.get('name', '').lower().replace(' ', '-').replace("'", ""),
                'name': monster.get('name'),
                'size': monster.get('size'),
                'type': self._format_monster_type(monster.get('type')),
                'cr': monster.get('cr'),
                'source': monster.get('source')
            } for monster in matching_monsters]
        }
    
    # MAGIC ITEMS FUNCTIONS
    async def get_magic_item_list(self, rarity: Optional[str] = None, item_type: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Get list of magic items"""
        url = f"{self.BASE_URL}/items.json"
        data = await self._fetch_json(url)
        
        items = data.get('item', [])
        
        # Filter magic items only
        magic_items = [item for item in items if item.get('rarity')]
        
        # Filter by rarity if specified
        if rarity:
            magic_items = [item for item in magic_items if item.get('rarity', '').lower() == rarity.lower()]
        
        # Filter by type if specified
        if item_type:
            magic_items = [item for item in magic_items if self._item_type_matches(item, item_type)]
        
        # Apply limit
        magic_items = magic_items[:limit]
        
        # Enhance results with MSRP data if available
        enhanced_results = []
        for item in magic_items:
            result = {
                'index': item.get('name', '').lower().replace(' ', '-').replace("'", ""),
                'name': item.get('name'),
                'type': item.get('type'),
                'rarity': item.get('rarity'),
                'source': item.get('source')
            }
            
            # Try to add MSRP pricing
            msrp_data = self._get_msrp_data(item.get('name', ''))
            if msrp_data:
                result.update({
                    'msrp_common': msrp_data.get('msrp_common'),
                    'msrp_rare': msrp_data.get('msrp_rare'),
                    'has_msrp_pricing': True
                })
            else:
                result['has_msrp_pricing'] = False
                
            enhanced_results.append(result)
        
        return {
            'count': len(enhanced_results),
            'results': enhanced_results
        }
    
    async def get_magic_item_details(self, item_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific magic item with MSRP pricing"""
        # Try to get 5etools data
        fivetools_item = None
        try:
            url = f"{self.BASE_URL}/items.json"
            data = await self._fetch_json(url)
            items = data.get('item', [])
            
            # Find item by name (case-insensitive)
            for i in items:
                if (i.get('name', '').lower() == item_name.lower() or 
                    i.get('name', '').lower().replace(' ', '-').replace("'", "") == item_name.lower()):
                    fivetools_item = i
                    break
        except Exception as e:
            logger.warning(f"Failed to fetch 5etools data for {item_name}: {e}")
        
        # Try to get MSRP data
        msrp_item = self._get_msrp_data(item_name)
        
        # Combine the data
        if fivetools_item and msrp_item:
            # Both sources available - merge them
            combined_item = fivetools_item.copy()
            combined_item.update({
                'msrp_common': msrp_item.get('msrp_common'),
                'msrp_rare': msrp_item.get('msrp_rare'),
                'msrp_rarity': msrp_item.get('rarity'),
                'msrp_source': msrp_item.get('source'),
                'msrp_type': msrp_item.get('type'),
                'msrp_attunement': msrp_item.get('attunement'),
                'data_completeness': 'full',
                'sources_used': ['5etools', 'MSRP'],
                'data_sources': 'Combined 5etools description with MSRP pricing'
            })
            return combined_item
            
        elif fivetools_item:
            # Only 5etools data available
            combined_item = fivetools_item.copy()
            combined_item.update({
                'data_completeness': 'partial',
                'sources_used': ['5etools'],
                'pricing_note': 'No MSRP pricing available - using 5etools rarity only'
            })
            return combined_item
            
        elif msrp_item:
            # Only MSRP data available
            combined_item = {
                'name': item_name,
                'msrp_common': msrp_item.get('msrp_common'),
                'msrp_rare': msrp_item.get('msrp_rare'),
                'rarity': msrp_item.get('rarity'),
                'source': msrp_item.get('source'),
                'type': msrp_item.get('type'),
                'attunement': msrp_item.get('attunement'),
                'data_completeness': 'partial',
                'sources_used': ['MSRP'],
                'description_note': 'No 5etools description available - MSRP data only'
            }
            return combined_item
        
        # Neither source has the item
        raise ValueError(f"Magic item '{item_name}' not found in either 5etools or MSRP data")
    
    # RULES AND CONDITIONS
    async def get_conditions_list(self) -> Dict[str, Any]:
        """Get list of all conditions"""
        url = f"{self.BASE_URL}/conditionsdiseases.json"
        data = await self._fetch_json(url)
        
        conditions = data.get('condition', [])
        
        return {
            'count': len(conditions),
            'results': [{
                'index': condition.get('name', '').lower().replace(' ', '-'),
                'name': condition.get('name'),
                'source': condition.get('source')
            } for condition in conditions]
        }
    
    async def get_condition_details(self, condition_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific condition"""
        url = f"{self.BASE_URL}/conditionsdiseases.json"
        data = await self._fetch_json(url)
        
        conditions = data.get('condition', [])
        
        # Find condition by name (case-insensitive)
        condition = None
        for c in conditions:
            if (c.get('name', '').lower() == condition_name.lower() or 
                c.get('name', '').lower().replace(' ', '-') == condition_name.lower()):
                condition = c
                break
        
        if not condition:
            raise ValueError(f"Condition '{condition_name}' not found")
        
        return condition
    
    async def search_rules(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search across conditions and other rule content"""
        results = []
        
        # Search conditions
        url = f"{self.BASE_URL}/conditionsdiseases.json"
        data = await self._fetch_json(url)
        
        conditions = data.get('condition', [])
        query_lower = query.lower()
        
        for condition in conditions:
            if query_lower in condition.get('name', '').lower():
                results.append({
                    'type': 'condition',
                    'name': condition.get('name'),
                    'index': condition.get('name', '').lower().replace(' ', '-'),
                    'source': condition.get('source')
                })
        
        return {
            'count': len(results[:limit]),
            'results': results[:limit]
        }
    
    # HELPER METHODS
    def _cr_in_range(self, cr, min_cr: Union[int, float], max_cr: Union[int, float]) -> bool:
        """Check if CR is within specified range"""
        if cr is None:
            return False
        
        # Handle 5e.tools CR format which can be dict, string, or number
        cr_value = cr
        if isinstance(cr, dict):
            cr_value = cr.get('cr', cr.get('value', 0))
        
        # Handle fractional CRs
        if isinstance(cr_value, str):
            if cr_value == "1/8":
                cr_num = 0.125
            elif cr_value == "1/4":
                cr_num = 0.25
            elif cr_value == "1/2":
                cr_num = 0.5
            else:
                try:
                    cr_num = float(cr_value)
                except ValueError:
                    return False
        else:
            try:
                cr_num = float(cr_value)
            except (ValueError, TypeError):
                return False
        
        return min_cr <= cr_num <= max_cr
    
    def _monster_type_matches(self, monster_type, type_filter: str) -> bool:
        """Check if monster type matches filter"""
        if isinstance(monster_type, dict):
            return monster_type.get('type', '').lower() == type_filter.lower()
        elif isinstance(monster_type, str):
            return monster_type.lower() == type_filter.lower()
        return False
    
    def _format_monster_type(self, monster_type) -> str:
        """Format monster type for display"""
        if isinstance(monster_type, dict):
            base_type = monster_type.get('type', '')
            subtype = monster_type.get('subtype', '')
            if subtype:
                return f"{base_type} ({subtype})"
            return base_type
        return str(monster_type) if monster_type else ""
    
    def _item_type_matches(self, item: Dict[str, Any], type_filter: str) -> bool:
        """Check if item type matches filter"""
        item_type = item.get('type', '').lower()
        return type_filter.lower() in item_type
    
    def _race_size_matches(self, race_size, size_filter: str) -> bool:
        """Check if race size matches filter"""
        if not race_size:
            return False
        
        # Handle different size formats from 5e.tools
        if isinstance(race_size, list):
            # Multiple sizes
            return any(size.lower() == size_filter.lower() for size in race_size if isinstance(size, str))
        elif isinstance(race_size, str):
            # Single size
            return race_size.lower() == size_filter.lower()
        elif isinstance(race_size, dict):
            # Complex size object
            if 'choose' in race_size:
                choices = race_size['choose'].get('from', [])
                return any(size.lower() == size_filter.lower() for size in choices if isinstance(size, str))
        
        return False
    
    def _format_race_size(self, race_size) -> str:
        """Format race size for display"""
        if not race_size:
            return ""
        
        if isinstance(race_size, list):
            return ", ".join(str(size) for size in race_size)
        elif isinstance(race_size, str):
            return race_size
        elif isinstance(race_size, dict):
            if 'choose' in race_size:
                choices = race_size['choose'].get('from', [])
                return f"Choose from: {', '.join(choices)}"
        
        return str(race_size)
    
    def _get_msrp_data(self, item_name: str) -> Optional[Dict[str, Any]]:
        """Get MSRP pricing data for an item"""
        if not self.msrp_data:
            return None
        
        # Try direct lookup first
        clean_name = item_name.lower().replace("'", "").replace(" ", "-").replace("(", "").replace(")", "").replace(",", "")
        if clean_name in self.msrp_data:
            return self.msrp_data[clean_name]
        
        # Try original name lowercase
        if item_name.lower() in self.msrp_data:
            return self.msrp_data[item_name.lower()]
        
        # Try fuzzy matching
        for stored_name, data in self.msrp_data.items():
            if self._msrp_fuzzy_match(clean_name, stored_name):
                return data
        
        return None
    
    def _msrp_fuzzy_match(self, name1: str, name2: str) -> bool:
        """Simple fuzzy matching for MSRP item names"""
        # Remove common variations
        clean1 = name1.replace("-", "").replace("any", "").replace("weapon", "").replace("armor", "")
        clean2 = name2.replace("-", "").replace("any", "").replace("weapon", "").replace("armor", "")
        
        # Check if core parts match
        words1 = set(clean1.split())
        words2 = set(clean2.split())
        
        # If most significant words overlap, consider it a match
        if len(words1) > 0 and len(words2) > 0:
            overlap = len(words1.intersection(words2))
            return overlap >= min(len(words1), len(words2)) * 0.7
        
        return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()