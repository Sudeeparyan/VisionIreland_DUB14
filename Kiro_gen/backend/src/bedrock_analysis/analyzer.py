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
        self, panel_id: str, image_data: bytes, sequence_number: int
    ) -> PanelNarrative:
        """
        Analyze a single panel image using Bedrock vision capabilities.

        Args:
            panel_id: Unique identifier for the panel
            image_data: Raw image bytes of the panel
            sequence_number: Sequential position of panel in comic

        Returns:
            PanelNarrative with visual analysis and generated description
        """
        # Encode image to base64 for Bedrock
        image_base64 = base64.standard_b64encode(image_data).decode("utf-8")

        # Create vision analysis prompt
        analysis_prompt = self._create_analysis_prompt(sequence_number)

        # Call Bedrock with vision capabilities
        visual_analysis = self._call_bedrock_vision(
            image_base64, analysis_prompt
        )

        # Generate narrative based on visual analysis
        narrative = self._generate_narrative(
            panel_id, visual_analysis, sequence_number
        )

        return narrative

    def _create_analysis_prompt(self, sequence_number: int) -> str:
        """Create a prompt for Bedrock to analyze panel visuals"""
        context_info = self._format_context_for_prompt()

        prompt = f"""Analyze this comic panel image and provide detailed visual analysis.

Panel Position: {sequence_number}

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
    "characters": ["character descriptions"],
    "objects": ["object list"],
    "spatial_layout": "description of spatial relationships",
    "colors": ["color palette"],
    "mood": "emotional tone",
    "scene": "location description",
    "action": "action description",
    "dialogue": ["dialogue text from speech bubbles"]
}}"""

        return prompt

    def _call_bedrock_vision(self, image_base64: str, prompt: str) -> dict:
        """
        Call Bedrock with vision analysis request.

        Args:
            image_base64: Base64-encoded image data
            prompt: Analysis prompt for the model

        Returns:
            Dictionary with visual analysis results
        """
        try:
            # Prepare message with image
            message = {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
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
            "scene": "Unknown location",
            "action": "Action unclear",
            "dialogue": [],
        }

    def _format_context_for_prompt(self) -> str:
        """Format current story context for the analysis prompt"""
        context_lines = []

        if self.context.characters:
            context_lines.append("Known Characters:")
            for char_id, char in self.context.characters.items():
                context_lines.append(
                    f"  - {char.name}: {char.visual_description}"
                )

        if self.context.scenes:
            context_lines.append("Known Scenes:")
            for scene_id, scene in self.context.scenes.items():
                context_lines.append(f"  - {scene.location}: {scene.visual_description}")

        if not context_lines:
            context_lines.append("No prior context (first panel)")

        return "\n".join(context_lines)

    def _generate_narrative(
        self, panel_id: str, visual_analysis: dict, sequence_number: int
    ) -> PanelNarrative:
        """
        Generate narrative from visual analysis results.

        Args:
            panel_id: Panel identifier
            visual_analysis: Results from Bedrock vision analysis
            sequence_number: Panel position in comic

        Returns:
            PanelNarrative with generated description
        """
        # Create VisualAnalysis object
        visual = VisualAnalysis(
            characters=visual_analysis.get("characters", []),
            objects=visual_analysis.get("objects", []),
            spatial_layout=visual_analysis.get("spatial_layout", ""),
            colors=visual_analysis.get("colors", []),
            mood=visual_analysis.get("mood", "neutral"),
        )

        # Extract dialogue
        dialogue_lines = []
        for dialogue_text in visual_analysis.get("dialogue", []):
            dialogue_lines.append(
                DialogueLine(character_id="unknown", text=dialogue_text)
            )

        # Create narrative
        narrative = PanelNarrative(
            panel_id=panel_id,
            visual_analysis=visual,
            action_description=visual_analysis.get("action", ""),
            dialogue=dialogue_lines,
            scene_description=visual_analysis.get("scene"),
        )

        # Generate full audio description
        narrative.audio_description = self._compose_audio_description(
            narrative, sequence_number
        )

        return narrative

    def _compose_audio_description(
        self, narrative: PanelNarrative, sequence_number: int
    ) -> str:
        """
        Compose professional audio description from narrative components.

        Args:
            narrative: Panel narrative with visual analysis
            sequence_number: Panel position

        Returns:
            Professional audio description text
        """
        description_parts = []

        # Add scene description if new scene
        if narrative.scene_description:
            description_parts.append(narrative.scene_description)

        # Add action description
        if narrative.action_description:
            description_parts.append(narrative.action_description)

        # Add dialogue
        for dialogue in narrative.dialogue:
            description_parts.append(f'"{dialogue.text}"')

        return " ".join(description_parts)

    def update_context(self, narrative: PanelNarrative) -> None:
        """
        Update analysis context based on panel narrative.

        Args:
            narrative: Panel narrative to incorporate into context
        """
        # Update character context
        for character_update in narrative.character_updates:
            self.context.characters[character_update.id] = character_update

        # Update scene context
        if narrative.scene_description:
            # Scene tracking would be implemented here
            pass

    def get_context(self) -> BedrockAnalysisContext:
        """Get current analysis context"""
        return self.context

    def reset_context(self) -> None:
        """Reset analysis context for new comic"""
        self.context = BedrockAnalysisContext()
