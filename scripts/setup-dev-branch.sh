#!/bin/bash

# Setup Dev Branch Configuration Script
# This script helps set up the local development environment for the dev branch

echo "Setting up development branch configuration..."

# Ensure we're in the repository root
cd "$(dirname "$0")/.."

# Fetch the latest changes from remote
echo "Fetching latest changes from remote..."
git fetch origin

# Check if dev branch exists
if ! git show-ref --verify --quiet refs/heads/dev; then
    echo "Creating local dev branch tracking origin/dev..."
    git checkout -b dev origin/dev
else
    echo "Updating local dev branch..."
    git checkout dev
    git pull origin dev
fi

# Set up git hooks if they don't exist
if [ ! -d .git/hooks ]; then
    mkdir -p .git/hooks
fi

# Create pre-commit hook for local checks
echo '#!/bin/sh

# Run linters and tests before commit
echo "Running pre-commit checks..."

# Backend checks
cd backend
poetry run ruff check .
if [ $? -ne 0 ]; then
    echo "Backend linting failed!"
    exit 1
fi

poetry run mypy cartaos
if [ $? -ne 0 ]; then
    echo "Backend type checking failed!"
    exit 1
fi

# Frontend checks
cd ../frontend
npm run lint
if [ $? -ne 0 ]; then
    echo "Frontend linting failed!"
    exit 1
fi

echo "All pre-commit checks passed!"
exit 0
' > .git/hooks/pre-commit

chmod +x .git/hooks/pre-commit

echo ""
"Development branch setup complete!"
echo "Please apply the branch protection rules from docs/branch-protection.md in your GitHub repository settings."
echo "Don't forget to install dependencies with 'cd backend && poetry install' and 'cd frontend && npm ci'"
