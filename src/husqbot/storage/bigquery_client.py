"""
BigQuery client for Husqvarna RAG Support System.
"""

import logging
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, Conflict

logger = logging.getLogger(__name__)


class BigQueryClient:
    """BigQuery client for managing manual chunks and embeddings."""
    
    def __init__(self, project_id: str, location: str = "us-central1"):
        """
        Initialize BigQuery client.
        
        Args:
            project_id: Google Cloud project ID
            location: BigQuery location
        """
        self.project_id = project_id
        self.location = location
        self.client = bigquery.Client(project=project_id)
        
        logger.info(f"Initialized BigQuery client for project {project_id}")
    
    async def create_dataset_if_not_exists(self, dataset_id: str = "husqvarna_rag_dataset") -> None:
        """
        Create BigQuery dataset if it doesn't exist.
        
        Args:
            dataset_id: Dataset ID to create
        """
        dataset_ref = self.client.dataset(dataset_id)
        
        try:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = self.location
            dataset = self.client.create_dataset(dataset)
            logger.info(f"Created dataset: {self.project_id}.{dataset_id}")
        except Conflict:
            logger.info(f"Dataset {dataset_id} already exists")
        except Exception as e:
            logger.error(f"Error creating dataset {dataset_id}: {e}")
            raise
    
    async def create_tables_if_not_exists(
        self, 
        dataset_id: str = "husqvarna_rag_dataset",
        table_id: str = "manual_chunks"
    ) -> None:
        """
        Create BigQuery tables if they don't exist.
        
        Args:
            dataset_id: Dataset ID
            table_id: Table ID for manual chunks
        """
        # Create manual chunks table
        await self._create_manual_chunks_table(dataset_id, table_id)
        
        # Create vector index
        await self._create_vector_index(dataset_id, table_id)
    
    async def _create_manual_chunks_table(self, dataset_id: str, table_id: str) -> None:
        """Create table to store manual chunks with embeddings."""
        
        schema = [
            bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("section", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("subsection", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("page_number", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("chunk_type", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("manual_type", "STRING", mode="NULLABLE"),  # owners, repair
            bigquery.SchemaField("embedding", "REPEATED FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="NULLABLE"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="NULLABLE"),
        ]
        
        table_ref = self.client.dataset(dataset_id).table(table_id)
        table = bigquery.Table(table_ref, schema=schema)
        
        try:
            table = self.client.create_table(table)
            logger.info(f"Created table: {self.project_id}.{dataset_id}.{table_id}")
        except Conflict:
            logger.info(f"Table {table_id} already exists")
        except Exception as e:
            logger.error(f"Error creating table {table_id}: {e}")
            raise
    
    async def _create_vector_index(self, dataset_id: str, table_id: str) -> None:
        """Create a vector index for efficient similarity search."""
        
        query = f"""
        CREATE OR REPLACE VECTOR INDEX manual_embedding_index
        ON `{self.project_id}.{dataset_id}.{table_id}` (embedding)
        OPTIONS (
            index_type = 'IVF',
            distance_type = 'COSINE'
        )
        """
        
        try:
            job = self.client.query(query)
            job.result()
            logger.info("Vector index created successfully")
        except Exception as e:
            logger.warning(f"Error creating vector index (may already exist): {e}")
    
    async def insert_chunks_with_embeddings(
        self, 
        chunks: List[Dict[str, Any]], 
        embeddings: List[List[float]],
        dataset_id: str = "husqvarna_rag_dataset",
        table_id: str = "manual_chunks"
    ) -> None:
        """
        Insert manual chunks with their embeddings into BigQuery.
        
        Args:
            chunks: List of chunk dictionaries
            embeddings: List of embedding vectors
            dataset_id: Dataset ID
            table_id: Table ID
        """
        from datetime import datetime
        
        # Prepare data for BigQuery
        rows_to_insert = []
        
        for chunk, embedding in zip(chunks, embeddings):
            row = {
                "id": chunk.get("id"),
                "section": chunk.get("section"),
                "subsection": chunk.get("subsection"),
                "content": chunk.get("content"),
                "page_number": chunk.get("page_number"),
                "chunk_type": chunk.get("chunk_type"),
                "manual_type": chunk.get("manual_type", "owners"),
                "embedding": embedding,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            rows_to_insert.append(row)
        
        # Insert into BigQuery
        table_ref = self.client.dataset(dataset_id).table(table_id)
        table = self.client.get_table(table_ref)
        
        errors = self.client.insert_rows_json(table, rows_to_insert)
        
        if errors:
            logger.error(f"Errors inserting rows: {errors}")
            raise Exception(f"Failed to insert chunks: {errors}")
        else:
            logger.info(f"Successfully inserted {len(rows_to_insert)} chunks into BigQuery")
    
    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        max_results: int = 5,
        safety_level: Optional[int] = None,
        dataset_id: str = "husqvarna_rag_dataset",
        table_id: str = "manual_chunks"
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query_embedding: Query embedding vector
            max_results: Maximum number of results to return
            safety_level: Optional safety level filter
            dataset_id: Dataset ID
            table_id: Table ID
            
        Returns:
            List of similar chunks with metadata
        """
        # Convert embedding to string format for SQL
        embedding_str = str(query_embedding)
        
        # Build the query
        safety_filter = ""
        if safety_level is not None:
            safety_filter = f"AND chunk_type IN ('warning', 'safety')"
        
        similarity_query = f"""
        SELECT 
            id,
            section,
            subsection,
            content,
            page_number,
            chunk_type,
            manual_type,
            VECTOR_SEARCH(
                embedding,
                {embedding_str},
                top_k => {max_results}
            ) as similarity_score
        FROM `{self.project_id}.{dataset_id}.{table_id}`
        WHERE embedding IS NOT NULL {safety_filter}
        ORDER BY similarity_score DESC
        LIMIT {max_results}
        """
        
        # Execute the query
        query_job = self.client.query(similarity_query)
        results = query_job.result()
        
        # Convert to list of dictionaries
        chunks = []
        for row in results:
            chunk = {
                "id": row.id,
                "section": row.section,
                "subsection": row.subsection,
                "content": row.content,
                "page_number": row.page_number,
                "chunk_type": row.chunk_type,
                "manual_type": row.manual_type,
                "similarity_score": row.similarity_score
            }
            chunks.append(chunk)
        
        return chunks
    
    async def get_chunk_count(
        self, 
        dataset_id: str = "husqvarna_rag_dataset",
        table_id: str = "manual_chunks"
    ) -> int:
        """
        Get the total number of chunks in the table.
        
        Args:
            dataset_id: Dataset ID
            table_id: Table ID
            
        Returns:
            Total number of chunks
        """
        query = f"""
        SELECT COUNT(*) as count
        FROM `{self.project_id}.{dataset_id}.{table_id}`
        """
        
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            return next(results).count
        except Exception as e:
            logger.error(f"Error getting chunk count: {e}")
            return 0
    
    async def analyze_manual_sections(
        self,
        dataset_id: str = "husqvarna_rag_dataset",
        table_id: str = "manual_chunks"
    ) -> Dict[str, Any]:
        """
        Analyze the distribution of content types in the manual.
        
        Args:
            dataset_id: Dataset ID
            table_id: Table ID
            
        Returns:
            Analysis results
        """
        query = f"""
        SELECT 
            chunk_type,
            manual_type,
            COUNT(*) as count,
            AVG(LENGTH(content)) as avg_content_length
        FROM `{self.project_id}.{dataset_id}.{table_id}`
        GROUP BY chunk_type, manual_type
        ORDER BY count DESC
        """
        
        try:
            results = self.client.query(query).result()
            
            analysis = {
                "total_chunks": 0,
                "by_type": {},
                "by_manual": {}
            }
            
            for row in results:
                analysis["total_chunks"] += row.count
                
                # By chunk type
                if row.chunk_type not in analysis["by_type"]:
                    analysis["by_type"][row.chunk_type] = {
                        "count": 0,
                        "avg_length": 0
                    }
                analysis["by_type"][row.chunk_type]["count"] += row.count
                analysis["by_type"][row.chunk_type]["avg_length"] = row.avg_content_length
                
                # By manual type
                if row.manual_type not in analysis["by_manual"]:
                    analysis["by_manual"][row.manual_type] = {
                        "count": 0,
                        "avg_length": 0
                    }
                analysis["by_manual"][row.manual_type]["count"] += row.count
                analysis["by_manual"][row.manual_type]["avg_length"] = row.avg_content_length
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing manual sections: {e}")
            return {}
    
    async def search_by_section(
        self,
        section_name: str,
        dataset_id: str = "husqvarna_rag_dataset",
        table_id: str = "manual_chunks"
    ) -> List[Dict[str, Any]]:
        """
        Search for content in a specific manual section.
        
        Args:
            section_name: Section name to search for
            dataset_id: Dataset ID
            table_id: Table ID
            
        Returns:
            List of chunks from the specified section
        """
        query = f"""
        SELECT 
            id,
            subsection,
            content,
            page_number,
            chunk_type,
            manual_type
        FROM `{self.project_id}.{dataset_id}.{table_id}`
        WHERE UPPER(section) LIKE UPPER('%{section_name}%')
        ORDER BY page_number
        """
        
        try:
            results = self.client.query(query).result()
            
            chunks = []
            for row in results:
                chunk = {
                    "id": row.id,
                    "subsection": row.subsection,
                    "content": row.content,
                    "page_number": row.page_number,
                    "chunk_type": row.chunk_type,
                    "manual_type": row.manual_type
                }
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error searching by section: {e}")
            return []
    
    async def clear_table(
        self,
        dataset_id: str = "husqvarna_rag_dataset",
        table_id: str = "manual_chunks"
    ) -> None:
        """
        Clear all data from the table.
        
        Args:
            dataset_id: Dataset ID
            table_id: Table ID
        """
        query = f"""
        DELETE FROM `{self.project_id}.{dataset_id}.{table_id}`
        WHERE 1=1
        """
        
        try:
            job = self.client.query(query)
            job.result()
            logger.info(f"Cleared table {table_id}")
        except Exception as e:
            logger.error(f"Error clearing table: {e}")
            raise 