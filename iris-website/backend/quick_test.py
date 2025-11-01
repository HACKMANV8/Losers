#!/usr/bin/env python3
"""
Quick test to verify the LLVM optimization service works
"""

from services.llvm_optimization_service import LLVMOptimizationService
import json

# Simple test program
TEST_CODE = """
#include <stdio.h>

int main() {
    int sum = 0;
    for (int i = 0; i < 100; i++) {
        sum += i;
    }
    printf("Sum: %d\\n", sum);
    return 0;
}
"""

# Test passes
TEST_PASSES = ["mem2reg", "simplifycfg", "instcombine"]

def main():
    print("="*60)
    print("Quick Test - LLVM Optimization Service")
    print("="*60)
    
    # Initialize service
    print("\n1. Initializing service for RISC-V...")
    service = LLVMOptimizationService(target_arch="riscv64")
    print("   ✓ Service initialized")
    
    # Test feature extraction
    print("\n2. Testing feature extraction...")
    success, features, error = service.extract_features_from_c(TEST_CODE)
    if success:
        print(f"   ✓ Extracted {len(features)} features")
        print(f"   Sample features:")
        for key in list(features.keys())[:5]:
            print(f"     - {key}: {features[key]}")
    else:
        print(f"   ✗ Feature extraction failed: {error}")
    
    # Test ML optimization
    print(f"\n3. Testing ML optimization with passes: {TEST_PASSES}")
    success, metrics, error = service.run_ml_passes(TEST_CODE, TEST_PASSES)
    if success:
        print(f"   ✓ ML optimization successful")
        print(f"   Metrics:")
        print(f"     - Execution time: {metrics['execution_time_avg']:.6f}s")
        print(f"     - Binary size: {metrics['binary_size']} bytes")
        print(f"     - Pass count: {metrics['pass_count']}")
        print(f"     - Optimization time: {metrics['optimization_time']:.4f}s")
    else:
        print(f"   ✗ ML optimization failed: {error}")
    
    # Test standard optimizations
    print("\n4. Testing standard optimizations...")
    results = service.run_standard_optimizations(TEST_CODE, ["-O0", "-O2"])
    for opt_level, metrics in results.items():
        if metrics.get('success'):
            print(f"   ✓ {opt_level}: exec={metrics['execution_time_avg']:.6f}s, size={metrics['binary_size']}B")
        else:
            print(f"   ✗ {opt_level}: {metrics.get('error')}")
    
    # Test comparison
    print("\n5. Testing comparison...")
    comparison = service.compare_with_standard(TEST_CODE, TEST_PASSES)
    if comparison['ml_optimization'] and comparison['ml_optimization'].get('execution_time_avg'):
        print("   ✓ Comparison completed")
        if 'vs_best' in comparison['comparison']:
            best_info = comparison['comparison']['vs_best']
            print(f"   Best standard: {best_info['best_standard']}")
            print(f"   ML beats best: {best_info['ml_beats_best']}")
            print(f"   Speedup vs best: {best_info['speedup_vs_best']:.2f}x")
    else:
        print("   ✗ Comparison failed")
    
    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)

if __name__ == "__main__":
    main()
