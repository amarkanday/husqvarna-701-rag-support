"""
Main RAG system for Husqvarna 701 Enduro support.
"""

import logging
from typing import List, Dict, Optional
import json

from google.cloud import bigquery
import vertexai
from husqbot.models.embeddings import EmbeddingGenerator


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HusqvarnaRAGSystem:
    """Retrieval-Augmented Generation system for Husqvarna 701 Enduro."""
    
    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        dataset_id: str = "husqvarna_rag_dataset",
        table_id: str = "document_chunks",
        model_name: str = "gemini-1.5-flash-001"
    ):
        """Initialize the RAG system.
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID
            model_name: Text generation model name
        """
        self.project_id = project_id
        self.location = location
        self.dataset_id = dataset_id
        self.table_id = table_id
        
        # Initialize clients
        self.bq_client = bigquery.Client()
        self.embedding_generator = EmbeddingGenerator(project_id, location)
        
        # Try to initialize text generation model with fallback
        vertexai.init(project=project_id, location=location)
        self.text_model = None
        self.use_fallback = False
        
        try:
            from vertexai.generative_models import GenerativeModel
            self.text_model = GenerativeModel(model_name)
            # Test the model
            test_response = self.text_model.generate_content("Hello")
            logger.info(f"Successfully initialized Gemini model: {model_name}")
        except Exception as e:
            logger.warning(f"Gemini model not available: {str(e)[:100]}...")
            logger.info("Using fallback text generation")
            self.use_fallback = True
        
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"
        
        logger.info(f"Initialized RAG system for project {project_id}")
    
    def search_similar_chunks(
        self, 
        query: str, 
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """Search for similar chunks using vector similarity.
        
        Args:
            query: User query
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score
        
        Returns:
            List of similar chunks with metadata
        """
        # Generate embedding for the query
        logger.info(f"Generating embedding for query: {query}")
        query_embedding = self.embedding_generator.generate_embeddings([query])[0]
        
        # Convert embedding to BigQuery array format
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        # BigQuery ML cosine similarity search - get more results for filtering
        search_query = f"""
        SELECT 
            chunk_id,
            content,
            source,
            page_number,
            safety_level,
            ML.DISTANCE(embedding, {embedding_str}, 'COSINE') as distance,
            (1 - ML.DISTANCE(embedding, {embedding_str}, 'COSINE')) as similarity
        FROM `{self.table_ref}`
        WHERE ARRAY_LENGTH(embedding) = ARRAY_LENGTH({embedding_str})
        ORDER BY similarity DESC
        LIMIT {top_k * 3}
        """
        
        logger.info("Executing similarity search in BigQuery")
        results = list(self.bq_client.query(search_query))
        
        # Filter by similarity threshold and remove duplicates
        similar_chunks = []
        seen_content = set()
        
        for row in results:
            if row.similarity >= similarity_threshold:
                content = row.content.strip()
                
                # Check for content similarity to avoid duplicates
                is_duplicate = False
                content_words = set(content.lower().split())
                
                for seen in seen_content:
                    seen_words = set(seen.lower().split())
                    if len(content_words) > 0 and len(seen_words) > 0:
                        common = content_words.intersection(seen_words)
                        similarity_ratio = len(common) / min(len(content_words), 
                                                           len(seen_words))
                        if similarity_ratio > 0.65:  # 65% similarity threshold
                            is_duplicate = True
                            break
                
                if not is_duplicate:
                    similar_chunks.append({
                        'chunk_id': row.chunk_id,
                        'content': content,
                        'source': row.source,
                        'page_number': row.page_number,
                        'safety_level': row.safety_level,
                        'similarity': round(row.similarity, 3),
                        'distance': round(row.distance, 3)
                    })
                    seen_content.add(content)
                    
                    if len(similar_chunks) >= top_k:
                        break
        
        logger.info(f"Found {len(similar_chunks)} unique relevant chunks")
        return similar_chunks
    
    def generate_response_fallback(
        self,
        query: str,
        context_chunks: List[Dict]
    ) -> str:
        """Generate a response using fallback method when Gemini is not available.
        
        Args:
            query: User query
            context_chunks: List of relevant chunks
        
        Returns:
            Generated response
        """
        if not context_chunks:
            return "I couldn't find relevant information in the Husqvarna 701 manuals for your question."
        
        # Consolidate similar content to avoid duplicates
        consolidated_chunks = self._consolidate_similar_chunks(context_chunks)
        
        # Create safety warning if needed
        safety_warning = ""
        high_safety_chunks = [c for c in consolidated_chunks if c['safety_level'] >= 3]
        if high_safety_chunks:
            safety_warning = "⚠️ **SAFETY WARNING**: This information involves potentially dangerous procedures. Please exercise extreme caution and consider consulting a professional mechanic.\n\n"
        
        # Format response with consolidated context
        response_parts = []
        response_parts.append(f"Based on the Husqvarna 701 Enduro manual, here's what I found regarding '{query}':\n")
        
        # Show up to 3 distinct chunks
        for i, chunk in enumerate(consolidated_chunks[:3], 1):
            source_info = f"**Source**: {chunk['source']} (Page {chunk['page_number']})"
            content = chunk['content'].strip()
            similarity = chunk['similarity']
            
            response_parts.append(f"**{i}. {source_info}** (Relevance: {similarity:.1%})")
            response_parts.append(f"{content}\n")
        
        if len(consolidated_chunks) > 3:
            response_parts.append(f"*Found {len(consolidated_chunks) - 3} additional relevant sections...*")
        elif len(context_chunks) > len(consolidated_chunks):
            removed_count = len(context_chunks) - len(consolidated_chunks)
            response_parts.append(f"*Consolidated {removed_count} similar sections for clarity...*")
        
        response_parts.append("\n**Note**: This response is based on content extracted from the official Husqvarna 701 Enduro manuals. For complex procedures, always refer to the complete manual or consult a qualified technician.")
        
        return safety_warning + "\n".join(response_parts)
    
    def _consolidate_similar_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Consolidate similar chunks to avoid duplicate content.
        
        Args:
            chunks: List of chunks to consolidate
            
        Returns:
            List of consolidated chunks
        """
        if not chunks:
            return chunks
        
        consolidated = []
        used_content = set()
        
        for chunk in chunks:
            content = chunk['content'].strip()
            
            # Check if this content is significantly similar to existing content
            is_duplicate = False
            content_words = set(content.lower().split())
            
            for existing_content in used_content:
                existing_words = set(existing_content.lower().split())
                
                # Calculate similarity based on common words
                if len(content_words) > 0 and len(existing_words) > 0:
                    common_words = content_words.intersection(existing_words)
                    similarity_ratio = len(common_words) / min(len(content_words), len(existing_words))
                    
                    # If more than 70% similar, consider it a duplicate
                    if similarity_ratio > 0.7:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                consolidated.append(chunk)
                used_content.add(content)
        
        # Sort by similarity score (highest first)
        consolidated.sort(key=lambda x: x['similarity'], reverse=True)
        
        return consolidated
    
    def generate_response(
        self, 
        query: str, 
        context_chunks: List[Dict],
        max_context_length: int = 4000  # Increased for better context
    ) -> str:
        """Generate a response using the context chunks.
        
        Args:
            query: User query
            context_chunks: List of relevant chunks
            max_context_length: Maximum context length for the prompt
        
        Returns:
            Generated response
        """
        if self.use_fallback:
            return self.generate_response_fallback(query, context_chunks)
        
        # Build enhanced context from chunks
        context_parts = []
        current_length = 0
        
        for i, chunk in enumerate(context_chunks, 1):
            # Enhanced context formatting with metadata
            chunk_text = (
                f"=== MANUAL SECTION {i} ===\n"
                f"Source: {chunk['source']}\n"
                f"Page: {chunk['page_number']}\n"
                f"Safety Level: {chunk['safety_level']}/3\n"
                f"Relevance: {chunk['similarity']:.1%}\n"
                f"Content:\n{chunk['content']}\n"
                f"=== END SECTION {i} ===\n"
            )
            
            if current_length + len(chunk_text) <= max_context_length:
                context_parts.append(chunk_text)
                current_length += len(chunk_text)
            else:
                break
        
        context = "\n".join(context_parts)
        
        # Create enhanced safety warning
        safety_warning = ""
        high_safety_chunks = [c for c in context_chunks if c['safety_level'] >= 3]
        if high_safety_chunks:
            safety_warning = (
                "🚨 **CRITICAL SAFETY WARNING** 🚨\n"
                "This response contains information about potentially dangerous "
                "procedures that could result in serious injury or death. "
                "Only qualified technicians should perform these operations. "
                "Always follow safety protocols and manufacturer guidelines.\n\n"
            )
        
        # Enhanced prompt with better instructions
        prompt = f"""You are an expert Husqvarna 701 Enduro motorcycle technician with extensive knowledge of maintenance, repair, and troubleshooting. Your role is to provide accurate, helpful, and safety-conscious guidance based on the official manual excerpts provided.

=== CONTEXT FROM HUSQVARNA 701 ENDURO MANUALS ===
{context}
=== END CONTEXT ===

USER QUESTION: {query}

=== RESPONSE INSTRUCTIONS ===
1. ACCURACY: Base your answer ONLY on the provided manual excerpts
2. STRUCTURE: Organize your response with clear headings and bullet points
3. SAFETY: Always prioritize safety - emphasize warnings and precautions
4. SPECIFICITY: Include exact specifications, torque values, part numbers when available
5. PRACTICALITY: Provide step-by-step instructions when applicable
6. SOURCES: Reference specific manual sections and page numbers
7. LIMITATIONS: If information is incomplete, clearly state what's missing
8. TOOLS: Mention required tools and equipment when relevant

=== RESPONSE FORMAT ===
- Start with a brief summary
- Provide detailed information organized by subtopics
- Include safety warnings prominently
- End with references to manual sections
- Use technical terminology appropriately

Generate a comprehensive, professional response:"""

        logger.info("Generating enhanced response using text generation model")
        
        # Generate response with enhanced parameters
        response = self.text_model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,  # Lower for more consistent technical info
                "max_output_tokens": 1500,  # Increased for detailed responses
                "top_p": 0.9,
                "top_k": 40,
                "candidate_count": 1
            }
        )
        
        return safety_warning + response.text
    
    def query(
        self, 
        user_query: str, 
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> Dict:
        """Complete RAG query pipeline.
        
        Args:
            user_query: User's question
            top_k: Number of chunks to retrieve
            similarity_threshold: Minimum similarity for chunks
        
        Returns:
            Dictionary with response and metadata
        """
        logger.info(f"Processing RAG query: {user_query}")
        
        try:
            # Step 1: Retrieve similar chunks
            similar_chunks = self.search_similar_chunks(
                user_query, top_k, similarity_threshold
            )
            
            if not similar_chunks:
                return {
                    'query': user_query,
                    'response': (
                        "I couldn't find relevant information in the Husqvarna 701 "
                        "manuals for your question. Please try rephrasing your "
                        "query or ask about specific maintenance, repair, or "
                        "operational topics."
                    ),
                    'sources': [],
                    'chunks_found': 0,
                    'success': True,
                    'fallback_mode': self.use_fallback
                }
            
            # Step 2: Generate response
            response = self.generate_response(user_query, similar_chunks)
            
            # Step 3: Format source information
            sources = []
            for chunk in similar_chunks:
                sources.append({
                    'source': chunk['source'],
                    'page': chunk['page_number'],
                    'similarity': chunk['similarity'],
                    'safety_level': chunk['safety_level']
                })
            
            return {
                'query': user_query,
                'response': response,
                'sources': sources,
                'chunks_found': len(similar_chunks),
                'success': True,
                'fallback_mode': self.use_fallback
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'query': user_query,
                'response': f"An error occurred while processing your query: {str(e)}",
                'sources': [],
                'chunks_found': 0,
                'success': False,
                'error': str(e),
                'fallback_mode': self.use_fallback
            }
    
    def get_system_stats(self) -> Dict:
        """Get system statistics.
        
        Returns:
            Dictionary with system statistics
        """
        try:
            stats_query = f"""
            SELECT 
                COUNT(*) as total_chunks,
                COUNT(CASE WHEN ARRAY_LENGTH(embedding) > 0 THEN 1 END) as chunks_with_embeddings,
                COUNT(DISTINCT source) as unique_sources,
                AVG(safety_level) as avg_safety_level,
                MIN(safety_level) as min_safety_level,
                MAX(safety_level) as max_safety_level
            FROM `{self.table_ref}`
            """
            
            result = list(self.bq_client.query(stats_query))[0]
            
            return {
                'total_chunks': result.total_chunks,
                'chunks_with_embeddings': result.chunks_with_embeddings,
                'embedding_coverage': round(
                    result.chunks_with_embeddings / result.total_chunks * 100, 1
                ),
                'unique_sources': result.unique_sources,
                'avg_safety_level': round(result.avg_safety_level, 2),
                'safety_level_range': [result.min_safety_level, result.max_safety_level],
                'text_generation_mode': 'fallback' if self.use_fallback else 'gemini'
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {'error': str(e)} 

    def search_images(
        self,
        query: str,
        max_results: int = 3,
        image_types: List[str] = None
    ) -> List[Dict]:
        """Search for relevant images based on query.
        
        Args:
            query: Search query
            max_results: Maximum number of images to return
            image_types: Filter by specific image types
            
        Returns:
            List of relevant image metadata
        """
        # Build the base query
        where_conditions = [
            "LOWER(description) LIKE LOWER(@query)",
            "OR LOWER(ocr_text) LIKE LOWER(@query)"
        ]
        
        # Add image type filter if specified
        if image_types:
            type_filter = " OR ".join([f"image_type = '{img_type}'" 
                                     for img_type in image_types])
            where_conditions.append(f"AND ({type_filter})")
        
        query_sql = f"""
        SELECT 
            image_id,
            source,
            page_number,
            description,
            ocr_text,
            image_type,
            complexity_level,
            width,
            height,
            image_base64
        FROM {self.table_ref.replace('document_chunks', 'image_metadata')}
        WHERE {' '.join(where_conditions)}
        ORDER BY 
            CASE 
                WHEN LOWER(description) LIKE LOWER(@query) THEN 1
                WHEN LOWER(ocr_text) LIKE LOWER(@query) THEN 2
                ELSE 3
            END,
            complexity_level ASC,
            page_number ASC
        LIMIT {max_results}
        """
        
        # Execute query
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("query", "STRING", f"%{query}%")
            ]
        )
        
        try:
            results = self.bq_client.query(query_sql, job_config=job_config).result()
            
            images = []
            for row in results:
                image_data = {
                    'image_id': row.image_id,
                    'source': row.source,
                    'page_number': row.page_number,
                    'description': row.description,
                    'ocr_text': row.ocr_text or '',
                    'image_type': row.image_type,
                    'complexity_level': row.complexity_level,
                    'width': row.width,
                    'height': row.height,
                    'image_base64': row.image_base64
                }
                images.append(image_data)
            
            logger.info(f"Found {len(images)} relevant images for query: {query}")
            return images
            
        except Exception as e:
            logger.error(f"Error searching images: {e}")
            return []
    
    def query_with_images(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        include_images: bool = True,
        max_images: int = 2
    ) -> Dict:
        """Enhanced query that includes both text chunks and relevant images.
        
        Args:
            query: User query
            top_k: Number of text chunks to retrieve
            similarity_threshold: Minimum similarity for text chunks
            include_images: Whether to include relevant images
            max_images: Maximum number of images to include
            
        Returns:
            Dictionary with response, chunks, images, and metadata
        """
        # Get regular text-based results
        result = self.query(query, top_k, similarity_threshold)
        
        # Add image search if requested
        if include_images:
            relevant_images = self.search_images(query, max_images)
            result['images'] = relevant_images
            result['has_images'] = len(relevant_images) > 0
            
            # Enhance response with image references if found
            if relevant_images and not self.use_fallback:
                result['response'] = self._enhance_response_with_images(
                    result['response'], relevant_images
                )
        else:
            result['images'] = []
            result['has_images'] = False
        
        return result
    
    def _enhance_response_with_images(
        self, 
        original_response: str, 
        images: List[Dict]
    ) -> str:
        """Enhance text response by referencing relevant images.
        
        Args:
            original_response: Original text response
            images: List of relevant images
            
        Returns:
            Enhanced response with image references
        """
        if not images:
            return original_response
        
        # Add image references section
        image_references = ["\n\n📷 **Relevant Visual References:**"]
        
        for i, img in enumerate(images, 1):
            source_info = f"**{img['source']}** (Page {img['page_number']})"
            img_type = img['image_type'].replace('_', ' ').title()
            
            image_ref = f"\n{i}. {source_info} - {img_type}"
            image_ref += f"\n   📋 {img['description'][:100]}..."
            
            if img['ocr_text']:
                image_ref += f"\n   📝 Text: {img['ocr_text'][:80]}..."
            
            image_references.append(image_ref)
        
        # Add note about image availability
        image_references.append(
            "\n*💡 Visual diagrams and images are available to help "
            "illustrate these procedures.*"
        )
        
        return original_response + "\n".join(image_references) 