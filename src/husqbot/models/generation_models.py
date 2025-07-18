"""
Generation models for Husqvarna RAG Support System.
"""

import logging
from vertexai.generative_models import GenerativeModel

logger = logging.getLogger(__name__)


class GenerationModel:
    """Handles text generation using Vertex AI Gemini models."""
    
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        """
        Initialize the generation model.
        
        Args:
            model_name: Name of the generation model to use
        """
        self.model_name = model_name
        self.model = GenerativeModel(model_name)
        
        logger.info(f"Initialized generation model: {model_name}")
    
    def generate_content(self, prompt: str, **kwargs):
        """
        Generate content using the model.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated content response
        """
        try:
            response = self.model.generate_content(prompt, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise
    
    def get_model_info(self) -> dict:
        """
        Get information about the model.
        
        Returns:
            Model information dictionary
        """
        return {
            "name": self.model_name,
            "type": "generation",
            "provider": "vertex_ai"
        } 