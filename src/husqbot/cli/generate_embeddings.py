import click
import logging
from google.cloud import bigquery
from husqbot.models.embeddings import EmbeddingGenerator
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    '--dataset-id',
    default='husqvarna_rag_dataset',
    help='BigQuery dataset ID'
)
@click.option(
    '--table-id',
    default='document_chunks',
    help='BigQuery table ID'
)
@click.option(
    '--batch-size',
    default=5,
    help='Number of chunks to process at once'
)
def generate_embeddings(
    project_id: str,
    location: str,
    dataset_id: str,
    table_id: str,
    batch_size: int
):
    """Generate embeddings for chunks without embeddings."""
    
    # Initialize components
    client = bigquery.Client()
    embedding_generator = EmbeddingGenerator(project_id, location)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    
    # Get chunks without embeddings
    query = f"""
    SELECT chunk_id, content
    FROM `{table_ref}`
    WHERE ARRAY_LENGTH(embedding) = 0
    ORDER BY chunk_id
    """
    
    logger.info("Fetching chunks without embeddings...")
    results = list(client.query(query))
    logger.info(f"Found {len(results)} chunks without embeddings")
    
    if not results:
        logger.info("All chunks already have embeddings!")
        return
    
    # Process chunks in batches
    processed = 0
    for i in range(0, len(results), batch_size):
        batch = results[i:i + batch_size]
        
        # Extract texts and chunk IDs
        texts = [row.content for row in batch]
        chunk_ids = [row.chunk_id for row in batch]
        
        logger.info(
            f"Processing batch {i//batch_size + 1} ({len(batch)} chunks)"
        )
        
        try:
            # Generate embeddings
            embeddings = embedding_generator.generate_embeddings(texts)
            
            # Update chunks with embeddings
            for chunk_id, embedding in zip(chunk_ids, embeddings):
                update_query = f"""
                UPDATE `{table_ref}`
                SET embedding = {embedding}
                WHERE chunk_id = '{chunk_id}'
                """
                client.query(update_query)
            
            processed += len(batch)
            logger.info(
                f"Updated {processed}/{len(results)} chunks "
                f"({processed/len(results)*100:.1f}%)"
            )
            
            # Small delay to avoid rate limiting
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
            raise
    
    logger.info(f"Successfully generated embeddings for {processed} chunks!")


if __name__ == '__main__':
    generate_embeddings() 