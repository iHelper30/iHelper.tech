#!/usr/bin/env python3
"""
Build System for iHelper.tech Knowledge Library
"""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import re
from datetime import datetime
import markdown2
import jinja2
from PIL import Image

from .core.content import ContentProcessor
from .core.metadata import MetadataManager
from .core.section import SectionManager
from .core.template import TemplateGenerator, TemplateValidator
from .core.utils import validate_links, check_html_links

# Optional imports
try:
    import csscompressor
    HAS_CSSCOMPRESSOR = True
except ImportError:
    HAS_CSSCOMPRESSOR = False
    
try:
    import htmlmin
    HAS_HTMLMIN = True
except ImportError:
    HAS_HTMLMIN = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('build.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BuildError(Exception):
    """Base class for build errors"""
    pass

class Builder:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.config = self._load_config()
        self.build_dir = self.root_path / self.config['build']['output_dir']
        self.static_dir = self.root_path / self.config['build']['static_dir']
        self.templates_dir = self.root_path / self.config['build']['templates_dir']
        
        # Set up Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Initialize components
        self.content_processor = ContentProcessor(self.config)
        self.metadata_manager = MetadataManager(self.config)
        self.section_manager = SectionManager(self.config)
        self.template_generator = TemplateGenerator(self.config)
        self.template_validator = TemplateValidator(self.config)
        
        self.max_workers = self.config["build"].get("max_workers", 4)
    
    def _load_config(self) -> Dict:
        """Load build configuration"""
        config_path = self.root_path / 'build_config.json'
        if not config_path.exists():
            raise BuildError("build_config.json not found")
        return json.loads(config_path.read_text(encoding='utf-8'))
        
    def clean_build_dir(self) -> None:
        """Clean the build directory"""
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        self.build_dir.mkdir(parents=True)
        
    def copy_static_assets(self) -> None:
        """Copy and optimize static assets"""
        static_build_dir = self.build_dir / 'static'
        static_build_dir.mkdir(exist_ok=True)
        
        # Copy CSS files
        css_dir = static_build_dir / 'css'
        css_dir.mkdir(exist_ok=True)
        for css_file in self.config['build']['assets']['css']:
            src = self.static_dir / 'css' / css_file
            dst = css_dir / css_file
            if src.exists():
                if self.config['build']['assets']['optimize'] and HAS_CSSCOMPRESSOR:
                    css_content = src.read_text(encoding='utf-8')
                    minified = csscompressor.compress(css_content)
                    dst.write_text(minified, encoding='utf-8')
                else:
                    shutil.copy2(src, dst)
                    
        # Copy JS files
        js_dir = static_build_dir / 'js'
        js_dir.mkdir(exist_ok=True)
        for js_file in self.config['build']['assets']['js']:
            src = self.static_dir / 'js' / js_file
            dst = js_dir / js_file
            if src.exists():
                shutil.copy2(src, dst)
                
    def process_section(self, section_dir: Path) -> None:
        """Process a single section"""
        try:
            # Load section config
            config_path = section_dir / 'section_config.json'
            if not config_path.exists():
                logger.error(f"No config found for {section_dir.name}")
                return
                
            with open(config_path, 'r', encoding='utf-8') as f:
                section_config = json.load(f)
                
            # Create section build directory
            build_section_dir = self.build_dir / section_dir.name
            build_section_dir.mkdir(exist_ok=True)
            
            # Process README.md
            readme_path = section_dir / 'README.md'
            if readme_path.exists():
                content = readme_path.read_text(encoding='utf-8')
                html_content = markdown2.markdown(
                    content,
                    extras=['metadata', 'tables', 'fenced-code-blocks']
                )
            else:
                html_content = "<p>Content coming soon.</p>"
                
            # Load template
            template = self.jinja_env.get_template('base.html')
            
            # Prepare template variables
            template_vars = {
                'meta': section_config['template']['slots']['meta'],
                'content': html_content,
                'navigation': self._generate_navigation(content),
                'resources': self._gather_resources(section_dir),
                'footer': {}  # Add footer content if needed
            }
            
            # Render template
            output = template.render(**template_vars)
            
            # Minify if configured
            if self.config['build']['content']['minify_html'] and HAS_HTMLMIN:
                output = htmlmin.minify(output)
                
            # Write output
            output_path = build_section_dir / 'index.html'
            output_path.write_text(output, encoding='utf-8')
            
            # Copy section assets
            self._copy_section_assets(section_dir, build_section_dir)
            
            logger.info(f"Successfully built section: {section_dir.name}")
            
        except Exception as e:
            logger.error(f"Error building section {section_dir.name}: {str(e)}")
            
    def _generate_navigation(self, content: str) -> str:
        """Generate navigation from content headers"""
        headers = re.findall(r'^(#{1,3})\s+(.+)$', content, re.MULTILINE)
        if not headers:
            return ""
            
        nav = ['<nav class="section-nav"><ul>']
        for hashes, title in headers:
            level = len(hashes)
            link = re.sub(r'[^\w\s-]', '', title.lower())
            link = re.sub(r'[-\s]+', '-', link).strip('-')
            indent = '  ' * (level - 1)
            nav.append(f'{indent}<li><a href="#{link}">{title}</a></li>')
        nav.append('</ul></nav>')
        return '\n'.join(nav)
        
    def _gather_resources(self, section_dir: Path) -> str:
        """Gather and format additional resources"""
        resources = []
        for pattern in ['*.md', '*.pdf', '*.ipynb']:
            for file in section_dir.glob(pattern):
                if file.name not in ['README.md', 'SEO.md']:
                    name = file.stem.replace('_', ' ').title()
                    link = file.name
                    resources.append(f'<li><a href="{link}">{name}</a></li>')
        
        if resources:
            return f"""
            <section class="additional-resources">
                <h2>Additional Resources</h2>
                <ul>
                    {''.join(resources)}
                </ul>
            </section>
            """
        return ""
        
    def _copy_section_assets(self, src_dir: Path, dst_dir: Path) -> None:
        """Copy section-specific assets"""
        # Copy images
        images_dir = src_dir / 'images'
        if images_dir.exists():
            dst_images = dst_dir / 'images'
            dst_images.mkdir(exist_ok=True)
            for img in images_dir.glob('*'):
                if img.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                    if self.config['build']['content']['optimize_images']:
                        self._optimize_image(img, dst_images / img.name)
                    else:
                        shutil.copy2(img, dst_images / img.name)
                        
    def _optimize_image(self, src: Path, dst: Path) -> None:
        """Optimize image for web"""
        try:
            with Image.open(src) as img:
                # Convert RGBA to RGB if needed
                if img.mode == 'RGBA':
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    img = bg
                
                # Optimize
                img.save(dst, optimize=True, quality=85)
        except Exception as e:
            logger.warning(f"Could not optimize image {src.name}: {str(e)}")
            shutil.copy2(src, dst)
            
    def build(self) -> None:
        """Build the entire site"""
        try:
            logger.info("Starting build process...")
            
            # Clean build directory
            self.clean_build_dir()
            
            # Copy static assets
            self.copy_static_assets()
            
            # Process all sections
            pattern = re.compile(r'^\d{2}_\w+')
            sections = [d for d in self.root_path.iterdir() 
                       if d.is_dir() and pattern.match(d.name)]
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                executor.map(self.process_section, sections)
                
            logger.info("Build completed successfully")
            
        except Exception as e:
            logger.error(f"Build failed: {str(e)}")
            raise BuildError(f"Build failed: {str(e)}")
            
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Build iHelper.tech knowledge library')
    parser.add_argument('--clean', action='store_true',
                       help='Clean build directory before building')
    
    args = parser.parse_args()
    
    builder = Builder('C:/Users/ihelp/Knowledge_Library/iHelper.tech')
    builder.build()
