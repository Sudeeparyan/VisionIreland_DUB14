"""
Comic Parser - Creates a structured comic book representation for narration
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class Character:
    """Represents a character in the comic."""

    name: str
    description: str
    voice_style: str = "neutral"  # neutral, excited, sad, angry, whisper, etc.
    appearances: List[int] = None  # Page numbers where character appears

    def __post_init__(self):
        if self.appearances is None:
            self.appearances = []


@dataclass
class Panel:
    """Represents a single panel in a comic page."""

    panel_number: int
    description: str
    dialogue: List[Dict]  # [{"character": "...", "text": "...", "tone": "..."}]
    sound_effects: List[str]
    action: str


@dataclass
class Page:
    """Represents a comic page."""

    page_number: int
    setting: str
    panels: List[Panel]
    narration_script: str
    action_summary: str
    characters_present: List[str]
    image_base64: Optional[str] = None


@dataclass
class Comic:
    """Represents a complete comic book."""

    title: str
    author: str
    page_count: int
    characters: Dict[str, Character]
    pages: List[Page]
    synopsis: str = ""


class ComicParser:
    """
    Parses analyzed comic data into a structured format
    suitable for voice narration.
    """

    def __init__(self):
        """Initialize the parser."""
        self.comic: Optional[Comic] = None
        self.character_registry: Dict[str, Character] = {}

    def parse_from_analysis(
        self, metadata: Dict, pages_data: List[Dict], analysis_results: List[Dict]
    ) -> Comic:
        """
        Create a Comic object from PDF extraction and analysis results.

        Args:
            metadata: PDF metadata
            pages_data: Raw page data from PDF extractor
            analysis_results: Analysis from ComicAnalyzer

        Returns:
            Structured Comic object
        """
        # Create page objects
        pages = []

        for i, analysis in enumerate(analysis_results):
            if not analysis.get("success"):
                continue

            parsed = analysis.get("parsed", {})
            page_data = pages_data[i] if i < len(pages_data) else {}

            # Extract panels from parsed data
            panels = self._parse_panels(parsed.get("panels", ""))

            # Extract characters
            self._extract_characters(parsed.get("characters", ""))

            page = Page(
                page_number=analysis["page_number"],
                setting=parsed.get("scene_setting", ""),
                panels=panels,
                narration_script=parsed.get("narration_script", ""),
                action_summary=parsed.get("action_summary", ""),
                characters_present=self._get_characters_on_page(parsed),
                image_base64=page_data.get("image_base64"),
            )
            pages.append(page)

        # Create the comic object
        self.comic = Comic(
            title=metadata.get("title", "Unknown Comic"),
            author=metadata.get("author", "Unknown Author"),
            page_count=metadata.get("page_count", len(pages)),
            characters=self.character_registry,
            pages=pages,
            synopsis=self._generate_synopsis(pages),
        )

        return self.comic

    def _parse_panels(self, panels_text: str) -> List[Panel]:
        """
        Parse panel descriptions from analysis text.

        Args:
            panels_text: Raw panels description

        Returns:
            List of Panel objects
        """
        panels = []

        if not panels_text:
            return panels

        # Simple parsing - split by panel numbers
        panel_chunks = []
        current_chunk = []

        for line in panels_text.split("\n"):
            if any(f"panel {i}" in line.lower() for i in range(1, 20)):
                if current_chunk:
                    panel_chunks.append("\n".join(current_chunk))
                current_chunk = [line]
            else:
                current_chunk.append(line)

        if current_chunk:
            panel_chunks.append("\n".join(current_chunk))

        # Create Panel objects
        for i, chunk in enumerate(panel_chunks):
            panel = Panel(
                panel_number=i + 1,
                description=chunk,
                dialogue=self._extract_dialogue(chunk),
                sound_effects=self._extract_sound_effects(chunk),
                action=self._extract_action(chunk),
            )
            panels.append(panel)

        return panels

    def _extract_dialogue(self, text: str) -> List[Dict]:
        """Extract dialogue from panel description."""
        dialogue = []

        # Look for quoted text or dialogue indicators
        import re

        # Pattern for "Character: dialogue" or "Character says 'dialogue'"
        patterns = [
            r'"([^"]+)"',  # Quoted text
            r"'([^']+)'",  # Single quoted text
            r"([A-Z][a-z]+):\s*(.+)",  # Character: dialogue
        ]

        for pattern in patterns[:2]:
            matches = re.findall(pattern, text)
            for match in matches:
                dialogue.append(
                    {"character": "Unknown", "text": match, "tone": "normal"}
                )

        # Named character dialogue
        char_matches = re.findall(patterns[2], text)
        for char, line in char_matches:
            dialogue.append({"character": char, "text": line.strip(), "tone": "normal"})

        return dialogue

    def _extract_sound_effects(self, text: str) -> List[str]:
        """Extract sound effects from panel description."""
        effects = []

        # Common comic sound effect patterns
        import re

        # Look for ALL CAPS words that might be sound effects
        caps_words = re.findall(r"\b([A-Z]{2,}!*)\b", text)

        # Common sound effects
        common_sfx = [
            "BOOM",
            "BAM",
            "POW",
            "CRASH",
            "BANG",
            "WHOOSH",
            "SLAM",
            "CRACK",
            "THUD",
            "SPLASH",
            "ZOOM",
            "ZAP",
            "WHAM",
            "KABOOM",
            "SWOOSH",
            "THWACK",
            "CRUNCH",
            "SNAP",
            "POP",
            "DING",
            "RING",
        ]

        for word in caps_words:
            clean_word = word.rstrip("!")
            if clean_word in common_sfx or len(clean_word) <= 6:
                effects.append(word)

        return effects

    def _extract_action(self, text: str) -> str:
        """Extract main action from panel description."""
        # Get the first sentence or main action line
        sentences = text.split(".")
        if sentences:
            return sentences[0].strip()
        return text[:100] if len(text) > 100 else text

    def _extract_characters(self, characters_text: str):
        """Extract and register characters from analysis."""
        if not characters_text:
            return

        # Simple extraction - look for names/descriptions
        import re

        # Look for character names (capitalized words at start of lines or after bullets)
        lines = characters_text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove bullet points
            line = re.sub(r"^[-*•]\s*", "", line)

            # First word might be character name
            words = line.split()
            if words:
                name = words[0].rstrip(":")
                if name and name[0].isupper() and name not in self.character_registry:
                    self.character_registry[name] = Character(
                        name=name, description=line, voice_style="neutral"
                    )

    def _get_characters_on_page(self, parsed: Dict) -> List[str]:
        """Get list of character names appearing on a page."""
        characters = []

        char_text = parsed.get("characters", "")
        for name in self.character_registry.keys():
            if name.lower() in char_text.lower():
                characters.append(name)

        return characters

    def _generate_synopsis(self, pages: List[Page]) -> str:
        """Generate a brief synopsis of the comic."""
        summaries = [p.action_summary for p in pages if p.action_summary]

        if not summaries:
            return "A comic book story waiting to be explored."

        # Combine first and last summary for synopsis
        if len(summaries) == 1:
            return summaries[0]

        return f"{summaries[0]} ... {summaries[-1]}"

    def to_dict(self) -> Dict:
        """Convert the comic to a dictionary."""
        if not self.comic:
            return {}

        return {
            "title": self.comic.title,
            "author": self.comic.author,
            "page_count": self.comic.page_count,
            "synopsis": self.comic.synopsis,
            "characters": {
                name: asdict(char) for name, char in self.comic.characters.items()
            },
            "pages": [
                {
                    "page_number": p.page_number,
                    "setting": p.setting,
                    "narration_script": p.narration_script,
                    "action_summary": p.action_summary,
                    "characters_present": p.characters_present,
                    "panels": [asdict(panel) for panel in p.panels],
                }
                for p in self.comic.pages
            ],
        }

    def save_to_file(self, filepath: str):
        """Save the parsed comic to a JSON file."""
        data = self.to_dict()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: str) -> Optional["ComicParser"]:
        """Load a parsed comic from a JSON file."""
        parser = cls()

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct the Comic object
            characters = {
                name: Character(**char_data)
                for name, char_data in data.get("characters", {}).items()
            }

            pages = []
            for page_data in data.get("pages", []):
                panels = [
                    Panel(**panel_data) for panel_data in page_data.get("panels", [])
                ]
                page = Page(
                    page_number=page_data["page_number"],
                    setting=page_data.get("setting", ""),
                    panels=panels,
                    narration_script=page_data.get("narration_script", ""),
                    action_summary=page_data.get("action_summary", ""),
                    characters_present=page_data.get("characters_present", []),
                )
                pages.append(page)

            parser.comic = Comic(
                title=data.get("title", "Unknown"),
                author=data.get("author", "Unknown"),
                page_count=data.get("page_count", len(pages)),
                characters=characters,
                pages=pages,
                synopsis=data.get("synopsis", ""),
            )
            parser.character_registry = characters

            return parser

        except Exception as e:
            print(f"Error loading comic from file: {e}")
            return None

    def get_page(self, page_number: int) -> Optional[Page]:
        """Get a specific page by number."""
        if not self.comic:
            return None

        for page in self.comic.pages:
            if page.page_number == page_number:
                return page
        return None

    def get_narration(self, page_number: int) -> str:
        """Get the narration script for a specific page."""
        page = self.get_page(page_number)
        if page:
            return page.narration_script
        return ""
