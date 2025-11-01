/**
 * LLVM Optimization Service
 * Client-side service for interacting with the simplified LLVM backend
 */

import API_ENDPOINTS from '@/config/api';

export interface OptimizationRequest {
  code?: string;
  file?: File;
  ir_passes?: string[];
  machine_config?: Record<string, any>;
  target_arch?: 'riscv64' | 'riscv32';
}

export interface OptimizationResult {
  success: boolean;
  metrics?: {
    execution_time_avg: number;
    binary_size: number;
    optimization_time: number;
    compile_time: number;
    ir_passes: string[];
    pass_count: number;
  };
  error?: string;
}

export interface FeatureExtractionResult {
  success: boolean;
  features?: Record<string, any>;
  feature_count?: number;
  error?: string;
}

export interface ComparisonResult {
  success: boolean;
  features?: Record<string, any>;
  ml_optimization?: any;
  standard_optimizations?: Record<string, any>;
  comparison?: Record<string, any>;
  error?: string;
}

/**
 * LLVM Service class for API interactions
 */
class LLVMService {
  /**
   * Extract features from C source code
   */
  async extractFeatures(code: string, target_arch: string = 'riscv64'): Promise<FeatureExtractionResult> {
    try {
      const response = await fetch(API_ENDPOINTS.features, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code, target_arch }),
      });

      return await response.json();
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Feature extraction failed',
      };
    }
  }

  /**
   * Run ML-generated optimization passes
   */
  async runOptimization(
    code: string,
    ir_passes: string[],
    machine_config: Record<string, any> = {},
    target_arch: string = 'riscv64'
  ): Promise<OptimizationResult> {
    try {
      const response = await fetch(API_ENDPOINTS.optimize, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code, ir_passes, machine_config, target_arch }),
      });

      return await response.json();
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Optimization failed',
      };
    }
  }

  /**
   * Run standard optimizations
   */
  async runStandardOptimizations(
    code: string,
    opt_levels: string[] = ['-O0', '-O1', '-O2', '-O3'],
    target_arch: string = 'riscv64'
  ): Promise<any> {
    try {
      const response = await fetch(API_ENDPOINTS.standard, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code, opt_levels, target_arch }),
      });

      return await response.json();
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Standard optimization failed',
      };
    }
  }

  /**
   * Compare ML optimization with standard optimizations
   */
  async compareOptimizations(
    code: string,
    ir_passes: string[],
    machine_config: Record<string, any> = {},
    target_arch: string = 'riscv64'
  ): Promise<ComparisonResult> {
    try {
      const response = await fetch(API_ENDPOINTS.compare, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code, ir_passes, machine_config, target_arch }),
      });

      return await response.json();
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Comparison failed',
      };
    }
  }

  /**
   * Handle file upload for optimization
   * Reads file content and calls the appropriate optimization method
   */
  async optimizeFile(
    file: File,
    ir_passes?: string[],
    machine_config?: Record<string, any>
  ): Promise<OptimizationResult> {
    try {
      // Read file content
      const code = await file.text();
      
      // Default passes if not provided
      const passes = ir_passes || ['mem2reg', 'simplifycfg', 'instcombine'];
      
      return await this.runOptimization(code, passes, machine_config);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'File optimization failed',
      };
    }
  }

  /**
   * Handle file upload for comparison
   */
  async compareFile(
    file: File,
    ir_passes?: string[],
    machine_config?: Record<string, any>
  ): Promise<ComparisonResult> {
    try {
      // Read file content
      const code = await file.text();
      
      // Default passes if not provided
      const passes = ir_passes || ['mem2reg', 'simplifycfg', 'instcombine'];
      
      return await this.compareOptimizations(code, passes, machine_config);
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'File comparison failed',
      };
    }
  }

  /**
   * Health check for the backend service
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(API_ENDPOINTS.health);
      const data = await response.json();
      return data.status === 'healthy';
    } catch {
      return false;
    }
  }

  /**
   * Get example optimization passes for UI
   */
  getExamplePasses(): string[][] {
    return [
      ['mem2reg', 'simplifycfg', 'instcombine'],
      ['mem2reg', 'loop-simplify', 'loop-rotate', 'licm', 'loop-unroll', 'simplifycfg'],
      ['mem2reg', 'gvn', 'simplifycfg', 'instcombine', 'loop-simplify', 'loop-rotate', 
       'licm', 'loop-unroll', 'sccp', 'dce', 'simplifycfg'],
    ];
  }

  /**
   * Get example C programs for testing
   */
  getExamplePrograms(): { name: string; code: string }[] {
    return [
      {
        name: 'Simple Loop',
        code: `#include <stdio.h>

int main() {
    int sum = 0;
    for (int i = 0; i < 1000; i++) {
        sum += i;
    }
    printf("Sum: %d\\n", sum);
    return 0;
}`,
      },
      {
        name: 'Matrix Multiply',
        code: `#include <stdio.h>

#define N 10

int main() {
    int a[N][N], b[N][N], c[N][N];
    
    // Initialize matrices
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            a[i][j] = i + j;
            b[i][j] = i - j;
            c[i][j] = 0;
        }
    }
    
    // Matrix multiplication
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            for (int k = 0; k < N; k++) {
                c[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    
    printf("Result: %d\\n", c[N-1][N-1]);
    return 0;
}`,
      },
      {
        name: 'Fibonacci',
        code: `#include <stdio.h>

int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main() {
    int n = 20;
    int result = fibonacci(n);
    printf("Fibonacci(%d) = %d\\n", n, result);
    return 0;
}`,
      },
    ];
  }
}

// Export singleton instance
export const llvmService = new LLVMService();

// Export types
export type { OptimizationRequest, OptimizationResult, FeatureExtractionResult, ComparisonResult };
