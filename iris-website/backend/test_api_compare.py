#!/usr/bin/env python3
"""
Test script for /api/compare endpoint
Tests the complete comparison workflow
"""

import requests
import json
import time
from pathlib import Path

# Backend URL
API_URL = "http://localhost:5001/api/compare"

# Test programs
TEST_PROGRAMS = {
    "simple": """
#include <stdio.h>

int main() {
    int x = 42;
    printf("%d\\n", x);
    return 0;
}
""",
    "fibonacci": """
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
""",
    "loops": """
#include <stdio.h>

int main() {
    int sum = 0;
    for (int i = 0; i < 1000; i++) {
        if (i % 2 == 0) {
            sum += i;
        } else {
            sum -= i;
        }
    }
    printf("%d\\n", sum);
    return 0;
}
""",
    "invalid_syntax": """
#include <stdio.h>

int main() {
    this is not valid C code!!!
    return 0;
}
"""
}

def test_comparison(test_name, source_code, predicted_passes, opt_levels=None, num_runs=3):
    """Test the /api/compare endpoint"""
    print("\n" + "=" * 70)
    print(f"TEST: {test_name}")
    print("=" * 70)
    
    # Prepare request
    files = {
        'source_file': ('test.c', source_code, 'text/plain')
    }
    
    data = {
        'predicted_passes': json.dumps(predicted_passes),
        'num_runs': num_runs
    }
    
    if opt_levels:
        data['optimization_levels'] = json.dumps(opt_levels)
    
    print(f"Predicted passes: {predicted_passes}")
    print(f"Optimization levels: {opt_levels or 'default'}")
    print(f"Number of runs: {num_runs}")
    
    # Send request
    print("\nSending request to API...")
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, files=files, data=data, timeout=120)
        request_time = time.time() - start_time
        
        print(f"Response received in {request_time:.2f}s")
        print(f"Status code: {response.status_code}")
        
        # Parse response
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            print("\n✅ SUCCESS!")
            
            # Display results
            print("\n" + "-" * 70)
            print("COMPILATION RESULTS")
            print("-" * 70)
            
            # ML-predicted
            ml_result = result.get('ml_predicted', {})
            print(f"\nML-Predicted:")
            if ml_result.get('success'):
                print(f"  ✅ Binary: {ml_result['binary_size_human']} ({ml_result['binary_size']} bytes)")
                print(f"  ✅ Runtime: {ml_result['runtime_mean']:.4f}s ± {ml_result['runtime_std']:.4f}s")
                print(f"  ✅ Passes: {', '.join(ml_result['passes_used'])}")
            else:
                print(f"  ❌ Failed: {ml_result.get('error')}")
            
            # LLVM optimizations
            for opt in ['o0', 'o2', 'o3', 'oz']:
                key = f'llvm_{opt}'
                if key in result:
                    opt_result = result[key]
                    print(f"\nLLVM -{opt.upper()}:")
                    if opt_result.get('success'):
                        print(f"  ✅ Binary: {opt_result['binary_size_human']} ({opt_result['binary_size']} bytes)")
                        print(f"  ✅ Runtime: {opt_result['runtime_mean']:.4f}s ± {opt_result['runtime_std']:.4f}s")
                    else:
                        print(f"  ❌ Failed: {opt_result.get('error')}")
            
            # Improvements
            improvements = result.get('improvements', {})
            if improvements:
                print("\n" + "-" * 70)
                print("IMPROVEMENTS")
                print("-" * 70)
                
                for comparison, metrics in improvements.items():
                    opt_name = comparison.replace('vs_', '-').upper()
                    print(f"\nvs {opt_name}:")
                    print(f"  Binary Size: {metrics['binary_size_reduction_percent']:+.2f}% " + 
                          f"({metrics['binary_size_reduction_bytes']:+d} bytes)")
                    print(f"  Runtime: {metrics['runtime_reduction_percent']:+.2f}% " +
                          f"({metrics['runtime_reduction_seconds']:+.4f}s)")
                    print(f"  Winners: Binary={metrics['winner_binary']}, Runtime={metrics['winner_runtime']}")
            
            # Summary
            summary = result.get('summary', {})
            if summary:
                print("\n" + "-" * 70)
                print("SUMMARY")
                print("-" * 70)
                
                ml_wins = summary.get('ml_wins', {})
                print(f"\nML Wins:")
                print(f"  Binary Size: {ml_wins.get('binary_size', 0)} wins")
                print(f"  Runtime: {ml_wins.get('runtime', 0)} wins")
                print(f"  Total: {ml_wins.get('total', 0)}/{ml_wins.get('out_of', 0)}")
                
                best_binary = summary.get('best_binary_size')
                best_runtime = summary.get('best_runtime')
                if best_binary:
                    print(f"\nBest Binary Size: {best_binary['method']} ({best_binary['size_human']})")
                if best_runtime:
                    print(f"Best Runtime: {best_runtime['method']} ({best_runtime['time']:.4f}s)")
            
            print(f"\nTotal processing time: {result.get('total_processing_time', 0):.2f}s")
            
        else:
            print(f"\n❌ FAILED!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR!")
        print("Make sure the Flask backend is running on http://localhost:5001")
        print("Start it with: python app.py")
    except requests.exceptions.Timeout:
        print("\n❌ TIMEOUT!")
        print("Request took too long (>120s)")
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🚀" * 35)
    print("API COMPARE ENDPOINT TEST SUITE")
    print("🚀" * 35)
    
    # Test 1: Simple program
    test_comparison(
        test_name="Simple Program",
        source_code=TEST_PROGRAMS["simple"],
        predicted_passes=["mem2reg", "simplifycfg"],
        opt_levels=["-O2", "-O3"],
        num_runs=3
    )
    
    # Test 2: Fibonacci (recursive)
    test_comparison(
        test_name="Fibonacci (Recursive)",
        source_code=TEST_PROGRAMS["fibonacci"],
        predicted_passes=["mem2reg", "inline", "gvn", "simplifycfg", "dce"],
        opt_levels=["-O0", "-O2", "-O3"],
        num_runs=5
    )
    
    # Test 3: Loops and conditionals
    test_comparison(
        test_name="Loops and Conditionals",
        source_code=TEST_PROGRAMS["loops"],
        predicted_passes=["mem2reg", "loop-unroll", "gvn", "simplifycfg"],
        num_runs=3
    )
    
    # Test 4: Error handling - invalid syntax
    test_comparison(
        test_name="Error Handling (Invalid Syntax)",
        source_code=TEST_PROGRAMS["invalid_syntax"],
        predicted_passes=["mem2reg"],
        opt_levels=["-O2"],
        num_runs=3
    )
    
    print("\n" + "=" * 70)
    print("✅ TEST SUITE COMPLETE!")
    print("=" * 70)

if __name__ == "__main__":
    main()
