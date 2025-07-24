"""
CLI for processing images from Husqvarna manuals.
"""

import click
import logging
import os
from pathlib import Path
from typing import Optional

from google.cloud import bigquery
from husqbot.data.image_processor import ImageProcessor
from husqbot.storage.bigquery_setup import setup_bigquery_resources

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Process images from Husqvarna 701 manuals."""
    pass


@click.command()
@click.option('--project-id', envvar='GOOGLE_CLOUD_PROJECT', 
              help='Google Cloud project ID', required=True)
@click.option('--location', default='us-central1', help='Google Cloud region')
@click.option('--dataset-id', default='husqvarna_rag_dataset',
              help='BigQuery dataset ID')
@click.option('--output-dir', help='Directory to save extracted images')
@click.option('--manual-type', 
              type=click.Choice(['owners', 'repair', 'both']),
              default='both', help='Type of manual to process')
@click.option('--part-number', type=int, 
              help='Specific part number to process (e.g., 1 for part001)')
def extract_images(
    project_id: str,
    location: str,
    dataset_id: str,
    output_dir: Optional[str],
    manual_type: str,
    part_number: Optional[int]
):
    """Extract and analyze images from PDF manuals."""
    
    # Setup BigQuery resources first
    logger.info("Setting up BigQuery resources...")
    setup_bigquery_resources(project_id, dataset_id)
    
    # Initialize image processor
    processor = ImageProcessor(project_id, location)
    
    # Set up output directory
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Images will be saved to: {output_path}")
    
    # Get data directory
    data_dir = Path(__file__).parent.parent.parent.parent / "data"
    
    # Determine which manuals to process
    manual_types = []
    if manual_type == 'both':
        manual_types = ['owners', 'repair']
    else:
        manual_types = [manual_type]
    
    total_images = 0
    
    for m_type in manual_types:
        logger.info(f"Processing {m_type} manual images...")
        
        split_dir = data_dir / "raw" / f"{m_type}_manual" / "split"
        
        if not split_dir.exists():
            logger.warning(f"Directory not found: {split_dir}")
            continue
        
        # Get PDF files to process
        if part_number:
            pdf_files = [split_dir / f"husky_{'om' if m_type == 'owners' else 'rm'}_701_part{part_number:03d}.pdf"]
            pdf_files = [f for f in pdf_files if f.exists()]
        else:
            pdf_files = sorted(split_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {split_dir}")
            continue
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            logger.info(f"Extracting images from: {pdf_file.name}")
            
            try:
                # Extract images
                images_metadata = processor.extract_images_from_pdf(
                    str(pdf_file),
                    output_dir
                )
                
                if images_metadata:
                    # Store in BigQuery
                    _store_images_in_bigquery(
                        project_id, dataset_id, images_metadata
                    )
                    
                    total_images += len(images_metadata)
                    logger.info(f"Processed {len(images_metadata)} images "
                               f"from {pdf_file.name}")
                else:
                    logger.info(f"No images extracted from {pdf_file.name}")
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
                continue
    
    logger.info(f"Total images processed: {total_images}")
    
    # Create summary
    if total_images > 0:
        _show_image_summary(project_id, dataset_id)


@click.command()
@click.option('--project-id', envvar='GOOGLE_CLOUD_PROJECT',
              help='Google Cloud project ID', required=True)
@click.option('--dataset-id', default='husqvarna_rag_dataset',
              help='BigQuery dataset ID')
def show_image_stats(project_id: str, dataset_id: str):
    """Show statistics about processed images."""
    _show_image_summary(project_id, dataset_id)


@click.command()
@click.option('--project-id', envvar='GOOGLE_CLOUD_PROJECT',
              help='Google Cloud project ID', required=True)
@click.option('--dataset-id', default='husqvarna_rag_dataset',
              help='BigQuery dataset ID')
@click.option('--query', '-q', required=True,
              help='Search query for images')
@click.option('--limit', default=5, help='Maximum number of results')
def search_images(project_id: str, dataset_id: str, query: str, limit: int):
    """Search for images by description or content."""
    
    client = bigquery.Client()
    
    # Search in description and OCR text
    sql_query = f"""
    SELECT 
        image_id,
        source,
        page_number,
        description,
        image_type,
        complexity_level,
        ocr_text
    FROM `{project_id}.{dataset_id}.image_metadata`
    WHERE 
        LOWER(description) LIKE LOWER('%{query}%')
        OR LOWER(ocr_text) LIKE LOWER('%{query}%')
    ORDER BY page_number
    LIMIT {limit}
    """
    
    try:
        results = client.query(sql_query).result()
        
        click.echo(f"\n🔍 Image search results for: '{query}'\n")
        click.echo("=" * 60)
        
        count = 0
        for row in results:
            count += 1
            click.echo(f"\n{count}. {row.source} (Page {row.page_number})")
            click.echo(f"   Type: {row.image_type}")
            click.echo(f"   Complexity: {row.complexity_level}/3")
            click.echo(f"   Description: {row.description[:150]}...")
            if row.ocr_text:
                click.echo(f"   Text: {row.ocr_text[:100]}...")
        
        if count == 0:
            click.echo("No images found matching your query.")
        else:
            click.echo(f"\nFound {count} matching images.")
            
    except Exception as e:
        click.echo(f"Error searching images: {e}")


def _store_images_in_bigquery(
    project_id: str, 
    dataset_id: str, 
    images_metadata: list
):
    """Store image metadata in BigQuery."""
    client = bigquery.Client()
    table_ref = f"{project_id}.{dataset_id}.image_metadata"
    
    # Prepare rows for BigQuery
    rows = []
    for img in images_metadata:
        row = {
            'image_id': img['image_id'],
            'source': img['source'],
            'page_number': img['page_number'],
            'image_path': img.get('image_path'),
            'description': img['description'],
            'ocr_text': img.get('ocr_text', ''),
            'image_type': img['image_type'],
            'complexity_level': img['complexity_level'],
            'width': img['width'],
            'height': img['height'],
            'image_base64': img.get('image_base64'),
            'created_at': img['created_at']
        }
        rows.append(row)
    
    # Insert into BigQuery
    errors = client.insert_rows_json(table_ref, rows)
    if errors:
        raise RuntimeError(f"Error inserting image rows: {errors}")


def _show_image_summary(project_id: str, dataset_id: str):
    """Show summary statistics of processed images."""
    client = bigquery.Client()
    
    # Get basic stats
    stats_query = f"""
    SELECT 
        COUNT(*) as total_images,
        COUNT(DISTINCT source) as total_sources,
        AVG(complexity_level) as avg_complexity
    FROM `{project_id}.{dataset_id}.image_metadata`
    """
    
    # Get breakdown by type
    type_query = f"""
    SELECT 
        image_type,
        COUNT(*) as count
    FROM `{project_id}.{dataset_id}.image_metadata`
    GROUP BY image_type
    ORDER BY count DESC
    """
    
    # Get breakdown by complexity
    complexity_query = f"""
    SELECT 
        complexity_level,
        COUNT(*) as count
    FROM `{project_id}.{dataset_id}.image_metadata`
    GROUP BY complexity_level
    ORDER BY complexity_level
    """
    
    try:
        stats = list(client.query(stats_query).result())[0]
        types = list(client.query(type_query).result())
        complexities = list(client.query(complexity_query).result())
        
        click.echo("\n📊 Image Processing Summary")
        click.echo("=" * 40)
        click.echo(f"Total Images: {stats.total_images}")
        click.echo(f"Sources: {stats.total_sources}")
        click.echo(f"Avg Complexity: {stats.avg_complexity:.1f}/3")
        
        click.echo("\n📈 By Image Type:")
        for row in types:
            click.echo(f"  {row.image_type}: {row.count}")
        
        click.echo("\n🎯 By Complexity Level:")
        complexity_labels = {1: "Basic", 2: "Intermediate", 3: "Advanced"}
        for row in complexities:
            label = complexity_labels.get(row.complexity_level, "Unknown")
            click.echo(f"  {label} (Level {row.complexity_level}): {row.count}")
            
    except Exception as e:
        click.echo(f"Error getting image statistics: {e}")


cli.add_command(extract_images)
cli.add_command(show_image_stats)
cli.add_command(search_images)


if __name__ == '__main__':
    cli() 