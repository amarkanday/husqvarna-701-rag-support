# 🏍️ Husqvarna 701 Enduro RAG Support System

## 📝 Implementation Details

### 1. Project Structure
```
husqvarna-701-rag-support/
├── src/
│   └── husqbot/
│       ├── core/
│       │   └── rag_system.py      # Core RAG functionality
│       ├── data/
│       │   ├── document_processor.py  # PDF processing
│       │   └── process_manuals.py     # Manual processing pipeline
│       ├── models/
│       │   └── embeddings.py      # Embedding generation
│       └── cli/
│           └── main.py            # CLI interface
├── data/
│   ├── raw/
│   │   ├── owners_manual/        # Place owner's manual PDFs here
│   │   └── repair_manual/        # Place repair manual PDFs here
│   └── processed/                # Processed chunks and embeddings
└── config/
    └── production.yaml           # Configuration settings
```

### 2. Core Components

#### 2.1 Document Processing (`document_processor.py`)
- Handles PDF document processing
- Intelligent chunking with configurable size and overlap
- Safety level assessment (1-3) based on content
- Metadata extraction (source, page numbers)
- Key features:
  - Chunk size: 1000 characters
  - Overlap: 200 characters
  - Automatic sentence boundary detection
  - Safety keyword detection

#### 2.2 Embedding Generation (`embeddings.py`)
- Uses Vertex AI's text embedding model
- Model: `textembedding-gecko@003`
- Batch processing (5 texts per batch)
- Features:
  - Efficient batch processing
  - Error handling
  - Automatic retries

#### 2.3 Core RAG System (`rag_system.py`)
- Main RAG functionality implementation
- Components:
  - Vector similarity search using BigQuery
  - Response generation using Gemini Pro
  - Safety warning integration
  - Skill level adaptation
- Features:
  - Configurable chunk retrieval
  - Context-aware responses
  - Safety-first approach

### 3. Data Storage

#### 3.1 BigQuery Schema
```sql
CREATE TABLE document_chunks (
    chunk_id STRING,
    content STRING,
    embedding ARRAY<FLOAT64>,
    source STRING,
    page_number INTEGER,
    safety_level INTEGER,
    created_at TIMESTAMP
)
```

#### 3.2 Vector Search
- Cosine similarity for semantic search
- Optimized BigQuery queries
- Top-k retrieval with configurable k

### 4. CLI Interface

#### 4.1 Available Commands
```bash
# Process manuals
python -m husqbot.cli.main process-manuals

# Interactive query mode
python -m husqbot.cli.main interactive
```

#### 4.2 Configuration Options
- `--project-id`: Google Cloud project ID
- `--location`: Google Cloud region (default: us-central1)

### 5. Setup Instructions

#### 5.1 Prerequisites
```bash
# Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Google Cloud Setup
gcloud auth application-default login
gcloud services enable bigquery.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

#### 5.2 Manual Processing
1. Place PDF manuals in respective directories:
   - `data/raw/owners_manual/`
   - `data/raw/repair_manual/`
2. Run processing pipeline:
   ```bash
   python -m husqbot.cli.main process-manuals
   ```

#### 5.3 Using the System
1. Start interactive mode:
   ```bash
   python -m husqbot.cli.main interactive
   ```
2. Ask questions about:
   - Maintenance procedures
   - Troubleshooting
   - Technical specifications
   - Safety information

### 6. Technical Details

#### 6.1 Dependencies
- `google-cloud-bigquery`: Vector storage and search
- `google-cloud-aiplatform`: Vertex AI integration
- `PyPDF2`: PDF processing
- `vertexai`: Embedding and text generation
- Additional utilities in `requirements.txt`

#### 6.2 Safety Features
- Automatic safety level assessment
- Warning prefixes for dangerous procedures
- Safety keyword detection:
  - High risk: warning, danger, fatal, death, serious injury
  - Medium risk: caution, attention, careful, important safety

#### 6.3 Performance Optimization
- Batch processing for embeddings
- Efficient chunk storage
- Optimized vector similarity search
- Caching capabilities

### 7. Future Enhancements
- [ ] Multi-language support
- [ ] Image processing capabilities
- [ ] User feedback integration
- [ ] Advanced caching system
- [ ] Performance monitoring
- [ ] API endpoint implementation

## 📚 Usage Examples

```python
# Initialize the system
from husqbot.core.rag_system import HusqvarnaRAGSystem

rag = HusqvarnaRAGSystem(
    project_id="your-project-id",
    location="us-central1"
)

# Query the system
response = rag.query(
    "How do I check the oil level?",
    skill_level="intermediate"
)
```

## 🔧 Maintenance

### Running Tests
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

### Code Formatting
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
mypy src/
```

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.