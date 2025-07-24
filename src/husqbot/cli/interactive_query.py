#!/usr/bin/env python3
"""
Interactive query interface for the Husqvarna 701 RAG system.
This module provides functions for testing user-supplied queries.
"""

import os
import sys
from typing import Dict, Any
from husqbot.core.rag_system import HusqvarnaRAGSystem


def test_single_query(
    query: str,
    project_id: str = None,
    location: str = "us-central1",
    top_k: int = 3,
    similarity_threshold: float = 0.6,
    show_full_response: bool = False,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Test a single query against the RAG system.
    
    Args:
        query: The question to ask
        project_id: Google Cloud project ID (defaults to env var)
        location: Google Cloud region
        top_k: Number of relevant chunks to retrieve
        similarity_threshold: Minimum similarity threshold
        show_full_response: Whether to show full response
        verbose: Whether to print results to console
    
    Returns:
        Dictionary with query results
    """
    # Get project ID from environment if not provided
    if not project_id:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            raise ValueError(
                "Project ID required. Set GOOGLE_CLOUD_PROJECT env var or "
                "pass project_id parameter."
            )
    
    if verbose:
        print(f"🔧 Initializing RAG system (project: {project_id})...")
    
    # Initialize RAG system
    rag = HusqvarnaRAGSystem(project_id=project_id, location=location)
    
    # Show system stats if verbose
    if verbose:
        stats = rag.get_system_stats()
        if 'error' not in stats:
            print(f"📊 System ready: {stats['chunks_with_embeddings']} chunks "
                  f"({stats['embedding_coverage']}% coverage)")
    
    if verbose:
        print(f"\n🔍 Processing query: '{query}'")
        print("=" * 60)
    
    # Process the query
    result = rag.query(query, top_k=top_k, similarity_threshold=similarity_threshold)
    
    # Format and display results if verbose
    if verbose:
        _display_result(result, show_full_response)
    
    return result


def interactive_query_session(
    project_id: str = None,
    location: str = "us-central1",
    top_k: int = 3,
    similarity_threshold: float = 0.6,
    show_full_response: bool = False
) -> None:
    """
    Start an interactive query session.
    
    Args:
        project_id: Google Cloud project ID (defaults to env var)
        location: Google Cloud region
        top_k: Number of relevant chunks to retrieve
        similarity_threshold: Minimum similarity threshold
        show_full_response: Whether to show full response
    """
    # Get project ID from environment if not provided
    if not project_id:
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            print("❌ Error: Project ID required.")
            print("Set GOOGLE_CLOUD_PROJECT environment variable or pass project_id parameter.")
            return
    
    print("🔧 Initializing Husqvarna 701 RAG System...")
    
    try:
        # Initialize RAG system
        rag = HusqvarnaRAGSystem(project_id=project_id, location=location)
        
        # Show system stats
        stats = rag.get_system_stats()
        if 'error' not in stats:
            print(f"📊 System ready: {stats['chunks_with_embeddings']} chunks "
                  f"({stats['embedding_coverage']}% coverage)")
        
        # Interactive loop
        print(f"\n🤖 Interactive Query Mode")
        print(f"Settings: top_k={top_k}, threshold={similarity_threshold}")
        print("=" * 60)
        print("Enter your questions about the Husqvarna 701 Enduro.")
        print("Type 'quit', 'exit', or press Ctrl+C to stop.")
        print("-" * 60)
        
        query_count = 0
        
        try:
            while True:
                user_query = input("\n🏍️  Your question: ").strip()
                
                if user_query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_query:
                    print("Please enter a question.")
                    continue
                
                query_count += 1
                print(f"\n[Query {query_count}] Processing...")
                
                try:
                    result = rag.query(
                        user_query, 
                        top_k=top_k, 
                        similarity_threshold=similarity_threshold
                    )
                    _display_result(result, show_full_response)
                    
                except Exception as e:
                    print(f"💥 Error processing query: {str(e)}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
        
        print(f"\n📈 Session complete: {query_count} queries processed")
    
    except Exception as e:
        print(f"❌ Error initializing system: {str(e)}")


def _display_result(result: Dict[str, Any], show_full_response: bool = False) -> None:
    """Display query results in a formatted way."""
    print(f"✅ Success: {result['success']}")
    print(f"📊 Chunks found: {result['chunks_found']}")
    print(f"🤖 Fallback mode: {result.get('fallback_mode', 'Unknown')}")
    
    if result['success'] and result['chunks_found'] > 0:
        response = result['response']
        if not show_full_response and len(response) > 500:
            response = response[:500] + "..."
        print(f"📝 Response:\n{response}")
        
        if result['sources']:
            print(f"\n📚 Sources ({len(result['sources'])} found):")
            for i, source in enumerate(result['sources'][:3], 1):
                print(f"  {i}. {source['source']} (Page {source['page']}, "
                      f"Similarity: {source['similarity']:.1%}, "
                      f"Safety: {source['safety_level']})")
    elif result['success']:
        print(f"📝 Response: {result['response']}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")


def run_sample_queries(
    project_id: str = None,
    location: str = "us-central1"
) -> None:
    """
    Run a set of sample queries to demonstrate the system.
    
    Args:
        project_id: Google Cloud project ID (defaults to env var)
        location: Google Cloud region
    """
    sample_queries = [
        "How do I check the oil level?",
        "What are the valve clearances?",
        "How often should I service the air filter?",
        "What type of spark plug should I use?",
        "How do I adjust the chain tension?"
    ]
    
    print("🚀 Running sample queries...")
    print("=" * 60)
    
    for i, query in enumerate(sample_queries, 1):
        print(f"\n[Sample Query {i}/{len(sample_queries)}]: {query}")
        print("-" * 40)
        
        try:
            result = test_single_query(
                query=query,
                project_id=project_id,
                location=location,
                verbose=False
            )
            
            if result['success'] and result['chunks_found'] > 0:
                print(f"✅ Found {result['chunks_found']} relevant chunks")
                response = result['response'][:200] + "..." if len(result['response']) > 200 else result['response']
                print(f"📝 Response: {response}")
            else:
                print(f"❌ No relevant information found")
                
        except Exception as e:
            print(f"💥 Error: {str(e)}")
    
    print(f"\n🎯 Sample queries complete!")


if __name__ == "__main__":
    # Simple command-line interface
    if len(sys.argv) > 1:
        if sys.argv[1] == "interactive":
            interactive_query_session()
        elif sys.argv[1] == "samples":
            run_sample_queries()
        elif sys.argv[1] == "query" and len(sys.argv) > 2:
            query = " ".join(sys.argv[2:])
            test_single_query(query, show_full_response=True)
        else:
            print("Usage:")
            print("  python interactive_query.py interactive")
            print("  python interactive_query.py samples")
            print("  python interactive_query.py query <your question>")
    else:
        print("🏍️ Husqvarna 701 RAG Query Interface")
        print("=" * 40)
        print("Available functions:")
        print("- test_single_query(query)")
        print("- interactive_query_session()")
        print("- run_sample_queries()")
        print("\nExample:")
        print("from husqbot.cli.interactive_query import test_single_query")
        print('result = test_single_query("How do I check the oil?")') 