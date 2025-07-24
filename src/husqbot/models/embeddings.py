import logging
from typing import List

import vertexai
from vertexai.language_models import TextEmbeddingModel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    def __init__(self, project_id: str, location: str = "us-central1"):
        """Initialize the embedding generator.
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
        """
        vertexai.init(project=project_id, location=location)
        # Updated to use the current gemini embedding model
        model_name = "gemini-embedding-001"
        logger.info(f"Initializing embedding model: {model_name}")
        self.model = TextEmbeddingModel.from_pretrained(model_name)
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
        
        Returns:
            List of embedding vectors
        """
        embeddings = []
        # Process texts individually since gemini-embedding-001 
        # accepts one input at a time
        for text in texts:
            try:
                batch_embeddings = self.model.get_embeddings([text])
                embeddings.extend([emb.values for emb in batch_embeddings])
            except Exception as e:
                logger.error(f"Error generating embedding for text: {e}")
                # Add a zero vector as placeholder for failed embeddings
                embeddings.append([0.0] * 768)  # Default dimension
        
        return embeddings
    
    def generate_embeddings_for_chunks(self, chunks: List[dict]) -> List[dict]:
        """Generate embeddings for document chunks.
        
        Args:
            chunks: List of chunk dictionaries with 'content' field
        
        Returns:
            List of chunks with 'embedding' field added
        """
        texts = [chunk['content'] for chunk in chunks]
        embeddings = self.generate_embeddings(texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
        
        return chunks 