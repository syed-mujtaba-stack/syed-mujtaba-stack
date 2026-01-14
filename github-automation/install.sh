#!/bin/bash

# GitHub Contribution Automation Installer
# One-click setup for GitHub contribution automation

echo "🚀 Setting up GitHub Contribution Automation..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "Please install Python 3 before continuing"
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip is required but not installed"
    echo "Please install pip before continuing"
    exit 1
fi

# Create .github directory structure
echo "📁 Creating GitHub Actions directory structure..."
mkdir -p .github/workflows

# Copy workflow file
echo "📋 Copying GitHub Actions workflow..."
cp workflow.yml .github/workflows/

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Make setup script executable
echo "🔧 Making setup script executable..."
chmod +x setup.py

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. Set GITHUB_TOKEN secret in your repository"
echo "2. Test with: python3 setup.py YOUR_TOKEN YOUR_USERNAME YOUR_REPO tutorial"
echo ""
echo "📚 For detailed instructions, see README.md"
