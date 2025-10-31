#!/usr/bin/env python3
"""
Demo: Using the Standard LLVM Optimization Compilation Pipeline
Shows how to compile with -O2 and -O3
"""

from compilation_pipeline import CompilationPipeline

# Sample C program
c_code = """
#include <stdio.h>

int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main() {
    int result = fibonacci(10);
    printf("%d\\n", result);
    return 0;
}
"""

# Initialize pipeline
pipeline = CompilationPipeline(target_arch="riscv64", use_qemu=True)

print("=" * 60)
print("Compiling with -O2")
print("=" * 60)

# Compile with -O2
o2_result = pipeline.compile_with_optimization_level(
    source_code=c_code,
    opt_level="-O2",
    num_runs=5,      # 5 runs for averaging
    timeout=10       # 10s timeout per run
)

if o2_result['success']:
    print(f"✅ Success!")
    print(f"Binary Size: {o2_result['binary_size_human']} ({o2_result['binary_size']} bytes)")
    print(f"Runtime Mean: {o2_result['runtime_mean']:.4f}s")
    print(f"Runtime Std: {o2_result['runtime_std']:.4f}s")
    print(f"Runtime Range: [{o2_result['runtime_min']:.4f}s - {o2_result['runtime_max']:.4f}s]")
    print(f"Compilation Time: {o2_result['compilation_time']:.2f}s")
else:
    print(f"❌ Failed: {o2_result['error']}")

print("\n" + "=" * 60)
print("Compiling with -O3")
print("=" * 60)

# Compile with -O3
o3_result = pipeline.compile_with_optimization_level(
    source_code=c_code,
    opt_level="-O3",
    num_runs=5,      # Same number of runs
    timeout=10       # Same timeout
)

if o3_result['success']:
    print(f"✅ Success!")
    print(f"Binary Size: {o3_result['binary_size_human']} ({o3_result['binary_size']} bytes)")
    print(f"Runtime Mean: {o3_result['runtime_mean']:.4f}s")
    print(f"Runtime Std: {o3_result['runtime_std']:.4f}s")
    print(f"Runtime Range: [{o3_result['runtime_min']:.4f}s - {o3_result['runtime_max']:.4f}s]")
    print(f"Compilation Time: {o3_result['compilation_time']:.2f}s")
else:
    print(f"❌ Failed: {o3_result['error']}")

# Compare -O2 vs -O3
if o2_result['success'] and o3_result['success']:
    print("\n" + "=" * 60)
    print("Comparison: -O2 vs -O3")
    print("=" * 60)
    
    size_diff = o3_result['binary_size'] - o2_result['binary_size']
    time_diff = o3_result['runtime_mean'] - o2_result['runtime_mean']
    
    print(f"Binary Size Difference: {size_diff:+d} bytes")
    print(f"Runtime Difference: {time_diff:+.4f}s")
    
    if size_diff < 0:
        print(f"  → -O3 produces {abs(size_diff)} bytes SMALLER binary")
    else:
        print(f"  → -O2 produces {abs(size_diff)} bytes SMALLER binary")
    
    if time_diff < 0:
        print(f"  → -O3 is {abs(time_diff):.4f}s FASTER")
    else:
        print(f"  → -O2 is {abs(time_diff):.4f}s FASTER")

print("\n" + "=" * 60)
print("✅ Demo Complete!")
print("=" * 60)
