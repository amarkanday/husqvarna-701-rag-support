#!/usr/bin/env python3
"""
Command-line interface for the Husqvarna 701 RAG Support System.
"""

import click
from pathlib import Path
from ..core.rag_system import HusqvarnaRAGSystem


@click.group()
def cli():
    """Husqvarna 701 RAG Support System CLI."""
    pass


@cli.command()
@click.option(
    '--project-id',
    envvar='GOOGLE_CLOUD_PROJECT',
    help='Google Cloud project ID'
)
@click.option(
    '--location',
    default='us-central1',
    help='Google Cloud region'
)
@click.option(
    '--manual-type',
    type=click.Choice(['owners', 'repair']),
    required=True,
    help='Type of manual to process'
)
@click.option(
    '--part-number',
    type=int,
    required=True,
    help='Part number of the split PDF to process'
)
@click.option(
    '--store-embeddings',
    is_flag=True,
    help='Generate and store embeddings'
)
def process_part(
    project_id: str,
    location: str,
    manual_type: str,
    part_number: int,
    store_embeddings: bool
):
    """Process a single part of a split manual."""
    data_dir = Path(__file__).parent.parent.parent.parent / "data"
    split_dir = data_dir / "raw" / f"{manual_type}_manual" / "split"
    
    # Find the specific part file
    pattern = f"*_part{part_number:03d}.pdf"
    part_file = list(split_dir.glob(pattern))
    if not part_file:
        raise click.ClickException(f"Part {part_number} not found")
    
    from ..data.process_manuals import process_single_manual
    process_single_manual(
        project_id,
        location,
        manual_type,
        input_file=str(part_file[0]),
        store_embeddings=store_embeddings
    )


@cli.command()
@click.option(
    '--project-id',
    envvar='GOOGLE_CLOUD_PROJECT',
    help='Google Cloud project ID'
)
@click.option(
    '--location',
    default='us-central1',
    help='Google Cloud region'
)
def interactive(project_id: str, location: str):
    """Start interactive query session."""
    rag_system = HusqvarnaRAGSystem(project_id, location)
    
    click.echo("Welcome to the Husqvarna 701 RAG Support System!")
    click.echo("Type 'exit' to quit.\n")
    
    while True:
        query = click.prompt("Your question")
        if query.lower() == 'exit':
            break
        
        try:
            response = rag_system.query(query)
            click.echo(f"\n{response}\n")
        except Exception as e:
            click.echo(f"Error: {str(e)}\n")


if __name__ == '__main__':
    cli() 