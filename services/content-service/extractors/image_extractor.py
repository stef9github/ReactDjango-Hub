"""
Image metadata extractor using Pillow and pytesseract for OCR
"""

import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
import time

from .base_extractor import BaseExtractor, ExtractedMetadata


class ImageExtractor(BaseExtractor):
    """Extract metadata from image files with OCR capability"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = [
            'image/jpeg',
            'image/png', 
            'image/tiff',
            'image/bmp',
            'image/gif',
            'image/webp'
        ]
        # OCR languages configured in environment
        import os
        self.ocr_languages = os.getenv('OCR_LANGUAGES', 'eng,fra,deu,spa').split(',')
        self.ocr_confidence_threshold = int(os.getenv('OCR_CONFIDENCE_THRESHOLD', 60))
    
    async def can_extract(self, file_path: Path, mime_type: str) -> bool:
        """Check if this extractor can handle image files"""
        return mime_type in self.supported_types
    
    async def extract_metadata(self, file_path: Path, mime_type: str) -> ExtractedMetadata:
        """Extract comprehensive metadata from image files"""
        start_time = time.time()
        metadata = ExtractedMetadata()
        metadata.extractor_version = f"ImageExtractor-{self.version}"
        
        try:
            # Run image extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            image_data = await loop.run_in_executor(None, self._extract_image_sync, file_path)
            
            if image_data:
                # Basic image properties
                metadata.dimensions = image_data.get('dimensions')
                metadata.resolution = image_data.get('resolution')
                metadata.color_mode = image_data.get('color_mode')
                metadata.format_version = image_data.get('format')
                metadata.compression = image_data.get('compression')
                metadata.raw_metadata = image_data.get('exif_data', {})
                
                # EXIF dates
                metadata.creation_date = image_data.get('creation_date')
                metadata.modification_date = image_data.get('modification_date')
                
                # OCR text extraction
                ocr_result = image_data.get('ocr_result')
                if ocr_result:
                    metadata.text_content = ocr_result.get('text', '')
                    metadata.ocr_confidence = ocr_result.get('confidence')
                    
                    # Process extracted text
                    if metadata.text_content and len(metadata.text_content.strip()) > 10:
                        metadata.word_count = self._count_words(metadata.text_content)
                        metadata.character_count = self._count_characters(metadata.text_content)
                        metadata.language = self._detect_language(metadata.text_content)
                        metadata.keywords = self._extract_keywords(metadata.text_content)
                        metadata.text_extraction_confidence = metadata.ocr_confidence / 100.0 if metadata.ocr_confidence else 0.5
                        
                        # Content-based suggestions
                        metadata.suggested_categories = self._suggest_categories(metadata.text_content)
                        metadata.suggested_tags = self._suggest_tags(metadata.text_content, str(file_path.stem))
                
                # Image-specific analysis
                self._analyze_image_content(metadata, image_data)
                
        except Exception as e:
            error_msg = f"Image extraction failed: {str(e)}"
            metadata.errors.append(error_msg)
            self.logger.error(error_msg)
        
        # Record processing time
        end_time = time.time()
        metadata.extraction_duration_ms = int((end_time - start_time) * 1000)
        
        return metadata
    
    def _extract_image_sync(self, file_path: Path) -> Dict[str, Any]:
        """Synchronous image extraction (runs in thread pool)"""
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            import pytesseract
            
            result = {}
            
            with Image.open(file_path) as img:
                # Basic image properties
                result['dimensions'] = {'width': img.width, 'height': img.height}
                result['color_mode'] = img.mode
                result['format'] = img.format
                
                # Resolution (DPI)
                dpi = getattr(img, 'dpi', None)
                if dpi:
                    result['resolution'] = {'x': dpi[0], 'y': dpi[1]}
                
                # EXIF data extraction
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if isinstance(value, str):
                            exif_data[tag] = value.strip()
                        else:
                            exif_data[tag] = value
                    
                    result['exif_data'] = exif_data
                    
                    # Extract common EXIF fields
                    result['creation_date'] = self._parse_date(exif_data.get('DateTime'))
                    result['modification_date'] = self._parse_date(exif_data.get('DateTimeOriginal'))
                
                # OCR text extraction
                try:
                    # Convert to RGB if necessary for OCR
                    ocr_image = img.convert('RGB') if img.mode != 'RGB' else img
                    
                    # Configure OCR with multiple languages
                    ocr_config = f'-l {"+".join(self.ocr_languages)} --psm 3'
                    
                    # Extract text with confidence
                    ocr_data = pytesseract.image_to_data(
                        ocr_image,
                        config=ocr_config,
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # Filter text by confidence threshold
                    filtered_words = []
                    confidences = []
                    
                    for i, confidence in enumerate(ocr_data['conf']):
                        if int(confidence) > self.ocr_confidence_threshold:
                            word = ocr_data['text'][i].strip()
                            if word:
                                filtered_words.append(word)
                                confidences.append(int(confidence))
                    
                    extracted_text = ' '.join(filtered_words)
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    result['ocr_result'] = {
                        'text': extracted_text,
                        'confidence': avg_confidence,
                        'word_count': len(filtered_words),
                        'raw_data': ocr_data
                    }
                    
                except ImportError:
                    result['ocr_result'] = {'error': 'pytesseract not available'}
                except Exception as e:
                    result['ocr_result'] = {'error': f'OCR failed: {str(e)}'}
                    self.logger.debug(f"OCR extraction failed: {e}")
        
        except ImportError:
            raise ImportError("Pillow library is required for image extraction")
        except Exception as e:
            self.logger.error(f"Image extraction error: {e}")
            raise
        
        return result
    
    def _analyze_image_content(self, metadata: ExtractedMetadata, image_data: Dict[str, Any]):
        """Analyze image content for additional insights"""
        # Image size classification
        dims = metadata.dimensions
        if dims:
            width, height = dims['width'], dims['height']
            total_pixels = width * height
            
            # Add size-based tags
            if total_pixels > 8000000:  # > 8MP
                metadata.suggested_tags.append('high-resolution')
            elif total_pixels < 500000:  # < 0.5MP
                metadata.suggested_tags.append('low-resolution')
            
            # Aspect ratio analysis
            aspect_ratio = width / height if height > 0 else 1
            if abs(aspect_ratio - 1) < 0.1:
                metadata.suggested_tags.append('square')
            elif aspect_ratio > 1.5:
                metadata.suggested_tags.append('landscape')
            elif aspect_ratio < 0.7:
                metadata.suggested_tags.append('portrait')
        
        # Color mode analysis
        if metadata.color_mode:
            if metadata.color_mode in ['1', 'L']:
                metadata.suggested_tags.append('monochrome')
            elif metadata.color_mode == 'CMYK':
                metadata.suggested_tags.append('print-ready')
        
        # EXIF-based suggestions
        exif = metadata.raw_metadata
        if exif:
            if 'Make' in exif or 'Model' in exif:
                metadata.suggested_categories.append('photography')
            if 'Software' in exif:
                software = exif['Software'].lower()
                if any(editor in software for editor in ['photoshop', 'gimp', 'illustrator']):
                    metadata.suggested_categories.append('design')
    
    def _suggest_categories(self, text_content: Optional[str]) -> List[str]:
        """Suggest document categories based on OCR text"""
        if not text_content:
            return ['image']
        
        categories = ['image']  # Always include base category
        content_lower = text_content.lower()
        
        # Document scans
        doc_keywords = ['page', 'document', 'letter', 'memo', 'report', 'form']
        if any(keyword in content_lower for keyword in doc_keywords):
            categories.append('scanned-document')
        
        # Charts and diagrams
        chart_keywords = ['chart', 'graph', 'diagram', 'figure', 'table', 'data']
        if any(keyword in content_lower for keyword in chart_keywords):
            categories.append('chart')
        
        # Screenshots
        ui_keywords = ['button', 'click', 'menu', 'window', 'application', 'software']
        if any(keyword in content_lower for keyword in ui_keywords):
            categories.append('screenshot')
        
        # Business cards/ID
        contact_keywords = ['phone', 'email', 'address', 'contact', 'company', 'manager']
        if any(keyword in content_lower for keyword in contact_keywords):
            categories.append('contact-info')
        
        return categories[:4]
    
    def _suggest_tags(self, text_content: Optional[str], filename: str) -> List[str]:
        """Suggest tags based on OCR text and filename"""
        tags = []
        
        # Extract from filename
        filename_clean = filename.replace('_', ' ').replace('-', ' ')
        filename_words = [word.lower() for word in filename_clean.split() if len(word) > 2]
        tags.extend(filename_words[:3])
        
        # Extract from OCR text
        if text_content and len(text_content) > 20:
            content_tags = self._extract_keywords(text_content, max_keywords=8)
            tags.extend(content_tags)
        
        # Remove duplicates and return
        return list(set(tags))[:12]
    
    def get_supported_mime_types(self) -> List[str]:
        """Get list of supported MIME types"""
        return self.supported_types.copy()