"""
CLI query commands for Husqvarna RAG Support System.
"""

import asyncio
import logging
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ...core.rag_system import HusqvarnaRAGSystem

logger = logging.getLogger(__name__)
console = Console()


async def interactive_query(project_id: str, location: str):
    """
    Start interactive query mode.
    
    Args:
        project_id: Google Cloud project ID
        location: Google Cloud location
    """
    # Initialize RAG system
    rag_system = HusqvarnaRAGSystem(project_id, location)
    
    console.print(Panel.fit(
        "[bold green]🏍️  Husqvarna 701 Enduro Manual Assistant[/bold green]\n"
        "Ask me anything about your motorcycle!\n"
        "Type 'quit' to exit\n"
        "Type 'help' for example questions",
        border_style="green"
    ))
    
    while True:
        try:
            question = Prompt.ask("\n[bold cyan]Your question[/bold cyan]")
            
            if question.lower() in ['quit', 'exit', 'q']:
                console.print("[yellow]Thanks for using the Husqvarna Manual Assistant![/yellow]")
                break
            
            if question.lower() == 'help':
                show_example_questions()
                continue
            
            if not question.strip():
                continue
            
            console.print("\n[dim]Searching manual...[/dim]")
            
            # Query the system
            result = await rag_system.query_system(
                query=question,
                user_skill_level="intermediate"
            )
            
            # Display answer
            console.print(f"\n[bold green]📖 Answer:[/bold green]")
            console.print(result.answer)
            
            # Display sources
            console.print(f"\n[bold blue]📚 Sources:[/bold blue] Found {len(result.sources)} relevant sections")
            for i, source in enumerate(result.sources[:3], 1):  # Show top 3 sources
                console.print(f"  {i}. {source.get('section', 'Unknown')} - Page {source.get('page_number', 'N/A')}")
            
            # Display metadata
            console.print(f"\n[dim]Confidence: {result.confidence:.2f} | Processing time: {result.processing_time:.2f}s[/dim]")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")


async def batch_query(
    queries: List[str],
    project_id: str,
    location: str,
    user_skill_level: str = "intermediate",
    max_chunks: int = 5,
    temperature: float = 0.2,
    output_file: Optional[str] = None
):
    """
    Process multiple queries in batch.
    
    Args:
        queries: List of queries to process
        project_id: Google Cloud project ID
        location: Google Cloud location
        user_skill_level: User's skill level
        max_chunks: Maximum chunks to retrieve
        temperature: Generation temperature
        output_file: Optional output file for results
    """
    # Initialize RAG system
    rag_system = HusqvarnaRAGSystem(project_id, location)
    
    console.print(f"[bold]Processing {len(queries)} queries...[/bold]")
    
    results = []
    
    for i, query in enumerate(queries, 1):
        try:
            console.print(f"\n[dim]Processing query {i}/{len(queries)}: {query[:50]}...[/dim]")
            
            result = await rag_system.query_system(
                query=query,
                user_skill_level=user_skill_level,
                max_chunks=max_chunks,
                temperature=temperature
            )
            
            results.append({
                "query": query,
                "answer": result.answer,
                "confidence": result.confidence,
                "processing_time": result.processing_time,
                "sources_count": len(result.sources),
                "success": True
            })
            
        except Exception as e:
            console.print(f"[red]❌ Error processing query {i}: {e}[/red]")
            results.append({
                "query": query,
                "error": str(e),
                "success": False
            })
    
    # Display results
    display_batch_results(results)
    
    # Save to file if requested
    if output_file:
        save_results_to_file(results, output_file)


def show_example_questions():
    """Show example questions for the user."""
    examples = {
        "Maintenance": [
            "How do I check the engine oil level?",
            "What is the recommended tire pressure?",
            "How often should I change the oil?",
            "How do I adjust the chain tension?"
        ],
        "Troubleshooting": [
            "Engine won't start, what should I check?",
            "Bike is running rough at idle",
            "Brakes feel spongy",
            "Battery keeps dying"
        ],
        "Repair": [
            "How do I replace the air filter?",
            "Brake pad replacement procedure",
            "How to adjust valve clearances",
            "Clutch cable adjustment"
        ],
        "Specifications": [
            "What are the valve clearance specs?",
            "Engine oil capacity",
            "Tire size specifications",
            "Battery specifications"
        ]
    }
    
    for category, questions in examples.items():
        table = Table(title=f"{category} Examples", show_header=False)
        table.add_column("Question", style="cyan")
        
        for question in questions:
            table.add_row(question)
        
        console.print(table)
        console.print()


def display_batch_results(results: List[dict]):
    """Display batch query results in a table."""
    
    # Create results table
    table = Table(title="Batch Query Results")
    table.add_column("Query", style="cyan", width=40)
    table.add_column("Status", style="green")
    table.add_column("Confidence", style="yellow")
    table.add_column("Time (s)", style="blue")
    table.add_column("Sources", style="magenta")
    
    successful_count = 0
    total_time = 0
    
    for result in results:
        if result["success"]:
            table.add_row(
                result["query"][:40] + "..." if len(result["query"]) > 40 else result["query"],
                "✅ Success",
                f"{result['confidence']:.2f}",
                f"{result['processing_time']:.2f}",
                str(result["sources_count"])
            )
            successful_count += 1
            total_time += result["processing_time"]
        else:
            table.add_row(
                result["query"][:40] + "..." if len(result["query"]) > 40 else result["query"],
                "❌ Failed",
                "N/A",
                "N/A",
                "N/A"
            )
    
    console.print(table)
    
    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Successful queries: {successful_count}/{len(results)}")
    console.print(f"  Total processing time: {total_time:.2f}s")
    console.print(f"  Average time per query: {total_time/len(results):.2f}s")


def save_results_to_file(results: List[dict], filename: str):
    """Save batch results to a file."""
    import json
    from datetime import datetime
    
    output_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_queries": len(results),
        "successful_queries": len([r for r in results if r["success"]]),
        "results": results
    }
    
    try:
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        console.print(f"[green]✅ Results saved to {filename}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error saving results: {e}[/red]")


async def test_rag_system(project_id: str, location: str):
    """
    Test the RAG system with sample questions.
    
    Args:
        project_id: Google Cloud project ID
        location: Google Cloud location
    """
    # Initialize RAG system
    rag_system = HusqvarnaRAGSystem(project_id, location)
    
    test_questions = [
        "How do I start the Husqvarna 701 Enduro motorcycle?",
        "What is the correct tire pressure for different riding conditions?",
        "How do I check the engine oil level?",
        "What should I do if the engine won't start when I press the start button?",
        "How do I adjust the suspension compression damping?",
        "What type of fuel should I use and what is the tank capacity?",
        "How do I add brake fluid to the front brake system?",
        "What are the riding modes and how do I change them?",
        "What should I do if the engine overheats?",
        "What are the service intervals for this motorcycle?"
    ]
    
    console.print("[bold]Testing RAG System with Husqvarna 701 Enduro Owner's Manual[/bold]")
    console.print("=" * 70)
    
    for i, question in enumerate(test_questions, 1):
        console.print(f"\n[bold cyan]🔍 Test Question {i}:[/bold cyan] {question}")
        console.print("-" * 50)
        
        try:
            result = await rag_system.query_system(
                query=question,
                user_skill_level="intermediate"
            )
            
            console.print(f"[green]📖 Answer:[/green] {result.answer}")
            console.print(f"[blue]📚 Found {len(result.sources)} relevant manual sections[/blue]")
            console.print(f"[dim]Confidence: {result.confidence:.2f} | Time: {result.processing_time:.2f}s[/dim]")
            
        except Exception as e:
            console.print(f"[red]❌ Error processing question: {e}[/red]")
        
        console.print("\n" + "=" * 70) 