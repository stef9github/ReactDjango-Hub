"""
Base metadata extractor class and data structures
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExtractedMetadata:
    """Container for extracted metadata from documents"""
    
    # Content information
    text_content: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    
    # Document properties
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    language: Optional[str] = None
    
    # Dates
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    
    # Image/media specific
    dimensions: Optional[Dict[str, int]] = None  # {"width": 1920, "height": 1080}
    resolution: Optional[Dict[str, int]] = None  # {"x": 300, "y": 300}
    color_mode: Optional[str] = None
    
    # Security and access
    encrypted: bool = False
    password_protected: bool = False
    
    # Technical metadata
    format_version: Optional[str] = None
    compression: Optional[str] = None
    
    # Extracted features
    tables_detected: int = 0
    images_detected: int = 0
    links_detected: int = 0
    
    # Confidence scores
    ocr_confidence: Optional[float] = None
    text_extraction_confidence: Optional[float] = None
    
    # Classification suggestions
    suggested_categories: List[str] = field(default_factory=list)
    suggested_tags: List[str] = field(default_factory=list)
    
    # Raw metadata for specific formats
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing information
    extraction_duration_ms: Optional[int] = None
    extractor_version: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Path):
                result[key] = str(value)
            else:
                result[key] = value
        return result
    
    def has_text_content(self) -> bool:
        """Check if meaningful text content was extracted"""
        return bool(self.text_content and len(self.text_content.strip()) > 10)
    
    def get_summary(self) -> str:
        """Get a brief summary of extracted metadata"""
        parts = []
        
        if self.title:
            parts.append(f"Title: {self.title}")
        if self.author:
            parts.append(f"Author: {self.author}")
        if self.page_count:
            parts.append(f"Pages: {self.page_count}")
        if self.word_count:
            parts.append(f"Words: {self.word_count}")
        if self.language:
            parts.append(f"Language: {self.language}")
            
        return " | ".join(parts) if parts else "No significant metadata extracted"


class BaseExtractor(ABC):
    """Abstract base class for metadata extractors"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.version = "1.0.0"
    
    @abstractmethod
    async def can_extract(self, file_path: Path, mime_type: str) -> bool:
        """Check if this extractor can handle the given file"""
        pass
    
    @abstractmethod 
    async def extract_metadata(self, file_path: Path, mime_type: str) -> ExtractedMetadata:
        """Extract metadata from the file"""
        pass
    
    @abstractmethod
    def get_supported_mime_types(self) -> List[str]:
        """Get list of supported MIME types"""
        pass
    
    def _safe_extract(self, extraction_func, *args, **kwargs) -> Any:
        """Safely execute extraction with error handling"""
        try:
            return extraction_func(*args, **kwargs)
        except Exception as e:
            self.logger.warning(f"Extraction failed: {e}")
            return None
    
    def _detect_language(self, text: str) -> Optional[str]:
        """Detect language of text content"""
        if not text or len(text.strip()) < 50:
            return None
            
        try:
            # Simple language detection - can be enhanced with proper library
            text_lower = text.lower()
            
            # French indicators
            french_indicators = ['le ', 'la ', 'les ', 'un ', 'une ', 'des ', 'du ', 'de ', 'et ', 'ou ', 'ce ', 'cette ', 'avec ', 'pour ', 'dans ']
            french_score = sum(1 for indicator in french_indicators if indicator in text_lower)
            
            # English indicators  
            english_indicators = ['the ', 'a ', 'an ', 'and ', 'or ', 'is ', 'are ', 'was ', 'were ', 'this ', 'that ', 'with ', 'for ', 'in ']
            english_score = sum(1 for indicator in english_indicators if indicator in text_lower)
            
            # German indicators
            german_indicators = ['der ', 'die ', 'das ', 'den ', 'dem ', 'des ', 'ein ', 'eine ', 'und ', 'oder ', 'ist ', 'sind ', 'mit ', 'für ', 'in ']
            german_score = sum(1 for indicator in german_indicators if indicator in text_lower)
            
            # Spanish indicators
            spanish_indicators = ['el ', 'la ', 'los ', 'las ', 'un ', 'una ', 'y ', 'o ', 'es ', 'son ', 'con ', 'para ', 'en ']
            spanish_score = sum(1 for indicator in spanish_indicators if indicator in text_lower)
            
            scores = {
                'fr': french_score,
                'en': english_score, 
                'de': german_score,
                'es': spanish_score
            }
            
            max_lang = max(scores, key=scores.get)
            if scores[max_lang] > 3:  # Minimum confidence threshold
                return max_lang
                
        except Exception as e:
            self.logger.debug(f"Language detection failed: {e}")
            
        return None
    
    def _extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """Extract potential keywords from text"""
        if not text or len(text.strip()) < 20:
            return []
            
        try:
            import re
            from collections import Counter
            
            # Clean text and extract words
            text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
            words = text_clean.split()
            
            # Filter out common stop words and short words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
                'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
                'they', 'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'de', 'du',
                'der', 'die', 'das', 'und', 'oder', 'ist', 'sind', 'el', 'la', 'los',
                'las', 'y', 'o', 'es', 'son'
            }
            
            # Filter and count words
            meaningful_words = [
                word for word in words 
                if len(word) > 3 and word not in stop_words and word.isalpha()
            ]
            
            # Get most common words
            word_counts = Counter(meaningful_words)
            keywords = [word for word, count in word_counts.most_common(max_keywords)]
            
            return keywords
            
        except Exception as e:
            self.logger.debug(f"Keyword extraction failed: {e}")
            return []
    
    def _count_words(self, text: str) -> int:
        """Count words in text"""
        if not text:
            return 0
        return len(text.split())
    
    def _count_characters(self, text: str) -> int:
        """Count characters in text (excluding whitespace)"""
        if not text:
            return 0
        return len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
    
    def _parse_date(self, date_str: Any) -> Optional[datetime]:
        """Parse various date formats to datetime"""
        if not date_str:
            return None
            
        if isinstance(date_str, datetime):
            return date_str
            
        if not isinstance(date_str, str):
            date_str = str(date_str)
            
        try:
            from dateutil.parser import parse
            return parse(date_str)
        except:
            try:
                # Try common formats
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
            except:
                pass
                
        return None