"""
Response generation for Husqvarna RAG Support System.
"""

import logging
from typing import List, Dict, Any, Optional
from vertexai.generative_models import GenerativeModel

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Generates responses using RAG with Gemini models."""
    
    def __init__(self, generation_model: GenerativeModel):
        """
        Initialize the response generator.
        
        Args:
            generation_model: Gemini model for text generation
        """
        self.generation_model = generation_model
        
        logger.info("Initialized response generator")
    
    async def generate_response(
        self,
        query: str,
        context: str,
        user_skill_level: str = "intermediate",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        Generate a response using RAG.
        
        Args:
            query: User's question
            context: Retrieved context from manual
            user_skill_level: User's skill level (beginner, intermediate, expert)
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters
            
        Returns:
            Generated response
        """
        try:
            # Create the prompt for Gemini
            prompt = self._build_prompt(query, context, user_skill_level)
            
            # Generate response
            response = self.generation_model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    **kwargs
                }
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _build_prompt(
        self, 
        query: str, 
        context: str, 
        user_skill_level: str
    ) -> str:
        """
        Build the prompt for response generation.
        
        Args:
            query: User's question
            context: Retrieved context
            user_skill_level: User's skill level
            
        Returns:
            Formatted prompt
        """
        # Adjust response style based on user skill level
        skill_instructions = {
            "beginner": "Use simple, clear language. Explain technical terms. Provide step-by-step instructions.",
            "intermediate": "Provide detailed technical information. Include specifications and procedures.",
            "expert": "Focus on technical details and advanced procedures. Assume technical knowledge."
        }
        
        skill_instruction = skill_instructions.get(user_skill_level, skill_instructions["intermediate"])
        
        prompt = f"""
        You are a helpful assistant for Husqvarna 701 Enduro motorcycle owners. 
        Use the following information from the owner's manual to answer the user's question.
        
        Context from Manual:
        {context}
        
        Question: {query}
        
        Instructions:
        - Provide a clear, accurate answer based on the manual content
        - {skill_instruction}
        - Include specific details like measurements, procedures, or warnings when relevant
        - If the information involves safety warnings, emphasize them prominently
        - Reference the manual section and page number when helpful
        - If you cannot find the answer in the provided context, say so clearly
        - Structure your response logically with clear sections if needed
        
        Answer:
        """
        
        return prompt
    
    async def generate_batch_responses(
        self,
        queries: List[str],
        contexts: List[str],
        user_skill_level: str = "intermediate",
        **kwargs
    ) -> List[str]:
        """
        Generate responses for multiple queries.
        
        Args:
            queries: List of user questions
            contexts: List of corresponding contexts
            user_skill_level: User's skill level
            **kwargs: Additional generation parameters
            
        Returns:
            List of generated responses
        """
        responses = []
        
        for i, (query, context) in enumerate(zip(queries, contexts)):
            try:
                response = await self.generate_response(
                    query, context, user_skill_level, **kwargs
                )
                responses.append(response)
                
                # Log progress
                if (i + 1) % 5 == 0:
                    logger.info(f"Generated responses for {i + 1}/{len(queries)} queries")
                    
            except Exception as e:
                logger.error(f"Error generating response for query {i}: {e}")
                responses.append(f"Error generating response: {str(e)}")
        
        return responses
    
    def _format_context_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks into context string.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            context_part = f"""
            Source {i} ({chunk.get('manual_type', 'unknown')}, {chunk.get('section', 'unknown')}):
            Subsection: {chunk.get('subsection', 'N/A')}
            Content: {chunk.get('content', 'N/A')}
            Page: {chunk.get('page_number', 'N/A')}
            Type: {chunk.get('chunk_type', 'N/A')}
            """
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    async def generate_enhanced_response(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        user_skill_level: str = "intermediate",
        include_sources: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an enhanced response with metadata.
        
        Args:
            query: User's question
            chunks: Retrieved chunks
            user_skill_level: User's skill level
            include_sources: Whether to include source information
            **kwargs: Additional generation parameters
            
        Returns:
            Dictionary with response and metadata
        """
        # Format context
        context = self._format_context_chunks(chunks)
        
        # Generate response
        response_text = await self.generate_response(
            query, context, user_skill_level, **kwargs
        )
        
        # Prepare result
        result = {
            "response": response_text,
            "sources": chunks if include_sources else [],
            "context_length": len(context),
            "chunks_used": len(chunks)
        }
        
        return result 