#!/usr/bin/env python3
"""
Build script for iHelper.tech
Following Windsurf rules for build configuration
"""
import os
import shutil
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def clean_directory(directory):
    """Clean a directory if it exists"""
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)

def copy_with_validation(src, dest, config):
    """Copy files with validation according to rules"""
    if not src.exists():
        return

    # Skip files that match ignore patterns
    for pattern in config.get('ignore', {}).get('patterns', []):
        if src.match(pattern):
            return

    # Check file size
    if src.is_file():
        size = src.stat().st_size
        max_size = int(str(config.get('security', {}).get('max_file_size', 5000000)).strip())
        if size > max_size:
            print(f"Warning: {src} exceeds maximum file size")
            return

    # Copy the file or directory
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dest)

def parse_value(value):
    """Parse a string value from the rules file"""
    value = value.strip()
    
    # Handle booleans
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    
    # Handle integers
    if value.replace(',', '').isdigit():
        return int(value.replace(',', ''))
    
    # Handle lists
    if value.startswith('[') and value.endswith(']'):
        try:
            # Remove comments from the list items
            clean_value = '[' + ','.join(item.split('#')[0].strip() for item in value[1:-1].split(',')) + ']'
            return json.loads(clean_value)
        except json.JSONDecodeError:
            pass
    
    # Handle strings (remove quotes and comments)
    if '#' in value:
        value = value.split('#')[0].strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value

def main():
    """Main build function"""
    # Load build config
    with open('build_config.json', 'r', encoding='utf-8') as f:
        build_config = json.load(f)

    # Load Windsurf rules
    rules = {}
    with open('.windsurfrules', 'r', encoding='utf-8') as f:
        current_section = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                rules[current_section] = {}
            elif '=' in line and current_section:
                key, value = [x.strip() for x in line.split('=', 1)]
                if '#' in value:  # Handle inline comments
                    value = value.split('#')[0].strip()
                rules[current_section][key] = parse_value(value)

    # Create clean build directory
    build_dir = Path(build_config['build']['output_dir'])
    if rules.get('build', {}).get('clean_build', True):
        clean_directory(build_dir)
    else:
        build_dir.mkdir(exist_ok=True)

    # Set up thread pool for parallel processing
    max_workers = int(str(rules.get('build', {}).get('max_workers', 4)).strip())
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        # Copy static files
        static_dir = Path(build_config['build']['static_dir'])
        if static_dir.exists():
            futures.append(
                executor.submit(
                    copy_with_validation,
                    static_dir,
                    build_dir / 'static',
                    rules
                )
            )

        # Copy content
        content_dir = Path(build_config['build']['content_dir'])
        if content_dir.exists():
            futures.append(
                executor.submit(
                    copy_with_validation,
                    content_dir,
                    build_dir / 'content',
                    rules
                )
            )

        # Copy index.html
        if Path('index.html').exists():
            futures.append(
                executor.submit(
                    copy_with_validation,
                    Path('index.html'),
                    build_dir / 'index.html',
                    rules
                )
            )

        # Wait for all tasks to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error during build: {e}")
                return 1

    print("Build completed successfully!")
    return 0

if __name__ == '__main__':
    exit(main())
