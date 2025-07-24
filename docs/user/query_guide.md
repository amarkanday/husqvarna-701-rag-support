# 🏍️ User Query Guide - Husqvarna 701 RAG System

This guide shows you how to test your own queries against the Husqvarna 701 Enduro RAG system.

## 🚀 Quick Start

### 1. CLI Commands

#### Test Individual Queries
```bash
# Test a single query
python -m husqbot.cli.test_rag query-system --project-id YOUR_PROJECT_ID -q "How do I check the oil level?"

# With full response and more chunks
python -m husqbot.cli.test_rag query-system --project-id YOUR_PROJECT_ID -q "What are the valve clearances?" -f -k 5

# Lower similarity threshold to find more matches
python -m husqbot.cli.test_rag query-system --project-id YOUR_PROJECT_ID -q "Engine specifications" -s 0.5
```

#### Interactive Mode
```bash
# Start interactive session
python -m husqbot.cli.test_rag query-system --project-id YOUR_PROJECT_ID

# With custom settings
python -m husqbot.cli.test_rag query-system --project-id YOUR_PROJECT_ID -k 5 -s 0.5 -f
```

#### System Information
```bash
# Show system statistics
python -m husqbot.cli.test_rag stats --project-id YOUR_PROJECT_ID

# Run predefined test suite
python -m husqbot.cli.test_rag test-system --project-id YOUR_PROJECT_ID
```

### 2. Python Functions

#### Single Query Test
```python
from husqbot.cli.interactive_query import test_single_query

# Basic query
result = test_single_query("How do I check the oil level?", project_id="your-project-id")

# With custom parameters
result = test_single_query(
    query="What are the valve clearances?",
    project_id="your-project-id",
    top_k=5,
    similarity_threshold=0.5,
    show_full_response=True
)

print(f"Success: {result['success']}")
print(f"Found {result['chunks_found']} relevant chunks")
print(f"Response: {result['response']}")
```

#### Interactive Session
```python
from husqbot.cli.interactive_query import interactive_query_session

# Start interactive mode
interactive_query_session(project_id="your-project-id")

# With custom settings
interactive_query_session(
    project_id="your-project-id",
    top_k=5,
    similarity_threshold=0.6,
    show_full_response=True
)
```

#### Sample Queries
```python
from husqbot.cli.interactive_query import run_sample_queries

# Run demonstration queries
run_sample_queries(project_id="your-project-id")
```

## 🎯 Query Examples

### Maintenance Questions
- "How do I check the oil level?"
- "What is the recommended tire pressure?"
- "How often should I change the air filter?"
- "What type of engine oil should I use?"
- "How do I adjust the chain tension?"

### Technical Specifications
- "What are the engine specifications?"
- "What is the compression ratio?"
- "What are the valve clearances?"
- "What are the torque specifications for the wheels?"
- "What type of spark plug should I use?"

### Troubleshooting
- "Why won't my bike start?"
- "What causes engine overheating?"
- "How do I diagnose electrical problems?"
- "What should I check if the bike won't idle?"

### Service Procedures
- "How do I replace the spark plug?"
- "How do I change the brake fluid?"
- "What is the maintenance schedule?"
- "How do I service the suspension?"

## ⚙️ Parameters

### Query Parameters
- **`top_k`** (default: 3): Number of relevant chunks to retrieve
- **`similarity_threshold`** (default: 0.6): Minimum similarity score (0.0-1.0)
- **`show_full_response`** (default: False): Show complete response without truncation

### Tuning Tips
- **Lower threshold (0.4-0.5)**: Find more matches, but may include less relevant content
- **Higher threshold (0.7-0.8)**: Find only highly relevant matches
- **More chunks (5-10)**: Get broader context, useful for complex topics
- **Fewer chunks (1-3)**: Get focused, specific answers

## 📊 Understanding Results

### Response Structure
```python
{
    'query': 'Your question',
    'response': 'Generated answer from manual content',
    'sources': [
        {
            'source': 'husky_om_701_part012.pdf',
            'page': 1,
            'similarity': 0.691,
            'safety_level': 1
        }
    ],
    'chunks_found': 3,
    'success': True,
    'fallback_mode': True
}
```

### Similarity Scores
- **0.9-1.0**: Extremely relevant (rare)
- **0.7-0.9**: Highly relevant
- **0.6-0.7**: Moderately relevant
- **0.4-0.6**: Somewhat relevant
- **0.0-0.4**: Weakly relevant

### Safety Levels
- **Level 1**: General information, safe procedures
- **Level 2**: Moderate caution required
- **Level 3**: High risk, professional attention recommended

## 🔧 Environment Setup

### Required Environment Variables
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### Authentication
```bash
# Set up application default credentials
gcloud auth application-default login
```

## 💡 Tips for Better Results

### 1. Query Formulation
- **Specific questions**: "What are the valve clearances?" vs "Tell me about valves"
- **Use motorcycle terminology**: "chain tension" vs "chain tightness"
- **Include context**: "oil change interval" vs just "oil"

### 2. Iterative Refinement
- Start with broad queries, then narrow down
- Try different phrasings if first attempt doesn't work
- Use lower similarity thresholds for exploratory searches

### 3. Safety Awareness
- Pay attention to safety warnings in responses
- Higher safety levels require professional consultation
- Always refer to complete manual for critical procedures

## 🛠️ Advanced Usage

### Custom RAG System
```python
from husqbot.core.rag_system import HusqvarnaRAGSystem

# Initialize with custom settings
rag = HusqvarnaRAGSystem(
    project_id="your-project-id",
    location="us-central1"
)

# Get system statistics
stats = rag.get_system_stats()
print(f"Coverage: {stats['embedding_coverage']}%")

# Custom query with detailed control
result = rag.query(
    "How do I check the oil level?",
    top_k=5,
    similarity_threshold=0.5
)
```

### Batch Processing
```python
queries = [
    "How do I check the oil level?",
    "What are the valve clearances?",
    "How do I adjust chain tension?"
]

results = []
for query in queries:
    result = test_single_query(query, verbose=False)
    results.append(result)
    
# Analyze results
successful = sum(1 for r in results if r['success'])
print(f"Success rate: {successful}/{len(queries)}")
```

## 🏍️ Example Session

```bash
$ python -m husqbot.cli.test_rag query-system --project-id rag-vs-101

🔧 Initializing Husqvarna 701 RAG System...
📊 System ready: 2191 chunks (33.9% coverage)

🤖 Interactive Query Mode
Settings: top_k=3, threshold=0.6
============================================================
Enter your questions about the Husqvarna 701 Enduro.
Type 'quit', 'exit', or press Ctrl+C to stop.
------------------------------------------------------------

🏍️  Your question: How do I check the oil level?

[Query 1] Processing...
✅ Success: True
📊 Chunks found: 3
🤖 Fallback mode: True
📝 Response:
⚠️ **SAFETY WARNING**: This information involves potentially dangerous procedures...

Based on the Husqvarna 701 Enduro manual, here's what I found regarding 'How do I check the oil level?':

**1. **Source**: husky_rm_701_part030.pdf (Page 2)** (Relevance: 69.8%)
Condition The engine is at operating temperature. Preparatory work -— Stand the motorcycle upright on a horizontal surface...

📚 Sources (3 found):
  1. husky_rm_701_part030.pdf (Page 2, Similarity: 69.8%, Safety: 3)
  2. husky_om_701_part012.pdf (Page 1, Similarity: 69.1%, Safety: 1)

🏍️  Your question: exit

📈 Session complete: 1 queries processed
```

## 🚨 Troubleshooting

### Common Issues
1. **No results found**: Try lowering similarity threshold or rephrasing query
2. **Authentication errors**: Check `gcloud auth application-default login`
3. **Project not found**: Verify `GOOGLE_CLOUD_PROJECT` environment variable
4. **Low embedding coverage**: Some manual parts may not have embeddings yet

### Getting Help
- Check system stats: `python -m husqbot.cli.test_rag stats --project-id YOUR_PROJECT_ID`
- Run test suite: `python -m husqbot.cli.test_rag test-system --project-id YOUR_PROJECT_ID`
- Try sample queries: `python -m husqbot.cli.interactive_query samples` 