# Deploy script for iHelper.tech
param(
    [string]$Environment = "staging"
)

Write-Host "Starting deployment process for iHelper.tech to $Environment environment..."

# Activate virtual environment
Write-Host "Activating virtual environment..."
.\venv\Scripts\Activate

# Install dependencies if needed
if (-not (Test-Path ".\venv\Lib\site-packages\markdown2")) {
    Write-Host "Installing dependencies..."
    pip install -r requirements.txt
}

# Run tests
Write-Host "Running tests..."
python -m pytest tests/

if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed! Aborting deployment."
    exit 1
}

# Build the site
Write-Host "Building site..."
python tools/build.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed! Aborting deployment."
    exit 1
}

# Validate build
Write-Host "Validating build..."
python tools/migrate_sections.py --validate

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build validation failed! Aborting deployment."
    exit 1
}

# Deploy to Cloudflare Pages
Write-Host "Deploying to Cloudflare Pages ($Environment)..."
wrangler pages publish build --project-name="ihelper-tech" --branch="$Environment"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deployment successful!"
    Write-Host "Site should be available at: https://$Environment.ihelper.tech"
} else {
    Write-Host "Deployment failed!"
    exit 1
}

# Deactivate virtual environment
deactivate
