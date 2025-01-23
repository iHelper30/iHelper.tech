from typing import Dict, List, Optional, Protocol, Any
from pathlib import Path
import os
import html5lib
from bs4 import BeautifulSoup
from dataclasses import dataclass
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationError:
    """Structured validation error reporting"""
    error_type: str
    message: str
    line_number: Optional[int]
    element: Optional[str]
    severity: str
    timestamp: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        return {
            'type': self.error_type,
            'message': self.message,
            'line_number': self.line_number,
            'element': self.element,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat()
        }

class HTMLValidatorProtocol(Protocol):
    """Protocol defining the interface for HTML validators"""
    def validate_html_structure(self, content: str) -> bool: ...
    def check_required_elements(self, soup: BeautifulSoup) -> None: ...
    def validate_template(self, file_path: str) -> bool: ...
    def validate_all_templates(self) -> Dict[str, bool]: ...

class TemplateValidator:
    """HTML template validator with enhanced error reporting and type safety"""
    
    def __init__(self, root_path: str) -> None:
        """Initialize the template validator
        
        Args:
            root_path: Root directory containing templates
        """
        self.root_path = Path(root_path)
        self.errors: List[ValidationError] = []
        self.required_elements = {
            'title': 'title tag',
            'meta_description': 'meta description',
            'main_content': 'main tag',
            'header': 'header tag',
            'footer': 'footer tag'
        }
        
    def validate_html_structure(self, content: str) -> bool:
        """Validate HTML5 structure
        
        Args:
            content: HTML content to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            parser = html5lib.HTMLParser(strict=True)
            parser.parse(content)
            return True
        except Exception as e:
            self.errors.append(ValidationError(
                error_type='structure',
                message=str(e),
                line_number=None,
                element=None,
                severity='error'
            ))
            logger.error(f'HTML Structure Error: {str(e)}')
            return False

    def check_required_elements(self, soup: BeautifulSoup) -> None:
        """Check for required HTML elements
        
        Args:
            soup: BeautifulSoup object of the HTML content
        """
        for element_id, description in self.required_elements.items():
            element = None
            if element_id == 'meta_description':
                element = soup.find('meta', attrs={'name': 'description'})
            else:
                element = soup.find(element_id)
                
            if not element:
                self.errors.append(ValidationError(
                    error_type='missing_element',
                    message=f'Missing required element: {description}',
                    line_number=None,
                    element=element_id,
                    severity='error'
                ))
                logger.warning(f'Missing required element: {description}')

    def check_accessibility(self, soup: BeautifulSoup) -> None:
        """Validate accessibility requirements
        
        Args:
            soup: BeautifulSoup object of the HTML content
        """
        # Check for img alt attributes
        for img in soup.find_all('img'):
            if not img.get('alt'):
                self.errors.append(ValidationError(
                    error_type='accessibility',
                    message='Image missing alt attribute',
                    line_number=None,
                    element=str(img),
                    severity='warning'
                ))
        
        # Check for proper heading hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        prev_level = 0
        for heading in headings:
            current_level = int(heading.name[1])
            if current_level > prev_level + 1:
                self.errors.append(ValidationError(
                    error_type='accessibility',
                    message=f'Incorrect heading hierarchy: h{prev_level} to h{current_level}',
                    line_number=None,
                    element=str(heading),
                    severity='warning'
                ))
            prev_level = current_level

    def validate_template(self, file_path: str) -> bool:
        """Comprehensive template validation
        
        Args:
            file_path: Path to the template file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            self.errors = []  # Reset errors for new validation
            
            if not self.validate_html_structure(html_content):
                return False
                
            soup = BeautifulSoup(html_content, 'html.parser')
            self.check_required_elements(soup)
            self.check_accessibility(soup)
            
            return len([e for e in self.errors if e.severity == 'error']) == 0
            
        except Exception as e:
            self.errors.append(ValidationError(
                error_type='system',
                message=f'Error processing file: {str(e)}',
                line_number=None,
                element=None,
                severity='error'
            ))
            logger.error(f'Error processing file {file_path}: {str(e)}')
            return False

    def validate_all_templates(self) -> Dict[str, bool]:
        """Validate all index.html files in the directory structure
        
        Returns:
            Dict[str, bool]: Mapping of template paths to validation results
        """
        results: Dict[str, bool] = {}
        valid_templates = 0
        total_templates = 0
        
        for folder in os.listdir(self.root_path):
            folder_path = self.root_path / folder
            if folder_path.is_dir():
                template_path = folder_path / 'index.html'
                if template_path.exists():
                    total_templates += 1
                    is_valid = self.validate_template(str(template_path))
                    results[str(template_path)] = is_valid
                    if is_valid:
                        valid_templates += 1
                        
        logger.info(f'Validated {total_templates} templates. '
                   f'{valid_templates} valid, '
                   f'{total_templates - valid_templates} invalid.')
        return results

    def get_error_report(self) -> List[Dict[str, Any]]:
        """Get a detailed report of all validation errors
        
        Returns:
            List[Dict[str, Any]]: List of error dictionaries
        """
        return [error.to_dict() for error in self.errors]

def main() -> None:
    """Main function for command-line execution"""
    import sys
    if len(sys.argv) != 2:
        print("Usage: python template_validator.py <root_path>")
        sys.exit(1)
        
    validator = TemplateValidator(sys.argv[1])
    results = validator.validate_all_templates()
    
    # Print results
    for template_path, is_valid in results.items():
        print(f"{template_path}: {'Valid' if is_valid else 'Invalid'}")
        
    if validator.errors:
        print("\nValidation Errors:")
        for error in validator.errors:
            error_dict = error.to_dict()
            print(f"- {error_dict['type']}: {error_dict['message']}")
            if error_dict['line_number']:
                print(f"  Line: {error_dict['line_number']}")
            if error_dict['element']:
                print(f"  Element: {error_dict['element']}")

if __name__ == '__main__':
    main()