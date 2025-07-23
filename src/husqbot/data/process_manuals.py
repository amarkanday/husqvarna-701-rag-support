import os
import json
from pathlib import Path
from google.cloud import bigquery
from .document_processor import DocumentProcessor
from ..models.embeddings import EmbeddingGenerator


def process_and_store_manuals(
    project_id: str,
    location: str = "us-central1",
    dataset_id: str = "husqvarna_rag_dataset",
    table_id: str = "document_chunks"
) -> None:
    """Process manuals and store chunks in BigQuery.
    
    Args:
        project_id: Google Cloud project ID
        location: Google Cloud region
        dataset_id: BigQuery dataset ID
        table_id: BigQuery table ID
    """
    # Initialize processors
    doc_processor = DocumentProcessor()
    embedding_generator = EmbeddingGenerator(project_id, location)
    
    # Get paths to manuals
    data_dir = Path(__file__).parent.parent.parent.parent / "data"
    owners_dir = data_dir / "raw" / "owners_manual"
    repair_dir = data_dir / "raw" / "repair_manual"
    
    # Process owner's manual
    owners_chunks = []
    for pdf_file in owners_dir.glob("*.pdf"):
        chunks = doc_processor.process_pdf(str(pdf_file))
        owners_chunks.extend(chunks)
    
    # Process repair manual
    repair_chunks = []
    for pdf_file in repair_dir.glob("*.pdf"):
        chunks = doc_processor.process_pdf(str(pdf_file))
        repair_chunks.extend(chunks)
    
    # Generate embeddings
    all_chunks = owners_chunks + repair_chunks
    chunks_with_embeddings = (
        embedding_generator.generate_embeddings_for_chunks(all_chunks)
    )
    
    # Store in BigQuery
    client = bigquery.Client()
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    
    # Convert chunks to rows
    rows = []
    for chunk in chunks_with_embeddings:
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
    
    # Insert rows
    errors = client.insert_rows_json(table_ref, rows)
    if errors:
        raise RuntimeError(f"Error inserting rows: {errors}")
    
    print(f"Successfully processed and stored {len(rows)} chunks")


def process_single_manual(
    project_id: str,
    location: str = "us-central1",
    manual_type: str = "owners",
    dataset_id: str = "husqvarna_rag_dataset",
    table_id: str = "document_chunks",
    batch_size: int = 5,
    input_file: str = None,
    store_embeddings: bool = False
) -> None:
    """Process a single manual and store chunks in BigQuery.
    
    Args:
        project_id: Google Cloud project ID
        location: Google Cloud region
        manual_type: Type of manual (owners/repair)
        dataset_id: BigQuery dataset ID
        table_id: BigQuery table ID
        batch_size: Number of chunks to process at once
        input_file: Specific PDF file to process
        store_embeddings: Whether to generate and store embeddings
    """
    # Initialize processors
    doc_processor = DocumentProcessor()
    embedding_generator = None
    if store_embeddings:
        embedding_generator = EmbeddingGenerator(project_id, location)
    
    # Get path to manual
    if input_file:
        pdf_files = [Path(input_file)]
    else:
        data_dir = Path(__file__).parent.parent.parent.parent / "data"
        manual_dir = data_dir / "raw" / f"{manual_type}_manual"
        pdf_files = list(manual_dir.glob("*.pdf"))
    
    # Process manual
    total_chunks = 0
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file}...")
        
        # Extract chunks from PDF
        chunks = doc_processor.process_pdf(str(pdf_file))
        
        # Save chunks to temporary file
        temp_dir = Path("data/processed/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / f"{pdf_file.stem}_chunks.json"
        
        with open(temp_file, 'w') as f:
            json.dump(chunks, f)
        
        print(f"Saved {len(chunks)} chunks to {temp_file}")
        
        # Process chunks in batches
        with open(temp_file, 'r') as f:
            chunks = json.load(f)
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                print(f"Processing batch {i//batch_size + 1}...")
                
                # Generate embeddings if requested
                if store_embeddings:
                    batch = embedding_generator.generate_embeddings_for_chunks(
                        batch
                    )
                else:
                    # Add placeholder embeddings
                    for chunk in batch:
                        chunk['embedding'] = []
                
                # Store batch in BigQuery
                client = bigquery.Client()
                table_ref = f"{project_id}.{dataset_id}.{table_id}"
                
                # Convert chunks to rows
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
                
                # Insert rows
                errors = client.insert_rows_json(table_ref, rows)
                if errors:
                    raise RuntimeError(f"Error inserting rows: {errors}")
                
                print(f"Stored {len(rows)} chunks from batch")
                total_chunks += len(rows)
        
        # Clean up temporary file
        temp_file.unlink()
    
    print(f"Successfully processed and stored {total_chunks} chunks total")


if __name__ == "__main__":
    # Get project ID from environment variable
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
    
    process_and_store_manuals(project_id) 