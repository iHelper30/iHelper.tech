#!/bin/bash

# Cloudflare Pages Deployment Script

# Login to Cloudflare
wrangler login

# Create Cloudflare Pages project
wrangler pages project create iHelper.tech \
    --production-branch main \
    --source-directory iHelper.tech

# Deploy the project
wrangler pages deploy iHelper.tech \
    --project-name iHelper.tech \
    --branch main

# Output deployment URL
echo "Deployment complete. Access your site at:"
wrangler pages url iHelper.tech
