# File-Specific Standard Operating Procedures (SOPs)

## Python Files SOP

### content_processor.py

#### Purpose
Maintain and modify the core content processing logic.

#### Dependencies
- library_metadata.json
- markdown2
- BeautifulSoup4
- All README.md files

#### Modification Procedure
1. Pre-modification Checks
   ```python
   # Verify imports
   import markdown2
   from bs4 import BeautifulSoup
   from typing import Dict, Tuple, Optional
   ```

2. Code Changes
   - Maintain type hints
   - Use error handling template:
   ```python
   try:
       # New code here
   except Exception as e:
       logger.error(f"Error in content processing: {str(e)}")
       return default_value
   ```

3. Testing Requirements
   - Unit tests for new functions
   - Integration tests with markdown files
   - Performance testing for large files

### template_validator.py

#### Purpose
Maintain HTML template validation logic.

#### Dependencies
- html5lib
- BeautifulSoup4
- All template files

#### Modification Procedure
1. Validation Rule Updates
   ```python
   def add_validation_rule(self, rule_name: str, rule_func: Callable) -> None:
       self.validation_rules[rule_name] = rule_func
   ```

2. Error Reporting
   ```python
   def report_error(self, error_type: str, details: str, line_number: Optional[int] = None) -> None:
       self.errors.append({
           'type': error_type,
           'details': details,
           'line': line_number
       })
   ```

## JSON Files SOP

### library_metadata.json

#### Purpose
Maintain central configuration and metadata.

#### Dependencies
- content_processor.py
- navigation_generator.py
- All section folders

#### Modification Procedure
1. Schema Validation
   ```json
   {
     "type": "object",
     "properties": {
       "total_knowledge_blocks": {"type": "integer"},
       "categories": {
         "type": "object",
         "additionalProperties": {"type": "integer"}
       }
     },
     "required": ["total_knowledge_blocks", "categories"]
   }
   ```

2. Category Updates
   - Update navigation.json
   - Rebuild navigation structure
   - Update all affected README.md files

### navigation.json

#### Purpose
Define site navigation structure.

#### Modification Procedure
1. Structure Updates
   ```json
   {
     "main_nav": {
       "sections": [],
       "categories": {}
     }
   }
   ```

2. Validation Requirements
   - Check all referenced paths exist
   - Verify category hierarchy
   - Update breadcrumb trails

## HTML Files SOP

### index.html

#### Purpose
Serve as entry points for sections.

#### Dependencies
- template_validator.py
- navigation_generator.py
- CSS/JS assets

#### Modification Procedure
1. Required Elements
   ```html
   <!DOCTYPE html>
   <html lang="en">
   <head>
     <meta charset="UTF-8">
     <meta name="viewport" content="width=device-width, initial-scale=1.0">
     <meta name="description" content="[REQUIRED]">
     <title>[REQUIRED]</title>
   </head>
   ```

2. Accessibility Requirements
   - ARIA labels
   - Semantic HTML
   - Keyboard navigation

3. Performance Optimization
   ```html
   <link rel="preload" href="critical.css" as="style">
   <link rel="preconnect" href="https://cdn.example.com">
   ```

## Markdown Files SOP

### README.md

#### Purpose
Provide section documentation and content.

#### Dependencies
- content_processor.py
- template_generator.py

#### Modification Procedure
1. Frontmatter Template
   ```yaml
   ---
   {
     "title": "Required Title",
     "description": "Required Description",
     "category": "Required Category",
     "tags": ["tag1", "tag2"]
   }
   ---
   ```

2. Content Structure
   ```markdown
   # Main Title
   
   ## Overview
   [Required section overview]
   
   ## Content Sections
   1. [Required ordered sections]
   2. [With clear hierarchy]
   
   ## Additional Resources
   - [Optional related links]
   ```

3. Validation Requirements
   - Valid JSON in frontmatter
   - All links functional
   - Images have alt text
   - Proper heading hierarchy

## Asset Files SOP

### Static Assets (CSS/JS/Images)

#### Purpose
Manage static resources for the knowledge library.

#### Modification Procedure
1. Image Optimization
   - Convert to WebP format
   - Implement responsive images
   - Optimize for web delivery

2. CSS Updates
   ```css
   /* Required structure */
   :root {
     /* CSS variables */
   }
   
   /* Component-specific styles */
   .component-name {
     /* styles */
   }
   ```

3. JavaScript Updates
   ```javascript
   // Required module structure
   const ModuleName = (function() {
     'use strict';
     
     // Private variables
     
     // Public interface
     return {
       // Methods
     };
   })();
   ```

4. Performance Requirements
   - Minification
   - Compression
   - Cache headers
   - Resource hints
