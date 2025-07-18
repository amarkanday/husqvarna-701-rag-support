"""
Query endpoints for the Husqvarna RAG Support System.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..models.request_models import QueryRequest
from ..models.response_models import QueryResponse, BatchQueryResponse
from ..dependencies import get_rag_system
from ...core.rag_system import HusqvarnaRAGSystem

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_system(
    request: QueryRequest,
    rag_system: HusqvarnaRAGSystem = Depends(get_rag_system)
):
    """
    Query the Husqvarna RAG system for technical support.
    
    This endpoint processes user questions about Husqvarna 701 Enduro
    maintenance, troubleshooting, and repair procedures.
    """
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        result = await rag_system.query_system(
            query=request.query,
            user_skill_level=request.user_skill_level,
            max_chunks=request.max_chunks,
            temperature=request.temperature
        )
        
        response = QueryResponse(
            answer=result.answer,
            sources=result.sources,
            confidence=result.confidence,
            safety_level=result.safety_level,
            processing_time=result.processing_time,
            metadata=result.metadata
        )
        
        logger.info(f"Query processed successfully in {result.processing_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.post("/query/batch", response_model=BatchQueryResponse)
async def batch_query(
    queries: List[str] = Field(..., min_items=1, max_items=10),
    user_skill_level: str = Query("intermediate", regex="^(beginner|intermediate|expert)$"),
    rag_system: HusqvarnaRAGSystem = Depends(get_rag_system)
):
    """
    Process multiple queries in batch.
    
    This endpoint allows processing multiple related questions efficiently.
    """
    try:
        logger.info(f"Processing batch query with {len(queries)} questions")
        
        results = await rag_system.batch_query(
            queries=queries,
            user_skill_level=user_skill_level
        )
        
        # Convert results to response format
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in batch query {i}: {result}")
                responses.append({
                    "query": queries[i],
                    "error": str(result),
                    "success": False
                })
            else:
                responses.append({
                    "query": queries[i],
                    "answer": result.answer,
                    "sources": result.sources,
                    "confidence": result.confidence,
                    "safety_level": result.safety_level,
                    "processing_time": result.processing_time,
                    "metadata": result.metadata,
                    "success": True
                })
        
        return BatchQueryResponse(
            results=responses,
            total_queries=len(queries),
            successful_queries=len([r for r in responses if r["success"]])
        )
        
    except Exception as e:
        logger.error(f"Error processing batch query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process batch query: {str(e)}"
        )


@router.get("/query/suggestions")
async def get_query_suggestions(
    category: Optional[str] = Query(None, description="Filter by category"),
    rag_system: HusqvarnaRAGSystem = Depends(get_rag_system)
):
    """
    Get suggested queries based on common issues and topics.
    """
    suggestions = {
        "maintenance": [
            "How do I check the engine oil level?",
            "What is the recommended tire pressure?",
            "How often should I change the oil?",
            "How do I adjust the chain tension?",
            "What are the service intervals?"
        ],
        "troubleshooting": [
            "Engine won't start, what should I check?",
            "Bike is running rough at idle",
            "Brakes feel spongy",
            "Battery keeps dying",
            "Engine is overheating"
        ],
        "repair": [
            "How do I replace the air filter?",
            "Brake pad replacement procedure",
            "How to adjust valve clearances",
            "Clutch cable adjustment",
            "Suspension setup guide"
        ],
        "specifications": [
            "What are the valve clearance specs?",
            "Engine oil capacity",
            "Tire size specifications",
            "Battery specifications",
            "Fuel tank capacity"
        ]
    }
    
    if category and category in suggestions:
        return {"suggestions": suggestions[category]}
    
    return {"suggestions": suggestions}


@router.get("/query/history")
async def get_query_history(
    limit: int = Query(10, ge=1, le=100),
    rag_system: HusqvarnaRAGSystem = Depends(get_rag_system)
):
    """
    Get recent query history (placeholder for future implementation).
    """
    # This would typically connect to a database to retrieve query history
    return {
        "message": "Query history feature coming soon",
        "limit": limit
    } 