#!/bin/bash

# Build and Deploy Script for Image Processing Lambda
# Usage: ./build_and_deploy.sh [local]

set -e

# Check if deploying to LocalStack
IS_LOCAL=${1:-""}
USE_LOCALSTACK=false

if [ "$IS_LOCAL" = "local" ]; then
  USE_LOCALSTACK=true
  echo "Building for LocalStack deployment..."
else
  echo "Building for AWS deployment..."
fi

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Clean up previous builds
echo "Cleaning up previous builds..."
rm -rf package
rm -f function.zip

# Create package directory
echo "Creating package directory..."
mkdir -p package

# Install Pillow for Linux x86_64 (required for AWS Lambda)
echo "Installing Pillow for Linux x86_64..."
pip install --platform manylinux2014_x86_64 \
  --target=package \
  --implementation cp \
  --python-version 3.9 \
  --only-binary=:all: \
  --upgrade \
  Pillow

# Copy Lambda function to package directory
echo "Copying Lambda function..."
cp src/lambda_function.py package/

# Create zip file
echo "Creating deployment package..."
cd package
zip -r ../function.zip .
cd ..

echo "Deployment package created: function.zip"

# Deploy using Terraform
if [ "$USE_LOCALSTACK" = true ]; then
  echo "Deploying to LocalStack using tflocal..."
  cd terraform
  
  # Check if tflocal is available
  if ! command -v tflocal &> /dev/null; then
    echo "Error: tflocal not found. Please install terraform-local:"
    echo "  pip install terraform-local"
    exit 1
  fi
  
  # Initialize Terraform if needed
  if [ ! -d ".terraform" ]; then
    echo "Initializing Terraform..."
    tflocal init
  fi
  
  # Apply with is_local=true
  echo "Applying Terraform configuration..."
  tflocal apply -var="is_local=true" -var="image_processor_lambda_zip_path=../function.zip" -auto-approve
else
  echo "Deploying to AWS using terraform..."
  cd terraform
  
  # Initialize Terraform if needed
  if [ ! -d ".terraform" ]; then
    echo "Initializing Terraform..."
    terraform init
  fi
  
  # Apply with is_local=false
  echo "Applying Terraform configuration..."
  terraform apply -var="is_local=false" -var="image_processor_lambda_zip_path=../function.zip"
fi

echo "Deployment complete!"

