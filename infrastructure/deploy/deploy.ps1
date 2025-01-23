# Deploy script for iHelper.tech
param(
    [string]$Environment = "staging"
)

Write-Host "Starting deployment process for iHelper.tech to $Environment environment..."

# Set branch name based on environment
$branchName = if ($Environment -eq "production") { "iHelper.tech" } else { "staging" }

# Activate virtual environment
Write-Host "Activating virtual environment..."
.\venv\Scripts\Activate

# Install dependencies if needed
if (-not (Test-Path ".\venv\Lib\site-packages\markdown2")) {
    Write-Host "Installing dependencies..."
    pip install --prefer-binary -r requirements.txt
}

# Build the site
Write-Host "Building site..."
python tools/build.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed! Aborting deployment."
    exit 1
}

# Deploy to Cloudflare Pages
Write-Host "Deploying to Cloudflare Pages ($Environment)..."
Write-Host "Using branch: $branchName"
wrangler pages publish build --project-name="ihelper-tech" --branch="$branchName"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deployment successful!"
    $domain = if ($Environment -eq "production") { "ihelper.tech" } else { "staging.ihelper.tech" }
    Write-Host "Site should be available at: https://$domain"
} else {
    Write-Host "Deployment failed!"
    exit 1
}

# Deactivate virtual environment
deactivate
