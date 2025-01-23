from functools import cached_property
from typing import Dict, Tuple, Optional, List, Any, Union
from pathlib import Path
import re
import json
import markdown2
import logging
from functools import lru_cache
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ContentProcessingError(Exception):
    """Base class for content processing errors"""
    pass

class FrontmatterError(ContentProcessingError):
    """Error in frontmatter parsing or validation"""
    pass

class ResourceError(ContentProcessingError):
    """Error in resource handling"""
    pass

class ValidationError(ContentProcessingError):
    """Error in content validation"""
    pass

class ContentProcessor:
    def __init__(self, root_path: Union[str, Path]):
        self.root_path = Path(root_path)
        self.library_metadata = self._load_library_metadata()
        
    @lru_cache(maxsize=1)
    def _load_library_metadata(self) -> Dict[str, Any]:
        """Load global library metadata"""
        metadata_file = self.root_path / 'library_metadata.json'
        if metadata_file.exists():
            return json.loads(metadata_file.read_text(encoding='utf-8'))
        return {}
        
    def parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Extract frontmatter and content from markdown"""
        frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        match = frontmatter_pattern.match(content)
        
        if match:
            try:
                frontmatter = json.loads(match.group(1))
                content = content[match.end():]
                return frontmatter, content
            except json.JSONDecodeError:
                pass
        
        return {}, content
        
    @lru_cache(maxsize=100)
    def process_markdown(self, folder_path: Path) -> Tuple[Dict, str]:
        """Process markdown file with frontmatter and additional resources"""
        readme_path = folder_path / 'README.md'
        if not readme_path.exists():
            return self._generate_default_metadata(folder_path), '<p>Content coming soon.</p>'
            
        content = readme_path.read_text(encoding='utf-8')
        metadata, markdown_content = self.parse_frontmatter(content)
        
        # Enhance metadata with library-wide information
        metadata = self._enhance_metadata(metadata, folder_path)
        
        # Process content
        markdown_content = self._process_content(markdown_content, folder_path)
        
        # Convert to HTML with extras
        html_content = markdown2.markdown(
            markdown_content,
            extras=[
                'metadata', 'tables', 'fenced-code-blocks', 
                'header-ids', 'footnotes', 'smarty-pants'
            ]
        )
        
        # Add additional resources section if available
        resources = self._gather_resources(folder_path)
        if resources:
            html_content += resources
            
        
        # Validate content
        is_valid, validation_errors = self.validate_content(markdown_content)
        if not is_valid:
            logger.warning("Content validation failed:")
            for error in validation_errors:
                logger.warning(f"- {error}")
        return metadata, html_content
        
    def _enhance_metadata(self, metadata: Dict, folder_path: Path) -> Dict:
        """Enhance metadata with additional information"""
        folder_name = folder_path.name
        section_id = folder_name.split('_')[0]
        
        # Get section metadata from library_metadata.json
        section_metadata = self.library_metadata.get(section_id, {})
        
        enhanced = {
            'title': metadata.get('title', folder_name.split('_', 1)[1].replace('_', ' ')),
            'subtitle': metadata.get('subtitle', section_metadata.get('subtitle', '')),
            'description': metadata.get('description', section_metadata.get('description', '')),
            'keywords': metadata.get('keywords', folder_name.lower().split('_')),
            'category': section_metadata.get('category', ''),
            'difficulty': section_metadata.get('difficulty', 'Beginner'),
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'section_id': section_id,
            'related_sections': section_metadata.get('related_sections', [])
        }
        
        return enhanced
        
    def _process_content(self, content: str, folder_path: Path) -> str:
        """Process markdown content with enhanced features"""
        # Fix internal links
        content = self._fix_internal_links(content)
        
        # Process custom directives
        content = self._process_directives(content, folder_path)
        
        return content
        
    def _fix_internal_links(self, content: str) -> str:
        """Convert relative markdown links to proper HTML paths"""
        def replace_link(match):
            link_text = match.group(1)
            link_path = match.group(2)
            
            if link_path.endswith('.md'):
                link_path = link_path[:-3] + '.html'
            return f'[{link_text}]({link_path})'
            
        pattern = r'\[(.*?)\]\((.*?\.md)\)'
        return re.sub(pattern, replace_link, content)
        
    def _process_directives(self, content: str, folder_path: Path) -> str:
        """Process custom markdown directives"""
        # Process code includes
        content = re.sub(
            r'@include\(code:(.*?)\)',
            lambda m: self._include_code(m.group(1), folder_path),
            content
        )
        
        # Process file references
        content = re.sub(
            r'@include\(file:(.*?)\)',
            lambda m: self._include_file(m.group(1), folder_path),
            content
        )
        
        return content
        
    def _include_code(self, filepath: str, base_path: Path) -> str:
        """Include code file with syntax highlighting"""
        try:
            file_path = (base_path / filepath).resolve()
            if file_path.exists() and file_path.is_relative_to(self.root_path):
                ext = file_path.suffix.lstrip('.')
                code = file_path.read_text(encoding='utf-8')
                return f'```{ext}\n{code}\n```'
        except Exception:
            pass
        return f'<!-- Failed to include code from {filepath} -->'
        
    def _include_file(self, filepath: str, base_path: Path) -> str:
        """Include general file content"""
        try:
            file_path = (base_path / filepath).resolve()
            if file_path.exists() and file_path.is_relative_to(self.root_path):
                content = file_path.read_text(encoding='utf-8')
                return content
        except Exception:
            pass
        return f'<!-- Failed to include file {filepath} -->'
        
    @lru_cache(maxsize=50)
    def _gather_resources(self, folder_path: Path) -> str:
        """Gather and format additional resources in the folder"""
        resources = []
        
        # Look for specific file types
        for ext in ['.pdf', '.docx', '.xlsx', '.pptx', '.zip']:
            files = list(folder_path.glob(f'*{ext}'))
            if files:
                resources.append(f'<h3>Additional {ext.upper()[1:]} Resources</h3>')
                resources.append('<ul>')
                for file in files:
                    resources.append(f'<li><a href="{file.name}">{file.stem}</a></li>')
                resources.append('</ul>')
        
        if resources:
            return '\n<section class="additional-resources">\n<h2>Additional Resources</h2>\n' + '\n'.join(resources) + '\n</section>'
        return ''
        
    def _generate_default_metadata(self, folder_path: Path) -> Dict:
        """Generate default metadata for folders without README"""
        folder_name = folder_path.name
        section_id = folder_name.split('_')[0]
        title = folder_name.split('_', 1)[1].replace('_', ' ')
        
        return {
            'title': title,
            'subtitle': f'Resources and guides for {title.lower()}',
            'description': f'Comprehensive information about {title.lower()}',
            'keywords': folder_name.lower().split('_'),
            'category': 'Resources',
            'difficulty': 'Beginner',
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'section_id': section_id
        }
        
    def generate_section_nav(self, content: str) -> str:
        """Generate section navigation from content headers"""
        headers = re.findall(r'<h([2-3])[^>]*>(.*?)</h\1>', content)
        if not headers:
            return ''
            
        nav = ['<nav class="section-nav"><ul>']
        for level, title in headers:
            indent = '  ' * (int(level) - 2)
            nav.append(f'{indent}<li><a href="#{title.lower().replace(" ", "-")}">{title}</a></li>')
        nav.append('</ul></nav>')
        
        return '\n'.join(nav)

    def process_folder(self, folder_name: str) -> Tuple[Dict, str]:
        """Process a knowledge block folder"""
        folder_path = self.root_path / folder_name
        metadata, content = self.process_markdown(folder_path)
        
        # Generate section navigation
        section_nav = self.generate_section_nav(content)
        
        # Add section navigation before main content
        if section_nav:
            content = f'{section_nav}\n{content}'
            
        return metadata, content

    def validate_content(self, content: str) -> Tuple[bool, List[str]]:
        """Validate content structure and requirements"""
        errors = []
        
        # Check for empty content
        if not content.strip():
            errors.append("Content is empty")
            return False, errors
            
        # Check for minimum content length
        if len(content) < 100:
            errors.append("Content is too short (minimum 100 characters)")
            
        # Check for required sections
        required_sections = ['Introduction', 'Content', 'Summary']
        for section in required_sections:
            if not re.search(r'#\s*' + re.escape(section), content, re.IGNORECASE):
                errors.append(f"Missing required section: {section}")
                
        # Check for broken internal links
        internal_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for text, link in internal_links:
            if link.startswith(('http://', 'https://')):
                continue
            link_path = self.root_path / link
            if not link_path.exists():
                errors.append(f"Broken internal link: {link}")
                
        # Check for proper heading hierarchy
        headings = re.findall(r'(#{1,6})\s*([^\n]+)', content)
        prev_level = 0
        for hashes, title in headings:
            current_level = len(hashes)
            if current_level > prev_level + 1:
                errors.append(f"Invalid heading hierarchy: {title}")
            prev_level = current_level
            
        return len(errors) == 0, errors

    @cached_property
    def markdown_extensions(self) -> List[str]:
        """Get markdown extensions with caching"""
        return [
            'metadata', 'tables', 'fenced-code-blocks',
            'header-ids', 'footnotes', 'smarty-pants'
        ]
        
    @lru_cache(maxsize=1000)
    def parse_markdown(self, content: str) -> str:
        """Parse markdown with caching"""
        return markdown2.markdown(content, extras=self.markdown_extensions)

    @cached_property
    def markdown_extensions(self) -> List[str]:
        """Get markdown extensions with caching"""
        return [
            'metadata', 'tables', 'fenced-code-blocks',
            'header-ids', 'footnotes', 'smarty-pants'
        ]
        
    @lru_cache(maxsize=1000)
    def parse_markdown(self, content: str) -> str:
        """Parse markdown with caching"""
        return markdown2.markdown(content, extras=self.markdown_extensions)

    def optimize_assets(self, folder_path: Path) -> None:
        """Optimize assets in the folder"""
        try:
            # Optimize images
            for img_path in folder_path.glob('*.{jpg,jpeg,png,gif}'):
                self._optimize_image(img_path)
                
            # Minify CSS and JS
            for css_path in folder_path.glob('*.css'):
                self._minify_css(css_path)
            for js_path in folder_path.glob('*.js'):
                self._minify_js(js_path)
                
        except Exception as e:
            logger.error(f"Error optimizing assets: {e}")
            
    def _optimize_image(self, img_path: Path) -> None:
        """Optimize image file size"""
        try:
            from PIL import Image
            
            with Image.open(img_path) as img:
                # Convert RGBA to RGB if alpha channel exists
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                    
                # Save with optimized settings
                img.save(img_path, optimize=True, quality=85)
                logger.info(f"Optimized image: {img_path}")
        except ImportError:
            logger.warning("Pillow not installed. Image optimization skipped.")
        except Exception as e:
            logger.error(f"Error optimizing image {img_path}: {e}")
            
    def _minify_css(self, css_path: Path) -> None:
        """Minify CSS file"""
        try:
            import csscompressor
            
            css_content = css_path.read_text()
            minified = csscompressor.compress(css_content)
            css_path.write_text(minified)
            logger.info(f"Minified CSS: {css_path}")
        except ImportError:
            logger.warning("csscompressor not installed. CSS minification skipped.")
        except Exception as e:
            logger.error(f"Error minifying CSS {css_path}: {e}")
            
    def _minify_js(self, js_path: Path) -> None:
        """Minify JavaScript file"""
        try:
            import rjsmin
            
            js_content = js_path.read_text()
            minified = rjsmin.jsmin(js_content)
            js_path.write_text(minified)
            logger.info(f"Minified JavaScript: {js_path}")
        except ImportError:
            logger.warning("rjsmin not installed. JavaScript minification skipped.")
        except Exception as e:
            logger.error(f"Error minifying JavaScript {js_path}: {e}")
