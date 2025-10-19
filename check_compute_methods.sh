#!/bin/bash

# Script to check for missing compute methods

echo "Checking for missing compute methods..."
echo "======================================"

# Extract compute method names and check if they exist
grep -r "compute='_compute_[^']*'" models/ | while IFS= read -r line; do
    file=$(echo "$line" | cut -d: -f1)
    method=$(echo "$line" | sed "s/.*compute='\\(_compute_[^']*\\)'.*/\\1/")
    
    if ! grep -q "def $method" "$file"; then
        echo "MISSING: $method in $file"
    fi
done

echo "======================================"
echo "Check completed."