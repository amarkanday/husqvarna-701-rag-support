# 📷 Image Processing Guide - Husqvarna 701 RAG System

This guide explains how to extract, process, and search images from your Husqvarna 701 manuals using the RAG system.

## 🎯 **Overview**

The image processing system provides:
- **Automatic extraction** of images from PDF manuals
- **AI-powered analysis** using Google Vertex AI Vision
- **Text extraction** from images using OCR
- **Smart categorization** by image type and complexity
- **Seamless integration** with text-based RAG searches

## 🛠️ **Setup Requirements**

### Dependencies
```bash
# Core image processing libraries (already installed)
pip install pdf2image pillow pytesseract

# System dependencies (install via Homebrew on macOS)
brew install poppler tesseract
```

### Google Cloud Setup
```bash
# Enable Vision API (if not already enabled)
gcloud services enable vision.googleapis.com

# Verify your project ID
echo $GOOGLE_CLOUD_PROJECT
```

## 📊 **Image Processing Features**

### 1. **Image Analysis**
- **AI Vision**: Detailed descriptions using Gemini 1.5 Flash
- **OCR Text Extraction**: Tesseract-based text recognition
- **Type Classification**: Automatic categorization (6 types)
- **Complexity Assessment**: 3-level technical difficulty rating

### 2. **Image Types Detected**
- `technical_diagram`: Wiring diagrams, schematics
- `photograph`: Real photos of parts/procedures
- `table_chart`: Specifications, data tables
- `safety_warning`: Warning labels, cautions
- `parts_diagram`: Exploded views, parts lists
- `procedure_illustration`: Step-by-step visuals
- `general`: Miscellaneous content

### 3. **Complexity Levels**
- **Level 1 (Basic)**: User-level maintenance
- **Level 2 (Intermediate)**: Mechanic-level procedures
- **Level 3 (Advanced)**: Specialist/dealer-only work

## 🚀 **How to Use**

### 1. **Extract Images from Manuals**

#### Process All Manuals
```bash
# Extract from both Owner's and Repair manuals
python -m husqbot.cli.process_images extract-images --project-id rag-vs-101

# Save images to local directory
python -m husqbot.cli.process_images extract-images \
    --project-id rag-vs-101 \
    --output-dir data/images/extracted
```

#### Process Specific Manual/Part
```bash
# Process only Owner's Manual
python -m husqbot.cli.process_images extract-images \
    --project-id rag-vs-101 \
    --manual-type owners

# Process specific part (e.g., part 5)
python -m husqbot.cli.process_images extract-images \
    --project-id rag-vs-101 \
    --manual-type repair \
    --part-number 5
```

### 2. **Search Images**

#### Command Line Search
```bash
# Search for brake-related images
python -m husqbot.cli.process_images search-images \
    --project-id rag-vs-101 \
    --query "brake system" \
    --limit 10

# Search for electrical diagrams
python -m husqbot.cli.process_images search-images \
    --project-id rag-vs-101 \
    --query "wiring electrical"
```

#### Python API
```python
from husqbot.core.rag_system import HusqvarnaRAGSystem

# Initialize RAG system
rag = HusqvarnaRAGSystem(project_id="rag-vs-101")

# Search for images only
images = rag.search_images("oil change procedure", max_results=5)

# Enhanced query with both text and images
result = rag.query_with_images(
    "How do I change the oil?",
    include_images=True,
    max_images=3
)

print("Text Response:", result['response'])
print("Found Images:", len(result['images']))
```

### 3. **View Statistics**

```bash
# Show image processing summary
python -m husqbot.cli.process_images show-image-stats --project-id rag-vs-101
```

Expected output:
```
📊 Image Processing Summary
========================================
Total Images: 156
Sources: 56
Avg Complexity: 2.1/3

📈 By Image Type:
  technical_diagram: 45
  procedure_illustration: 38
  parts_diagram: 32
  photograph: 23
  safety_warning: 12
  table_chart: 6

🎯 By Complexity Level:
  Basic (Level 1): 34
  Intermediate (Level 2): 67
  Advanced (Level 3): 55
```

## 💡 **Integration with RAG Queries**

### Enhanced Text + Image Responses

When you ask questions, the system can now provide both text and relevant images:

```python
# Example query
result = rag.query_with_images("brake fluid replacement procedure")

# Response includes:
# - Text-based answer from manual chunks
# - Relevant images (diagrams, photos)
# - Safety warnings
# - Visual references with descriptions
```

**Sample Enhanced Response:**
```
Based on the Husqvarna 701 Enduro manual, here's the brake fluid replacement procedure:

1. Remove the reservoir cap and old fluid...
2. Connect a clear tube to the bleed nipple...
3. Press the brake lever slowly while opening the nipple...

📷 Relevant Visual References:

1. husky_rm_701_part015.pdf (Page 23) - Technical Diagram
   📋 Brake system hydraulic schematic showing master cylinder, lines, and caliper connections...
   📝 Text: BRAKE FLUID DOT 4 ONLY WARNING...

2. husky_om_701_part008.pdf (Page 45) - Procedure Illustration  
   📋 Step-by-step brake bleeding procedure with numbered steps and component callouts...

💡 Visual diagrams and images are available to help illustrate these procedures.
```

## 🔧 **Advanced Usage**

### 1. **Custom Image Processing**
```python
from husqbot.data.image_processor import ImageProcessor

processor = ImageProcessor(
    project_id="rag-vs-101",
    min_image_size=(200, 200),  # Larger minimum size
    max_image_size=(1024, 1024),  # Smaller max for faster processing
    image_quality=95  # Higher quality images
)

# Process specific PDF
images = processor.extract_images_from_pdf(
    "data/raw/owners_manual/split/husky_om_701_part001.pdf",
    output_dir="data/images/custom"
)
```

### 2. **Filter by Image Type**
```python
# Search only for safety warnings
safety_images = rag.search_images(
    "electrical warning", 
    image_types=["safety_warning"]
)

# Search for technical diagrams only
diagrams = rag.search_images(
    "engine timing", 
    image_types=["technical_diagram", "parts_diagram"]
)
```

### 3. **BigQuery Direct Access**
```sql
-- Query image metadata directly
SELECT 
    source,
    page_number,
    image_type,
    complexity_level,
    description
FROM `rag-vs-101.husqvarna_rag_dataset.image_metadata`
WHERE 
    image_type = 'technical_diagram'
    AND complexity_level >= 2
ORDER BY page_number;
```

## 🎛️ **Configuration Options**

### Image Processor Settings
```python
ImageProcessor(
    project_id="your-project",
    location="us-central1",           # Vertex AI region
    min_image_size=(100, 100),        # Skip small images
    max_image_size=(2048, 2048),      # Resize large images
    image_quality=85                  # JPEG compression (1-100)
)
```

### RAG System Integration
```python
# Control image inclusion in responses
result = rag.query_with_images(
    query="maintenance schedule",
    top_k=5,                          # Text chunks
    similarity_threshold=0.7,         # Text relevance
    include_images=True,              # Enable images
    max_images=2                      # Limit image count
)
```

## 📈 **Performance Tips**

1. **Batch Processing**: Process multiple PDFs together for efficiency
2. **Output Directory**: Use local storage for faster subsequent access
3. **Image Quality**: Lower quality (60-80) for faster processing
4. **Complexity Filtering**: Filter by complexity for targeted results

## 🔍 **Troubleshooting**

### Common Issues

1. **"Vision model not available"**
   - Check Vertex AI API is enabled: `gcloud services list --enabled | grep aiplatform`
   - Verify project permissions for Vertex AI

2. **"OCR errors"**
   - Install Tesseract: `brew install tesseract`
   - Check PDF quality - low-resolution PDFs may have poor text extraction

3. **"No images found"**
   - Verify BigQuery table exists: Check `image_metadata` table
   - Check manual parts are processed: Use `show-image-stats`

4. **"BigQuery errors"**
   - Ensure table schema is up to date
   - Run: `python -m husqbot.storage.bigquery_setup`

### Debugging Commands
```bash
# Test image processor
python -c "
from src.husqbot.data.image_processor import ImageProcessor
processor = ImageProcessor('rag-vs-101')
print('✅ Processor ready:', processor.vision_model is not None)
"

# Check BigQuery tables
bq ls rag-vs-101:husqvarna_rag_dataset

# Count processed images
bq query --nouse_legacy_sql 'SELECT COUNT(*) FROM `rag-vs-101.husqvarna_rag_dataset.image_metadata`'
```

## 🚀 **Next Steps**

1. **Start with a test**: Process one manual part first
2. **Review results**: Use `show-image-stats` to verify processing
3. **Test integration**: Try `query_with_images()` with simple queries
4. **Scale up**: Process all manuals once satisfied with results

This image processing system significantly enhances the RAG experience by providing visual context alongside textual information, making complex motorcycle maintenance procedures much clearer and more accessible. 