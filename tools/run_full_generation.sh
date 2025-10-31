#!/bin/bash
# Hybrid Training Data Generation Script for RISC-V
# Generates comprehensive dataset using both IR passes and machine-level flags
# Target Architecture: RISC-V (using QEMU emulation)

set -e

echo "=========================================="
echo "RISC-V Hybrid Training Data Generation"
echo "ML-Guided Compiler Optimization"
echo "IR-Level + Machine-Level Optimizations"
echo "=========================================="

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
PROGRAMS_DIR="$PROJECT_ROOT/training_programs"
OUTPUT_DIR="$SCRIPT_DIR/training_data"
NUM_SEQUENCES=200
MAX_WORKERS=4
TARGET_ARCH="riscv64"  # Default: RISC-V 64-bit
USE_QEMU=true           # Use QEMU emulation by default

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--num-sequences)
            NUM_SEQUENCES="$2"
            shift 2
            ;;
        -w|--workers)
            MAX_WORKERS="$2"
            shift 2
            ;;
        --quick)
            NUM_SEQUENCES=50
            echo "Quick mode: generating only 50 sequences per program"
            shift
            ;;
        --test)
            NUM_SEQUENCES=10
            echo "Test mode: generating only 10 sequences per program"
            shift
            ;;
        --target-arch)
            TARGET_ARCH="$2"
            shift 2
            ;;
        --riscv64)
            TARGET_ARCH="riscv64"
            echo "Target: RISC-V 64-bit"
            shift
            ;;
        --riscv32)
            TARGET_ARCH="riscv32"
            echo "Target: RISC-V 32-bit"
            shift
            ;;
        --native)
            TARGET_ARCH="native"
            USE_QEMU=false
            echo "Target: Native (x86_64) - WARNING: Not RISC-V!"
            shift
            ;;
        --no-qemu)
            USE_QEMU=false
            echo "QEMU disabled (for native RISC-V hardware)"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "RISC-V Hybrid Training Data Generation (IR + Machine Optimizations)"
            echo ""
            echo "Options:"
            echo "  -n, --num-sequences N    Number of hybrid sequences per program (default: 200)"
            echo "  -w, --workers N          Number of parallel workers (default: 4)"
            echo "  --quick                  Quick mode (50 sequences)"
            echo "  --test                   Test mode (10 sequences)"
            echo ""
            echo "RISC-V Target Options:"
            echo "  --target-arch ARCH       Target architecture: riscv64, riscv32, native"
            echo "  --riscv64                Target RISC-V 64-bit (default)"
            echo "  --riscv32                Target RISC-V 32-bit"
            echo "  --native                 Target native x86_64 (NOT recommended)"
            echo "  --no-qemu                Disable QEMU (for real RISC-V hardware)"
            echo ""
            echo "  -h, --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                       # Generate hybrid data with RISC-V 64-bit (default)"
            echo "  $0 --riscv32             # Generate hybrid data with RISC-V 32-bit"
            echo "  $0 --quick --riscv64     # Quick hybrid generation with RISC-V 64-bit"
            echo "  $0 --no-qemu             # For native RISC-V hardware"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo ""
echo "Configuration:"
echo "  Programs directory: $PROGRAMS_DIR"
echo "  Output directory:   $OUTPUT_DIR"
echo "  Sequences/program:  $NUM_SEQUENCES"
echo "  Parallel workers:   $MAX_WORKERS"
echo "  Target arch:        $TARGET_ARCH"
if [ "$TARGET_ARCH" != "native" ]; then
    if [ "$USE_QEMU" = true ]; then
        echo "  QEMU emulation:     Enabled"
    else
        echo "  QEMU emulation:     Disabled (native RISC-V hardware)"
    fi
fi
echo ""

# Check if programs directory exists
if [ ! -d "$PROGRAMS_DIR" ]; then
    echo "ERROR: Programs directory not found: $PROGRAMS_DIR"
    exit 1
fi

# Count programs
NUM_PROGRAMS=$(find "$PROGRAMS_DIR" -name "*.c" | wc -l)
echo "Found $NUM_PROGRAMS training programs"

if [ $NUM_PROGRAMS -eq 0 ]; then
    echo "ERROR: No .c files found in $PROGRAMS_DIR"
    exit 1
fi

# Estimate
TOTAL_ATTEMPTS=$((NUM_PROGRAMS * NUM_SEQUENCES))
EXPECTED_SUCCESS=$((TOTAL_ATTEMPTS * 85 / 100))
echo "Expected ~$EXPECTED_SUCCESS valid data points (85% success rate)"
echo ""

# Check RISC-V toolchain availability
if [ "$TARGET_ARCH" = "riscv64" ] || [ "$TARGET_ARCH" = "riscv32" ]; then
    echo "Checking RISC-V toolchain..."
    
    # Check if clang supports RISC-V
    if ! llc --version 2>/dev/null | grep -q riscv; then
        echo "⚠️  WARNING: RISC-V target not found in LLVM/Clang"
        echo "    Install with: sudo apt install clang-18 llvm-18"
        echo ""
    else
        echo "✓ RISC-V support detected in LLVM"
    fi
    
    # Check if QEMU is available (if needed)
    if [ "$USE_QEMU" = true ]; then
        if [ "$TARGET_ARCH" = "riscv64" ]; then
            QEMU_BIN="qemu-riscv64"
        else
            QEMU_BIN="qemu-riscv32"
        fi
        
        if ! command -v $QEMU_BIN &> /dev/null; then
            echo "⚠️  WARNING: $QEMU_BIN not found"
            echo "    Install with: sudo apt install qemu-user-static"
            echo ""
        else
            echo "✓ QEMU emulator found: $QEMU_BIN"
        fi
    fi
    
    echo ""
fi

# Confirm
read -p "Proceed with generation? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Record start time
START_TIME=$(date +%s)

echo ""
echo "=========================================="
echo "Starting HYBRID generation..."
echo "(IR passes + Machine-level flags)"
echo "Random sequences only (no O1/O2/O3)"
echo "=========================================="
echo ""

# Build Python command with RISC-V target flags (HYBRID MODE)
PYTHON_CMD="python3 $SCRIPT_DIR/generate_training_data_hybrid.py \
    --programs-dir \"$PROGRAMS_DIR\" \
    --output-dir \"$OUTPUT_DIR\" \
    --num-sequences \"$NUM_SEQUENCES\" \
    --strategy random \
    --no-presets \
    --max-workers \"$MAX_WORKERS\" \
    --target-arch \"$TARGET_ARCH\" \
    --output-file \"training_data_hybrid.json\""

# Add --no-qemu flag if needed
if [ "$USE_QEMU" = false ]; then
    PYTHON_CMD="$PYTHON_CMD --no-qemu"
fi

# Run generation (change to tools directory first)
echo "Executing: $PYTHON_CMD"
echo ""
cd "$SCRIPT_DIR"
eval $PYTHON_CMD

# Record end time
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo ""
echo "=========================================="
echo "Generation Complete!"
echo "=========================================="
echo "Time taken: ${MINUTES}m ${SECONDS}s"
echo ""

# Show file info
if [ -f "$OUTPUT_DIR/training_data_hybrid.json" ]; then
    SIZE=$(du -h "$OUTPUT_DIR/training_data_hybrid.json" | cut -f1)
    POINTS=$(python3 -c "import json; d=json.load(open('$OUTPUT_DIR/training_data_hybrid.json')); print(d['metadata']['total_data_points'])")
    
    echo "Output file: $OUTPUT_DIR/training_data_hybrid.json"
    echo "File size:   $SIZE"
    echo "Data points: $POINTS"
    echo "Optimization: Hybrid (IR + Machine)"
    echo ""
fi

echo ""
echo "Next steps:"
echo "  1. Inspect the data: less $OUTPUT_DIR/training_data_hybrid.json"
echo "  2. Load in Python: import json; data = json.load(open('$OUTPUT_DIR/training_data_hybrid.json'))"
echo "  3. Convert to CSV: python3 json_to_csv.py (if needed)"
echo "  4. Train HYBRID ML model on both IR passes and machine flags"
echo "  5. Evaluate model on test programs (RISC-V target)"
echo ""
echo "🚀 Your HYBRID training data combines IR + machine-level optimizations!"
echo "📊 Total optimization space: ~92 optimizations (77 IR + 15 machine)"
echo ""
