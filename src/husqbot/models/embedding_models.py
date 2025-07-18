"""
Embedding models for Husqvarna RAG Support System.
"""

import logging
from typing import List, Optional
from vertexai.generative_models import GenerativeModel

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """Handles text embedding generation using Vertex AI."""
    
    def __init__(self, model_name: str = "textembedding-gecko@003"):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the embedding model to use
        """
        self.model_name = model_name
        self.model = GenerativeModel(model_name)
        
        logger.info(f"Initialized embedding model: {model_name}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = self.model.predict(text)
            embedding = response.embeddings[0].values
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i, text in enumerate(texts):
            try:
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)
                
                # Log progress for large batches
                if (i + 1) % 10 == 0:
                    logger.info(f"Generated embeddings for {i + 1}/{len(texts)} texts")
                    
            except Exception as e:
                logger.error(f"Error generating embedding for text {i}: {e}")
                # Return zero vector as fallback
                embeddings.append([0.0] * 768)
        
        return embeddings
    
    async def generate_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int = 10
    ) -> List[List[float]]:
        """
        Generate embeddings in batches for efficiency.
        
        Args:
            texts: List of texts to embed
            batch_size: Size of each batch
            
        Returns:
            List of embedding vectors
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.generate_embeddings(batch)
            all_embeddings.extend(batch_embeddings)
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
        
        return all_embeddings
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension
        """
        # textembedding-gecko@003 has 768 dimensions
        if "gecko" in self.model_name:
            return 768
        else:
            # Default fallback
            return 768 