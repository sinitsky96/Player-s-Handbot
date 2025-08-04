#!/usr/bin/env python3
"""
MSRP Loader
Loads and parses the Merchant's Sorcerous Rarities Pricelist Excel file
"""

import pandas as pd
import logging
from typing import Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger("msrp-loader")

class MSRPLoader:
    """Loader for MSRP (Merchant's Sorcerous Rarities Pricelist) data"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.items = {}  # Item name -> pricing data
        
    def load_data(self) -> Dict[str, Dict[str, Any]]:
        """Load and parse all magic item pricing data from CSV file"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"MSRP CSV file not found: {self.file_path}")
        
        logger.info(f"Loading MSRP data from {self.file_path}")
        
        try:
            self._load_csv()
        except Exception as e:
            logger.error(f"Failed to load CSV data: {e}")
            raise
        
        logger.info(f"Loaded {len(self.items)} items from MSRP data")
        return self.items
    
    def _load_csv(self):
        """Load data from CSV file"""
        # Read CSV file, skipping the first 5 rows which contain metadata
        # The actual headers are on row 6 (index 5)
        df = pd.read_csv(self.file_path, skiprows=5)
        
        logger.info(f"CSV loaded with {len(df)} rows and {len(df.columns)} columns")
        logger.info(f"First few column names: {list(df.columns[:5])}")
        
        # Find the item column (there's an empty column at the start, so Item is at index 1)
        item_col = 1  # Item column is actually the second column
        
        # Verify we have the expected structure
        if len(df.columns) < 11:
            logger.warning(f"CSV has fewer columns than expected. Found {len(df.columns)} columns")
            return
        
        processed_count = 0
        # Process each row
        for idx, row in df.iterrows():
            try:
                # Get item name from column 1 (second column)
                item_name = row.iloc[item_col] if item_col < len(row) else None
                if pd.isna(item_name) or str(item_name).strip() == '':
                    continue
                
                item_name = str(item_name).strip()
                
                # Skip header rows
                if item_name.lower() in ['item', 'nan']:
                    continue
                
                # Extract pricing and metadata from subsequent columns
                # CSV structure: [empty], Item, MSRP (common), MSRP (rare), Sane Price, DMPG Price, XGE Price, Rarity, Source, Page, Type, Attunement
                # Indices:       0        1     2              3             4           5           6          7       8       9     10    11
                item_data = {
                    'sheet_source': 'CSV',
                    'msrp_common': self._safe_price(row.iloc[2] if len(row) > 2 else None),
                    'msrp_rare': self._safe_price(row.iloc[3] if len(row) > 3 else None),
                    'rarity': self._safe_string(row.iloc[7] if len(row) > 7 else None),
                    'source': self._safe_string(row.iloc[8] if len(row) > 8 else None),
                    'type': self._safe_string(row.iloc[10] if len(row) > 10 else None),
                    'attunement': self._safe_string(row.iloc[11] if len(row) > 11 else None)
                }
                
                # Clean up the item name for consistent lookup
                clean_name = self._normalize_item_name(item_name)
                
                # Store both original and normalized names for lookup
                self.items[clean_name] = item_data
                if clean_name != item_name.lower():
                    self.items[item_name.lower()] = item_data
                
                processed_count += 1
                if processed_count <= 5:  # Log first few items for debugging
                    logger.info(f"Processed item: {item_name} -> {clean_name}")
                
            except Exception as e:
                logger.debug(f"Error processing row {idx} in CSV: {e}")
                continue
        
        logger.info(f"Successfully processed {processed_count} items")
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if pd.isna(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_price(self, value) -> Optional[float]:
        """Safely convert price string to float (e.g., '75 gp' -> 75.0)"""
        if pd.isna(value):
            return None
        try:
            # Convert to string and remove 'gp' and other currency indicators
            price_str = str(value).lower().replace('gp', '').replace(',', '').strip()
            return float(price_str)
        except (ValueError, TypeError):
            return None
    
    def _safe_string(self, value) -> Optional[str]:
        """Safely convert value to string"""
        if pd.isna(value):
            return None
        return str(value).strip()
    
    def _normalize_item_name(self, name: str) -> str:
        """Normalize item name for consistent lookup"""
        return name.lower().replace("'", "").replace(" ", "-").replace("(", "").replace(")", "").replace(",", "")
    
    def get_item_data(self, item_name: str) -> Optional[Dict[str, Any]]:
        """Get pricing data for a specific item"""
        # Try exact match first
        clean_name = self._normalize_item_name(item_name)
        if clean_name in self.items:
            return self.items[clean_name]
        
        # Try original name lowercase
        if item_name.lower() in self.items:
            return self.items[item_name.lower()]
        
        # Try partial matches (for cases like "Weapon, +1" vs "+1 Weapon")
        for stored_name, data in self.items.items():
            if self._fuzzy_match(clean_name, stored_name):
                return data
        
        return None
    
    def _fuzzy_match(self, name1: str, name2: str) -> bool:
        """Simple fuzzy matching for item names"""
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

def load_msrp_data(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Convenience function to load MSRP data"""
    loader = MSRPLoader(file_path)
    return loader.load_data()