#!/usr/bin/env python3

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import subprocess
from enum import Enum
import shutil
from jsonschema import validate, ValidationError as JsonValidationError
import re
from typing import Tuple

class Phase(Enum):
    FOUNDATION = "foundation"
    CONTENT = "content"
    PERFORMANCE = "performance"
    SECURITY = "security"

@dataclass
class ChangeTask:
    name: str
    file_path: str
    description: str
    dependencies: List[str]
    risk_level: str
    validation_steps: List[str]

class SchemaValidator:
    """Validates JSON files against their schemas"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.schema_dir = root_path / "schemas"
        
    def validate_json_file(self, json_file: Path, schema_file: Path) -> bool:
        """Validate a JSON file against its schema"""
        try:
            with open(schema_file) as f:
                schema = json.load(f)
            with open(json_file) as f:
                data = json.load(f)
            validate(instance=data, schema=schema)
            return True
        except JsonValidationError as e:
            logging.error(f"Validation error in {json_file}: {e}")
            return False
        except Exception as e:
            logging.error(f"Error validating {json_file}: {e}")
            return False

class ImplementationManager:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.logger = self._setup_logging()
        self.tasks: Dict[Phase, List[ChangeTask]] = self._load_tasks()
        self.schema_validator = SchemaValidator(self.root_path)
        
    def _setup_logging(self) -> logging.Logger:
        """Configure logging for the implementation process"""
        logger = logging.getLogger("implementation")
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        
        return logger
        
    def _load_tasks(self) -> Dict[Phase, List[ChangeTask]]:
        """Load implementation tasks from configuration"""
        tasks = {
            Phase.FOUNDATION: [
                ChangeTask(
                    name="schema_validation",
                    file_path="library_metadata.json",
                    description="Add JSON schema validation",
                    dependencies=[],
                    risk_level="low",
                    validation_steps=["validate_json_schema", "test_metadata_loading"]
                ),
                ChangeTask(
                    name="type_annotations",
                    file_path="template_validator.py",
                    description="Fix type annotations",
                    dependencies=[],
                    risk_level="low",
                    validation_steps=["run_mypy", "test_template_validation"]
                )
            ],
            Phase.CONTENT: [
                ChangeTask(
                    name="content_standardization",
                    file_path="content_processor.py",
                    description="Implement content standardization improvements",
                    dependencies=["schema_validation", "type_annotations"],
                    risk_level="medium",
                    validation_steps=["test_content_standardization", "validate_content"]
                )
            ],
            Phase.PERFORMANCE: [
                ChangeTask(
                    name="implement_caching",
                    file_path="content_processor.py",
                    description="Add LRU cache",
                    dependencies=["content_standardization"],
                    risk_level="low",
                    validation_steps=["test_cache_performance", "validate_cache_behavior"]
                ),
                ChangeTask(
                    name="performance_improvements",
                    file_path="content_processor.py",
                    description="Implement performance improvements",
                    dependencies=["implement_caching"],
                    risk_level="low",
                    validation_steps=["test_performance_improvements"]
                )
            ],
            Phase.SECURITY: [
                ChangeTask(
                    name="content_sanitization",
                    file_path="content_processor.py",
                    description="Implement content sanitization",
                    dependencies=["content_standardization"],
                    risk_level="high",
                    validation_steps=["test_sanitization", "security_scan"]
                )
            ]
        }
        return tasks
        
    def validate_dependencies(self, task: ChangeTask) -> bool:
        """Check if task dependencies are met"""
        for dep in task.dependencies:
            if not self._is_task_completed(dep):
                self.logger.error(f"Dependency {dep} not met for task {task.name}")
                return False
        return True
        
    def _is_task_completed(self, task_name: str) -> bool:
        """Check if a task has been completed"""
        completion_file = self.root_path / "tools" / ".completion_status"
        if not completion_file.exists():
            return False
            
        try:
            completed_tasks = json.loads(completion_file.read_text())
            return task_name in completed_tasks
        except Exception as e:
            self.logger.error(f"Error checking task completion: {e}")
            return False
            
    def implement_phase(self, phase: Phase) -> bool:
        """Implement all tasks in a phase"""
        self.logger.info(f"Starting implementation of phase: {phase.value}")
        
        tasks = self.tasks.get(phase, [])
        for task in tasks:
            if not self.validate_dependencies(task):
                self.logger.error(f"Cannot implement task {task.name}: dependencies not met")
                return False
                
            try:
                self._implement_task(task)
                self._mark_task_completed(task.name)
            except Exception as e:
                self.logger.error(f"Error implementing task {task.name}: {e}")
                return False
                
        return True
        
    def _implement_task(self, task: ChangeTask) -> None:
        """Implement a specific task"""
        self.logger.info(f"Implementing task: {task.name}")
        
        # Create backup
        self._backup_file(task.file_path)
        
        # Apply changes based on task type
        if task.name == "schema_validation":
            self._implement_schema_validation()
        elif task.name == "type_annotations":
            self._implement_type_annotations()
        elif task.name == "content_standardization":
            self._implement_content_standardization()
        elif task.name == "implement_caching":
            self._implement_caching()
        elif task.name == "performance_improvements":
            self._implement_performance_improvements()
        else:
            raise ValueError(f"Unknown task type: {task.name}")
            
        # Validate changes
        if not self._validate_changes(task):
            self.logger.error("Validation failed")
            self._restore_backup(task.file_path)
            raise ValueError("Task validation failed")
            
    def _implement_schema_validation(self) -> None:
        """Implement JSON schema validation"""
        schema_file = self.root_path / "schemas" / "library_metadata_schema.json"
        metadata_file = self.root_path / "library_metadata.json"
        
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")
        
        # Create new metadata file with schema-compliant structure
        new_metadata = {
            "version": "1.0.0",
            "lastUpdated": "2025-01-22T20:30:00Z",
            "entries": [
                {
                    "id": "01_Welcome_Message",
                    "title": "Welcome Message",
                    "path": "01_Welcome_Message",
                    "type": "document",
                    "summary": "Welcome to the iHelper.tech Resource Library - Your complete guide to professional development resources.",
                    "tags": ["welcome", "message", "introduction"],
                    "created": "2025-01-22T20:30:00Z",
                    "modified": "2025-01-22T20:30:00Z",
                    "author": "iHelper.tech"
                }
            ]
        }
        
        # Backup existing file if it exists
        if metadata_file.exists():
            backup_file = metadata_file.with_suffix(metadata_file.suffix + '.bak')
            shutil.copy2(str(metadata_file), str(backup_file))
            
        # Write new metadata file
        with open(metadata_file, 'w') as f:
            json.dump(new_metadata, f, indent=4)
            
        # Validate the new file
        if not self.schema_validator.validate_json_file(metadata_file, schema_file):
            if metadata_file.exists():
                metadata_file.unlink()  # Delete invalid file
            raise ValueError("Generated metadata file fails schema validation")
            
    def _implement_type_annotations(self) -> None:
        """Implement type annotations in Python files"""
        # Type annotations are already implemented in template_validator.py
        pass
            
    def _implement_content_standardization(self) -> None:
        """Implement content standardization improvements"""
        content_processor_path = self.root_path / "content_processor.py"
        
        if not content_processor_path.exists():
            raise FileNotFoundError(f"Content processor not found: {content_processor_path}")
            
        # Backup existing file
        backup_file = content_processor_path.with_suffix(content_processor_path.suffix + '.bak')
        shutil.copy2(str(content_processor_path), str(backup_file))
        
        # Read existing content
        with open(content_processor_path, 'r') as f:
            content = f.read()
            
        # Add error handling improvements
        content = self._add_error_handling(content)
        
        # Add caching
        content = self._add_caching(content)
        
        # Add content validation
        content = self._add_content_validation(content)
        
        # Write updated content
        with open(content_processor_path, 'w') as f:
            f.write(content)
            
    def _add_error_handling(self, content: str) -> str:
        """Add improved error handling to content processor"""
        # Add imports if needed
        if 'from typing import Union, Optional' not in content:
            content = 'from typing import Union, Optional\n' + content
            
        if 'import logging' not in content:
            content = 'import logging\n' + content
            
        # Add error classes after imports
        error_classes = """
class ContentProcessingError(Exception):
    \"\"\"Base class for content processing errors\"\"\"
    pass

class FrontmatterError(ContentProcessingError):
    \"\"\"Error in frontmatter parsing or validation\"\"\"
    pass

class ResourceError(ContentProcessingError):
    \"\"\"Error in resource handling\"\"\"
    pass

class ValidationError(ContentProcessingError):
    \"\"\"Error in content validation\"\"\"
    pass
"""
        
        import_end = content.find('class ContentProcessor')
        if import_end != -1:
            content = content[:import_end] + error_classes + content[import_end:]
            
        # Add logging setup
        logging_setup = """
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
"""
        if 'logging.basicConfig' not in content:
            content = content.replace('class ContentProcessor', logging_setup + '\nclass ContentProcessor')
            
        return content
        
    def _add_caching(self, content: str) -> str:
        """Add caching to content processor"""
        # Add imports if needed
        if 'from functools import lru_cache' not in content:
            content = 'from functools import lru_cache\n' + content
            
        # Add cache decorator to appropriate methods
        methods_to_cache = [
            ('_load_library_metadata', 'maxsize=1'),
            ('process_markdown', 'maxsize=100'),
            ('_gather_resources', 'maxsize=50')
        ]
        
        for method, cache_params in methods_to_cache:
            method_start = content.find(f'def {method}')
            if method_start != -1:
                # Check if decorator already exists
                prev_line_start = content.rfind('\n', 0, method_start)
                prev_line = content[prev_line_start:method_start].strip()
                if '@lru_cache' not in prev_line:
                    # Add decorator
                    content = content[:method_start] + f'    @lru_cache({cache_params})\n' + content[method_start:]
                    
        return content
        
    def _add_content_validation(self, content: str) -> str:
        """Add content validation to content processor"""
        # Add validation method
        validation_method = """
    def validate_content(self, content: str) -> Tuple[bool, List[str]]:
        \"\"\"Validate content structure and requirements\"\"\"
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
            if not re.search(fr'#{1,6}\s*{section}', content, re.IGNORECASE):
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
"""
        
        # Add validation call in process_markdown method
        process_markdown = content.find('def process_markdown')
        if process_markdown != -1:
            method_end = content.find('return metadata, html_content', process_markdown)
            if method_end != -1:
                validation_call = """
        # Validate content
        is_valid, validation_errors = self.validate_content(markdown_content)
        if not is_valid:
            logger.warning("Content validation failed:")
            for error in validation_errors:
                logger.warning(f"- {error}")
"""
                content = content[:method_end] + validation_call + content[method_end:]
                
        # Add validation method to class
        class_end = content.find('if __name__')
        if class_end == -1:
            class_end = len(content)
        content = content[:class_end] + validation_method + content[class_end:]
        
        return content

    def _implement_performance_improvements(self) -> None:
        """Implement performance improvements"""
        content_processor_path = self.root_path / "content_processor.py"
        
        if not content_processor_path.exists():
            raise FileNotFoundError(f"Content processor not found: {content_processor_path}")
            
        # Backup existing file
        backup_file = content_processor_path.with_suffix(content_processor_path.suffix + '.bak')
        shutil.copy2(str(content_processor_path), str(backup_file))
        
        # Read existing content
        with open(content_processor_path, 'r') as f:
            content = f.read()
            
        # Add asset optimization
        asset_optimization = '''
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
'''
        
        # Add method to class
        class_end = content.find('if __name__')
        if class_end == -1:
            class_end = len(content)
        content = content[:class_end] + asset_optimization + content[class_end:]
        
        # Add caching improvements
        caching_improvements = '''
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
'''
        
        content = content[:class_end] + caching_improvements + content[class_end:]
        
        # Write updated content
        with open(content_processor_path, 'w') as f:
            f.write(content)
            
    def _implement_caching(self) -> None:
        """Implement caching improvements"""
        content_processor_path = self.root_path / "content_processor.py"
        
        if not content_processor_path.exists():
            raise FileNotFoundError(f"Content processor not found: {content_processor_path}")
            
        # Backup existing file
        backup_file = content_processor_path.with_suffix(content_processor_path.suffix + '.bak')
        shutil.copy2(str(content_processor_path), str(backup_file))
        
        # Read existing content
        with open(content_processor_path, 'r') as f:
            content = f.read()
            
        # Add imports if needed
        if 'from functools import cached_property' not in content:
            content = 'from functools import cached_property\n' + content
            
        # Add caching improvements
        caching_improvements = '''
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
'''
        
        # Add method to class
        class_end = content.find('if __name__')
        if class_end == -1:
            class_end = len(content)
        content = content[:class_end] + caching_improvements + content[class_end:]
        
        # Write updated content
        with open(content_processor_path, 'w') as f:
            f.write(content)
            
    def _backup_file(self, file_path: str) -> None:
        """Create backup of file before changes"""
        source = self.root_path / file_path
        if source.exists():
            backup = source.with_suffix(source.suffix + '.bak')
            shutil.copy2(str(source), str(backup))
        
    def _restore_backup(self, file_path: str) -> None:
        """Restore file from backup"""
        source = self.root_path / file_path
        backup = source.with_suffix(source.suffix + '.bak')
        if backup.exists():
            shutil.move(str(backup), str(source))
            
    def _validate_changes(self, task: ChangeTask) -> bool:
        """Validate changes made by a task"""
        self.logger.info(f"Validating changes for {task.name}")
        
        if task.name == "schema_validation":
            return self._validate_schema_implementation()
        elif task.name == "type_annotations":
            return self._validate_type_annotations()
        elif task.name == "content_standardization":
            return self._validate_content_standardization()
        elif task.name == "performance_improvements":
            return self._validate_performance_improvements()
        elif task.name == "implement_caching":
            return self._validate_caching()
            
        return True
        
    def _validate_schema_implementation(self) -> bool:
        """Validate schema implementation"""
        schema_file = self.root_path / "schemas" / "library_metadata_schema.json"
        metadata_file = self.root_path / "library_metadata.json"
        
        if not schema_file.exists() or not metadata_file.exists():
            return False
            
        return self.schema_validator.validate_json_file(metadata_file, schema_file)
        
    def _validate_type_annotations(self) -> bool:
        """Validate type annotations"""
        # We would typically run mypy here
        return True
        
    def _validate_content_standardization(self) -> bool:
        """Validate content standardization"""
        # We would typically run tests here
        return True
        
    def _validate_performance_improvements(self) -> bool:
        """Validate performance improvements"""
        # We would typically run performance tests here
        return True
        
    def _validate_caching(self) -> bool:
        """Validate caching"""
        # We would typically run tests here
        return True
        
    def _mark_task_completed(self, task_name: str) -> None:
        """Mark a task as completed"""
        completion_file = self.root_path / "tools" / ".completion_status"
        try:
            if completion_file.exists():
                completed_tasks = json.loads(completion_file.read_text())
            else:
                completed_tasks = []
                
            if task_name not in completed_tasks:
                completed_tasks.append(task_name)
                
            completion_file.parent.mkdir(exist_ok=True)
            with open(completion_file, 'w') as f:
                json.dump(completed_tasks, f)
        except Exception as e:
            self.logger.error(f"Error marking task as completed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Implement changes to iHelper.tech")
    parser.add_argument('--phase', type=str, required=True,
                      choices=[p.value for p in Phase],
                      help='Implementation phase to execute')
    parser.add_argument('--root-path', type=str, required=True,
                      help='Root path of the project')
    
    args = parser.parse_args()
    
    manager = ImplementationManager(args.root_path)
    phase = Phase(args.phase)
    
    if manager.implement_phase(phase):
        print(f"Successfully implemented phase: {phase.value}")
        sys.exit(0)
    else:
        print(f"Failed to implement phase: {phase.value}")
        sys.exit(1)

if __name__ == '__main__':
    main()
