"""Fallback mechanisms for service failures."""

import logging
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
import asyncio

from ..config import settings

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """Available fallback strategies."""
    ALTERNATIVE_MODEL = "alternative_model"
    ALTERNATIVE_VOICE = "alternative_voice"
    CACHED_RESPONSE = "cached_response"
    SIMPLIFIED_PROCESSING = "simplified_processing"
    GRACEFUL_DEGRADATION = "graceful_degradation"


class FallbackHandler:
    """Handles fallback mechanisms when primary services fail."""
    
    def __init__(self):
        """Initialize fallback handler."""
        self.fallback_models = {
            "bedrock": [
                "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                "us.anthropic.claude-3-haiku-20240307-v1:0",
                "amazon.nova-pro-v1:0",
                "amazon.nova-lite-v1:0"
            ]
        }
        
        self.fallback_voices = {
            "neural": [
                "Joanna", "Matthew", "Amy", "Brian", "Emma", "Justin"
            ],
            "standard": [
                "Joanna", "Matthew", "Amy", "Brian", "Kimberly", "Kendra"
            ]
        }
        
        self.cache = {}
        self.fallback_stats = {
            "bedrock_fallbacks": 0,
            "polly_fallbacks": 0,
            "s3_fallbacks": 0,
            "total_fallbacks": 0
        }

    async def handle_bedrock_fallback(
        self,
        original_model: str,
        panel_data: bytes,
        context: Dict[str, Any],
        error: Exception
    ) -> Optional[Dict[str, Any]]:
        """Handle Bedrock API fallback.
        
        Args:
            original_model: The model that failed
            panel_data: Panel image data
            context: Analysis context
            error: The original error
            
        Returns:
            Fallback analysis result or None if all fallbacks fail
        """
        logger.warning(f"Bedrock fallback triggered for model {original_model}: {error}")
        
        # Try alternative models
        for fallback_model in self.fallback_models["bedrock"]:
            if fallback_model == original_model:
                continue
                
            try:
                logger.info(f"Trying fallback model: {fallback_model}")
                
                # Import here to avoid circular imports
                from ..bedrock_analysis.panel_analyzer import BedrockPanelAnalyzer
                
                # Create analyzer with fallback model
                analyzer = BedrockPanelAnalyzer(model_id=fallback_model)
                
                # Attempt analysis with simplified prompt for reliability
                result = await analyzer.analyze_panel_with_fallback(
                    panel_data=panel_data,
                    context=context
                )
                
                self.fallback_stats["bedrock_fallbacks"] += 1
                self.fallback_stats["total_fallbacks"] += 1
                
                logger.info(f"Bedrock fallback successful with model {fallback_model}")
                return result
                
            except Exception as fallback_error:
                logger.warning(f"Fallback model {fallback_model} also failed: {fallback_error}")
                continue
        
        # If all models fail, try cached response
        cache_key = f"bedrock_{hash(panel_data)}"
        if cache_key in self.cache:
            logger.info("Using cached Bedrock response as fallback")
            return self.cache[cache_key]
        
        # Last resort: return simplified analysis
        logger.warning("All Bedrock fallbacks failed, using simplified analysis")
        return await self._create_simplified_analysis(panel_data, context)

    async def handle_polly_fallback(
        self,
        text: str,
        original_voice: str,
        original_engine: str,
        error: Exception
    ) -> Optional[bytes]:
        """Handle Polly API fallback.
        
        Args:
            text: Text to synthesize
            original_voice: The voice that failed
            original_engine: The engine that failed
            error: The original error
            
        Returns:
            Fallback audio data or None if all fallbacks fail
        """
        logger.warning(f"Polly fallback triggered for voice {original_voice}: {error}")
        
        # Try alternative voices with same engine first
        engine_voices = self.fallback_voices.get(original_engine, [])
        for fallback_voice in engine_voices:
            if fallback_voice == original_voice:
                continue
                
            try:
                logger.info(f"Trying fallback voice: {fallback_voice}")
                
                # Import here to avoid circular imports
                from ..polly_generation.generator import PollyAudioGenerator
                
                # Create generator with fallback voice
                generator = PollyAudioGenerator(
                    use_neural=(original_engine == "neural")
                )
                
                # Attempt synthesis
                audio_data = await generator.synthesize_with_fallback(
                    text=text,
                    voice_id=fallback_voice,
                    engine=original_engine
                )
                
                self.fallback_stats["polly_fallbacks"] += 1
                self.fallback_stats["total_fallbacks"] += 1
                
                logger.info(f"Polly fallback successful with voice {fallback_voice}")
                return audio_data
                
            except Exception as fallback_error:
                logger.warning(f"Fallback voice {fallback_voice} also failed: {fallback_error}")
                continue
        
        # Try switching to standard engine if neural failed
        if original_engine == "neural":
            try:
                logger.info("Trying standard engine as fallback")
                
                from ..polly_generation.generator import PollyAudioGenerator
                
                generator = PollyAudioGenerator(use_neural=False)
                
                # Use first available standard voice
                fallback_voice = self.fallback_voices["standard"][0]
                audio_data = await generator.synthesize_with_fallback(
                    text=text,
                    voice_id=fallback_voice,
                    engine="standard"
                )
                
                self.fallback_stats["polly_fallbacks"] += 1
                self.fallback_stats["total_fallbacks"] += 1
                
                logger.info("Polly fallback successful with standard engine")
                return audio_data
                
            except Exception as fallback_error:
                logger.warning(f"Standard engine fallback also failed: {fallback_error}")
        
        # Check cache for similar text
        cache_key = f"polly_{hash(text)}"
        if cache_key in self.cache:
            logger.info("Using cached Polly response as fallback")
            return self.cache[cache_key]
        
        logger.error("All Polly fallbacks failed")
        return None

    async def handle_s3_fallback(
        self,
        audio_data: bytes,
        key: str,
        bucket: str,
        error: Exception
    ) -> Optional[str]:
        """Handle S3 storage fallback.
        
        Args:
            audio_data: Audio data to store
            key: S3 key
            bucket: S3 bucket
            error: The original error
            
        Returns:
            Fallback storage location or None if all fallbacks fail
        """
        logger.warning(f"S3 fallback triggered for bucket {bucket}: {error}")
        
        # Try local storage as fallback
        try:
            logger.info("Trying local storage as S3 fallback")
            
            # Import here to avoid circular imports
            from ..storage.local_manager import LocalStorageManager
            
            local_manager = LocalStorageManager(settings.local_storage_path)
            
            # Store locally with same key structure
            local_path = await local_manager.store_audio_with_fallback(
                audio_data=audio_data,
                filename=key
            )
            
            self.fallback_stats["s3_fallbacks"] += 1
            self.fallback_stats["total_fallbacks"] += 1
            
            logger.info(f"S3 fallback successful, stored locally at {local_path}")
            return local_path
            
        except Exception as fallback_error:
            logger.warning(f"Local storage fallback also failed: {fallback_error}")
        
        # Try alternative S3 bucket if configured
        fallback_bucket = f"{bucket}-fallback"
        try:
            logger.info(f"Trying fallback bucket: {fallback_bucket}")
            
            from ..storage.s3_manager import S3StorageManager
            
            s3_manager = S3StorageManager(fallback_bucket)
            s3_url = await s3_manager.upload_audio_with_fallback(
                audio_data=audio_data,
                key=key
            )
            
            self.fallback_stats["s3_fallbacks"] += 1
            self.fallback_stats["total_fallbacks"] += 1
            
            logger.info(f"S3 fallback successful with bucket {fallback_bucket}")
            return s3_url
            
        except Exception as fallback_error:
            logger.warning(f"Fallback bucket also failed: {fallback_error}")
        
        logger.error("All S3 fallbacks failed")
        return None

    async def _create_simplified_analysis(
        self,
        panel_data: bytes,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create simplified analysis when all Bedrock models fail.
        
        Args:
            panel_data: Panel image data
            context: Analysis context
            
        Returns:
            Simplified analysis result
        """
        # Create basic analysis based on context or defaults
        panel_number = context.get("panel_number", 1)
        
        return {
            "panel_id": f"panel_{panel_number}",
            "narrative": f"Panel {panel_number} shows a scene from the comic story.",
            "characters": context.get("known_characters", ["Character"]),
            "scene": context.get("current_scene", "Scene"),
            "visual_elements": ["Comic panel"],
            "dialogue": [],
            "actions": ["Scene continues"],
            "emotions": ["neutral"],
            "fallback_used": True,
            "fallback_reason": "All Bedrock models unavailable"
        }

    def cache_response(self, service: str, key: str, response: Any) -> None:
        """Cache a successful response for fallback use.
        
        Args:
            service: Service name (bedrock, polly, s3)
            key: Cache key
            response: Response to cache
        """
        cache_key = f"{service}_{key}"
        self.cache[cache_key] = response
        
        # Limit cache size
        if len(self.cache) > 1000:
            # Remove oldest entries
            oldest_keys = list(self.cache.keys())[:100]
            for old_key in oldest_keys:
                del self.cache[old_key]

    def get_fallback_stats(self) -> Dict[str, int]:
        """Get fallback usage statistics.
        
        Returns:
            Dictionary with fallback statistics
        """
        return self.fallback_stats.copy()

    def reset_stats(self) -> None:
        """Reset fallback statistics."""
        for key in self.fallback_stats:
            self.fallback_stats[key] = 0


# Global fallback handler instance
fallback_handler = FallbackHandler()