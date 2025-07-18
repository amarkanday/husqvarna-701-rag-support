# Husqvarna 701 RAG Support System - Directory Structure

```
husqvarna-701-rag-support/
├── README.md                              # Main project documentation
├── LICENSE                                # MIT License file
├── CONTRIBUTING.md                        # Contributing guidelines
├── requirements.txt                       # Production dependencies
├── requirements-dev.txt                   # Development dependencies
├── Makefile                              # Build and deployment commands
├── .gitignore                            # Git ignore patterns
├── .pre-commit-config.yaml               # Pre-commit hooks configuration
├── docker-compose.yml                    # Local development with Docker
├── Dockerfile                            # Production Docker image
├── .dockerignore                         # Docker ignore patterns
│
├── src/
│   └── husqbot/                          # Main application package
│       ├── __init__.py
│       ├── core/                         # Core RAG functionality
│       │   ├── __init__.py
│       │   ├── rag_system.py             # Main RAG system class
│       │   ├── intent_detection.py       # Query intent classification
│       │   ├── safety_enhancement.py     # Safety warning detection
│       │   ├── response_generation.py    # Gemini response generation
│       │   └── config.py                 # Core configuration
│       │
│       ├── data/                         # Data processing pipeline
│       │   ├── __init__.py
│       │   ├── document_processor.py     # Manual processing and chunking
│       │   ├── embedding_generator.py    # Vertex AI embedding creation
│       │   ├── chunk_generator.py        # Intelligent text chunking
│       │   ├── safety_classifier.py      # Safety level classification
│       │   └── data_loader.py            # Manual data loading utilities
│       │
│       ├── models/                       # ML model configurations
│       │   ├── __init__.py
│       │   ├── embedding_models.py       # Embedding model configs
│       │   ├── generation_models.py      # Generation model configs
│       │   ├── intent_models.py          # Intent detection models
│       │   └── model_registry.py         # Model management
│       │
│       ├── storage/                      # BigQuery and GCS clients
│       │   ├── __init__.py
│       │   ├── bigquery_client.py        # BigQuery operations
│       │   ├── vector_search.py          # Vector search implementation
│       │   ├── cache_manager.py          # Embedding and response caching
│       │   ├── gcs_client.py             # Google Cloud Storage operations
│       │   └── connection_pool.py        # Database connection management
│       │
│       ├── api/                          # FastAPI web interface
│       │   ├── __init__.py
│       │   ├── fastapi_app.py            # Main FastAPI application
│       │   ├── routes/                   # API route definitions
│       │   │   ├── __init__.py
│       │   │   ├── query.py              # Query endpoint
│       │   │   ├── health.py             # Health check endpoint
│       │   │   ├── admin.py              # Admin endpoints
│       │   │   └── metrics.py            # Metrics endpoint
│       │   ├── middleware/               # FastAPI middleware
│       │   │   ├── __init__.py
│       │   │   ├── auth.py               # Authentication middleware
│       │   │   ├── logging.py            # Request logging
│       │   │   └── cors.py               # CORS configuration
│       │   ├── models/                   # Pydantic models
│       │   │   ├── __init__.py
│       │   │   ├── request_models.py     # Request schemas
│       │   │   ├── response_models.py    # Response schemas
│       │   │   └── error_models.py       # Error response schemas
│       │   └── dependencies.py           # FastAPI dependencies
│       │
│       ├── cli/                          # Command-line interface
│       │   ├── __init__.py
│       │   ├── main.py                   # CLI entry point
│       │   ├── commands/                 # CLI commands
│       │   │   ├── __init__.py
│       │   │   ├── setup.py              # System setup command
│       │   │   ├── query.py              # Interactive query command
│       │   │   ├── import_data.py        # Data import command
│       │   │   └── admin.py              # Admin commands
│       │   └── utils.py                  # CLI utilities
│       │
│       └── utils/                        # Utilities and helpers
│           ├── __init__.py
│           ├── logging_config.py         # Logging configuration
│           ├── exceptions.py             # Custom exceptions
│           ├── validators.py             # Input validation
│           ├── text_processing.py        # Text processing utilities
│           ├── metrics.py                # Performance metrics
│           └── helpers.py                # General helper functions
│
├── tests/                                # Test suite
│   ├── __init__.py
│   ├── conftest.py                       # Pytest configuration
│   ├── unit/                             # Unit tests
│   │   ├── __init__.py
│   │   ├── test_core/                    # Core functionality tests
│   │   │   ├── __init__.py
│   │   │   ├── test_rag_system.py
│   │   │   ├── test_intent_detection.py
│   │   │   └── test_safety_enhancement.py
│   │   ├── test_data/                    # Data processing tests
│   │   │   ├── __init__.py
│   │   │   ├── test_document_processor.py
│   │   │   └── test_embedding_generator.py
│   │   ├── test_storage/                 # Storage tests
│   │   │   ├── __init__.py
│   │   │   ├── test_bigquery_client.py
│   │   │   └── test_vector_search.py
│   │   └── test_api/                     # API tests
│   │       ├── __init__.py
│   │       ├── test_routes.py
│   │       └── test_models.py
│   ├── integration/                      # Integration tests
│   │   ├── __init__.py
│   │   ├── test_end_to_end.py            # End-to-end workflow tests
│   │   ├── test_api_integration.py       # API integration tests
│   │   └── test_google_cloud.py          # Google Cloud integration tests
│   ├── fixtures/                         # Test fixtures and data
│   │   ├── __init__.py
│   │   ├── sample_queries.json           # Sample query data
│   │   ├── sample_responses.json         # Sample response data
│   │   └── test_documents/               # Test document files
│   └── performance/                      # Performance tests
│       ├── __init__.py
│       ├── test_response_times.py        # Response time benchmarks
│       └── test_concurrent_users.py      # Concurrent user load tests
│
├── notebooks/                            # Jupyter notebooks
│   ├── 01_data_exploration.ipynb         # Manual data exploration
│   ├── 02_embedding_analysis.ipynb       # Embedding quality analysis
│   ├── 03_rag_testing.ipynb              # RAG system testing
│   ├── 04_performance_analysis.ipynb     # Performance analysis
│   └── 05_model_comparison.ipynb         # Model comparison studies
│
├── scripts/                              # Utility scripts
│   ├── setup/                            # Setup and initialization scripts
│   │   ├── create_bigquery_resources.py  # BigQuery dataset/table creation
│   │   ├── setup_gcp_apis.py             # Enable required GCP APIs
│   │   ├── create_service_account.py     # Service account creation
│   │   └── import_manuals.py             # Manual data import
│   ├── deployment/                       # Deployment scripts
│   │   ├── deploy_cloud_run.sh           # Cloud Run deployment
│   │   ├── deploy_kubernetes.sh          # Kubernetes deployment
│   │   └── setup_monitoring.sh           # Monitoring setup
│   ├── maintenance/                      # Maintenance scripts
│   │   ├── cleanup_cache.py              # Cache cleanup
│   │   ├── update_embeddings.py          # Embedding updates
│   │   └── backup_data.py                # Data backup
│   └── analysis/                         # Analysis scripts
│       ├── query_analysis.py             # Query pattern analysis
│       ├── performance_report.py         # Performance reporting
│       └── usage_statistics.py           # Usage statistics
│
├── config/                               # Configuration files
│   ├── development.yaml                  # Development configuration
│   ├── production.yaml                   # Production configuration
│   ├── testing.yaml                      # Testing configuration
│   ├── logging.yaml                      # Logging configuration
│   └── monitoring.yaml                   # Monitoring configuration
│
├── docs/                                 # Documentation
│   ├── guides/                           # User guides
│   │   ├── installation.md               # Installation guide
│   │   ├── deployment.md                 # Deployment guide
│   │   ├── configuration.md              # Configuration guide
│   │   └── troubleshooting.md            # Troubleshooting guide
│   ├── api/                              # API documentation
│   │   ├── endpoints.md                  # API endpoint documentation
│   │   ├── models.md                     # Data models documentation
│   │   └── examples.md                   # API usage examples
│   ├── technical/                        # Technical documentation
│   │   ├── architecture.md               # System architecture
│   │   ├── performance_tuning.md         # Performance optimization
│   │   ├── security.md                   # Security considerations
│   │   └── scaling.md                    # Scaling strategies
│   └── user/                             # User documentation
│       ├── getting_started.md            # Getting started guide
│       ├── query_examples.md             # Query examples
│       └── best_practices.md             # Best practices
│
├── deployment/                           # Deployment configurations
│   ├── kubernetes/                       # Kubernetes manifests
│   │   ├── deployment.yaml               # Main deployment
│   │   ├── service.yaml                  # Service definition
│   │   ├── ingress.yaml                  # Ingress configuration
│   │   ├── configmap.yaml                # ConfigMap
│   │   ├── secret.yaml                   # Secret configuration
│   │   └── hpa.yaml                      # Horizontal Pod Autoscaler
│   ├── cloud-run/                        # Cloud Run configuration
│   │   ├── service.yaml                  # Cloud Run service config
│   │   └── cloudbuild.yaml               # Cloud Build configuration
│   └── terraform/                        # Infrastructure as Code
│       ├── main.tf                       # Main Terraform configuration
│       ├── variables.tf                  # Terraform variables
│       ├── outputs.tf                    # Terraform outputs
│       └── modules/                      # Terraform modules
│           ├── bigquery/                 # BigQuery module
│           ├── cloud-run/                # Cloud Run module
│           └── monitoring/               # Monitoring module
│
├── monitoring/                           # Monitoring and alerting
│   ├── alerts.yml                        # Alerting rules
│   ├── dashboards/                       # Monitoring dashboards
│   │   ├── performance.json              # Performance dashboard
│   │   ├── errors.json                   # Error tracking dashboard
│   │   └── usage.json                    # Usage analytics dashboard
│   └── logging/                          # Logging configuration
│       ├── log_format.json               # Log format specification
│       └── log_filters.yaml              # Log filtering rules
│
├── data/                                 # Data directory (gitignored)
│   ├── manuals/                          # Husqvarna manual files
│   │   ├── owners_manual.pdf             # Owner's manual
│   │   ├── repair_manual.pdf             # Repair manual
│   │   └── processed/                    # Processed manual data
│   ├── embeddings/                       # Generated embeddings
│   ├── cache/                            # Local cache storage
│   └── exports/                          # Data exports
│
├── .github/                              # GitHub configuration
│   ├── workflows/                        # GitHub Actions workflows
│   │   ├── tests.yml                     # Test workflow
│   │   ├── deploy.yml                    # Deployment workflow
│   │   ├── security.yml                  # Security scanning
│   │   └── release.yml                   # Release workflow
│   ├── ISSUE_TEMPLATE/                   # Issue templates
│   │   ├── bug_report.md                 # Bug report template
│   │   ├── feature_request.md            # Feature request template
│   │   └── question.md                   # Question template
│   └── PULL_REQUEST_TEMPLATE.md          # Pull request template
│
└── assets/                               # Static assets
    ├── images/                           # Project images
    │   ├── logo.png                      # Project logo
    │   ├── architecture.png              # Architecture diagram
    │   └── screenshots/                  # Application screenshots
    └── icons/                            # Icons and graphics
```

## Key Directory Explanations

### `src/husqbot/` - Main Application
- **core/**: Core RAG functionality including the main system class
- **data/**: Document processing and embedding generation
- **models/**: ML model configurations and management
- **storage/**: BigQuery and GCS client implementations
- **api/**: FastAPI web interface with routes and middleware
- **cli/**: Command-line interface for system management
- **utils/**: Shared utilities and helper functions

### `tests/` - Comprehensive Testing
- **unit/**: Unit tests for individual components
- **integration/**: End-to-end and integration tests
- **fixtures/**: Test data and fixtures
- **performance/**: Performance and load testing

### `scripts/` - Utility Scripts
- **setup/**: Initialization and setup scripts
- **deployment/**: Deployment automation scripts
- **maintenance/**: System maintenance scripts
- **analysis/**: Data analysis and reporting scripts

### `config/` - Configuration Management
- Environment-specific configuration files
- Logging and monitoring configurations

### `deployment/` - Infrastructure
- **kubernetes/**: Kubernetes manifests
- **cloud-run/**: Cloud Run configurations
- **terraform/**: Infrastructure as Code

### `monitoring/` - Observability
- Alerting rules and monitoring dashboards
- Logging configurations

### `docs/` - Documentation
- User guides, API documentation, and technical specs
- Organized by audience and purpose

This structure follows Python best practices, supports scalable development, and provides clear separation of concerns for the Husqvarna 701 RAG Support System. 