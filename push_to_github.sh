#!/bin/bash
# Quick push script for ClipNest MVP to GitHub

echo "ClipNest MVP - GitHub Push Script"
echo "===================================="
echo ""

if [ -z "$1" ]; then
    echo "Usage: $0 <github_url>"
    echo "Example: $0 https://github.com/your-username/clipnest.git"
    echo "Or: $0 git@github.com:your-username/clipnest.git"
    exit 1
fi

REPO_URL="$1"

echo "Configuring git remote to: $REPO_URL"
git remote set-url origin "$REPO_URL"

echo "Pushing to GitHub on 'master' branch..."
git push -u origin master

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Push successful!"
    echo "Repository URL: $REPO_URL"
    echo "Branch: master"
else
    echo ""
    echo "✗ Push failed. Check credentials and repository URL."
    exit 1
fi
