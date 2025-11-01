#!/bin/bash

# Cleanup script to remove unnecessary files from the backend
# This keeps only the simplified LLVM optimization service

echo "Cleaning up unnecessary backend files..."

# Files to keep (simplified backend)
KEEP_FILES=(
    "services/llvm_optimization_service.py"
    "routes/llvm_api.py" 
    "utils/logger_simple.py"
    "app_simplified.py"
    "test_api.py"
    "quick_test.py"
    "README_SIMPLIFIED.md"
    "IMPLEMENTATION_SUMMARY.md"
    "cleanup_backend.sh"
)

# Directories to check
DIRS=("services" "routes" "utils")

echo "The following files are marked as essential for the simplified backend:"
for file in "${KEEP_FILES[@]}"; do
    echo "  ✓ $file"
done

echo ""
echo "Files that can be removed (old complex backend):"

# List removable Python files
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        for file in "$dir"/*.py; do
            if [ -f "$file" ]; then
                basename_file=$(basename "$file")
                full_path="$dir/$basename_file"
                
                # Check if file is in keep list
                keep=false
                for keep_file in "${KEEP_FILES[@]}"; do
                    if [[ "$full_path" == "$keep_file" ]]; then
                        keep=true
                        break
                    fi
                done
                
                if [ "$keep" = false ] && [ "$basename_file" != "__init__.py" ]; then
                    echo "  - $full_path"
                fi
            fi
        done
    fi
done

# Also list old app files
for file in app.py app.py.backup compare_api.py config.py; do
    if [ -f "$file" ]; then
        echo "  - $file"
    fi
done

echo ""
echo "To remove these files and use only the simplified backend, run:"
echo "  ./cleanup_backend.sh --remove"
echo ""
echo "WARNING: This will permanently delete the old backend files!"

# If --remove flag is provided, actually delete the files
if [ "$1" = "--remove" ]; then
    echo ""
    echo "Removing old backend files..."
    
    # Remove old service files
    rm -f services/model_service.py
    rm -f services/feature_service.py
    rm -f services/compilation_service.py
    rm -f services/comparison_service.py
    
    # Remove old route files  
    rm -f routes/optimize_routes.py
    rm -f routes/compare_routes.py
    rm -f routes/analytics_routes.py
    rm -f routes/utility_routes.py
    
    # Remove old utility files
    rm -f utils/validators.py
    rm -f utils/response_formatter.py
    rm -f utils/logger.py
    rm -f utils/cache_manager.py
    rm -f utils/file_manager.py
    rm -f utils/memory_manager.py
    
    # Remove old app files
    rm -f app.py
    rm -f app.py.backup
    rm -f compare_api.py
    rm -f config.py
    
    # Remove __pycache__ directories
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    
    echo "✓ Cleanup complete! Only simplified backend files remain."
    echo ""
    echo "To use the simplified backend:"
    echo "  python3 app_simplified.py"
fi
