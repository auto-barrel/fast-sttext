#!/bin/bash
set -e

echo "🚀 Starting..."

# Fix permissions for mounted volume
if [ -d "/app/output" ]; then
    echo "Setting up output directory permissions..."

    # Try to make the directory writable
    chmod 777 /app/output 2>/dev/null || {
        echo "Warning: Cannot change permissions on /app/output"
        echo "This might be due to volume mount restrictions"
    }

    # Test if we can write
    if touch /app/output/.write_test 2>/dev/null && rm -f /app/output/.write_test 2>/dev/null; then
        echo "Output directory is writable"
    else
        echo "Warning: Cannot write to output directory"
        echo "Attempting to create with different permissions..."

        # Try to create a subdirectory as fallback
        mkdir -p /app/output/data 2>/dev/null && chmod 777 /app/output/data 2>/dev/null || true
    fi
else
    echo "Creating output directory..."
    mkdir -p /app/output
    chmod 777 /app/output
    echo "Output directory created"
fi

# Display environment info for debugging
echo "🔍 Environment Information:"
echo "   Current user: $(whoami)"
echo "   Current UID: $(id -u)"
echo "   Current GID: $(id -g)"
echo "   Working directory: $(pwd)"
echo "   Output directory exists: $([ -d /app/output ] && echo 'Yes' || echo 'No')"
echo "   Output directory permissions: $(ls -ld /app/output 2>/dev/null || echo 'N/A')"

echo "Starting application..."
echo "----------------------------------------"

# Execute the main command
exec "$@"