#!/usr/bin/env python3
"""
Metadata Manager - Tool for incrementally updating library_metadata.json
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetadataManager:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.metadata_path = self.root_path / 'library_metadata.json'
        self.backup_dir = self.root_path / 'backups' / 'metadata'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def backup_metadata(self) -> Path:
        """Create a backup of the current metadata file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f'library_metadata_{timestamp}.json'
        if self.metadata_path.exists():
            shutil.copy2(self.metadata_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        return backup_path
        
    def load_metadata(self) -> Dict:
        """Load current metadata, creating if doesn't exist"""
        if self.metadata_path.exists():
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "1.0.0",
            "lastUpdated": datetime.utcnow().isoformat(),
            "entries": []
        }
        
    def save_metadata(self, metadata: Dict) -> None:
        """Save metadata with proper formatting"""
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
        logger.info("Metadata saved successfully")
        
    def update_section_metadata(self, section_id: str) -> bool:
        """Update metadata for a single section"""
        section_dir = self.root_path / section_id
        if not section_dir.exists():
            logger.error(f"Section directory not found: {section_id}")
            return False
            
        config_path = section_dir / 'section_config.json'
        if not config_path.exists():
            logger.error(f"Section config not found: {section_id}")
            return False
            
        try:
            # Load current metadata
            metadata = self.load_metadata()
            
            # Load section config
            with open(config_path, 'r', encoding='utf-8') as f:
                section_config = json.load(f)
                
            # Create or update entry
            entry = {
                "id": section_id,
                "title": section_config['template']['slots']['meta']['title'],
                "path": section_id,
                "type": "document",
                "summary": section_config['template']['slots']['meta']['description'],
                "tags": section_config['template']['slots']['meta']['keywords'],
                "created": section_config['metadata']['created'],
                "modified": section_config['metadata']['modified'],
                "author": section_config['metadata']['author']
            }
            
            # Update or add entry
            entry_index = next((i for i, e in enumerate(metadata['entries']) 
                              if e['id'] == section_id), None)
            if entry_index is not None:
                metadata['entries'][entry_index] = entry
            else:
                metadata['entries'].append(entry)
                
            # Update last modified
            metadata['lastUpdated'] = datetime.utcnow().isoformat()
            
            # Save changes
            self.save_metadata(metadata)
            logger.info(f"Updated metadata for section: {section_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating metadata for {section_id}: {str(e)}")
            return False
            
    def migrate_section(self, section_id: str) -> bool:
        """Migrate a section to the new structure and update metadata"""
        section_dir = self.root_path / section_id
        if not section_dir.exists():
            logger.error(f"Section directory not found: {section_id}")
            return False
            
        try:
            # Read README.md for content
            readme_path = section_dir / 'README.md'
            if not readme_path.exists():
                logger.error(f"README.md not found in {section_id}")
                return False
                
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract title and description
            import re
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            desc_match = re.search(r'^##\s+Overview.+?\n(.+?)(?=\n\n|\n##|$)', 
                                 content, re.MULTILINE | re.DOTALL)
                                 
            title = title_match.group(1) if title_match else section_id
            description = desc_match.group(1).strip() if desc_match else ""
            
            # Create section config if it doesn't exist
            config_path = section_dir / 'section_config.json'
            if not config_path.exists():
                # Load template config
                template_config_path = self.root_path / 'templates' / 'section_config.json'
                with open(template_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # Update config with section info
                config['metadata'].update({
                    'section_id': section_id,
                    'created': datetime.utcnow().isoformat(),
                    'modified': datetime.utcnow().isoformat()
                })
                config['template']['slots']['meta'].update({
                    'title': title,
                    'description': description,
                    'keywords': title.lower().split(),
                    'subtitle': f"Essential Resources for {title}",
                    'breadcrumb': title
                })
                
                # Save config
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                    
            # Create SEO.md if it doesn't exist
            seo_path = section_dir / 'SEO.md'
            if not seo_path.exists():
                seo_content = f"""# SEO Information for {title}

## Meta Description
{description}

## Keywords
{', '.join(title.lower().split())}

## Target Audience
- Audience 1
- Audience 2

## Search Intent
- Intent 1
- Intent 2
"""
                with open(seo_path, 'w', encoding='utf-8') as f:
                    f.write(seo_content)
                    
            # Update metadata
            self.update_section_metadata(section_id)
            
            logger.info(f"Successfully migrated section: {section_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating section {section_id}: {str(e)}")
            return False
            
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage iHelper.tech library metadata')
    parser.add_argument('action', choices=['update', 'migrate'])
    parser.add_argument('section_id', help='Section ID to process')
    
    args = parser.parse_args()
    
    manager = MetadataManager('C:/Users/ihelp/Knowledge_Library/iHelper.tech')
    
    if args.action == 'update':
        success = manager.update_section_metadata(args.section_id)
        if not success:
            parser.exit(1, 'Failed to update metadata\n')
    elif args.action == 'migrate':
        success = manager.migrate_section(args.section_id)
        if not success:
            parser.exit(1, 'Failed to migrate section\n')
