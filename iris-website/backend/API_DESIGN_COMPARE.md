# API Design: `/api/compare` Endpoint

## Overview
Backend endpoint for comparing ML-predicted LLVM pass sequences against standard optimization levels on RISC-V architecture.

---

## 1. API Specification

### Endpoint
```
POST /api/compare
```

### Request Format

#### Content-Type
`multipart/form-data` or `application/json`

#### Parameters

**Option A: multipart/form-data (Recommended)**
```
POST /api/compare
Content-Type: multipart/form-data

Fields:
- source_file: File (C/C++ source code)
- predicted_passes: string (JSON array of pass names)
- optimization_levels: string (optional, JSON array, default: ["-O0", "-O2", "-O3", "-Oz"])
- num_runs: integer (optional, number of runtime measurements, default: 5)
- timeout: integer (optional, timeout per run in seconds, default: 10)
```

**Option B: application/json**
```json
{
  "source_code": "string (base64 encoded or plain text)",
  "file_name": "string",
  "predicted_passes": ["mem2reg", "inline", "gvn"],
  "optimization_levels": ["-O0", "-O2", "-O3", "-Oz"],
  "num_runs": 5,
  "timeout": 10
}
```

**Recommendation**: Use Option A (multipart) to match existing `/api/optimize` pattern.

---

## 2. Response Format

### Success Response (200 OK)

```json
{
  "success": true,
  "file_name": "quicksort.c",
  "target_architecture": "riscv64",
  "num_runs": 5,
  "timestamp": 1698765432000,
  
  "ml_predicted": {
    "binary_size": 12345,
    "binary_size_human": "12.05 KB",
    "runtime_mean": 0.4234,
    "runtime_std": 0.0023,
    "runtime_min": 0.4201,
    "runtime_max": 0.4267,
    "passes_used": ["mem2reg", "inline", "gvn", "simplifycfg"],
    "num_passes": 4,
    "compilation_time": 1.234,
    "success": true
  },
  
  "llvm_o0": {
    "binary_size": 18432,
    "binary_size_human": "18.00 KB",
    "runtime_mean": 0.8901,
    "runtime_std": 0.0045,
    "runtime_min": 0.8845,
    "runtime_max": 0.8956,
    "passes_used": ["-O0"],
    "num_passes": 1,
    "compilation_time": 0.567,
    "success": true
  },
  
  "llvm_o2": {
    "binary_size": 15100,
    "binary_size_human": "14.75 KB",
    "runtime_mean": 0.5123,
    "runtime_std": 0.0034,
    "runtime_min": 0.5089,
    "runtime_max": 0.5167,
    "passes_used": ["-O2"],
    "num_passes": 1,
    "compilation_time": 0.789,
    "success": true
  },
  
  "llvm_o3": {
    "binary_size": 14800,
    "binary_size_human": "14.45 KB",
    "runtime_mean": 0.4834,
    "runtime_std": 0.0029,
    "runtime_min": 0.4801,
    "runtime_max": 0.4867,
    "passes_used": ["-O3"],
    "num_passes": 1,
    "compilation_time": 0.823,
    "success": true
  },
  
  "llvm_oz": {
    "binary_size": 13200,
    "binary_size_human": "12.89 KB",
    "runtime_mean": 0.5456,
    "runtime_std": 0.0031,
    "runtime_min": 0.5421,
    "runtime_max": 0.5489,
    "passes_used": ["-Oz"],
    "num_passes": 1,
    "compilation_time": 0.712,
    "success": true
  },
  
  "improvements": {
    "vs_o0": {
      "binary_size_reduction_percent": -33.0,
      "binary_size_reduction_bytes": -6087,
      "runtime_reduction_percent": -52.4,
      "runtime_reduction_seconds": -0.4667,
      "winner_binary": "ml_predicted",
      "winner_runtime": "ml_predicted"
    },
    "vs_o2": {
      "binary_size_reduction_percent": -18.2,
      "binary_size_reduction_bytes": -2755,
      "runtime_reduction_percent": -17.3,
      "runtime_reduction_seconds": -0.0889,
      "winner_binary": "ml_predicted",
      "winner_runtime": "ml_predicted"
    },
    "vs_o3": {
      "binary_size_reduction_percent": -16.6,
      "binary_size_reduction_bytes": -2455,
      "runtime_reduction_percent": -12.4,
      "runtime_reduction_seconds": -0.0600,
      "winner_binary": "ml_predicted",
      "winner_runtime": "ml_predicted"
    },
    "vs_oz": {
      "binary_size_reduction_percent": -6.5,
      "binary_size_reduction_bytes": -855,
      "runtime_reduction_percent": -22.4,
      "runtime_reduction_seconds": -0.1222,
      "winner_binary": "ml_predicted",
      "winner_runtime": "ml_predicted"
    }
  },
  
  "summary": {
    "best_binary_size": {
      "method": "ml_predicted",
      "size": 12345,
      "improvement_vs_best_llvm": -6.5
    },
    "best_runtime": {
      "method": "ml_predicted",
      "time": 0.4234,
      "improvement_vs_best_llvm": -12.4
    },
    "ml_wins": {
      "binary_size": 4,
      "runtime": 4,
      "total": 8,
      "out_of": 8
    }
  },
  
  "total_processing_time": 8.234,
  "error": null
}
```

### Partial Success Response (200 OK with failures)

```json
{
  "success": true,
  "file_name": "problematic.c",
  "target_architecture": "riscv64",
  
  "ml_predicted": {
    "success": false,
    "error": "Compilation failed: opt returned non-zero exit code",
    "error_details": "Pass 'invalid-pass' not found in pass registry"
  },
  
  "llvm_o2": {
    "success": true,
    "binary_size": 15100,
    "runtime_mean": 0.5123,
    ...
  },
  
  "llvm_o3": {
    "success": false,
    "error": "Runtime timeout: Program exceeded 10 second limit",
    "timeout": 10
  },
  
  "improvements": {
    "vs_o2": null,
    "vs_o3": null
  },
  
  "summary": {
    "note": "Some compilations failed. Improvements cannot be calculated."
  },
  
  "error": "One or more compilations failed. See individual results."
}
```

### Error Response (400 Bad Request)

```json
{
  "success": false,
  "error": "Invalid request: No source file provided",
  "error_code": "MISSING_SOURCE_FILE",
  "total_processing_time": 0.001
}
```

### Error Response (500 Internal Server Error)

```json
{
  "success": false,
  "error": "Internal server error: LLVM toolchain not available",
  "error_code": "TOOLCHAIN_ERROR",
  "error_details": "clang: command not found",
  "total_processing_time": 0.123
}
```

---

## 3. Compilation Pipeline Design

### Architecture: RISC-V Target (Critical!)

**ALL compilations MUST target RISC-V architecture** per project requirements.

### Pipeline A: ML-Predicted Passes

```bash
# Step 1: C → Unoptimized Bitcode (RISC-V)
clang --target=riscv64-unknown-linux-gnu \
      -O0 \
      -emit-llvm \
      -c source.c \
      -o source.bc

# Step 2: Apply ML-Predicted Passes
opt -passes=mem2reg,inline,gvn,simplifycfg \
    source.bc \
    -o source_ml.bc

# Step 3: Bitcode → Assembly (RISC-V)
llc -march=riscv64 \
    source_ml.bc \
    -o source_ml.s

# Step 4: Assembly → Executable (Static linking for QEMU)
riscv64-linux-gnu-gcc source_ml.s \
                      -o source_ml.exe \
                      -static

# Step 5: Measure Binary Size
stat -c%s source_ml.exe  # Returns bytes

# Step 6: Measure Runtime (via QEMU)
for i in {1..5}; do
    time qemu-riscv64 source_ml.exe
done
# Calculate mean, std, min, max
```

### Pipeline B: Standard LLVM Optimization (-O0, -O2, -O3, -Oz)

```bash
# Direct compilation with optimization level
clang --target=riscv64-unknown-linux-gnu \
      -O2 \
      source.c \
      -o source_o2.exe \
      -static

# Measure binary size
stat -c%s source_o2.exe

# Measure runtime
for i in {1..5}; do
    time qemu-riscv64 source_o2.exe
done
```

### Critical Compilation Flags

| Flag | Purpose | Required? |
|------|---------|-----------|
| `--target=riscv64-unknown-linux-gnu` | Target RISC-V 64-bit | ✅ YES |
| `-static` | Static linking for QEMU | ✅ YES |
| `-march=riscv64` | Architecture for llc | ✅ YES (llc only) |
| `-emit-llvm` | Generate LLVM IR | ✅ YES (first step) |
| `-O0` | No optimization (baseline) | ✅ YES (initial bc) |

---

## 4. Measurement Strategy

### Binary Size Measurement

**Method**: Use `os.path.getsize()` in Python

```python
def measure_binary_size(executable_path: str) -> int:
    """
    Measure binary size in bytes.
    
    Returns:
        int: Size in bytes
    """
    return os.path.getsize(executable_path)
```

**Accuracy**: Perfect - file system reports exact size
**Time**: Instant (<1ms)

### Runtime Measurement

**Method**: Multiple runs with time.perf_counter() + statistical analysis

```python
def measure_runtime(executable_path: str, 
                   num_runs: int = 5, 
                   timeout: int = 10) -> Dict[str, float]:
    """
    Measure execution runtime with multiple runs.
    
    Args:
        executable_path: Path to RISC-V executable
        num_runs: Number of runs for averaging (default: 5)
        timeout: Timeout per run in seconds (default: 10)
    
    Returns:
        {
            'mean': float,      # Average time
            'std': float,       # Standard deviation
            'min': float,       # Minimum time
            'max': float,       # Maximum time
            'runs': int,        # Number of successful runs
            'success': bool     # All runs completed
        }
    """
    import time
    import statistics
    import subprocess
    
    times = []
    
    for run_idx in range(num_runs):
        try:
            start = time.perf_counter()
            subprocess.run(
                ['qemu-riscv64', executable_path],
                check=True,
                capture_output=True,
                timeout=timeout
            )
            end = time.perf_counter()
            times.append(end - start)
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Timeout exceeded ({timeout}s)',
                'runs': len(times)
            }
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'Program crashed with exit code {e.returncode}',
                'stderr': e.stderr.decode(),
                'runs': len(times)
            }
    
    return {
        'mean': statistics.mean(times),
        'std': statistics.stdev(times) if len(times) > 1 else 0.0,
        'min': min(times),
        'max': max(times),
        'runs': len(times),
        'success': True
    }
```

**Accuracy Considerations:**

1. **Number of Runs**: 
   - Minimum: 3 runs (for basic statistics)
   - Recommended: 5 runs (balance speed vs accuracy)
   - Maximum: 10 runs (diminishing returns)

2. **Warm-up Run**: 
   - Consider discarding first run (cold cache)
   - Or: Always include warm-up, don't count it

3. **QEMU Overhead**:
   - QEMU emulation adds ~10-50ms overhead
   - Overhead is consistent across all comparisons
   - Relative comparisons remain valid

4. **Statistical Significance**:
   - Report standard deviation
   - Flag high variance as unreliable
   - Consider coefficient of variation (CV = std/mean)

### Timeout Strategy

**Default Timeout**: 10 seconds per run

**Rationale**:
- Training programs typically run in <1 second
- 10s allows for worst-case scenarios
- Prevents infinite loops from hanging server

**Progressive Timeout**:
```python
# If -O0 takes 2s, scale other timeouts
base_timeout = o0_runtime * 5  # 5x safety margin
ml_timeout = min(base_timeout, 10)  # Cap at 10s
```

---

## 5. Improvement Calculation

### Binary Size Reduction

```python
def calculate_size_reduction(ml_size: int, baseline_size: int) -> Dict:
    """
    Calculate binary size reduction metrics.
    
    Positive percentage = ML is LARGER (worse)
    Negative percentage = ML is SMALLER (better)
    """
    reduction_bytes = ml_size - baseline_size
    reduction_percent = (reduction_bytes / baseline_size) * 100
    
    return {
        'reduction_bytes': reduction_bytes,
        'reduction_percent': reduction_percent,
        'winner': 'ml_predicted' if reduction_bytes < 0 else 'baseline'
    }
```

### Runtime Reduction

```python
def calculate_runtime_reduction(ml_time: float, baseline_time: float) -> Dict:
    """
    Calculate runtime reduction metrics.
    
    Positive percentage = ML is SLOWER (worse)
    Negative percentage = ML is FASTER (better)
    """
    reduction_seconds = ml_time - baseline_time
    reduction_percent = (reduction_seconds / baseline_time) * 100
    
    return {
        'reduction_seconds': reduction_seconds,
        'reduction_percent': reduction_percent,
        'winner': 'ml_predicted' if reduction_seconds < 0 else 'baseline'
    }
```

### Winner Determination

```python
def determine_winner(improvements: Dict) -> Dict:
    """
    Determine overall winner across all metrics.
    """
    ml_wins_binary = sum(1 for v in improvements.values() 
                         if v['winner_binary'] == 'ml_predicted')
    ml_wins_runtime = sum(1 for v in improvements.values() 
                          if v['winner_runtime'] == 'ml_predicted')
    
    return {
        'binary_size': ml_wins_binary,
        'runtime': ml_wins_runtime,
        'total': ml_wins_binary + ml_wins_runtime,
        'out_of': len(improvements) * 2
    }
```

---

## 6. Error Handling

### Error Categories

#### 1. Request Validation Errors (400 Bad Request)

| Error | Code | Message |
|-------|------|---------|
| No source file | `MISSING_SOURCE_FILE` | "No source file provided" |
| Empty file | `EMPTY_SOURCE_FILE` | "Source file is empty" |
| Invalid file type | `INVALID_FILE_TYPE` | "File must be .c or .cpp" |
| Invalid passes | `INVALID_PASSES` | "predicted_passes must be array of strings" |
| Invalid opt level | `INVALID_OPT_LEVEL` | "Invalid optimization level: -O4" |
| File too large | `FILE_TOO_LARGE` | "File exceeds 10MB limit" |

#### 2. Compilation Errors (200 OK, partial failure)

| Error | Handling | Include in Response |
|-------|----------|-------------------|
| Clang fails | Mark method as failed | error, stderr output |
| Opt fails | Mark method as failed | error, invalid pass name |
| LLC fails | Mark method as failed | error, stderr |
| GCC linking fails | Mark method as failed | error, linker output |

**Example**:
```json
{
  "ml_predicted": {
    "success": false,
    "error": "opt failed: Unknown pass 'invalid-pass'",
    "error_details": "Error during pass execution...",
    "stderr": "opt: error: unknown pass name 'invalid-pass'"
  }
}
```

#### 3. Runtime Errors (200 OK, partial failure)

| Error | Handling | Include in Response |
|-------|----------|-------------------|
| Program crashes | Mark method as failed | exit code, stderr |
| Segmentation fault | Mark method as failed | signal type |
| Timeout | Mark method as failed | timeout value |
| QEMU error | Mark method as failed | QEMU error message |

**Example**:
```json
{
  "llvm_o3": {
    "success": false,
    "error": "Runtime failure: Segmentation fault",
    "error_details": "Signal: 11 (SIGSEGV)",
    "stderr": "qemu: uncaught target signal 11..."
  }
}
```

#### 4. System Errors (500 Internal Server Error)

| Error | Code | Message |
|-------|------|---------|
| Clang not found | `TOOLCHAIN_ERROR` | "LLVM toolchain not available" |
| QEMU not found | `QEMU_ERROR` | "QEMU emulator not available" |
| Out of disk space | `DISK_ERROR` | "Insufficient disk space" |
| Out of memory | `MEMORY_ERROR` | "Server out of memory" |
| Unknown error | `INTERNAL_ERROR` | "Unexpected server error" |

### Error Recovery Strategy

```python
def safe_compile_and_measure(method_name: str, compile_func, measure_func):
    """
    Safely compile and measure with error handling.
    """
    result = {
        'method': method_name,
        'success': False
    }
    
    try:
        # Step 1: Compile
        executable = compile_func()
        result['compilation_time'] = ...
        
        # Step 2: Measure binary size
        result['binary_size'] = os.path.getsize(executable)
        
        # Step 3: Measure runtime
        runtime_data = measure_runtime(executable)
        
        if runtime_data['success']:
            result['runtime_mean'] = runtime_data['mean']
            result['runtime_std'] = runtime_data['std']
            result['runtime_min'] = runtime_data['min']
            result['runtime_max'] = runtime_data['max']
            result['success'] = True
        else:
            result['error'] = runtime_data['error']
            
    except subprocess.CalledProcessError as e:
        result['error'] = f"Compilation failed: {e.stderr.decode()}"
    except subprocess.TimeoutExpired:
        result['error'] = "Compilation timeout"
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
    
    return result
```

### Graceful Degradation

**Philosophy**: Return as much data as possible, even if some methods fail.

**Rules**:
1. If ALL methods fail → 500 Internal Server Error
2. If ML method fails but LLVM works → 200 OK with partial data
3. If one LLVM level fails → Continue with others
4. If runtime measurement fails → Return binary size only
5. Always include error details for failed methods

---

## 7. Performance Considerations

### Timeout Management

**Total Endpoint Timeout**: 60 seconds

**Breakdown**:
- Compilation (4 methods × ~3s): ~12s
- Runtime measurement (4 methods × 5 runs × 2s): ~40s
- Overhead: ~8s
- **Total**: ~60s

**Implementation**:
```python
@app.route('/api/compare', methods=['POST'])
@timeout(60)  # Decorator or manual timeout
def api_compare():
    ...
```

### Parallel vs Sequential Execution

**Option A: Sequential (Recommended)**
- Simpler implementation
- Easier error handling
- More predictable timing
- Lower memory usage

**Option B: Parallel**
- Faster (4x speedup potential)
- More complex
- Risk of resource contention
- May overwhelm QEMU

**Recommendation**: Start with sequential, add parallel later if needed.

### Resource Cleanup

```python
try:
    # Create temp files
    with tempfile.TemporaryDirectory() as temp_dir:
        # All compilation happens here
        ...
finally:
    # Temp directory automatically cleaned up
    pass
```

**Critical**: Always clean up temporary files to prevent disk space leaks.

### Caching Strategy (Future)

**Idea**: Cache comparison results by source code hash

```python
cache_key = hashlib.sha256(source_code.encode()).hexdigest()
if cache_key in comparison_cache:
    return cached_result
```

**Benefits**:
- Instant results for repeated comparisons
- Reduces server load

**Limitations**:
- Need cache invalidation strategy
- Memory usage grows

---

## 8. Security Considerations

### Input Validation

1. **File Size Limit**: 10MB maximum
2. **File Type**: Only `.c` and `.cpp`
3. **Pass Names**: Validate against known LLVM passes
4. **Optimization Levels**: Only allow `-O0`, `-O1`, `-O2`, `-O3`, `-Os`, `-Oz`

### Sandboxing

**Risk**: User-supplied C code could contain malicious code

**Mitigation**:
1. All execution in QEMU (sandboxed by default)
2. Timeout limits prevent infinite loops
3. Temporary directories isolate compilations
4. No network access during execution

### Resource Limits

```python
# Limit CPU time
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))

# Limit memory
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))  # 512MB

# Limit file size
resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024 * 1024, 100 * 1024 * 1024))  # 100MB
```

---

## 9. Testing Strategy

### Unit Tests

```python
def test_compare_simple_program():
    """Test comparison with simple hello world."""
    source = 'int main() { return 0; }'
    passes = ['mem2reg', 'simplifycfg']
    
    response = client.post('/api/compare', data={
        'source_code': source,
        'predicted_passes': json.dumps(passes)
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    assert 'ml_predicted' in data
    assert 'llvm_o2' in data
    assert data['ml_predicted']['success'] == True
```

### Integration Tests

1. Test with all 30 training programs
2. Compare against known baselines
3. Verify RISC-V compilation works
4. Test error handling (invalid passes, etc.)

### Edge Cases

- Empty C file
- C file with syntax errors
- Infinite loop program
- Program that crashes
- Very large binary (>100MB)
- Very slow program (>10s runtime)

---

## 10. API Usage Example (Frontend)

```typescript
async function compareOptimizations(sourceCode: string, predictedPasses: string[]) {
  const formData = new FormData();
  
  // Convert source code to File object
  const blob = new Blob([sourceCode], { type: 'text/plain' });
  const file = new File([blob], 'program.c');
  
  formData.append('source_file', file);
  formData.append('predicted_passes', JSON.stringify(predictedPasses));
  formData.append('optimization_levels', JSON.stringify(['-O0', '-O2', '-O3', '-Oz']));
  formData.append('num_runs', '5');
  
  try {
    const response = await fetch('http://localhost:5001/api/compare', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    
    if (data.success) {
      console.log('ML wins:', data.summary.ml_wins);
      console.log('Best binary size:', data.summary.best_binary_size);
      console.log('Best runtime:', data.summary.best_runtime);
    } else {
      console.error('Comparison failed:', data.error);
    }
    
    return data;
  } catch (error) {
    console.error('Network error:', error);
    throw error;
  }
}
```

---

## 11. Implementation Checklist

- [ ] Create `/api/compare` endpoint in Flask
- [ ] Implement request validation
- [ ] Implement ML-predicted compilation pipeline
- [ ] Implement LLVM optimization compilation pipeline
- [ ] Implement binary size measurement
- [ ] Implement runtime measurement with statistics
- [ ] Implement improvement calculation
- [ ] Implement error handling for all failure modes
- [ ] Add timeout protection
- [ ] Add resource cleanup
- [ ] Add logging for debugging
- [ ] Test with sample programs
- [ ] Test error cases
- [ ] Integrate with frontend Comparison page
- [ ] Add caching (optional)
- [ ] Add rate limiting (optional)

---

## 12. Next Steps

1. **Implementation Phase**: Implement the endpoint in `backend/app.py`
2. **Testing Phase**: Test with training programs
3. **Frontend Integration**: Update Comparison page to call API
4. **Visualization**: Add charts showing improvements
5. **Optimization**: Add caching and parallel execution

---

**Status**: 📋 Design Complete - Ready for Implementation  
**Target**: RISC-V Architecture (riscv64-unknown-linux-gnu)  
**Goal**: Beat standard optimization levels (-O2, -O3) with ML predictions
