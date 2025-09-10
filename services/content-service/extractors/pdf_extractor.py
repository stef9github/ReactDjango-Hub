"""
PDF metadata extractor using PyPDF2 and additional libraries
"""

import asyncio
from pathlib import Path
from typing import List, Optional
import time

from .base_extractor import BaseExtractor, ExtractedMetadata


class PDFExtractor(BaseExtractor):
    """Extract metadata from PDF files"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = [
            'application/pdf'
        ]
    
    async def can_extract(self, file_path: Path, mime_type: str) -> bool:
        """Check if this extractor can handle PDF files"""
        return mime_type in self.supported_types and file_path.suffix.lower() == '.pdf'
    
    async def extract_metadata(self, file_path: Path, mime_type: str) -> ExtractedMetadata:
        """Extract comprehensive metadata from PDF files"""
        start_time = time.time()
        metadata = ExtractedMetadata()
        metadata.extractor_version = f"PDFExtractor-{self.version}"
        
        try:
            # Run PDF extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            pdf_data = await loop.run_in_executor(None, self._extract_pdf_sync, file_path)
            
            # Populate metadata from PDF data
            if pdf_data:
                metadata.title = pdf_data.get('title')
                metadata.author = pdf_data.get('author')
                metadata.subject = pdf_data.get('subject')
                metadata.creator = pdf_data.get('creator')
                metadata.producer = pdf_data.get('producer')
                metadata.creation_date = pdf_data.get('creation_date')
                metadata.modification_date = pdf_data.get('modification_date')
                metadata.page_count = pdf_data.get('page_count', 0)
                metadata.text_content = pdf_data.get('text_content', '')
                metadata.encrypted = pdf_data.get('encrypted', False)
                metadata.password_protected = pdf_data.get('password_protected', False)
                metadata.format_version = pdf_data.get('pdf_version')
                metadata.raw_metadata = pdf_data.get('raw_metadata', {})
                
                # Process extracted text
                if metadata.text_content:
                    metadata.word_count = self._count_words(metadata.text_content)
                    metadata.character_count = self._count_characters(metadata.text_content)
                    metadata.language = self._detect_language(metadata.text_content)
                    metadata.keywords = self._extract_keywords(metadata.text_content)
                    
                    # Simple content analysis
                    content_lower = metadata.text_content.lower()
                    metadata.tables_detected = content_lower.count('table')
                    metadata.images_detected = pdf_data.get('image_count', 0)
                    metadata.links_detected = content_lower.count('http')
                    
                    # Confidence based on text length and page count
                    if metadata.page_count and metadata.page_count > 0:
                        avg_words_per_page = metadata.word_count / metadata.page_count
                        if avg_words_per_page > 100:
                            metadata.text_extraction_confidence = 0.9
                        elif avg_words_per_page > 50:
                            metadata.text_extraction_confidence = 0.7
                        else:
                            metadata.text_extraction_confidence = 0.4
                
                # Content-based classification suggestions
                metadata.suggested_categories = self._suggest_categories(metadata.text_content)
                metadata.suggested_tags = self._suggest_tags(metadata.text_content, metadata.title)
                
        except Exception as e:
            error_msg = f"PDF extraction failed: {str(e)}"
            metadata.errors.append(error_msg)
            self.logger.error(error_msg)
        
        # Record processing time
        end_time = time.time()
        metadata.extraction_duration_ms = int((end_time - start_time) * 1000)
        
        return metadata
    
    def _extract_pdf_sync(self, file_path: Path) -> dict:
        """Synchronous PDF extraction (runs in thread pool)"""
        try:
            import PyPDF2
            
            result = {
                'text_content': '',
                'page_count': 0,
                'encrypted': False,
                'password_protected': False,
                'image_count': 0,
                'raw_metadata': {}
            }
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Basic PDF info
                result['page_count'] = len(pdf_reader.pages)
                result['encrypted'] = pdf_reader.is_encrypted
                
                # Handle encrypted PDFs
                if result['encrypted']:
                    result['password_protected'] = True
                    try:
                        # Try empty password (some PDFs are "encrypted" but with no password)
                        pdf_reader.decrypt('')
                    except:
                        # Cannot proceed without password
                        result['text_content'] = ''
                        return result
                
                # Extract metadata
                if pdf_reader.metadata:
                    metadata_dict = {}
                    for key, value in pdf_reader.metadata.items():
                        clean_key = key.replace('/', '').lower()
                        if isinstance(value, str):
                            metadata_dict[clean_key] = value.strip()
                        else:
                            metadata_dict[clean_key] = value
                    
                    result['raw_metadata'] = metadata_dict
                    result['title'] = metadata_dict.get('title')
                    result['author'] = metadata_dict.get('author')
                    result['subject'] = metadata_dict.get('subject')
                    result['creator'] = metadata_dict.get('creator')
                    result['producer'] = metadata_dict.get('producer')
                    
                    # Parse dates
                    if 'creationdate' in metadata_dict:
                        result['creation_date'] = self._parse_date(metadata_dict['creationdate'])
                    if 'moddate' in metadata_dict:
                        result['modification_date'] = self._parse_date(metadata_dict['moddate'])
                
                # Extract text from all pages
                text_content = []
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(page_text)
                    except Exception as e:
                        self.logger.debug(f"Failed to extract text from page {page_num}: {e}")
                        continue
                
                result['text_content'] = '\n'.join(text_content)
                
                # Try to get PDF version
                if hasattr(pdf_reader, 'pdf_header'):
                    result['pdf_version'] = pdf_reader.pdf_header
                
        except ImportError:
            raise ImportError("PyPDF2 library is required for PDF extraction")
        except Exception as e:
            self.logger.error(f"PDF extraction error: {e}")
            raise
        
        return result
    
    def _suggest_categories(self, text_content: Optional[str]) -> List[str]:
        """Suggest document categories based on content"""
        if not text_content:
            return []
        
        categories = []
        content_lower = text_content.lower()
        
        # Business documents
        business_keywords = ['contract', 'agreement', 'invoice', 'proposal', 'report', 'analysis', 'budget', 'financial']
        if any(keyword in content_lower for keyword in business_keywords):
            categories.append('business')
        
        # Legal documents
        legal_keywords = ['legal', 'law', 'court', 'lawsuit', 'attorney', 'counsel', 'jurisdiction', 'whereas']
        if any(keyword in content_lower for keyword in legal_keywords):
            categories.append('legal')
        
        # Technical documents
        tech_keywords = ['technical', 'specification', 'manual', 'guide', 'documentation', 'api', 'system']
        if any(keyword in content_lower for keyword in tech_keywords):
            categories.append('technical')
        
        # Academic documents
        academic_keywords = ['research', 'study', 'paper', 'thesis', 'dissertation', 'abstract', 'bibliography']
        if any(keyword in content_lower for keyword in academic_keywords):
            categories.append('academic')
        
        # Medical documents
        medical_keywords = ['medical', 'patient', 'diagnosis', 'treatment', 'clinical', 'health', 'medicine']
        if any(keyword in content_lower for keyword in medical_keywords):
            categories.append('medical')
        
        return categories[:3]  # Limit to top 3 categories
    
    def _suggest_tags(self, text_content: Optional[str], title: Optional[str]) -> List[str]:
        """Suggest tags based on content and title"""
        tags = []
        
        # Extract from title
        if title:
            title_words = [word.strip('.,!?').lower() for word in title.split() if len(word) > 3]
            tags.extend(title_words[:5])
        
        # Extract from content
        if text_content:
            content_tags = self._extract_keywords(text_content, max_keywords=10)
            tags.extend(content_tags[:8])
        
        # Remove duplicates and return
        return list(set(tags))[:15]
    
    def get_supported_mime_types(self) -> List[str]:
        """Get list of supported MIME types"""
        return self.supported_types.copy()