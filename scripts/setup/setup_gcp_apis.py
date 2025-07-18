#!/usr/bin/env python3
"""
Script to enable required Google Cloud APIs for the Husqvarna RAG Support System.
"""

import os
import sys
import subprocess
import logging
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_command(command: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a shell command and return the result.
    
    Args:
        command: Command to run
        check: Whether to raise exception on non-zero exit code
        
    Returns:
        CompletedProcess object
    """
    logger.info(f"Running: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, check=check)
    
    if result.stdout:
        logger.info(f"Output: {result.stdout.strip()}")
    if result.stderr:
        logger.warning(f"Stderr: {result.stderr.strip()}")
    
    return result


def check_gcloud_auth() -> bool:
    """Check if gcloud is authenticated."""
    try:
        result = run_command(["gcloud", "auth", "list", "--filter=status:ACTIVE"], check=False)
        return result.returncode == 0 and "ACTIVE" in result.stdout
    except Exception:
        return False


def get_project_id() -> str:
    """Get the current Google Cloud project ID."""
    try:
        result = run_command(["gcloud", "config", "get-value", "project"])
        project_id = result.stdout.strip()
        if not project_id:
            raise ValueError("No project ID configured")
        return project_id
    except Exception as e:
        logger.error(f"Failed to get project ID: {e}")
        raise


def enable_apis(project_id: str, apis: List[str]) -> None:
    """
    Enable Google Cloud APIs for the project.
    
    Args:
        project_id: Google Cloud project ID
        apis: List of API names to enable
    """
    logger.info(f"Enabling APIs for project: {project_id}")
    
    for api in apis:
        logger.info(f"Enabling API: {api}")
        try:
            run_command([
                "gcloud", "services", "enable", api,
                "--project", project_id
            ])
            logger.info(f"✅ API {api} enabled successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to enable API {api}: {e}")
            raise


def setup_service_account(project_id: str) -> None:
    """
    Setup service account for the RAG system.
    
    Args:
        project_id: Google Cloud project ID
    """
    service_account_name = "husqvarna-rag-sa"
    service_account_email = f"{service_account_name}@{project_id}.iam.gserviceaccount.com"
    
    logger.info(f"Setting up service account: {service_account_email}")
    
    try:
        # Check if service account exists
        result = run_command([
            "gcloud", "iam", "service-accounts", "describe", service_account_email,
            "--project", project_id
        ], check=False)
        
        if result.returncode != 0:
            # Create service account
            logger.info("Creating service account...")
            run_command([
                "gcloud", "iam", "service-accounts", "create", service_account_name,
                "--display-name", "Husqvarna RAG Support System Service Account",
                "--description", "Service account for Husqvarna RAG Support System",
                "--project", project_id
            ])
            logger.info("✅ Service account created successfully")
        else:
            logger.info("✅ Service account already exists")
        
        # Grant necessary roles
        roles = [
            "roles/bigquery.dataEditor",
            "roles/bigquery.jobUser",
            "roles/aiplatform.user",
            "roles/storage.objectViewer",
            "roles/logging.logWriter"
        ]
        
        for role in roles:
            logger.info(f"Granting role: {role}")
            run_command([
                "gcloud", "projects", "add-iam-policy-binding", project_id,
                "--member", f"serviceAccount:{service_account_email}",
                "--role", role
            ])
            logger.info(f"✅ Role {role} granted successfully")
        
        # Create and download key
        key_file = "service-account-key.json"
        if not os.path.exists(key_file):
            logger.info("Creating service account key...")
            run_command([
                "gcloud", "iam", "service-accounts", "keys", "create", key_file,
                "--iam-account", service_account_email,
                "--project", project_id
            ])
            logger.info(f"✅ Service account key created: {key_file}")
        else:
            logger.info("✅ Service account key already exists")
        
    except Exception as e:
        logger.error(f"Failed to setup service account: {e}")
        raise


def main():
    """Main function to run the script."""
    # Required APIs for the RAG system
    required_apis = [
        "bigquery.googleapis.com",
        "aiplatform.googleapis.com",
        "storage.googleapis.com",
        "logging.googleapis.com",
        "cloudresourcemanager.googleapis.com"
    ]
    
    try:
        # Check authentication
        if not check_gcloud_auth():
            logger.error("❌ gcloud is not authenticated. Please run: gcloud auth login")
            sys.exit(1)
        
        logger.info("✅ gcloud authentication verified")
        
        # Get project ID
        project_id = get_project_id()
        logger.info(f"✅ Using project: {project_id}")
        
        # Enable APIs
        enable_apis(project_id, required_apis)
        
        # Setup service account
        setup_service_account(project_id)
        
        logger.info("🎉 Google Cloud setup completed successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable:")
        logger.info(f"   export GOOGLE_APPLICATION_CREDENTIALS=$(pwd)/service-account-key.json")
        logger.info("2. Run the BigQuery setup script:")
        logger.info("   python scripts/setup/create_bigquery_resources.py")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 