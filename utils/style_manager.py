"""
Style Manager - Load and manage style guides from JSON.
Prevents "style bleed" by isolating each persona.
"""

import json
import os
from pathlib import Path


class StyleManager:
    """Load and retrieve style guides for BBC or Taylor Swift."""
    
    def __init__(self, style_guides_path: str = "../artifact/style_guides.json"):
        """
        Initialize StyleManager with path to style guides JSON.
        
        Args:
            style_guides_path: Path to the style_guides.json file
        """
        self.style_guides_path = style_guides_path
        self.style_guides = self._load_style_guides()
    
    def _load_style_guides(self) -> dict:
        """Load style guides from JSON file."""
        if not os.path.exists(self.style_guides_path):
            raise FileNotFoundError(f"Style guides not found at: {self.style_guides_path}")
        
        with open(self.style_guides_path, 'r') as f:
            return json.load(f)
    
    def get_style(self, source_type: str) -> str:
        """
        Get the style guide for a specific source type.
        
        Args:
            source_type: Either "bbc" or "taylor_swift"
            
        Returns:
            The style guide as a JSON string
        """
        source_type = source_type.lower()
        
        if source_type not in self.style_guides:
            raise ValueError(f"Unknown source type: {source_type}. Use 'bbc' or 'taylor_swift'")
        
        style = self.style_guides[source_type]
        
        # If it's already a string, return it
        if isinstance(style, str):
            return style
        
        # If it's a dict, convert to formatted JSON string
        return json.dumps(style, indent=2)
    
    def get_style_dict(self, source_type: str) -> dict:
        """
        Get the style guide as a dictionary.
        
        Args:
            source_type: Either "bbc" or "taylor_swift"
            
        Returns:
            The style guide as a dictionary
        """
        source_type = source_type.lower()
        
        if source_type not in self.style_guides:
            raise ValueError(f"Unknown source type: {source_type}. Use 'bbc' or 'taylor_swift'")
        
        style = self.style_guides[source_type]
        
        # If it's a string, parse it
        if isinstance(style, str):
            return json.loads(style)
        
        return style
    
    def get_key_phrases(self, source_type: str) -> list:
        """Get the key phrases for a specific source type."""
        style_dict = self.get_style_dict(source_type)
        return style_dict.get("Key Phrases", [])
    
    def get_tone(self, source_type: str) -> str:
        """Get the tone description for a specific source type."""
        style_dict = self.get_style_dict(source_type)
        return style_dict.get("Tone", "")
    
    def get_structure(self, source_type: str) -> str:
        """Get the structure description for a specific source type."""
        style_dict = self.get_style_dict(source_type)
        return style_dict.get("Structure", "")
    
    def reload(self):
        """Reload style guides from file."""
        self.style_guides = self._load_style_guides()


# Convenience function for quick access
def get_style(source_type: str, style_guides_path: str = "../artifact/style_guides.json") -> str:
    """
    Quick function to get style guide.
    
    Args:
        source_type: "bbc" or "taylor_swift"
        style_guides_path: Path to style guides JSON
        
    Returns:
        Style guide as JSON string
    """
    manager = StyleManager(style_guides_path)
    return manager.get_style(source_type)
