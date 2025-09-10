"""
Text file metadata extractor for plain text and rich text documents
"""

import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
import time

from .base_extractor import BaseExtractor, ExtractedMetadata


class TextExtractor(BaseExtractor):
    """Extract metadata from text-based files"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = [
            'text/plain',
            'text/html',
            'text/markdown',
            'text/csv',
            'text/xml',
            'application/xml',
            'text/rtf'
        ]
        # Common encodings to try
        self.encodings = ['utf-8', 'utf-16', 'iso-8859-1', 'windows-1252', 'ascii']
    
    async def can_extract(self, file_path: Path, mime_type: str) -> bool:
        """Check if this extractor can handle text files"""
        return mime_type in self.supported_types or file_path.suffix.lower() in ['.txt', '.md', '.csv', '.html', '.xml', '.rtf']
    
    async def extract_metadata(self, file_path: Path, mime_type: str) -> ExtractedMetadata:
        """Extract comprehensive metadata from text files"""
        start_time = time.time()
        metadata = ExtractedMetadata()
        metadata.extractor_version = f"TextExtractor-{self.version}"
        
        try:
            # Run text extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            text_data = await loop.run_in_executor(None, self._extract_text_sync, file_path, mime_type)
            
            if text_data:
                metadata.text_content = text_data.get('content', '')
                metadata.format_version = text_data.get('detected_format')
                metadata.raw_metadata = text_data.get('metadata', {})
                
                # Analyze text content
                if metadata.text_content:
                    metadata.word_count = self._count_words(metadata.text_content)
                    metadata.character_count = self._count_characters(metadata.text_content)
                    metadata.language = self._detect_language(metadata.text_content)
                    metadata.keywords = self._extract_keywords(metadata.text_content)
                    
                    # Extract title from content
                    metadata.title = self._extract_title(metadata.text_content, mime_type)
                    
                    # Text quality assessment
                    metadata.text_extraction_confidence = self._assess_text_quality(metadata.text_content)
                    
                    # Content analysis
                    metadata.tables_detected = self._count_tables(metadata.text_content, mime_type)
                    metadata.links_detected = self._count_links(metadata.text_content)
                    
                    # Content-based classification
                    metadata.suggested_categories = self._suggest_categories(metadata.text_content, mime_type)
                    metadata.suggested_tags = self._suggest_tags(metadata.text_content, file_path.stem, mime_type)
                    
                    # Format-specific analysis
                    if mime_type == 'text/csv':
                        self._analyze_csv_content(metadata, metadata.text_content)
                    elif mime_type in ['text/html', 'text/xml', 'application/xml']:
                        self._analyze_markup_content(metadata, metadata.text_content, mime_type)
                
        except Exception as e:
            error_msg = f"Text extraction failed: {str(e)}"
            metadata.errors.append(error_msg)
            self.logger.error(error_msg)
        
        # Record processing time
        end_time = time.time()
        metadata.extraction_duration_ms = int((end_time - start_time) * 1000)
        
        return metadata
    
    def _extract_text_sync(self, file_path: Path, mime_type: str) -> Dict[str, Any]:
        """Synchronous text extraction (runs in thread pool)"""
        result = {
            'content': '',
            'detected_format': mime_type,
            'metadata': {}
        }
        
        try:
            # Try different encodings to read the file
            content = None
            encoding_used = None
            
            for encoding in self.encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        encoding_used = encoding
                        break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    self.logger.debug(f"Failed to read with encoding {encoding}: {e}")
                    continue
            
            if content is None:
                raise ValueError(f"Could not read file with any supported encoding: {self.encodings}")
            
            result['content'] = content
            result['metadata']['encoding'] = encoding_used
            result['metadata']['file_size_bytes'] = file_path.stat().st_size
            result['metadata']['line_count'] = len(content.splitlines())
            
            # Format-specific processing
            if mime_type == 'text/html':
                result.update(self._process_html(content))
            elif mime_type in ['text/xml', 'application/xml']:
                result.update(self._process_xml(content))
            elif mime_type == 'text/csv':
                result.update(self._process_csv(content))
            elif mime_type == 'text/markdown':
                result.update(self._process_markdown(content))
            elif mime_type == 'text/rtf':
                result.update(self._process_rtf(content))
        
        except Exception as e:
            self.logger.error(f"Text extraction error: {e}")
            raise
        
        return result
    
    def _process_html(self, content: str) -> Dict[str, Any]:
        """Process HTML content to extract metadata"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            result = {'metadata': {}}
            
            # Extract HTML title
            title_tag = soup.find('title')
            if title_tag:
                result['metadata']['html_title'] = title_tag.get_text().strip()
            
            # Extract meta tags
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
                content_attr = meta.get('content')
                if name and content_attr:
                    result['metadata'][f'meta_{name}'] = content_attr
            
            # Extract clean text content
            for script in soup(["script", "style"]):
                script.decompose()
            result['content'] = soup.get_text()
            
            return result
            
        except ImportError:
            self.logger.warning("BeautifulSoup not available for HTML processing")
            return {'metadata': {'html_processing': 'disabled'}}
        except Exception as e:
            self.logger.debug(f"HTML processing failed: {e}")
            return {'metadata': {'html_processing_error': str(e)}}
    
    def _process_xml(self, content: str) -> Dict[str, Any]:
        """Process XML content to extract metadata"""
        try:
            import xml.etree.ElementTree as ET
            
            result = {'metadata': {}}
            
            root = ET.fromstring(content)
            result['metadata']['xml_root_tag'] = root.tag
            result['metadata']['xml_namespace'] = root.tag.split('}')[0][1:] if '}' in root.tag else None
            
            # Count elements
            all_elements = root.findall('.//*')
            result['metadata']['xml_element_count'] = len(all_elements)
            
            # Extract text content
            result['content'] = ET.tostring(root, method='text', encoding='unicode')
            
            return result
            
        except Exception as e:
            self.logger.debug(f"XML processing failed: {e}")
            return {'metadata': {'xml_processing_error': str(e)}}
    
    def _process_csv(self, content: str) -> Dict[str, Any]:
        """Process CSV content to extract metadata"""
        try:
            import csv
            from io import StringIO
            
            result = {'metadata': {}}
            
            # Detect CSV dialect
            sniffer = csv.Sniffer()
            sample = content[:1024]
            dialect = sniffer.sniff(sample)
            
            result['metadata']['csv_delimiter'] = dialect.delimiter
            result['metadata']['csv_quotechar'] = dialect.quotechar
            
            # Count rows and columns
            reader = csv.reader(StringIO(content), dialect=dialect)
            rows = list(reader)
            
            result['metadata']['csv_row_count'] = len(rows)
            result['metadata']['csv_column_count'] = len(rows[0]) if rows else 0
            
            # Extract headers if available
            if rows:
                result['metadata']['csv_headers'] = rows[0]
            
            return result
            
        except Exception as e:
            self.logger.debug(f"CSV processing failed: {e}")
            return {'metadata': {'csv_processing_error': str(e)}}
    
    def _process_markdown(self, content: str) -> Dict[str, Any]:
        """Process Markdown content to extract metadata"""
        result = {'metadata': {}}
        
        lines = content.splitlines()
        
        # Extract title (first # heading)
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                result['metadata']['markdown_title'] = line[2:].strip()
                break
        
        # Count headings
        heading_count = sum(1 for line in lines if line.strip().startswith('#'))
        result['metadata']['markdown_heading_count'] = heading_count
        
        # Count code blocks
        code_block_count = content.count('```')
        result['metadata']['markdown_code_blocks'] = code_block_count // 2
        
        return result
    
    def _process_rtf(self, content: str) -> Dict[str, Any]:
        """Process RTF content to extract metadata"""
        result = {'metadata': {}}
        
        # Basic RTF analysis
        if content.startswith('{\\rtf'):
            result['metadata']['rtf_version'] = content[5:6] if len(content) > 5 else 'unknown'
        
        # Extract plain text (simple RTF stripping)
        import re
        # Remove RTF control words and groups
        text = re.sub(r'\\[a-z]+\d*', ' ', content)
        text = re.sub(r'[{}]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        result['content'] = text
        return result
    
    def _extract_title(self, content: str, mime_type: str) -> Optional[str]:
        """Extract title from content based on format"""
        if not content:
            return None
        
        lines = content.splitlines()
        if not lines:
            return None
        
        # For Markdown, look for # heading
        if mime_type == 'text/markdown':
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                if line.startswith('# '):
                    return line[2:].strip()
        
        # For other text files, use first non-empty line as potential title
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line) < 100:  # Reasonable title length
                return line
        
        return None
    
    def _assess_text_quality(self, content: str) -> float:
        """Assess the quality/confidence of extracted text"""
        if not content:
            return 0.0
        
        score = 1.0
        
        # Check for reasonable word-to-character ratio
        words = len(content.split())
        chars = len(content)
        if chars > 0:
            ratio = words / chars
            if ratio < 0.1:  # Too few words per character
                score *= 0.7
        
        # Check for reasonable sentence structure
        sentences = content.count('.') + content.count('!') + content.count('?')
        if words > 20 and sentences == 0:  # Long text with no punctuation
            score *= 0.8
        
        # Check for excessive special characters
        special_chars = sum(1 for c in content if not c.isalnum() and not c.isspace())
        if chars > 0 and special_chars / chars > 0.3:
            score *= 0.7
        
        return min(score, 1.0)
    
    def _count_tables(self, content: str, mime_type: str) -> int:
        """Count potential tables in text content"""
        if mime_type == 'text/csv':
            return 1
        
        # Look for table-like structures
        table_indicators = content.lower().count('table') + content.count('|')
        
        # CSV-like content (multiple tabs or commas per line)
        lines = content.splitlines()
        csv_like_lines = sum(1 for line in lines if line.count('\t') > 2 or line.count(',') > 2)
        
        return min(table_indicators + (csv_like_lines // 5), 10)  # Cap at 10
    
    def _count_links(self, content: str) -> int:
        """Count links in text content"""
        import re
        
        # URL pattern
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, content, re.IGNORECASE)
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        
        return len(urls) + len(emails)
    
    def _analyze_csv_content(self, metadata: ExtractedMetadata, content: str):
        """Analyze CSV-specific content"""
        metadata.suggested_categories.append('data')
        metadata.suggested_tags.extend(['spreadsheet', 'data', 'table'])
    
    def _analyze_markup_content(self, metadata: ExtractedMetadata, content: str, mime_type: str):
        """Analyze HTML/XML markup content"""
        if mime_type == 'text/html':
            metadata.suggested_categories.append('web')
            metadata.suggested_tags.extend(['html', 'web', 'markup'])
        else:
            metadata.suggested_categories.append('data')
            metadata.suggested_tags.extend(['xml', 'data', 'structured'])
    
    def _suggest_categories(self, content: str, mime_type: str) -> List[str]:
        """Suggest categories based on content and file type"""
        categories = ['text']
        content_lower = content.lower() if content else ''
        
        # Format-based categories
        if mime_type == 'text/csv':
            categories.append('data')
        elif mime_type in ['text/html', 'text/xml']:
            categories.append('markup')
        elif mime_type == 'text/markdown':
            categories.append('documentation')
        
        # Content-based categories
        if any(word in content_lower for word in ['readme', 'documentation', 'guide', 'manual']):
            categories.append('documentation')
        
        if any(word in content_lower for word in ['config', 'configuration', 'settings']):
            categories.append('configuration')
        
        if any(word in content_lower for word in ['log', 'error', 'debug', 'trace']):
            categories.append('logs')
        
        if any(word in content_lower for word in ['script', 'code', 'function', 'class']):
            categories.append('code')
        
        return categories[:4]
    
    def _suggest_tags(self, content: str, filename: str, mime_type: str) -> List[str]:
        """Suggest tags based on content, filename, and format"""
        tags = []
        
        # Format-based tags
        format_tags = {
            'text/csv': ['csv', 'data', 'table'],
            'text/html': ['html', 'web'],
            'text/xml': ['xml', 'structured'],
            'text/markdown': ['markdown', 'documentation'],
            'text/rtf': ['rtf', 'formatted']
        }
        tags.extend(format_tags.get(mime_type, ['text']))
        
        # Filename-based tags
        filename_clean = filename.replace('_', ' ').replace('-', ' ')
        filename_words = [word.lower() for word in filename_clean.split() if len(word) > 2]
        tags.extend(filename_words[:3])
        
        # Content-based tags
        if content:
            content_tags = self._extract_keywords(content, max_keywords=8)
            tags.extend(content_tags)
        
        return list(set(tags))[:15]
    
    def get_supported_mime_types(self) -> List[str]:
        """Get list of supported MIME types"""
        return self.supported_types.copy()