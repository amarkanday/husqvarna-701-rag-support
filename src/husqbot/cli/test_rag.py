import click
from husqbot.core.rag_system import HusqvarnaRAGSystem


def format_response(result: dict, show_full_response: bool = False) -> None:
    """Format and display the RAG response."""
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


@click.group()
def cli():
    """Test the Husqvarna 701 RAG system."""
    pass


@click.command()
@click.option(
    '--project-id',
    envvar='GOOGLE_CLOUD_PROJECT',
    help='Google Cloud project ID',
    required=True
)
@click.option(
    '--location',
    default='us-central1',
    help='Google Cloud region'
)
def test_system(project_id: str, location: str):
    """Test the RAG system with predefined sample queries."""
    
    print("🔧 Initializing Husqvarna 701 RAG System...")
    rag = HusqvarnaRAGSystem(project_id=project_id, location=location)
    
    # Get system statistics first
    print("\n📊 System Statistics:")
    stats = rag.get_system_stats()
    if 'error' not in stats:
        print(f"  • Total chunks: {stats['total_chunks']}")
        print(f"  • Chunks with embeddings: {stats['chunks_with_embeddings']}")
        print(f"  • Embedding coverage: {stats['embedding_coverage']}%")
        print(f"  • Unique sources: {stats['unique_sources']}")
        print(f"  • Average safety level: {stats['avg_safety_level']}")
        print(f"  • Text generation mode: {stats.get('text_generation_mode', 'unknown')}")
    else:
        print(f"  Error getting stats: {stats['error']}")
    
    # Sample test queries
    test_queries = [
        "How do I check the oil level?",
        "What is the recommended tire pressure?",
        "How do I change the air filter?",
        "What are the engine specifications?",
        "How do I adjust the chain tension?",
        "What type of fuel should I use?",
        "How do I replace the spark plug?",
        "What is the maintenance schedule?",
        "How do I check the brake fluid?",
        "What are the torque specifications for the wheels?"
    ]
    
    print(f"\n🤖 Testing RAG System with {len(test_queries)} queries...")
    print("=" * 80)
    
    successful_queries = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Query {i}/{len(test_queries)}]: {query}")
        print("-" * 50)
        
        try:
            result = rag.query(query, top_k=3, similarity_threshold=0.6)
            
            if result['success']:
                successful_queries += 1
                print(f"✅ Success! Found {result['chunks_found']} relevant chunks")
                
                # Show response (truncated)
                response = result['response']
                if len(response) > 300:
                    response = response[:300] + "..."
                print(f"📝 Response: {response}")
                
                # Show sources
                if result['sources']:
                    print("📚 Sources:")
                    for source in result['sources'][:2]:  # Show top 2 sources
                        print(f"  • {source['source']} (Page {source['page']}, "
                              f"Similarity: {source['similarity']}, "
                              f"Safety: {source['safety_level']})")
                
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"💥 Exception: {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 Test Summary:")
    print(f"  • Successful queries: {successful_queries}/{len(test_queries)}")
    print(f"  • Success rate: {successful_queries/len(test_queries)*100:.1f}%")
    
    if successful_queries > 0:
        print("✅ RAG system is working!")
    else:
        print("❌ RAG system needs troubleshooting")


@click.command()
@click.option(
    '--project-id',
    envvar='GOOGLE_CLOUD_PROJECT',
    help='Google Cloud project ID',
    required=True
)
@click.option(
    '--location',
    default='us-central1',
    help='Google Cloud region'
)
@click.option(
    '--query',
    '-q',
    help='Single query to test (non-interactive mode)'
)
@click.option(
    '--top-k',
    '-k',
    default=3,
    help='Number of relevant chunks to retrieve (default: 3)'
)
@click.option(
    '--similarity-threshold',
    '-s',
    default=0.6,
    help='Minimum similarity threshold (default: 0.6)'
)
@click.option(
    '--show-full-response',
    '-f',
    is_flag=True,
    help='Show full response without truncation'
)
def query_system(
    project_id: str, 
    location: str, 
    query: str, 
    top_k: int, 
    similarity_threshold: float,
    show_full_response: bool
):
    """Test user-supplied queries against the RAG system."""
    
    print("🔧 Initializing Husqvarna 701 RAG System...")
    rag = HusqvarnaRAGSystem(project_id=project_id, location=location)
    
    # Show system stats
    stats = rag.get_system_stats()
    if 'error' not in stats:
        print(f"📊 System ready: {stats['chunks_with_embeddings']} chunks "
              f"({stats['embedding_coverage']}% coverage)")
    
    if query:
        # Non-interactive mode - single query
        print(f"\n🔍 Testing query: '{query}'")
        print("=" * 60)
        
        try:
            result = rag.query(query, top_k=top_k, similarity_threshold=similarity_threshold)
            format_response(result, show_full_response)
        except Exception as e:
            print(f"💥 Error: {str(e)}")
    else:
        # Interactive mode
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
                    format_response(result, show_full_response)
                    
                except Exception as e:
                    print(f"💥 Error processing query: {str(e)}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
        
        print(f"\n📈 Session complete: {query_count} queries processed")


@click.command()
@click.option(
    '--project-id',
    envvar='GOOGLE_CLOUD_PROJECT',
    help='Google Cloud project ID',
    required=True
)
@click.option(
    '--location',
    default='us-central1',
    help='Google Cloud region'
)
def stats(project_id: str, location: str):
    """Show detailed system statistics."""
    
    print("🔧 Getting system statistics...")
    rag = HusqvarnaRAGSystem(project_id=project_id, location=location)
    
    stats = rag.get_system_stats()
    
    if 'error' in stats:
        print(f"❌ Error: {stats['error']}")
        return
    
    print("\n📊 Husqvarna 701 RAG System Statistics")
    print("=" * 50)
    print(f"Total chunks: {stats['total_chunks']:,}")
    print(f"Chunks with embeddings: {stats['chunks_with_embeddings']:,}")
    print(f"Embedding coverage: {stats['embedding_coverage']}%")
    print(f"Unique sources: {stats['unique_sources']}")
    print(f"Average safety level: {stats['avg_safety_level']}")
    print(f"Safety level range: {stats['safety_level_range']}")
    print(f"Text generation mode: {stats.get('text_generation_mode', 'unknown')}")
    
    # Calculate missing embeddings
    missing = stats['total_chunks'] - stats['chunks_with_embeddings']
    if missing > 0:
        print(f"\n⚠️  Missing embeddings: {missing:,} chunks need processing")
    else:
        print(f"\n✅ All chunks have embeddings!")


# Add commands to the CLI group
cli.add_command(test_system)
cli.add_command(query_system)
cli.add_command(stats)


if __name__ == '__main__':
    cli() 