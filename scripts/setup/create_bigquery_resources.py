#!/usr/bin/env python3
"""
Script to create BigQuery resources for the Husqvarna RAG Support System.
"""

import os
import sys
import asyncio
import logging
from typing import Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from husqbot.storage.bigquery_client import BigQueryClient
from husqbot.utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def create_bigquery_resources(
    project_id: Optional[str] = None,
    location: str = "us-central1",
    dataset_id: str = "husqvarna_rag_dataset",
    table_id: str = "document_chunks"
):
    """
    Create BigQuery dataset and tables for the RAG system.
    
    Args:
        project_id: Google Cloud project ID
        location: BigQuery location
        dataset_id: Dataset ID to create
        table_id: Table ID for document chunks
    """
    if not project_id:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT environment variable must be set"
            )
    
    logger.info(f"Creating BigQuery resources for project: {project_id}")
    logger.info(f"Location: {location}")
    logger.info(f"Dataset: {dataset_id}")
    logger.info(f"Table: {table_id}")
    
    try:
        # Initialize BigQuery client
        client = BigQueryClient(project_id, location)
        
        # Create dataset
        logger.info("Creating dataset...")
        await client.create_dataset_if_not_exists(dataset_id)
        logger.info(f"Dataset '{dataset_id}' created/verified successfully")
        
        # Create tables
        logger.info("Creating tables...")
        await client.create_tables_if_not_exists(dataset_id, table_id)
        logger.info(f"Tables created/verified successfully")
        
        # Verify setup
        chunk_count = await client.get_chunk_count(dataset_id, table_id)
        logger.info(f"Current chunk count: {chunk_count}")
        
        logger.info("BigQuery resources setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to create BigQuery resources: {e}")
        raise


def main():
    """Main function to run the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create BigQuery resources for Husqvarna RAG System"
    )
    parser.add_argument(
        "--project-id",
        help="Google Cloud project ID (defaults to GOOGLE_CLOUD_PROJECT env var)"
    )
    parser.add_argument(
        "--location",
        default="us-central1",
        help="BigQuery location (default: us-central1)"
    )
    parser.add_argument(
        "--dataset-id",
        default="husqvarna_rag_dataset",
        help="Dataset ID (default: husqvarna_rag_dataset)"
    )
    parser.add_argument(
        "--table-id",
        default="document_chunks",
        help="Table ID for document chunks (default: document_chunks)"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(create_bigquery_resources(
            project_id=args.project_id,
            location=args.location,
            dataset_id=args.dataset_id,
            table_id=args.table_id
        ))
        print("✅ BigQuery resources created successfully!")
        
    except Exception as e:
        print(f"❌ Failed to create BigQuery resources: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 