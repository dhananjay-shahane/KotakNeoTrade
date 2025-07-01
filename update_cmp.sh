#!/bin/bash
# Google Finance CMP Updater - Shell script wrapper
# Usage: ./update_cmp.sh [symbol1] [symbol2] ...
# Examples:
#   ./update_cmp.sh                    # Update all symbols
#   ./update_cmp.sh NIFTYBEES         # Update specific symbol
#   ./update_cmp.sh NIFTYBEES GOLDBEES # Update multiple symbols

echo "🚀 Starting Google Finance CMP Updater..."
echo "=================================================="

# Check if python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 is not installed or not in PATH"
    exit 1
fi

# Check if required packages are installed
python3 -c "import yfinance, psycopg2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing required packages..."
    pip install yfinance psycopg2-binary
fi

# Run the CMP updater
python3 Scripts/google_finance_cmp_updater.py "$@"

echo "=================================================="
echo "✅ CMP Update completed!"
echo "📊 Check cmp_updater.log for detailed logs"