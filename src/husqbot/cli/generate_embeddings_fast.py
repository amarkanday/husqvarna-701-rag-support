import click
import logging
from google.cloud import bigquery
from husqbot.models.embeddings import EmbeddingGenerator
import time
import json

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
    default=50,
    help='Number of chunks to process at once'
)
@click.option(
    '--checkpoint-file',
    default='embedding_checkpoint.json',
    help='File to save progress checkpoints'
)
def generate_embeddings_fast(
    project_id: str,
    location: str,
    dataset_id: str,
    table_id: str,
    batch_size: int,
    checkpoint_file: str
):
    """Generate embeddings for chunks without embeddings (optimized)."""
    
    # Initialize components
    client = bigquery.Client()
    embedding_generator = EmbeddingGenerator(project_id, location)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    
    # Load checkpoint if exists
    processed_chunks = set()
    try:
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
            processed_chunks = set(checkpoint.get('processed_chunks', []))
                         logger.info(
                 f"Loaded checkpoint with {len(processed_chunks)} processed chunks"
             )
    except FileNotFoundError:
        logger.info("No checkpoint file found, starting fresh")
    
    # Get chunks without embeddings
    query = f"""
    SELECT chunk_id, content
    FROM `{table_ref}`
    WHERE ARRAY_LENGTH(embedding) = 0
    ORDER BY chunk_id
    """
    
    logger.info("Fetching chunks without embeddings...")
    results = list(client.query(query))
    
    # Filter out already processed chunks
    remaining_chunks = [
        row for row in results 
        if row.chunk_id not in processed_chunks
    ]
    
    logger.info(f"Found {len(remaining_chunks)} chunks to process "
               f"(after filtering {len(processed_chunks)} already processed)")
    
    if not remaining_chunks:
        logger.info("All chunks already have embeddings!")
        return
    
    # Process chunks in batches
    processed = len(processed_chunks)
    total_to_process = len(results)
    
    for i in range(0, len(remaining_chunks), batch_size):
        batch = remaining_chunks[i:i + batch_size]
        
        # Extract texts and chunk IDs
        texts = [row.content for row in batch]
        chunk_ids = [row.chunk_id for row in batch]
        
        logger.info(f"Processing batch {i//batch_size + 1} "
                   f"({len(batch)} chunks)")
        
        try:
            # Generate embeddings
            embeddings = embedding_generator.generate_embeddings(texts)
            
            # Prepare update query for batch update
            updates = []
            for chunk_id, embedding in zip(chunk_ids, embeddings):
                # Convert embedding to BigQuery ARRAY format
                embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                updates.append(f"('{chunk_id}', {embedding_str})")
            
            # Use a more efficient batch update approach
            update_query = f"""
            UPDATE `{table_ref}` AS t
            SET embedding = temp.embedding
            FROM (
                SELECT chunk_id, embedding
                FROM UNNEST([
                    {','.join(f'STRUCT("{chunk_id}" as chunk_id, {embedding_str} as embedding)' 
                             for chunk_id, embedding_str in zip(chunk_ids, [
                                 '[' + ','.join(map(str, emb)) + ']' 
                                 for emb in embeddings
                             ]))}
                ])
            ) AS temp
            WHERE t.chunk_id = temp.chunk_id
            """
            
            # Execute update
            client.query(update_query)
            
            # Update progress tracking
            processed += len(batch)
            processed_chunks.update(chunk_ids)
            
            # Save checkpoint
            with open(checkpoint_file, 'w') as f:
                json.dump({
                    'processed_chunks': list(processed_chunks),
                    'last_processed': time.time()
                }, f)
            
            logger.info(f"Updated {processed}/{total_to_process} chunks "
                       f"({processed/total_to_process*100:.1f}%)")
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
            # Continue with next batch instead of stopping
            continue
    
    logger.info(f"Successfully generated embeddings for {processed} chunks!")
    
    # Clean up checkpoint file
    try:
        import os
        os.remove(checkpoint_file)
        logger.info("Removed checkpoint file")
    except:
        pass


if __name__ == '__main__':
    generate_embeddings_fast() 