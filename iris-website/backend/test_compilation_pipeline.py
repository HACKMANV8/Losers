#!/usr/bin/env python3
"""
Test script for the compilation pipeline.
"""

from compilation_pipeline import CompilationPipeline, calculate_improvements

# Simple test program
TEST_PROGRAM = """
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

def test_ml_compilation():
    """Test ML-predicted pass compilation."""
    print("=" * 60)
    print("Testing ML-Predicted Pass Compilation")
    print("=" * 60)
    
    pipeline = CompilationPipeline(target_arch="riscv64", use_qemu=True)
    
    # Test with common optimization passes
    predicted_passes = ["mem2reg", "inline", "gvn", "simplifycfg"]
    
    result = pipeline.compile_with_ml_passes(
        source_code=TEST_PROGRAM,
        predicted_passes=predicted_passes,
        num_runs=3,
        timeout=10
    )
    
    print(f"\nSuccess: {result['success']}")
    if result['success']:
        print(f"Binary Size: {result['binary_size_human']} ({result['binary_size']} bytes)")
        print(f"Runtime Mean: {result['runtime_mean']:.4f}s")
        print(f"Runtime Std: {result['runtime_std']:.4f}s")
        print(f"Runtime Range: [{result['runtime_min']:.4f}s - {result['runtime_max']:.4f}s]")
        print(f"Passes Used: {', '.join(result['passes_used'])}")
        print(f"Compilation Time: {result['compilation_time']:.2f}s")
    else:
        print(f"Error: {result['error']}")
    
    return result

def test_standard_optimization():
    """Test standard LLVM optimization level."""
    print("\n" + "=" * 60)
    print("Testing Standard LLVM Optimization (-O2)")
    print("=" * 60)
    
    pipeline = CompilationPipeline(target_arch="riscv64", use_qemu=True)
    
    result = pipeline.compile_with_optimization_level(
        source_code=TEST_PROGRAM,
        opt_level="-O2",
        num_runs=3,
        timeout=10
    )
    
    print(f"\nSuccess: {result['success']}")
    if result['success']:
        print(f"Binary Size: {result['binary_size_human']} ({result['binary_size']} bytes)")
        print(f"Runtime Mean: {result['runtime_mean']:.4f}s")
        print(f"Runtime Std: {result['runtime_std']:.4f}s")
        print(f"Runtime Range: [{result['runtime_min']:.4f}s - {result['runtime_max']:.4f}s]")
        print(f"Optimization Level: {result['passes_used'][0]}")
        print(f"Compilation Time: {result['compilation_time']:.2f}s")
    else:
        print(f"Error: {result['error']}")
    
    return result

def test_comparison():
    """Test full comparison between ML and standard optimization."""
    print("\n" + "=" * 60)
    print("Testing Comparison: ML vs -O3")
    print("=" * 60)
    
    pipeline = CompilationPipeline(target_arch="riscv64", use_qemu=True)
    
    # ML-predicted compilation
    ml_result = pipeline.compile_with_ml_passes(
        source_code=TEST_PROGRAM,
        predicted_passes=["mem2reg", "inline", "gvn", "simplifycfg", "dce"],
        num_runs=5,
        timeout=10
    )
    
    # Standard -O3 compilation
    o3_result = pipeline.compile_with_optimization_level(
        source_code=TEST_PROGRAM,
        opt_level="-O3",
        num_runs=5,
        timeout=10
    )
    
    if ml_result['success'] and o3_result['success']:
        improvements = calculate_improvements(ml_result, o3_result)
        
        print("\n--- Comparison Results ---")
        print(f"ML Binary Size: {ml_result['binary_size_human']}")
        print(f"-O3 Binary Size: {o3_result['binary_size_human']}")
        print(f"Size Reduction: {improvements['binary_size_reduction_percent']:.2f}%")
        print(f"Size Winner: {improvements['winner_binary']}")
        
        print(f"\nML Runtime: {ml_result['runtime_mean']:.4f}s")
        print(f"-O3 Runtime: {o3_result['runtime_mean']:.4f}s")
        print(f"Runtime Reduction: {improvements['runtime_reduction_percent']:.2f}%")
        print(f"Runtime Winner: {improvements['winner_runtime']}")
    else:
        print("\n⚠️  One or both compilations failed")
        if not ml_result['success']:
            print(f"ML Error: {ml_result['error']}")
        if not o3_result['success']:
            print(f"-O3 Error: {o3_result['error']}")

def test_error_handling():
    """Test error handling with invalid code."""
    print("\n" + "=" * 60)
    print("Testing Error Handling (Invalid C Code)")
    print("=" * 60)
    
    pipeline = CompilationPipeline(target_arch="riscv64", use_qemu=True)
    
    invalid_code = """
    int main() {
        this is not valid C code!!!
        return 0;
    }
    """
    
    result = pipeline.compile_with_ml_passes(
        source_code=invalid_code,
        predicted_passes=["mem2reg"],
        num_runs=3,
        timeout=10
    )
    
    print(f"\nSuccess: {result['success']}")
    print(f"Error Message: {result.get('error', 'N/A')}")
    print("✓ Error handled gracefully" if not result['success'] else "✗ Should have failed")

def test_invalid_passes():
    """Test with invalid pass names."""
    print("\n" + "=" * 60)
    print("Testing Invalid Pass Names")
    print("=" * 60)
    
    pipeline = CompilationPipeline(target_arch="riscv64", use_qemu=True)
    
    result = pipeline.compile_with_ml_passes(
        source_code=TEST_PROGRAM,
        predicted_passes=["mem2reg", "invalid-pass-name", "gvn"],
        num_runs=3,
        timeout=10
    )
    
    print(f"\nSuccess: {result['success']}")
    print(f"Error Message: {result.get('error', 'N/A')}")
    print("✓ Error handled gracefully" if not result['success'] else "✗ Should have failed")

if __name__ == "__main__":
    print("\n" + "🚀 " * 20)
    print("COMPILATION PIPELINE TEST SUITE")
    print("🚀 " * 20)
    
    try:
        # Run tests
        test_ml_compilation()
        test_standard_optimization()
        test_comparison()
        test_error_handling()
        test_invalid_passes()
        
        print("\n" + "=" * 60)
        print("✅ Test Suite Complete!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
