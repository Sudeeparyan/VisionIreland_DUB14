"""Bedrock vision-based panel analysis module"""

import json
import base64
from typing import Optional, List
from .models import (
    Character,
    Scene,
    PanelNarrative,
    VisualAnalysis,
    DialogueLine,
    BedrockAnalysisContext,
    VoiceProfile,
)
from ..aws_clients import aws_clients


class BedrockPanelAnalyzer:
    """Analyzes comic panels using Bedrock vision capabilities"""

    # Bedrock model IDs
    NOVA_PRO_MODEL = "amazon.nova-pro-v1:0"
    CLAUDE_MODEL = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    def __init__(self, model_id: Optional[str] = None):
        """
        Initialize the analyzer with a specific model.

        Args:
            model_id: Bedrock model ID to use. Defaults to Nova Pro.
        """
        self.model_id = model_id or self.NOVA_PRO_MODEL
        self.bedrock_client = aws_clients.bedrock
        self.context = BedrockAnalysisContext()

    def analyze_panel(
        self, panel_id: str, image_data: str, image_format: str = 'png', context=None
    ) -> dict:
        """
        Analyze a single panel image using Bedrock vision capabilities.

        Args:
            panel_id: Unique identifier for the panel
            image_data: Base64-encoded image data
            image_format: Image format (png, jpeg)
            context: Optional analysis context

        Returns:
            Dictionary with visual analysis results
        """
        # Create vision analysis prompt
        analysis_prompt = self._create_analysis_prompt(context)

        # Call Bedrock with vision capabilities
        visual_analysis = self._call_bedrock_vision(
            image_data, analysis_prompt, image_format
        )

        return visual_analysis

    def _create_analysis_prompt(self, context=None) -> str:
        """Create a prompt for Bedrock to analyze panel visuals"""
        context_info = self._format_context_for_prompt(context)

        prompt = f"""Analyze this comic panel image and provide detailed visual analysis.

Current Story Context:
{context_info}

Please analyze the panel and provide:
1. Characters visible (identify by appearance, note if new or returning)
2. Objects and elements in the scene
3. Spatial layout and positioning of elements
4. Color palette and visual style
5. Emotional tone and mood
6. Scene/location (new or established)
7. Action or movement depicted
8. Any dialogue or text visible in speech bubbles

Format your response as JSON with these exact keys:
{{
    "characters": [
        {{"name": "character name", "visual_description": "appearance", "personality": "inferred personality"}}
    ],
    "objects": ["object list"],
    "spatial_layout": "description of spatial relationships",
    "colors": ["color palette"],
    "mood": "emotional tone",
    "scene": {{
        "location": "location name",
        "visual_description": "scene description",
        "time_of_day": "time if identifiable",
        "atmosphere": "atmosphere/mood",
        "color_palette": ["colors"],
        "lighting": "lighting description"
    }},
    "action_description": "action description",
    "dialogue": [
        {{"character": "character name", "text": "dialogue text", "emotion": "emotion if apparent"}}
    ]
}}"""

        return prompt

    def _call_bedrock_vision(self, image_base64: str, prompt: str, image_format: str = 'png') -> dict:
        """
        Call Bedrock with vision analysis request.

        Args:
            image_base64: Base64-encoded image data
            prompt: Analysis prompt for the model
            image_format: Image format (png, jpeg)

        Returns:
            Dictionary with visual analysis results
        """
        try:
            # Determine media type
            media_type = f"image/{image_format}" if image_format else "image/png"
            
            # Prepare message with image
            message = {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_base64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }

            # Call Bedrock
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=[message],
                inferenceConfig={"maxTokens": 2048, "temperature": 0.7},
            )

            # Extract response text
            response_text = response["output"]["message"]["content"][0]["text"]

            # Parse JSON response
            analysis = json.loads(response_text)
            return analysis

        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return self._create_fallback_analysis()
        except Exception as e:
            raise RuntimeError(f"Bedrock vision analysis failed: {str(e)}")

    def _create_fallback_analysis(self) -> dict:
        """Create a fallback analysis structure if parsing fails"""
        return {
            "characters": [],
            "objects": [],
            "spatial_layout": "Unable to analyze spatial layout",
            "colors": [],
            "mood": "neutral",
            "scene": {
                "location": "Unknown location",
                "visual_description": "Unable to analyze scene",
                "time_of_day": None,
                "atmosphere": None,
                "color_palette": [],
                "lighting": None
            },
            "action_description": "Action unclear",
            "dialogue": [],
        }

    def _format_context_for_prompt(self, context=None) -> str:
        """Format current story context for the analysis prompt"""
        if context is None:
            return "No prior context (first panel)"
        
        context_lines = []

        if context.characters:
            context_lines.append("Known Characters:")
            for char_id, char in context.characters.items():
                context_lines.append(
                    f"  - {char.name}: {char.visual_description}"
                )

        if context.scenes:
            context_lines.append("Known Scenes:")
            for scene_id, scene in context.scenes.items():
                context_lines.append(f"  - {scene.location}: {scene.visual_description}")

        if not context_lines:
            context_lines.append("No prior context (first panel)")

        return "\n".join(context_lines)

    def get_context(self) -> BedrockAnalysisContext:
        """Get current analysis context"""
        return self.context

    def reset_context(self) -> None:
        """Reset analysis context for new comic"""
        self.context = BedrockAnalysisContext()
