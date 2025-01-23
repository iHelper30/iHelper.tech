import unittest
from pathlib import Path
import json
import shutil
import tempfile
from content_processor import ContentProcessor

class TestContentProcessor(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for tests
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create test metadata
        self.metadata = {
            "version": "1.0.0",
            "lastUpdated": "2025-01-22T20:37:00Z",
            "entries": [
                {
                    "id": "test_doc",
                    "title": "Test Document",
                    "path": "test_doc",
                    "type": "document",
                    "summary": "Test document for validation",
                    "tags": ["test", "validation"],
                    "created": "2025-01-22T20:37:00Z",
                    "modified": "2025-01-22T20:37:00Z",
                    "author": "Test"
                }
            ]
        }
        
        # Write test metadata
        with open(self.test_dir / "library_metadata.json", "w") as f:
            json.dump(self.metadata, f)
            
        # Create test content directory
        self.content_dir = self.test_dir / "test_doc"
        self.content_dir.mkdir()
        
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_valid_content(self):
        # Create valid content
        content = """# Introduction
This is a test document.

# Content
This is the main content section.

# Summary
This is the summary."""
        
        readme_path = self.content_dir / "README.md"
        readme_path.write_text(content)
        
        processor = ContentProcessor(str(self.test_dir))
        is_valid, errors = processor.validate_content(content)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
    def test_invalid_content(self):
        # Create invalid content (missing sections)
        content = """# Test
This is just some text without proper sections."""
        
        readme_path = self.content_dir / "README.md"
        readme_path.write_text(content)
        
        processor = ContentProcessor(str(self.test_dir))
        is_valid, errors = processor.validate_content(content)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
    def test_broken_links(self):
        # Create content with broken link
        content = """# Introduction
This is a test document.

# Content
Here's a [broken link](nonexistent.md).

# Summary
This is the summary."""
        
        readme_path = self.content_dir / "README.md"
        readme_path.write_text(content)
        
        processor = ContentProcessor(str(self.test_dir))
        is_valid, errors = processor.validate_content(content)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("broken" in error.lower() for error in errors))
        
    def test_heading_hierarchy(self):
        # Create content with invalid heading hierarchy
        content = """# Introduction
This is a test document.

# Content
This is content.

### Invalid Jump
This heading skips a level.

# Summary
This is the summary."""
        
        readme_path = self.content_dir / "README.md"
        readme_path.write_text(content)
        
        processor = ContentProcessor(str(self.test_dir))
        is_valid, errors = processor.validate_content(content)
        
        self.assertFalse(is_valid)
        self.assertTrue(any("hierarchy" in error.lower() for error in errors))

if __name__ == '__main__':
    unittest.main()
