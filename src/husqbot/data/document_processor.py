"""
Document processing for Husqvarna RAG Support System.
"""

import logging
from typing import List, Dict
from datetime import datetime
import uuid
import PyPDF2
from pathlib import Path


logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process documents for RAG system."""
    
    def __init__(
        self,
        chunk_size: int = 500,  # Reduced from 1000
        overlap: int = 100,     # Reduced from 200
        page_batch_size: int = 2  # Reduced from 5
    ):
        """Initialize document processor.
        
        Args:
            chunk_size: Maximum number of characters per chunk
            overlap: Number of characters to overlap between chunks
            page_batch_size: Number of pages to process at once
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.page_batch_size = page_batch_size
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
    
    def process_pdf(self, file_path: str) -> List[Dict]:
        """Process a PDF file into chunks.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing chunk information
        """
        chunks = []
        source = Path(file_path).name
        
        logger.info(f"Opening PDF file: {file_path}")
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            logger.info(f"PDF has {total_pages} pages")
            
            # Process pages in batches
            for start_page in range(0, total_pages, self.page_batch_size):
                end_page = min(start_page + self.page_batch_size, total_pages)
                batch_info = (
                    f"Processing pages {start_page + 1} to {end_page} "
                    f"of {total_pages}"
                )
                logger.info(batch_info)
                
                # Process each page in the batch
                for page_num in range(start_page, end_page):
                    page_info = f"Extracting text from page {page_num + 1}"
                    logger.info(page_info)
                    
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    text_info = (
                        f"Extracted {len(text)} characters from "
                        f"page {page_num + 1}"
                    )
                    logger.info(text_info)
                    
                    # Create chunks from page text
                    page_chunks = self._create_chunks(text)
                    chunks_info = (
                        f"Created {len(page_chunks)} chunks from "
                        f"page {page_num + 1}"
                    )
                    logger.info(chunks_info)
                    
                    # Add metadata to chunks
                    for chunk in page_chunks:
                        chunk_dict = {
                            'chunk_id': str(uuid.uuid4()),
                            'content': chunk,
                            'source': source,
                            'page_number': page_num + 1,
                            'safety_level': self._assess_safety(chunk),
                            'created_at': datetime.utcnow().isoformat()
                        }
                        chunks.append(chunk_dict)
                
                batch_complete = (
                    f"Completed batch of {end_page - start_page} pages"
                )
                logger.info(batch_complete)
        
        final_info = f"Finished processing PDF. Created {len(chunks)} chunks"
        logger.info(final_info)
        return chunks
    
    def _create_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks.
        
        Args:
            text: Text to split into chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            # Get chunk of text
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Adjust chunk to end at sentence boundary if possible
            if end < len(text):
                last_period = chunk.rfind('.')
                if last_period != -1:
                    chunk = chunk[:last_period + 1]
                    end = start + last_period + 1
            
            chunk = chunk.strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            start = end - self.overlap
        
        return chunks
    
    def _assess_safety(self, text: str) -> int:
        """Assess safety level of text chunk.
        
        Args:
            text: Text to assess
            
        Returns:
            Safety level (1-3, where 3 is highest safety concern)
        """
        # Keywords indicating safety concerns
        high_risk = ['warning', 'danger', 'fatal', 'death', 'serious injury']
        medium_risk = ['caution', 'attention', 'careful', 'important safety']
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in high_risk):
            return 3
        elif any(word in text_lower for word in medium_risk):
            return 2
        return 1 