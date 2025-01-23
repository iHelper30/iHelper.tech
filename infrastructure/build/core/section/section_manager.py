#!/usr/bin/env python3
"""
Section Manager - Tool for managing iHelper.tech knowledge library sections
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class SectionManager:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.templates_dir = self.root_path / 'templates'
        self.base_template = self.templates_dir / 'base.html'
        self.config_template = self.templates_dir / 'section_config.json'
        
    def create_section(self, section_id: str, title: str, description: str) -> None:
        """Create a new section with basic structure"""
        section_dir = self.root_path / section_id
        if section_dir.exists():
            raise ValueError(f"Section {section_id} already exists")
            
        # Create directory structure
        section_dir.mkdir(parents=True)
        (section_dir / 'images').mkdir()
        
        # Copy and customize section config
        config = self._load_config_template()
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
        
        with open(section_dir / 'section_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
            
        # Create basic README.md
        readme_content = f"""# {title}

## Overview 🎯

{description}

## Key Features 💡

- Feature 1
- Feature 2
- Feature 3

## Content Structure 📋

- Section 1
- Section 2
- Section 3

## Usage Instructions 🔍

1. Step 1
2. Step 2
3. Step 3
"""
        with open(section_dir / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
            
        # Create SEO.md
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
        with open(section_dir / 'SEO.md', 'w', encoding='utf-8') as f:
            f.write(seo_content)
            
    def update_section(self, section_id: str, **kwargs) -> None:
        """Update an existing section's configuration"""
        section_dir = self.root_path / section_id
        if not section_dir.exists():
            raise ValueError(f"Section {section_id} does not exist")
            
        config_path = section_dir / 'section_config.json'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Update metadata
        if 'title' in kwargs:
            config['template']['slots']['meta']['title'] = kwargs['title']
        if 'description' in kwargs:
            config['template']['slots']['meta']['description'] = kwargs['description']
            
        config['metadata']['modified'] = datetime.utcnow().isoformat()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
            
    def validate_section(self, section_id: str) -> List[str]:
        """Validate a section's structure and content"""
        section_dir = self.root_path / section_id
        if not section_dir.exists():
            return [f"Section {section_id} does not exist"]
            
        errors = []
        
        # Check required files
        required_files = ['README.md', 'SEO.md', 'section_config.json']
        for file in required_files:
            if not (section_dir / file).exists():
                errors.append(f"Missing required file: {file}")
                
        # Validate config
        try:
            with open(section_dir / 'section_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Basic config validation
            required_keys = ['version', 'template', 'metadata']
            for key in required_keys:
                if key not in config:
                    errors.append(f"Missing required config key: {key}")
        except Exception as e:
            errors.append(f"Error reading config: {str(e)}")
            
        return errors
        
    def _load_config_template(self) -> Dict:
        """Load the base configuration template"""
        with open(self.config_template, 'r', encoding='utf-8') as f:
            return json.load(f)
            
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage iHelper.tech knowledge library sections')
    parser.add_argument('action', choices=['create', 'update', 'validate'])
    parser.add_argument('section_id', help='Section ID (e.g., 01_Welcome_Message)')
    parser.add_argument('--title', help='Section title')
    parser.add_argument('--description', help='Section description')
    
    args = parser.parse_args()
    
    manager = SectionManager('C:/Users/ihelp/Knowledge_Library/iHelper.tech')
    
    if args.action == 'create':
        if not args.title or not args.description:
            parser.error('create requires --title and --description')
        manager.create_section(args.section_id, args.title, args.description)
    elif args.action == 'update':
        kwargs = {}
        if args.title:
            kwargs['title'] = args.title
        if args.description:
            kwargs['description'] = args.description
        manager.update_section(args.section_id, **kwargs)
    elif args.action == 'validate':
        errors = manager.validate_section(args.section_id)
        if errors:
            print('Validation errors:')
            for error in errors:
                print(f'- {error}')
        else:
            print('Section is valid')
