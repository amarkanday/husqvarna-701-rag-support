from typing import List, Dict
import vertexai
from vertexai.language_models import TextEmbeddingModel


class EmbeddingGenerator:
    """Generate embeddings using Vertex AI."""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """Initialize the embedding generator.
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
        """
        vertexai.init(project=project_id, location=location)
        model_name = "textembedding-gecko@latest"
        self.model = TextEmbeddingModel.from_pretrained(model_name)
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        embeddings = []
        
        # Process in batches of 5 to avoid rate limits
        batch_size = 5
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.model.get_embeddings(batch)
            embeddings.extend([emb.values for emb in batch_embeddings])
        
        return embeddings
    
    def generate_embeddings_for_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Generate embeddings for document chunks.
        
        Args:
            chunks: List of document chunks (dictionaries)
            
        Returns:
            List of chunks with embeddings added
        """
        # Extract text content from chunks
        texts = [chunk['content'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk['embedding'] = embedding
        
        return chunks 