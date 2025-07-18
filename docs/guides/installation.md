# Installation Guide

This guide will walk you through setting up the Husqvarna 701 RAG Support System on your local machine or cloud environment.

## Prerequisites

### System Requirements

- **Python**: 3.9 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 2GB free space
- **Network**: Internet connection for downloading dependencies and accessing Google Cloud

### Google Cloud Requirements

- **Google Cloud Project**: Active project with billing enabled
- **Google Cloud CLI**: Installed and authenticated
- **Required APIs**: BigQuery, Vertex AI, Cloud Storage, Cloud Logging

### Software Dependencies

- **Git**: For cloning the repository
- **Docker**: Optional, for containerized deployment
- **Make**: For running build commands (optional)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/husqvarna-701-rag-support.git
cd husqvarna-701-rag-support
```

### 2. Set Up Python Environment

#### Option A: Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Option B: Conda Environment

```bash
# Create conda environment
conda create -n husqvarna-rag python=3.11

# Activate environment
conda activate husqvarna-rag

# Install dependencies
pip install -r requirements.txt
```

### 3. Google Cloud Setup

#### 3.1 Install and Authenticate Google Cloud CLI

```bash
# Install gcloud CLI (if not already installed)
# Follow instructions at: https://cloud.google.com/sdk/docs/install

# Authenticate with Google Cloud
gcloud auth login

# Set your project ID
export GOOGLE_CLOUD_PROJECT="your-project-id"
gcloud config set project $GOOGLE_CLOUD_PROJECT
```

#### 3.2 Enable Required APIs and Create Resources

```bash
# Run the automated setup script
python scripts/setup/setup_gcp_apis.py

# Create BigQuery resources
python scripts/setup/create_bigquery_resources.py
```

#### 3.3 Set Up Service Account Credentials

```bash
# Set the credentials environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/service-account-key.json"
```

### 4. Configuration

#### 4.1 Environment Variables

Create a `.env` file in the project root:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO

# Cache Configuration
REDIS_URL=redis://localhost:6379

# API Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

#### 4.2 Configuration Files

The system uses YAML configuration files in the `config/` directory:

- `config/development.yaml` - Development settings
- `config/production.yaml` - Production settings

You can customize these files based on your needs.

### 5. Data Setup

#### 5.1 Prepare Manual Documents

Place your Husqvarna 701 Enduro manuals in the `data/manuals/` directory:

```bash
mkdir -p data/manuals
# Copy your PDF manuals to data/manuals/
# - owners_manual.pdf
# - repair_manual.pdf
```

#### 5.2 Import Data

```bash
# Run the data import script
python scripts/setup/import_manuals.py
```

### 6. Verify Installation

#### 6.1 Run Tests

```bash
# Run all tests
make test

# Or run specific test categories
make test-unit
make test-integration
```

#### 6.2 Start the Application

```bash
# Development mode
make run-dev

# Or directly with uvicorn
uvicorn src.husqbot.api.fastapi_app:app --reload --host 0.0.0.0 --port 8000
```

#### 6.3 Test the API

```bash
# Test the health endpoint
curl http://localhost:8000/health

# Test a query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I check the engine oil level?",
    "user_skill_level": "intermediate"
  }'
```

## Docker Installation (Alternative)

### 1. Build Docker Image

```bash
docker build -t husqvarna-rag .
```

### 2. Run with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f app
```

### 3. Access the Application

- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Jupyter Notebooks**: http://localhost:8888

## Troubleshooting

### Common Issues

#### 1. Google Cloud Authentication

**Problem**: `google.auth.exceptions.DefaultCredentialsError`

**Solution**:
```bash
# Re-authenticate with gcloud
gcloud auth application-default login

# Or set service account credentials
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
```

#### 2. BigQuery Dataset Not Found

**Problem**: `google.api_core.exceptions.NotFound: 404 Dataset not found`

**Solution**:
```bash
# Run BigQuery setup script
python scripts/setup/create_bigquery_resources.py
```

#### 3. Memory Issues

**Problem**: Out of memory during embedding generation

**Solution**:
```bash
# Reduce batch size
export EMBEDDING_BATCH_SIZE=5

# Or increase system memory
```

#### 4. Port Already in Use

**Problem**: `OSError: [Errno 98] Address already in use`

**Solution**:
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn src.husqbot.api.fastapi_app:app --port 8001
```

### Getting Help

If you encounter issues not covered here:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review the [API Documentation](../api/endpoints.md)
3. Open an issue on GitHub
4. Check the application logs for detailed error messages

## Next Steps

After successful installation:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Run Jupyter Notebooks**: Start with `notebooks/01_data_exploration.ipynb`
3. **Customize Configuration**: Modify settings in `config/` directory
4. **Deploy to Production**: Follow the [Deployment Guide](deployment.md)

## Support

For additional support:

- 📖 [Documentation](../)
- 🐛 [GitHub Issues](https://github.com/yourusername/husqvarna-701-rag-support/issues)
- 💬 [GitHub Discussions](https://github.com/yourusername/husqvarna-701-rag-support/discussions)
- 📧 [Email Support](mailto:your.email@example.com) 