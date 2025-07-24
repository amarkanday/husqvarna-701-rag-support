"""
Image processing for Husqvarna RAG Support System.
Handles extraction, analysis, and indexing of images from manuals.
"""

import logging
import uuid
import base64
import io
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import tempfile

try:
    from pdf2image import convert_from_path
    from PIL import Image
    import pytesseract
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
except ImportError:
    raise ImportError(
        "Required packages missing. Install with: "
        "pip install pdf2image pillow pytesseract google-cloud-aiplatform"
    )

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImageProcessor:
    """Processes images from PDF manuals for the RAG system."""
    
    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        min_image_size: Tuple[int, int] = (100, 100),
        max_image_size: Tuple[int, int] = (2048, 2048),
        image_quality: int = 85
    ):
        """Initialize the image processor.
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            min_image_size: Minimum (width, height) for image to be processed
            max_image_size: Maximum (width, height) before resizing
            image_quality: JPEG quality for stored images (1-100)
        """
        self.project_id = project_id
        self.location = location
        self.min_image_size = min_image_size
        self.max_image_size = max_image_size
        self.image_quality = image_quality
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # Initialize Vision model for image analysis
        try:
            self.vision_model = GenerativeModel("gemini-1.5-flash")
            logger.info("Initialized Gemini Vision model for image analysis")
        except Exception as e:
            logger.warning(f"Could not initialize vision model: {e}")
            self.vision_model = None
    
    def extract_images_from_pdf(
        self, 
        pdf_path: str,
        output_dir: Optional[str] = None
    ) -> List[Dict]:
        """Extract all images from a PDF and analyze them.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted images (optional)
            
        Returns:
            List of image metadata dictionaries
        """
        logger.info(f"Extracting images from PDF: {pdf_path}")
        
        source = Path(pdf_path).name
        images_metadata = []
        
        # Set up output directory
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert PDF pages to images
            page_images = convert_from_path(
                pdf_path,
                dpi=300,  # High DPI for good image quality
                output_folder=temp_dir,
                fmt='png'
            )
            
            for page_num, page_image in enumerate(page_images, start=1):
                logger.info(f"Processing page {page_num} for images")
                
                # Extract images from this page
                page_image_metadata = self._extract_images_from_page(
                    page_image, 
                    source, 
                    page_num,
                    output_dir
                )
                
                images_metadata.extend(page_image_metadata)
        
        logger.info(f"Extracted {len(images_metadata)} images from {source}")
        return images_metadata
    
    def _extract_images_from_page(
        self,
        page_image: Image.Image,
        source: str,
        page_num: int,
        output_dir: Optional[str] = None
    ) -> List[Dict]:
        """Extract and analyze images from a single page.
        
        Args:
            page_image: PIL Image of the page
            source: Source PDF filename
            page_num: Page number
            output_dir: Directory to save images
            
        Returns:
            List of image metadata
        """
        images_metadata = []
        
        # For now, treat the entire page as one image
        # Later we could add image segmentation to find individual diagrams
        
        # Check if image meets minimum size requirements
        if (page_image.width < self.min_image_size[0] or
                page_image.height < self.min_image_size[1]):
            logger.debug(f"Page {page_num} too small to process as image")
            return images_metadata
        
        # Resize if needed
        processed_image = self._resize_image(page_image)
        
        # Generate unique image ID
        image_id = str(uuid.uuid4())
        
        # Save image if output directory specified
        image_path = None
        if output_dir:
            image_filename = (f"{source}_page{page_num:03d}_"
                             f"{image_id[:8]}.jpg")
            image_path = Path(output_dir) / image_filename
            processed_image.save(image_path, 'JPEG', 
                               quality=self.image_quality)
            logger.debug(f"Saved image: {image_path}")
        
        # Analyze image content
        description = self._analyze_image_content(processed_image)
        
        # Extract any text from the image
        ocr_text = self._extract_text_from_image(processed_image)
        
        # Classify image type
        image_type = self._classify_image_type(description, ocr_text)
        
        # Assess technical complexity
        complexity_level = self._assess_technical_complexity(description, 
                                                           ocr_text)
        
        # Create metadata
        image_metadata = {
            'image_id': image_id,
            'source': source,
            'page_number': page_num,
            'image_path': str(image_path) if image_path else None,
            'description': description,
            'ocr_text': ocr_text,
            'image_type': image_type,
            'complexity_level': complexity_level,
            'width': processed_image.width,
            'height': processed_image.height,
            'created_at': datetime.utcnow().isoformat(),
            # Store image as base64 for easy embedding in responses
            'image_base64': self._image_to_base64(processed_image)
        }
        
        images_metadata.append(image_metadata)
        return images_metadata
    
    def _resize_image(self, image: Image.Image) -> Image.Image:
        """Resize image if it exceeds maximum dimensions.
        
        Args:
            image: PIL Image
            
        Returns:
            Resized PIL Image
        """
        if (image.width <= self.max_image_size[0] and 
                image.height <= self.max_image_size[1]):
            return image
        
        # Calculate resize ratio to maintain aspect ratio
        width_ratio = self.max_image_size[0] / image.width
        height_ratio = self.max_image_size[1] / image.height
        resize_ratio = min(width_ratio, height_ratio)
        
        new_width = int(image.width * resize_ratio)
        new_height = int(image.height * resize_ratio)
        
        resized_image = image.resize((new_width, new_height), 
                                   Image.Resampling.LANCZOS)
        logger.debug(f"Resized image from {image.size} to {resized_image.size}")
        
        return resized_image
    
    def _analyze_image_content(self, image: Image.Image) -> str:
        """Analyze image content using Vertex AI Vision.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            Description of the image content
        """
        if not self.vision_model:
            return ("Image analysis not available "
                   "(Vision model not initialized)")
        
        try:
            # Convert image to base64 for API
            image_base64 = self._image_to_base64(image)
            
            # Create image part for Gemini
            image_part = Part.from_data(
                data=base64.b64decode(image_base64),
                mime_type="image/jpeg"
            )
            
            # Specialized prompt for motorcycle manual images
            prompt = """
            Analyze this image from a Husqvarna 701 Enduro motorcycle manual. 
            Provide a detailed description focusing on:
            
            1. Type of content (diagram, photo, schematic, table, etc.)
            2. Main subject (engine parts, electrical system, controls, etc.)
            3. Key components visible
            4. Any labels, numbers, or callouts
            5. Purpose (maintenance procedure, parts identification, warning, etc.)
            
            Be specific about motorcycle parts and technical details. 
            Format as a clear, searchable description.
            """
            
            response = self.vision_model.generate_content([prompt, image_part])
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error analyzing image with Vision API: {e}")
            return f"Image analysis failed: {str(e)[:100]}"
    
    def _extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from image using OCR.
        
        Args:
            image: PIL Image
            
        Returns:
            Extracted text
        """
        try:
            # Use Tesseract for OCR
            text = pytesseract.image_to_string(image, config='--psm 6')
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
    
    def _classify_image_type(self, description: str, ocr_text: str) -> str:
        """Classify the type of image based on content.
        
        Args:
            description: AI-generated description
            ocr_text: Extracted text
            
        Returns:
            Image type classification
        """
        description_lower = description.lower()
        
        # Classification keywords
        keywords_map = {
            'technical_diagram': ['diagram', 'schematic', 'wiring', 'circuit'],
            'photograph': ['photo', 'photograph', 'picture'],
            'table_chart': ['table', 'chart', 'specification'],
            'safety_warning': ['warning', 'caution', 'danger'],
            'parts_diagram': ['parts', 'exploded', 'assembly'],
            'procedure_illustration': ['procedure', 'step', 'instruction']
        }
        
        for img_type, keywords in keywords_map.items():
            if any(word in description_lower for word in keywords):
                return img_type
        
        return 'general'
    
    def _assess_technical_complexity(self, description: str, ocr_text: str) -> int:
        """Assess technical complexity of the image content.
        
        Args:
            description: AI-generated description
            ocr_text: Extracted text
            
        Returns:
            Complexity level (1-3)
            1: Basic/user-level
            2: Intermediate/mechanic-level  
            3: Advanced/specialist-level
        """
        content = (description + " " + ocr_text).lower()
        
        # Advanced complexity indicators
        advanced_keywords = [
            'electrical', 'wiring', 'circuit', 'ecu', 'injection',
            'timing', 'valve', 'piston', 'crankshaft', 'transmission'
        ]
        
        # Intermediate complexity indicators  
        intermediate_keywords = [
            'maintenance', 'adjustment', 'replacement', 'installation',
            'brake', 'suspension', 'chain', 'filter'
        ]
        
        # Check for complexity indicators
        advanced_count = sum(1 for keyword in advanced_keywords 
                           if keyword in content)
        intermediate_count = sum(1 for keyword in intermediate_keywords 
                               if keyword in content)
        
        if advanced_count >= 2:
            return 3
        elif intermediate_count >= 2 or advanced_count >= 1:
            return 2
        else:
            return 1
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string.
        
        Args:
            image: PIL Image
            
        Returns:
            Base64 encoded image string
        """
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=self.image_quality)
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def create_image_summary(self, images_metadata: List[Dict]) -> Dict:
        """Create a summary of extracted images.
        
        Args:
            images_metadata: List of image metadata
            
        Returns:
            Summary statistics
        """
        if not images_metadata:
            return {'total_images': 0}
        
        # Count by type
        type_counts = {}
        complexity_counts = {1: 0, 2: 0, 3: 0}
        
        for img in images_metadata:
            img_type = img.get('image_type', 'unknown')
            type_counts[img_type] = type_counts.get(img_type, 0) + 1
            
            complexity = img.get('complexity_level', 1)
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        
        return {
            'total_images': len(images_metadata),
            'by_type': type_counts,
            'by_complexity': complexity_counts,
            'sources': list(set(img['source'] for img in images_metadata))
        } 