#!/bin/bash

# GitHub Repository Creation Script
# This script creates and initializes a GitHub repository for iHelper.tech

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: Git is not installed"
    exit 1
fi

# Initialize repository if not already initialized
if [ ! -d ".git" ]; then
    git init
    if [ $? -ne 0 ]; then
        echo "Failed to initialize git repository"
        exit 1
    fi
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.env
venv/
ENV/
.venv
.idea/
.vscode/
*.bak
EOL
fi

# Add all files
git add .

# Initial commit if no commits exist
if ! git rev-parse --verify HEAD &> /dev/null; then
    git commit -m "Initial commit: Knowledge Library System"
fi

# Check if remote origin exists
if ! git remote | grep -q "origin"; then
    # Prompt for GitHub repository URL
    echo "Enter your GitHub repository URL (e.g., https://github.com/username/repo.git):"
    read REPO_URL
    
    # Add remote origin
    git remote add origin "$REPO_URL"
    if [ $? -ne 0 ]; then
        echo "Failed to add remote origin"
        exit 1
    fi
fi

# Push to GitHub
if ! git push -u origin main; then
    # Try pushing to master if main fails
    if ! git push -u origin master; then
        echo "Failed to push to repository"
        echo "Please ensure you have the correct permissions and the repository exists"
        exit 1
    fi
fi

echo "Repository successfully created and pushed to GitHub"
echo "Don't forget to:"
echo "1. Update repository settings on GitHub"
echo "2. Add collaborators if needed"
echo "3. Enable GitHub Pages if you plan to use it"
echo "4. Set up branch protection rules if desired"
