"""
Document processing for Husqvarna RAG Support System.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Dict
import tempfile
import os

try:
    from pdf2image import convert_from_path
    import pytesseract
except ImportError:
    raise ImportError(
        "pdf2image and pytesseract are required. "
        "Install them with: pip install pdf2image pytesseract"
    )

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    def __init__(
        self,
        chunk_size: int = 800,  # Increased for more context
        overlap: int = 200,     # Increased overlap for better continuity
        page_batch_size: int = 2,
        min_chunk_size: int = 100  # Minimum viable chunk size
    ):
        """Initialize the document processor.
        
        Args:
            chunk_size: Size of each text chunk
            overlap: Number of characters to overlap between chunks
            page_batch_size: Number of pages to process at once
            min_chunk_size: Minimum size for a chunk to be considered valid
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.page_batch_size = page_batch_size
        self.min_chunk_size = min_chunk_size
    
    def process_pdf(self, file_path: str) -> List[Dict]:
        """Process a PDF file and return chunks.
        
        Args:
            file_path: Path to the PDF file
        
        Returns:
            List of chunks with metadata
        """
        logger.info(f"Opening PDF file: {file_path}")
        chunks = []
        source = file_path.split('/')[-1]
        
        # Create a temporary directory for image files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert PDF pages to images
            images = convert_from_path(
                file_path,
                dpi=300,  # Higher DPI for better OCR
                output_folder=temp_dir,
                fmt='png',
                thread_count=os.cpu_count() or 1
            )
            
            # Process each page
            for page_num, image in enumerate(images, start=1):
                logger.info(f"Processing page {page_num}")
                
                # Extract text using OCR
                text = pytesseract.image_to_string(image)
                
                if not text.strip():
                    logger.warning(
                        f"No text extracted from page {page_num}"
                    )
                    continue
                
                logger.info(
                    f"Extracted {len(text)} characters from page {page_num}"
                )
                
                # Create chunks from the page text
                page_chunks = self._create_chunks(text)
                logger.info(
                    f"Created {len(page_chunks)} chunks from page {page_num}"
                )
                
                # Add metadata to chunks
                for chunk in page_chunks:
                    if not chunk.strip():
                        continue
                    chunk_dict = {
                        'chunk_id': str(uuid.uuid4()),
                        'content': chunk,
                        'source': source,
                        'page_number': page_num,
                        'safety_level': self._assess_safety(chunk),
                        'created_at': datetime.utcnow().isoformat()
                    }
                    chunks.append(chunk_dict)
        
        return chunks
    
    def _create_chunks(self, text: str) -> List[str]:
        """Create overlapping chunks from text with intelligent boundary detection.
        
        Args:
            text: Text to chunk
        
        Returns:
            List of text chunks
        """
        if not text.strip():
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If we're at the end of the text, take what's left
            if end >= len(text):
                chunk = text[start:].strip()
                if len(chunk) >= self.min_chunk_size:
                    chunks.append(chunk)
                break
            
            chunk = text[start:end]
            
            # Smart boundary detection - prefer sentence endings
            adjusted_end = self._find_optimal_break_point(text, start, end)
            chunk = text[start:adjusted_end].strip()
            
            # Only add chunks that meet minimum size requirement
            if len(chunk) >= self.min_chunk_size:
                chunks.append(chunk)
                
                # Move start position for next chunk with overlap
                start = adjusted_end - self.overlap
                
                # Ensure overlap doesn't push us backwards
                if start <= chunks.__len__() > 1:
                    start = adjusted_end - min(self.overlap, len(chunk) // 3)
            else:
                # If chunk is too small, move forward without overlap
                start = adjusted_end
        
        return [c for c in chunks if c and len(c.strip()) >= self.min_chunk_size]
    
    def _find_optimal_break_point(self, text: str, start: int, end: int) -> int:
        """Find the optimal break point for a chunk based on semantic boundaries.
        
        Args:
            text: Full text
            start: Start position of chunk
            end: Proposed end position
            
        Returns:
            Optimal end position
        """
        chunk = text[start:end]
        
        # Look back from the end to find good break points
        search_window = min(100, len(chunk) // 2)
        
        # Priority 1: Sentence endings (., !, ?)
        for i in range(search_window):
            pos = len(chunk) - i - 1
            if pos < 0:
                break
                
            char = chunk[pos]
            if char in '.!?' and pos > 0:
                # Check if it's a real sentence ending (not abbreviation)
                if self._is_sentence_ending(chunk, pos):
                    return start + pos + 1
        
        # Priority 2: Paragraph breaks (double newlines)
        for i in range(search_window):
            pos = len(chunk) - i - 1
            if pos < 1:
                break
                
            if chunk[pos-1:pos+1] == '\n\n':
                return start + pos + 1
        
        # Priority 3: Line breaks
        for i in range(search_window):
            pos = len(chunk) - i - 1
            if pos < 0:
                break
                
            if chunk[pos] == '\n':
                return start + pos + 1
        
        # Priority 4: Word boundaries (spaces)
        for i in range(search_window):
            pos = len(chunk) - i - 1
            if pos < 0:
                break
                
            if chunk[pos] == ' ':
                return start + pos
        
        # Fallback: use original end
        return end
    
    def _is_sentence_ending(self, text: str, pos: int) -> bool:
        """Check if a period/punctuation is likely a sentence ending.
        
        Args:
            text: Text to check
            pos: Position of punctuation
            
        Returns:
            True if likely sentence ending
        """
        # Common abbreviations that shouldn't end chunks
        abbreviations = ['Dr.', 'Mr.', 'Mrs.', 'vs.', 'etc.', 'Inc.', 'Ltd.', 'Co.']
        
        # Look at context around the punctuation
        start_window = max(0, pos - 10)
        end_window = min(len(text), pos + 5)
        context = text[start_window:end_window]
        
        # Check if it's part of a known abbreviation
        for abbrev in abbreviations:
            if abbrev.lower() in context.lower():
                return False
        
        # Check if followed by lowercase (likely not sentence end)
        if pos + 1 < len(text) and text[pos + 1].islower():
            return False
            
        # Check if preceded by single letter (likely initial)
        if pos > 1 and text[pos-1].isupper() and text[pos-2] == ' ':
            return False
        
        return True
    
    def _assess_safety(self, text: str) -> int:
        """Assess the safety level of text.
        
        Args:
            text: Text to assess
        
        Returns:
            Safety level (1-3)
            1: Normal content
            2: Caution required
            3: High risk, requires expertise
        """
        text = text.lower()
        
        # High risk keywords
        high_risk = [
            'warning', 'danger', 'fatal', 'death', 'serious injury',
            'explosion', 'fire', 'toxic'
        ]
        
        # Medium risk keywords
        medium_risk = [
            'caution', 'attention', 'careful', 'important safety',
            'hot surface', 'sharp edge'
        ]
        
        # Check for high risk content
        for word in high_risk:
            if word in text:
                return 3
        
        # Check for medium risk content
        for word in medium_risk:
            if word in text:
                return 2
        
        return 1 