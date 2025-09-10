"""
Metadata extractor factory for selecting appropriate extractor
"""

from pathlib import Path
from typing import List, Optional
import logging

from .base_extractor import BaseExtractor, ExtractedMetadata
from .pdf_extractor import PDFExtractor
from .image_extractor import ImageExtractor
from .text_extractor import TextExtractor
from .office_extractor import OfficeExtractor

logger = logging.getLogger(__name__)


class MetadataExtractorFactory:
    """Factory class for creating and managing metadata extractors"""
    
    def __init__(self):
        # Initialize all available extractors
        self.extractors: List[BaseExtractor] = [
            PDFExtractor(),
            ImageExtractor(),
            TextExtractor(),
            OfficeExtractor()
        ]
        
        # Cache supported MIME types for quick lookup
        self._mime_type_cache = {}
        self._build_mime_type_cache()
        
        logger.info(f"Initialized MetadataExtractorFactory with {len(self.extractors)} extractors")
    
    def _build_mime_type_cache(self):
        """Build cache of MIME types to extractor mappings"""
        for extractor in self.extractors:
            try:
                supported_types = extractor.get_supported_mime_types()
                for mime_type in supported_types:
                    if mime_type not in self._mime_type_cache:
                        self._mime_type_cache[mime_type] = []
                    self._mime_type_cache[mime_type].append(extractor)
            except Exception as e:
                logger.warning(f"Failed to get supported MIME types from {extractor.__class__.__name__}: {e}")
    
    async def get_extractor(self, file_path: Path, mime_type: str) -> Optional[BaseExtractor]:
        """
        Get the best extractor for the given file and MIME type
        
        Args:
            file_path: Path to the file
            mime_type: MIME type of the file
            
        Returns:
            Best matching extractor or None if no extractor can handle the file
        """
        try:
            # First, check MIME type cache for quick lookup
            potential_extractors = self._mime_type_cache.get(mime_type, [])
            
            # If no extractors found by MIME type, check all extractors
            if not potential_extractors:
                potential_extractors = self.extractors
            
            # Test each potential extractor to see if it can handle the file
            for extractor in potential_extractors:
                try:
                    if await extractor.can_extract(file_path, mime_type):
                        logger.debug(f"Selected {extractor.__class__.__name__} for {file_path} ({mime_type})")
                        return extractor
                except Exception as e:
                    logger.warning(f"Error checking if {extractor.__class__.__name__} can extract {file_path}: {e}")
                    continue
            
            logger.info(f"No suitable extractor found for {file_path} ({mime_type})")
            return None
            
        except Exception as e:
            logger.error(f"Error finding extractor for {file_path}: {e}")
            return None
    
    async def extract_metadata(self, file_path: Path, mime_type: str) -> ExtractedMetadata:
        """
        Extract metadata from file using the best available extractor
        
        Args:
            file_path: Path to the file
            mime_type: MIME type of the file
            
        Returns:
            ExtractedMetadata object with extracted information
        """
        # Validate inputs
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not mime_type:
            raise ValueError("MIME type is required")
        
        # Get appropriate extractor
        extractor = await self.get_extractor(file_path, mime_type)
        
        if extractor is None:
            # Create basic metadata for unsupported files
            metadata = ExtractedMetadata()
            metadata.warnings.append(f"No extractor available for MIME type: {mime_type}")
            metadata.suggested_categories = ['unknown']
            metadata.suggested_tags = [file_path.suffix.lower().lstrip('.') if file_path.suffix else 'file']
            metadata.extractor_version = "UnsupportedExtractor-1.0.0"
            return metadata
        
        try:
            # Extract metadata using selected extractor
            metadata = await extractor.extract_metadata(file_path, mime_type)
            
            # Add file system metadata if not already present
            if not metadata.creation_date or not metadata.modification_date:
                stat = file_path.stat()
                if not metadata.creation_date:
                    metadata.creation_date = extractor._parse_date(stat.st_ctime)
                if not metadata.modification_date:
                    metadata.modification_date = extractor._parse_date(stat.st_mtime)
            
            logger.info(f"Successfully extracted metadata from {file_path} using {extractor.__class__.__name__}")
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed for {file_path}: {e}")
            
            # Return metadata with error information
            metadata = ExtractedMetadata()
            metadata.errors.append(f"Extraction failed: {str(e)}")
            metadata.extractor_version = f"{extractor.__class__.__name__}-error"
            
            # Try to provide basic file information
            try:
                stat = file_path.stat()
                metadata.creation_date = extractor._parse_date(stat.st_ctime)
                metadata.modification_date = extractor._parse_date(stat.st_mtime)
            except:
                pass
            
            return metadata
    
    def get_supported_mime_types(self) -> List[str]:
        """Get all supported MIME types across all extractors"""
        return list(self._mime_type_cache.keys())
    
    def get_extractor_info(self) -> dict:
        """Get information about available extractors"""
        info = {
            'total_extractors': len(self.extractors),
            'extractors': []
        }
        
        for extractor in self.extractors:
            extractor_info = {
                'name': extractor.__class__.__name__,
                'version': getattr(extractor, 'version', 'unknown'),
                'supported_mime_types': []
            }
            
            try:
                extractor_info['supported_mime_types'] = extractor.get_supported_mime_types()
            except Exception as e:
                logger.warning(f"Failed to get MIME types from {extractor.__class__.__name__}: {e}")
            
            info['extractors'].append(extractor_info)
        
        return info
    
    async def test_extractor_availability(self) -> dict:
        """Test availability of all extractors and their dependencies"""
        results = {
            'available_extractors': [],
            'unavailable_extractors': [],
            'dependency_issues': []
        }
        
        for extractor in self.extractors:
            extractor_name = extractor.__class__.__name__
            
            try:
                # Create a dummy path for testing
                test_path = Path('test_file.txt')
                
                # Test if extractor can be initialized and basic methods work
                await extractor.can_extract(test_path, 'text/plain')
                supported_types = extractor.get_supported_mime_types()
                
                results['available_extractors'].append({
                    'name': extractor_name,
                    'version': getattr(extractor, 'version', 'unknown'),
                    'supported_types_count': len(supported_types)
                })
                
            except ImportError as e:
                results['unavailable_extractors'].append({
                    'name': extractor_name,
                    'error': f"Missing dependency: {str(e)}"
                })
                results['dependency_issues'].append(str(e))
                
            except Exception as e:
                results['unavailable_extractors'].append({
                    'name': extractor_name,
                    'error': str(e)
                })
        
        return results


# Global factory instance
metadata_factory = MetadataExtractorFactory()