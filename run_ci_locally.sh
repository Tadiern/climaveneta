#!/bin/bash
# Run local CI checks before pushing

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "🔍 Running local CI checks..."
echo ""

echo "1️⃣  Linting with ruff..."
python -m ruff check . || {
    echo "❌ Lint failed!"
    exit 1
}
echo "✅ Lint passed!"
echo ""

echo "2️⃣  Running Hassfest validation..."
HA_CORE_PATH="${HA_CORE_PATH:-/usr/src/homeassistant}"
if [[ -f "$HA_CORE_PATH/script/hassfest/__main__.py" ]]; then
    (
        cd "$HA_CORE_PATH"
        python -m script.hassfest \
            --action validate \
            --integration-path "$ROOT_DIR/custom_components/climaveneta" \
            --core-path "$HA_CORE_PATH"
    ) || {
        echo "❌ Hassfest validation failed!"
        exit 1
    }
    echo "✅ Hassfest validation passed!"
else
    echo "⚠️  Hassfest skipped: set HA_CORE_PATH to a Home Assistant checkout."
fi
echo ""

echo "3️⃣  Running tests (current Python)..."
python -m pytest -q || {
    echo "❌ Tests failed!"
    exit 1
}
echo "✅ Tests passed!"
echo ""

echo "📝 Note: HACS validation still runs in GitHub CI"
echo "        Use 'act -j validate-hacs' locally if needed (requires act/network)"
echo ""
echo "🎉 All local checks passed! Safe to push."
