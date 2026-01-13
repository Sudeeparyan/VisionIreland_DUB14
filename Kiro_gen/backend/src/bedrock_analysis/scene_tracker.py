"""Scene detection and context management for comic panels."""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from .models import Scene

logger = logging.getLogger(__name__)


@dataclass
class SceneChange:
    """Record of a scene change between panels."""
    from_scene_id: Optional[str]
    to_scene_id: str
    panel_number: int
    reason: str = "Scene change detected"


class SceneTracker:
    """Tracks scene detection and context across panels."""

    def __init__(self):
        """Initialize scene tracker."""
        self.scenes: Dict[str, Scene] = {}
        self.scene_counter = 0
        self.scene_changes: List[SceneChange] = []
        self.current_scene_id: Optional[str] = None

    def register_scene(
        self,
        location: str,
        visual_description: str,
        panel_number: int,
        time_of_day: Optional[str] = None,
        atmosphere: Optional[str] = None,
        color_palette: Optional[List[str]] = None,
        lighting: Optional[str] = None
    ) -> Scene:
        """Register a new scene.
        
        Args:
            location: Scene location/setting name
            visual_description: Description of scene appearance
            panel_number: Panel where scene first appears
            time_of_day: Time of day (morning, afternoon, etc.)
            atmosphere: Scene atmosphere/mood
            color_palette: Colors present in scene
            lighting: Lighting description
            
        Returns:
            Scene object
        """
        scene_id = f"scene_{self.scene_counter}"
        self.scene_counter += 1
        
        scene = Scene(
            id=scene_id,
            location=location,
            visual_description=visual_description,
            time_of_day=time_of_day,
            atmosphere=atmosphere,
            color_palette=color_palette or [],
            lighting=lighting,
            first_introduced=panel_number,
            last_seen=panel_number
        )
        
        self.scenes[scene_id] = scene
        logger.info(f"Registered new scene: {location} (ID: {scene_id})")
        
        return scene

    def set_scene_for_panel(
        self,
        scene_id: str,
        panel_number: int,
        visual_description: Optional[str] = None
    ) -> Optional[Scene]:
        """Set the scene for a panel.
        
        Args:
            scene_id: ID of scene
            panel_number: Panel number
            visual_description: Updated visual description if changed
            
        Returns:
            Scene object, or None if scene not found
        """
        if scene_id not in self.scenes:
            logger.warning(f"Scene {scene_id} not found")
            return None
        
        scene = self.scenes[scene_id]
        scene.last_seen = panel_number
        
        # Update visual description if provided
        if visual_description:
            scene.visual_description = visual_description
        
        # Track scene change if different from current
        if self.current_scene_id != scene_id:
            change = SceneChange(
                from_scene_id=self.current_scene_id,
                to_scene_id=scene_id,
                panel_number=panel_number,
                reason="Scene change detected"
            )
            self.scene_changes.append(change)
            self.current_scene_id = scene_id
            logger.info(f"Scene changed to {scene.location} in panel {panel_number}")
        
        return scene

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """Get scene by ID.
        
        Args:
            scene_id: Scene ID
            
        Returns:
            Scene object, or None if not found
        """
        return self.scenes.get(scene_id)

    def get_scene_by_location(self, location: str) -> Optional[Scene]:
        """Get scene by location name.
        
        Args:
            location: Location name
            
        Returns:
            Scene object, or None if not found
        """
        for scene in self.scenes.values():
            if scene.location.lower() == location.lower():
                return scene
        return None

    def get_all_scenes(self) -> List[Scene]:
        """Get all registered scenes.
        
        Returns:
            List of Scene objects
        """
        return list(self.scenes.values())

    def get_scenes_in_panel_range(self, start_panel: int, end_panel: int) -> List[Scene]:
        """Get all scenes appearing in a panel range.
        
        Args:
            start_panel: Starting panel number
            end_panel: Ending panel number
            
        Returns:
            List of Scene objects
        """
        return [
            scene for scene in self.scenes.values()
            if scene.first_introduced <= end_panel and scene.last_seen >= start_panel
        ]

    def get_scene_changes(self) -> List[SceneChange]:
        """Get all scene changes.
        
        Returns:
            List of SceneChange objects
        """
        return self.scene_changes.copy()

    def get_scene_changes_in_range(self, start_panel: int, end_panel: int) -> List[SceneChange]:
        """Get scene changes in a panel range.
        
        Args:
            start_panel: Starting panel number
            end_panel: Ending panel number
            
        Returns:
            List of SceneChange objects
        """
        return [
            change for change in self.scene_changes
            if start_panel <= change.panel_number <= end_panel
        ]

    def is_scene_introduced(self, scene_id: str, panel_number: int) -> bool:
        """Check if scene has been introduced by a given panel.
        
        Args:
            scene_id: Scene ID
            panel_number: Panel number to check
            
        Returns:
            True if scene introduced by this panel
        """
        if scene_id not in self.scenes:
            return False
        
        scene = self.scenes[scene_id]
        return scene.first_introduced <= panel_number

    def get_introduced_scenes(self, panel_number: int) -> List[Scene]:
        """Get all scenes introduced up to a given panel.
        
        Args:
            panel_number: Panel number
            
        Returns:
            List of Scene objects
        """
        return [
            scene for scene in self.scenes.values()
            if scene.first_introduced <= panel_number
        ]

    def get_new_scenes_in_panel(self, panel_number: int) -> List[Scene]:
        """Get scenes first appearing in a specific panel.
        
        Args:
            panel_number: Panel number
            
        Returns:
            List of Scene objects
        """
        return [
            scene for scene in self.scenes.values()
            if scene.first_introduced == panel_number
        ]

    def update_scene_atmosphere(self, scene_id: str, atmosphere: str) -> bool:
        """Update scene atmosphere/mood.
        
        Args:
            scene_id: Scene ID
            atmosphere: New atmosphere description
            
        Returns:
            True if update successful
        """
        if scene_id not in self.scenes:
            logger.warning(f"Scene {scene_id} not found")
            return False
        
        self.scenes[scene_id].atmosphere = atmosphere
        logger.info(f"Updated atmosphere for scene {scene_id}")
        return True

    def add_color_to_palette(self, scene_id: str, color: str) -> bool:
        """Add color to scene's color palette.
        
        Args:
            scene_id: Scene ID
            color: Color description
            
        Returns:
            True if added successfully
        """
        if scene_id not in self.scenes:
            logger.warning(f"Scene {scene_id} not found")
            return False
        
        scene = self.scenes[scene_id]
        if color not in scene.color_palette:
            scene.color_palette.append(color)
            logger.info(f"Added color to scene {scene_id}")
        
        return True

    def get_scene_summary(self, scene_id: str) -> Optional[Dict]:
        """Get summary information about a scene.
        
        Args:
            scene_id: Scene ID
            
        Returns:
            Dictionary with scene summary, or None if not found
        """
        if scene_id not in self.scenes:
            return None
        
        scene = self.scenes[scene_id]
        
        return {
            'id': scene.id,
            'location': scene.location,
            'visual_description': scene.visual_description,
            'time_of_day': scene.time_of_day,
            'atmosphere': scene.atmosphere,
            'color_palette': scene.color_palette,
            'lighting': scene.lighting,
            'first_introduced': scene.first_introduced,
            'last_seen': scene.last_seen,
            'appearance_span': scene.last_seen - scene.first_introduced + 1,
        }

    def get_current_scene(self) -> Optional[Scene]:
        """Get the current scene.
        
        Returns:
            Current Scene object, or None if no scene set
        """
        if self.current_scene_id is None:
            return None
        return self.scenes.get(self.current_scene_id)

    def reset(self) -> None:
        """Reset tracker for new comic."""
        self.scenes.clear()
        self.scene_changes.clear()
        self.current_scene_id = None
        self.scene_counter = 0
        logger.info("Scene tracker reset")
