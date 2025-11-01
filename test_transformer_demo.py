#!/usr/bin/env python3
"""
Simple demonstration of transformer model usage for pass prediction.
This shows how the model is integrated into the LLVM optimization service.
"""

import sys
from pathlib import Path

# Add project directories to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'iris-website' / 'backend'))
sys.path.insert(0, str(project_root / 'tools'))
sys.path.insert(0, str(project_root))

from services.llvm_optimization_service import LLVMOptimizationService

# Sample C programs
BUBBLE_SORT_CODE = """
#include <stdio.h>

void bubble_sort(int arr[], int n) {
    for (int i = 0; i < n-1; i++) {
        for (int j = 0; j < n-i-1; j++) {
            if (arr[j] > arr[j+1]) {
                int temp = arr[j];
                arr[j] = arr[j+1];
                arr[j+1] = temp;
            }
        }
    }
}

int main() {
    int arr[] = {64, 34, 25, 12, 22, 11, 90};
    int n = sizeof(arr)/sizeof(arr[0]);
    bubble_sort(arr, n);
    
    for (int i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
    return 0;
}
"""

QUICKSORT_CODE = """
#include <stdio.h>

void quickSort(int arr[], int left, int right) {
    int i = left, j = right;
    int tmp;
    int pivot = arr[(left + right) / 2];
    
    while (i <= j) {
        while (arr[i] < pivot)
            i++;
        while (arr[j] > pivot)
            j--;
        if (i <= j) {
            tmp = arr[i];
            arr[i] = arr[j];
            arr[j] = tmp;
            i++;
            j--;
        }
    }
    
    if (left < j)
        quickSort(arr, left, j);
    if (i < right)
        quickSort(arr, i, right);
}

int main() {
    int arr[] = {10, 7, 8, 9, 1, 5};
    int n = sizeof(arr)/sizeof(arr[0]);
    quickSort(arr, 0, n-1);
    
    for (int i = 0; i < n; i++)
        printf("%d ", arr[i]);
    return 0;
}
"""

MATRIX_MULT_CODE = """
#include <stdio.h>

#define N 50

void matrix_multiply(int A[N][N], int B[N][N], int C[N][N]) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            C[i][j] = 0;
            for (int k = 0; k < N; k++) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
}

int main() {
    static int A[N][N], B[N][N], C[N][N];
    
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            A[i][j] = i + j;
            B[i][j] = i - j;
        }
    }
    
    matrix_multiply(A, B, C);
    printf("Result: %d\\n", C[0][0]);
    return 0;
}
"""

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f" {title}")
    print('=' * 80)

def test_transformer_prediction(service, code_name, code, opt_hint="O_0"):
    """Test transformer prediction for a given code sample."""
    print(f"\n--- Testing: {code_name} (Optimization hint: {opt_hint}) ---")
    
    # Extract features
    print("1. Extracting features...")
    success, features, error = service.extract_features_from_c(code)
    if not success:
        print(f"   ✗ Feature extraction failed: {error}")
        return
    
    print(f"   ✓ Extracted {len(features)} features")
    
    # Predict passes using transformer
    print("2. Predicting passes with transformer...")
    success, passes, error = service.predict_passes_with_transformer(
        features, 
        opt_level=opt_hint,
        beam_size=5
    )
    
    if not success:
        print(f"   ✗ Pass prediction failed: {error}")
        return
    
    print(f"   ✓ Predicted {len(passes)} optimization passes")
    print(f"   First 10 passes: {passes[:10]}")
    
    # Run optimization with predicted passes
    print("3. Running optimization with predicted passes...")
    success, metrics, error = service.run_ml_passes(
        code,
        ir_passes=passes,  # Use the predicted passes
        use_transformer=False  # Don't predict again, we already have passes
    )
    
    if not success:
        print(f"   ✗ Optimization failed: {error}")
        return
    
    print(f"   ✓ Optimization successful!")
    print(f"   - Execution time: {metrics['execution_time_avg']:.6f}s")
    print(f"   - Binary size: {metrics['binary_size']} bytes")
    print(f"   - Optimization time: {metrics['optimization_time']:.4f}s")
    
    return metrics, passes

def compare_with_defaults(service, code_name, code):
    """Compare transformer predictions with default passes."""
    print(f"\n--- Comparing Transformer vs Default Passes for {code_name} ---")
    
    # Default passes (commonly used)
    default_passes = ['mem2reg', 'simplifycfg', 'instcombine', 'reassociate', 
                     'gvn', 'licm', 'dce', 'adce']
    
    # Run with default passes
    print("\n1. Running with default passes...")
    success, default_metrics, error = service.run_ml_passes(
        code,
        ir_passes=default_passes,
        use_transformer=False
    )
    
    if success:
        print(f"   Default passes execution time: {default_metrics['execution_time_avg']:.6f}s")
        print(f"   Default passes binary size: {default_metrics['binary_size']} bytes")
    
    # Run with transformer for different optimization levels
    opt_levels = ["O_0", "O_1", "O_2", "O_3"]
    best_time = float('inf')
    best_level = None
    best_passes = None
    
    print("\n2. Testing transformer with different optimization hints...")
    for opt_level in opt_levels:
        print(f"\n   Testing {opt_level}:")
        success, metrics, error = service.run_ml_passes(
            code,
            ir_passes=None,  # Let transformer predict
            use_transformer=True,
            opt_level_hint=opt_level
        )
        
        if success:
            print(f"     - Execution time: {metrics['execution_time_avg']:.6f}s")
            print(f"     - Binary size: {metrics['binary_size']} bytes")
            print(f"     - Passes used: {metrics.get('pass_count', 'N/A')}")
            
            if metrics['execution_time_avg'] < best_time:
                best_time = metrics['execution_time_avg']
                best_level = opt_level
                best_passes = metrics.get('ir_passes', [])
    
    if best_level and default_metrics:
        print(f"\n3. Summary:")
        print(f"   Best transformer optimization: {best_level}")
        speedup = default_metrics['execution_time_avg'] / best_time
        print(f"   Speedup vs default passes: {speedup:.2f}x")
        print(f"   Best passes (first 10): {best_passes[:10]}")

def main():
    """Main demonstration function."""
    print_section("Transformer Model Pass Prediction Demo")
    
    print("\nInitializing LLVM Optimization Service...")
    try:
        service = LLVMOptimizationService(target_arch="riscv64")
        
        if service.transformer_model is None:
            print("✗ Transformer model not loaded. Please ensure model file exists at:")
            print("  models_seqgen/passgen_transformer_model_best.pth")
            print("  or")
            print("  models_seqgen/passgen_transformer_model_final.pth")
            return
        
        print("✓ Service initialized with transformer model")
        print(f"  - Target architecture: {service.target_arch}")
        print(f"  - Vocabulary size: {len(service.joint_pass_vocab)} passes")
        print(f"  - Feature count: {len(service.feature_keys)} features")
        
    except Exception as e:
        print(f"✗ Failed to initialize service: {e}")
        return
    
    # Test different programs
    test_programs = [
        ("Bubble Sort", BUBBLE_SORT_CODE, "O_2"),
        ("Quick Sort", QUICKSORT_CODE, "O_2"),
        ("Matrix Multiplication", MATRIX_MULT_CODE, "O_3")
    ]
    
    print_section("Testing Transformer Predictions")
    
    all_results = []
    for name, code, opt_hint in test_programs:
        result = test_transformer_prediction(service, name, code, opt_hint)
        if result:
            metrics, passes = result
            all_results.append((name, metrics, passes))
    
    # Compare with defaults for one example
    print_section("Comparison with Default Optimization Passes")
    compare_with_defaults(service, "Quick Sort", QUICKSORT_CODE)
    
    # Summary
    if all_results:
        print_section("Summary of All Tests")
        print("\n{:<25} {:<15} {:<15} {:<10}".format(
            "Program", "Exec Time (s)", "Binary Size", "Pass Count"
        ))
        print("-" * 70)
        for name, metrics, passes in all_results:
            print("{:<25} {:<15.6f} {:<15} {:<10}".format(
                name,
                metrics['execution_time_avg'],
                metrics['binary_size'],
                len(passes)
            ))
    
    print_section("Demo Complete!")
    print("\nThe transformer model successfully predicted optimization passes")
    print("tailored for RISC-V architecture based on program features.")
    print("\nTo use in production, start the API server:")
    print("  cd iris-website/backend")
    print("  python3 app_simplified.py")

if __name__ == "__main__":
    main()
