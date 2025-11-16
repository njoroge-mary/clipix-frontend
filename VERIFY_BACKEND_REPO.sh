#!/bin/bash

echo "=================================================="
echo "  VERIFYING BACKEND REPOSITORY"
echo "=================================================="
echo ""

cd /app/backend

echo "Files to be pushed to GitHub:"
echo "------------------------------"
git ls-files | sort
echo ""

echo "=================================================="
echo "  KEY FILES CHECK"
echo "=================================================="
echo ""

files=(
    "requirements.txt"
    "server.py"
    "video_processor.py"
    "caption_generator.py"
    "Dockerfile"
    "runtime.txt"
    "render.yaml"
    ".gitignore"
    "README.md"
)

for file in "${files[@]}"; do
    if git ls-files | grep -q "^${file}$"; then
        echo "✅ $file"
    else
        echo "❌ MISSING: $file"
    fi
done

echo ""
echo "=================================================="
echo "  COMMITS"
echo "=================================================="
echo ""
git log --oneline --all

echo ""
echo "=================================================="
echo "  PUSH COMMAND"
echo "=================================================="
echo ""
echo "Run this to push everything to GitHub:"
echo ""
echo "  cd /app/backend && git push origin main --force"
echo ""
echo "=================================================="
