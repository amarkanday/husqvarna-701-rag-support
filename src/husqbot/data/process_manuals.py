import logging
import json
from pathlib import Path
from typing import Optional

from google.cloud import bigquery

from husqbot.data.document_processor import DocumentProcessor
from husqbot.models.embeddings import EmbeddingGenerator


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_single_manual(
    project_id: str,
    location: str = "us-central1",
    manual_type: str = "owners",
    dataset_id: str = "husqvarna_rag_dataset",
    table_id: str = "document_chunks",
    batch_size: int = 5,
    input_file: Optional[str] = None,
    store_embeddings: bool = False
) -> None:
    """Process a single manual or part of a manual.
    
    Args:
        project_id: Google Cloud project ID
        location: Google Cloud region
        manual_type: Type of manual (owners/repair)
        dataset_id: BigQuery dataset ID
        table_id: BigQuery table ID
        batch_size: Number of chunks to process at once
        input_file: Specific PDF file to process (if None, process all)
        store_embeddings: Whether to generate and store embeddings
    """
    doc_processor = DocumentProcessor()
    embedding_generator = None
    if store_embeddings:
        embedding_generator = EmbeddingGenerator(project_id, location)
    
    # Get the data directory
    data_dir = Path(__file__).parent.parent.parent.parent / "data"
    split_dir = data_dir / "raw" / f"{manual_type}_manual" / "split"
    
    # Process the specified file
    if input_file:
        pdf_file = split_dir / input_file
        logger.info(f"Processing {pdf_file}...")
        
        # Extract chunks
        chunks = doc_processor.process_pdf(str(pdf_file))
        
        # Create a temporary file to store chunks
        temp_dir = data_dir / "processed" / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / f"{pdf_file.stem}_chunks.json"
        
        # Save chunks to temporary file
        with open(temp_file, 'w') as f:
            json.dump(chunks, f)
        
        # Process chunks in batches
        client = bigquery.Client()
        table_ref = f"{project_id}.{dataset_id}.{table_id}"
        
        with open(temp_file, 'r') as f:
            chunks = json.load(f)
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                if store_embeddings and embedding_generator:
                    texts = [chunk['content'] for chunk in batch]
                    embeddings = embedding_generator.generate_embeddings(texts)
                    for chunk, embedding in zip(batch, embeddings):
                        chunk['embedding'] = embedding
                else:
                    for chunk in batch:
                        chunk['embedding'] = []
                
                # Prepare rows for BigQuery
                rows = []
                for chunk in batch:
                    row = {
                        'chunk_id': chunk['chunk_id'],
                        'content': chunk['content'],
                        'embedding': chunk['embedding'],
                        'source': chunk['source'],
                        'page_number': chunk['page_number'],
                        'safety_level': chunk['safety_level'],
                        'created_at': chunk['created_at']
                    }
                    rows.append(row)
                
                # Insert into BigQuery
                errors = client.insert_rows_json(table_ref, rows)
                if errors:
                    raise RuntimeError(f"Error inserting rows: {errors}")
        
        # Clean up temporary file
        temp_file.unlink()
    else:
        # Process all files in the directory
        pdf_files = sorted(split_dir.glob("*.pdf"))
        for pdf_file in pdf_files:
            process_single_manual(
                project_id=project_id,
                location=location,
                manual_type=manual_type,
                dataset_id=dataset_id,
                table_id=table_id,
                batch_size=batch_size,
                input_file=pdf_file.name,
                store_embeddings=store_embeddings
            ) 