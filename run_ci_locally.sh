#!/bin/bash
# Run local CI checks before pushing

set -e

echo "🔍 Running local CI checks..."
echo ""

echo "1️⃣  Linting with ruff..."
python -m ruff check . || {
    echo "❌ Lint failed!"
    exit 1
}
echo "✅ Lint passed!"
echo ""

echo "2️⃣  Running tests (Python 3.12/3.13)..."
python -m pytest -q || {
    echo "❌ Tests failed!"
    exit 1
}
echo "✅ Tests passed!"
echo ""

echo "🎉 All checks passed! Safe to push."
