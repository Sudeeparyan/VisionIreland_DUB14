"""
Comic Analyzer - Uses Gemini Vision to analyze comic book pages
Provides detailed descriptions for blind users
"""

import base64
from typing import Dict, List, Optional
from google import genai
from google.genai import types
from ..config import GOOGLE_API_KEY, VISION_MODEL


class ComicAnalyzer:
    """
    Analyzes comic book pages using Gemini Vision API.
    Extracts:
    - Scene descriptions
    - Character identification
    - Dialogue/speech bubbles
    - Action descriptions
    - Emotional context
    """

    def __init__(self):
        """Initialize the analyzer with Gemini client."""
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.model = VISION_MODEL

    async def analyze_page(
        self,
        image_base64: str,
        page_number: int,
        context: Optional[str] = None,
        child_mode: bool = False,
    ) -> Dict:
        """
        Analyze a comic page image.

        Args:
            image_base64: Base64 encoded image
            page_number: Page number for context
            context: Optional previous page context
            child_mode: If True, use simpler language

        Returns:
            Dictionary with analysis results
        """

        # Build the analysis prompt
        language_instruction = ""
        if child_mode:
            language_instruction = """
            IMPORTANT: Use simple words that a 6-year-old can understand.
            Keep descriptions short and fun.
            Use friendly, encouraging language.
            """

        context_instruction = ""
        if context:
            context_instruction = f"""
            Previous page context: {context}
            Continue the story from where we left off.
            """

        analysis_prompt = f"""You are an expert comic book narrator for blind people and children.
        
        Analyze this comic book page (Page {page_number}) and provide:
        
        {language_instruction}
        {context_instruction}
        
        1. **SCENE_SETTING**: Describe where the scene takes place (location, time of day, atmosphere)
        
        2. **CHARACTERS**: List each character visible with:
           - Name (if identifiable) or description
           - What they look like (clothing, expression, pose)
           - What they seem to be feeling
        
        3. **PANELS**: For each panel on the page (from top-left to bottom-right):
           - Panel number
           - What's happening in the panel
           - Any dialogue or speech bubbles (with speaker identified)
           - Sound effects shown
           - Important visual details
        
        4. **ACTION_SUMMARY**: A brief summary of what happens on this page
        
        5. **NARRATION_SCRIPT**: Write a complete narration script that I can read aloud, including:
           - Scene descriptions
           - Dialogue with character names (use different tones: "said excitedly", "whispered", etc.)
           - Sound effects written as words
           - Dramatic pauses indicated with [PAUSE]
           - This should bring the page to life for someone who cannot see it
        
        6. **CLIFFHANGER**: If this page ends with suspense, describe what question it leaves
        
        Format your response as a structured analysis that can be parsed.
        Be vivid and engaging - you're bringing visual art to life through words!
        """

        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)

            # Create the content with image
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(
                                data=image_data, mime_type="image/png"
                            ),
                            types.Part.from_text(text=analysis_prompt),
                        ]
                    )
                ],
            )

            # Parse the response
            analysis_text = response.text

            return {
                "page_number": page_number,
                "raw_analysis": analysis_text,
                "parsed": self._parse_analysis(analysis_text),
                "success": True,
            }

        except Exception as e:
            print(f"Error analyzing page {page_number}: {e}")
            return {"page_number": page_number, "error": str(e), "success": False}

    def _parse_analysis(self, analysis_text: str) -> Dict:
        """
        Parse the analysis text into structured data.

        Args:
            analysis_text: Raw analysis from Gemini

        Returns:
            Parsed dictionary with sections
        """
        sections = {
            "scene_setting": "",
            "characters": [],
            "panels": [],
            "action_summary": "",
            "narration_script": "",
            "cliffhanger": "",
        }

        # Simple parsing - look for section headers
        current_section = None
        current_content = []

        for line in analysis_text.split("\n"):
            line_lower = line.lower().strip()

            if "scene_setting" in line_lower or "scene setting" in line_lower:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "scene_setting"
                current_content = []
            elif "characters" in line_lower and "**" in line:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "characters"
                current_content = []
            elif "panels" in line_lower and "**" in line:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "panels"
                current_content = []
            elif "action_summary" in line_lower or "action summary" in line_lower:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "action_summary"
                current_content = []
            elif "narration_script" in line_lower or "narration script" in line_lower:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "narration_script"
                current_content = []
            elif "cliffhanger" in line_lower and "**" in line:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "cliffhanger"
                current_content = []
            elif current_section:
                current_content.append(line)

        # Don't forget the last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

        # If parsing didn't work well, use the full text as narration
        if not sections["narration_script"]:
            sections["narration_script"] = analysis_text

        return sections

    async def analyze_comic(
        self, pages: List[Dict], child_mode: bool = False
    ) -> List[Dict]:
        """
        Analyze all pages of a comic.

        Args:
            pages: List of page data dictionaries with image_base64
            child_mode: If True, use simpler language

        Returns:
            List of analysis results
        """
        results = []
        context = None

        for page in pages:
            if page.get("image_base64"):
                analysis = await self.analyze_page(
                    image_base64=page["image_base64"],
                    page_number=page["page_number"],
                    context=context,
                    child_mode=child_mode,
                )
                results.append(analysis)

                # Update context for next page
                if analysis.get("success") and analysis.get("parsed"):
                    context = analysis["parsed"].get("action_summary", "")

        return results

    async def describe_panel(
        self, image_base64: str, detail_level: str = "full"
    ) -> str:
        """
        Get a quick description of a specific panel or image.

        Args:
            image_base64: Base64 encoded image
            detail_level: "brief", "standard", or "full"

        Returns:
            Description string
        """
        detail_prompts = {
            "brief": "In one sentence, describe what's happening in this comic panel.",
            "standard": "Describe this comic panel in 2-3 sentences, mentioning characters, action, and any dialogue.",
            "full": "Provide a detailed description of this comic panel for a blind person, including all visual elements, expressions, dialogue, and atmosphere.",
        }

        prompt = detail_prompts.get(detail_level, detail_prompts["standard"])

        try:
            image_data = base64.b64decode(image_base64)

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(
                                data=image_data, mime_type="image/png"
                            ),
                            types.Part.from_text(prompt),
                        ]
                    )
                ],
            )

            return response.text

        except Exception as e:
            return f"Unable to describe this panel: {str(e)}"
