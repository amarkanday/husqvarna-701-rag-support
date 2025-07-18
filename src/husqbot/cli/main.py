#!/usr/bin/env python3
"""
Command-line interface for the Husqvarna 701 RAG Support System.
"""

import os
import sys
import asyncio
import logging
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from .commands.setup import setup_system
from .commands.query import interactive_query, batch_query
from .commands.admin import show_stats, clear_cache
from ..core.rag_system import HusqvarnaRAGSystem
from ..utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

console = Console()


@click.group()
@click.version_option(version="1.0.0")
@click.option("--project-id", envvar="GOOGLE_CLOUD_PROJECT", help="Google Cloud project ID")
@click.option("--location", default="us-central1", help="Google Cloud location")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, project_id: Optional[str], location: str, verbose: bool):
    """
    Husqvarna 701 RAG Support System CLI
    
    AI-powered technical support system for Husqvarna 701 Enduro motorcycles.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not project_id:
        console.print("[red]Error: GOOGLE_CLOUD_PROJECT environment variable must be set[/red]")
        sys.exit(1)
    
    ctx.ensure_object(dict)
    ctx.obj["project_id"] = project_id
    ctx.obj["location"] = location


@cli.command()
@click.pass_context
def setup(ctx):
    """Setup the complete RAG system."""
    project_id = ctx.obj["project_id"]
    location = ctx.obj["location"]
    
    console.print(Panel.fit(
        f"[bold blue]Setting up Husqvarna RAG System[/bold blue]\n"
        f"Project: {project_id}\n"
        f"Location: {location}",
        border_style="blue"
    ))
    
    try:
        asyncio.run(setup_system(project_id, location))
        console.print("[green]✅ Setup completed successfully![/green]")
    except Exception as e:
        console.print(f"[red]❌ Setup failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive query mode."""
    project_id = ctx.obj["project_id"]
    location = ctx.obj["location"]
    
    console.print(Panel.fit(
        "[bold green]Husqvarna 701 RAG Support System - Interactive Mode[/bold green]\n"
        "Ask questions about your Husqvarna 701 Enduro maintenance and repair.\n"
        "Type 'quit' to exit.",
        border_style="green"
    ))
    
    try:
        asyncio.run(interactive_query(project_id, location))
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("query", required=True)
@click.option("--skill-level", "-s", default="intermediate", 
              type=click.Choice(["beginner", "intermediate", "expert"]),
              help="User skill level")
@click.option("--max-chunks", "-c", default=5, help="Maximum chunks to retrieve")
@click.option("--temperature", "-t", default=0.2, help="Response temperature")
@click.pass_context
def query(ctx, query: str, skill_level: str, max_chunks: int, temperature: float):
    """Query the RAG system with a single question."""
    project_id = ctx.obj["project_id"]
    location = ctx.obj["location"]
    
    console.print(f"[bold]Query:[/bold] {query}")
    console.print(f"[bold]Skill Level:[/bold] {skill_level}")
    
    try:
        asyncio.run(batch_query([query], project_id, location, skill_level, max_chunks, temperature))
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("queries", nargs=-1, required=True)
@click.option("--skill-level", "-s", default="intermediate",
              type=click.Choice(["beginner", "intermediate", "expert"]),
              help="User skill level")
@click.option("--output", "-o", help="Output file for results")
@click.pass_context
def batch(ctx, queries: tuple, skill_level: str, output: Optional[str]):
    """Process multiple queries in batch."""
    project_id = ctx.obj["project_id"]
    location = ctx.obj["location"]
    
    console.print(f"[bold]Processing {len(queries)} queries...[/bold]")
    
    try:
        asyncio.run(batch_query(list(queries), project_id, location, skill_level, output_file=output))
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def stats(ctx):
    """Show system statistics."""
    project_id = ctx.obj["project_id"]
    location = ctx.obj["location"]
    
    try:
        asyncio.run(show_stats(project_id, location))
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def cache(ctx):
    """Manage cache operations."""
    project_id = ctx.obj["project_id"]
    location = ctx.obj["location"]
    
    if Confirm.ask("Are you sure you want to clear the cache?"):
        try:
            asyncio.run(clear_cache(project_id, location))
            console.print("[green]✅ Cache cleared successfully![/green]")
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
            sys.exit(1)


@cli.command()
def examples():
    """Show example queries."""
    examples_data = {
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
    
    for category, queries in examples_data.items():
        table = Table(title=f"{category} Examples")
        table.add_column("Query", style="cyan")
        
        for query in queries:
            table.add_row(query)
        
        console.print(table)
        console.print()


@cli.command()
def config():
    """Show current configuration."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "Not set")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "Not set")
    
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Google Cloud Project", project_id)
    table.add_row("Location", location)
    table.add_row("Credentials", credentials)
    table.add_row("Python Version", sys.version.split()[0])
    
    console.print(table)


if __name__ == "__main__":
    cli() 