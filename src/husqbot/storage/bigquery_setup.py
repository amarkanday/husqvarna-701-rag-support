from google.cloud import bigquery


def setup_bigquery_resources():
    """Set up BigQuery dataset and tables."""
    client = bigquery.Client()
    
    # Set dataset_id to the ID of the dataset to create
    dataset_id = f"{client.project}.husqvarna_rag_dataset"
    
    # Construct a full Dataset object to send to the API
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "us-central1"
    
    # Send the dataset to the API for creation, with an explicit timeout
    dataset = client.create_dataset(dataset, timeout=30)
    print(f"Created dataset {client.project}.{dataset.dataset_id}")
    
    # Create document chunks table
    schema = [
        bigquery.SchemaField("chunk_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
        bigquery.SchemaField("source", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("page_number", "INTEGER"),
        bigquery.SchemaField("safety_level", "INTEGER"),
        bigquery.SchemaField("created_at", "TIMESTAMP"),
    ]
    
    table_id = f"{dataset_id}.document_chunks"
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table)
    print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")


if __name__ == "__main__":
    setup_bigquery_resources() 