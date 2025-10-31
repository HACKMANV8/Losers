# ✅ Compilation Pipeline - Implementation Summary

## What Was Built

### 🎯 Core Module: `compilation_pipeline.py`

**Purpose**: Compile C programs with ML-predicted LLVM passes or standard optimization levels, targeting RISC-V architecture.

**Key Innovation**: **Reuses existing code** from `/home/yash/hackman/tools/` instead of duplicating functionality.

---

## 📦 Main Components

### 1. `CompilationPipeline` Class

```python
from compilation_pipeline import CompilationPipeline

pipeline = CompilationPipeline(target_arch="riscv64", use_qemu=True)
```

**Two Main Methods**:

#### A. `compile_with_ml_passes()` 
Compiles with ML-predicted pass sequence:
```
C Code → [clang] → Bitcode → [opt + ML passes] → Optimized BC → [llc] → Assembly → [gcc] → Executable
                                                                                              ↓
                                                                                    [QEMU + Statistics]
```

#### B. `compile_with_optimization_level()`
Compiles with standard optimization (-O0, -O2, -O3, -Oz):
```
C Code → [clang -O2] → Executable → [QEMU + Statistics]
```

---

## 📊 What Gets Measured

### Binary Size
- Exact file size in bytes
- Human-readable format (KB, MB)

### Runtime Performance
- **5 runs** via QEMU emulation
- **Statistics**: mean, std deviation, min, max
- **Timeout**: 10s per run
- **Crash detection**: Exit codes, stderr

---

## 🎯 RISC-V Compilation (Critical!)

**All compilation targets RISC-V architecture**:

```bash
# ML Path
clang --target=riscv64-unknown-linux-gnu -O0 -emit-llvm -c program.c -o program.bc
opt -passes=mem2reg,inline,gvn program.bc -o program_opt.bc
llc -march=riscv64 program_opt.bc -o program.s
riscv64-linux-gnu-gcc program.s -o program.exe -static
qemu-riscv64 program.exe

# Standard Path
clang --target=riscv64-unknown-linux-gnu -O2 program.c -o program.exe -static
qemu-riscv64 program.exe
```

---

## 📈 Improvement Calculation

```python
from compilation_pipeline import calculate_improvements

improvements = calculate_improvements(ml_result, o3_result)

# Returns:
{
    'binary_size_reduction_percent': -18.5,  # Negative = ML wins!
    'runtime_reduction_percent': -17.3,      # Negative = ML faster!
    'winner_binary': 'ml_predicted',
    'winner_runtime': 'ml_predicted'
}
```

**Interpretation**:
- ✅ **Negative % = ML is BETTER** (smaller binary, faster runtime)
- ❌ **Positive % = ML is WORSE** (larger binary, slower runtime)

---

## 🛡️ Error Handling

**Handles all failure scenarios**:
- ❌ Compilation failures (syntax errors, invalid passes)
- ❌ Runtime crashes (segfaults, exit codes)
- ❌ Timeouts (infinite loops)
- ❌ QEMU errors

**Always returns structured response**:
```python
{
    'success': False,
    'error': 'Runtime timeout: Program exceeded 10s limit',
    'compilation_time': 1.23
}
```

---

## 🧪 Testing

**Test Suite**: `test_compilation_pipeline.py`

Run tests:
```bash
cd /home/yash/hackman/iris-website/backend
python3 test_compilation_pipeline.py
```

**Coverage**:
- ✅ ML-predicted compilation
- ✅ Standard optimization compilation  
- ✅ Full comparison (ML vs -O3)
- ✅ Error handling (invalid code)
- ✅ Invalid pass names
- ✅ Runtime statistics
- ✅ RISC-V targeting

---

## 🔌 API Integration Ready

**Import in `app.py`**:
```python
from compilation_pipeline import CompilationPipeline, calculate_improvements

# Initialize once
pipeline = CompilationPipeline(target_arch="riscv64", use_qemu=True)

# Use in /api/compare endpoint
@app.route('/api/compare', methods=['POST'])
def api_compare():
    ml_result = pipeline.compile_with_ml_passes(source_code, predicted_passes)
    o2_result = pipeline.compile_with_optimization_level(source_code, "-O2")
    o3_result = pipeline.compile_with_optimization_level(source_code, "-O3")
    
    improvements = {
        'vs_o2': calculate_improvements(ml_result, o2_result),
        'vs_o3': calculate_improvements(ml_result, o3_result)
    }
    
    return jsonify({
        'ml_predicted': ml_result,
        'llvm_o2': o2_result,
        'llvm_o3': o3_result,
        'improvements': improvements
    })
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `compilation_pipeline.py` | Main compilation module (450 lines) |
| `test_compilation_pipeline.py` | Test suite |
| `COMPILATION_PIPELINE_IMPLEMENTATION.md` | Detailed documentation |
| `README_PIPELINE.md` | This quick reference |

---

## ⚡ Quick Start

```python
from compilation_pipeline import CompilationPipeline

# Initialize
pipeline = CompilationPipeline(target_arch="riscv64")

# Your C code
c_code = """
int main() {
    return 42;
}
"""

# Compile with ML passes
result = pipeline.compile_with_ml_passes(
    source_code=c_code,
    predicted_passes=["mem2reg", "simplifycfg"],
    num_runs=5
)

# Check results
if result['success']:
    print(f"Binary: {result['binary_size_human']}")
    print(f"Runtime: {result['runtime_mean']:.4f}s")
    print(f"Passes: {result['passes_used']}")
```

---

## 🎯 Next Steps

1. ✅ **DONE**: Compilation pipeline implemented
2. ⏭️ **NEXT**: Integrate into `/api/compare` endpoint in `app.py`
3. ⏭️ **NEXT**: Connect frontend Comparison page to backend
4. ⏭️ **NEXT**: Add visualization (charts/graphs)
5. ⏭️ **NEXT**: Test with real programs from training set

---

## 🚀 Status

**✅ Compilation Pipeline: COMPLETE**

Ready to integrate into Flask backend and start comparing ML predictions against standard LLVM optimization levels!

**Key Achievement**: All compilation properly targets RISC-V architecture as required by the project! 🎯
