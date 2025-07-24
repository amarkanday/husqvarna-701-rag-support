"""
BigQuery setup for Husqvarna RAG Support System.
"""

import logging
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

logger = logging.getLogger(__name__)


def setup_bigquery_resources(
    project_id: str,
    dataset_id: str = "husqvarna_rag_dataset",
    location: str = "US"
) -> None:
    """Set up BigQuery dataset and tables for the RAG system.
    
    Args:
        project_id: Google Cloud project ID
        dataset_id: BigQuery dataset ID
        location: BigQuery location
    """
    client = bigquery.Client()
    
    # Create dataset
    dataset_ref = client.dataset(dataset_id)
    try:
        client.get_dataset(dataset_ref)
        logger.info(f"Dataset {dataset_id} already exists")
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location
        dataset = client.create_dataset(dataset)
        logger.info(f"Created dataset {dataset_id}")
    
    # Create document_chunks table
    chunks_table_ref = dataset_ref.table("document_chunks")
    try:
        client.get_table(chunks_table_ref)
        logger.info("Table document_chunks already exists")
    except NotFound:
        chunks_schema = [
            bigquery.SchemaField("chunk_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
            bigquery.SchemaField("source", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("page_number", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("safety_level", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        chunks_table = bigquery.Table(chunks_table_ref, schema=chunks_schema)
        chunks_table = client.create_table(chunks_table)
        logger.info("Created table document_chunks")
    
    # Create image_metadata table
    images_table_ref = dataset_ref.table("image_metadata")
    try:
        client.get_table(images_table_ref)
        logger.info("Table image_metadata already exists")
    except NotFound:
        images_schema = [
            bigquery.SchemaField("image_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("source", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("page_number", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("image_path", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("description", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("ocr_text", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("image_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("complexity_level", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("width", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("height", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("image_base64", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        images_table = bigquery.Table(images_table_ref, schema=images_schema)
        images_table = client.create_table(images_table)
        logger.info("Created table image_metadata")


if __name__ == "__main__":
    import os
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
    
    setup_bigquery_resources(project_id) 