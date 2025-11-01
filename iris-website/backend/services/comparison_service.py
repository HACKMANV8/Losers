#!/usr/bin/env python3
"""
Comparison Service - Handles comparison between ML and standard optimizations
Refactored from compare_api.py
"""

import time
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

from config import CompilationConfig
from utils.logger import get_logger
from .compilation_service import CompilationService

logger = get_logger(__name__)


class ComparisonService:
    """Service for comparing ML-generated optimizations vs standard levels"""
    
    def __init__(self, target_arch: str = CompilationConfig.DEFAULT_TARGET_ARCH):
        """
        Initialize comparison service.
        
        Args:
            target_arch: Target architecture
        """
        self.target_arch = target_arch
        self.compilation_service = CompilationService(target_arch)
        logger.info(f"ComparisonService initialized for {target_arch}")
    
    def compile_with_ml_passes(
        self,
        c_file: Path,
        ir_passes: List[str],
        machine_config: Optional[Dict] = None
    ) -> Dict:
        """
        Compile with ML-generated passes and machine config.
        
        Args:
            c_file: Path to C source file
            ir_passes: ML-generated IR pass sequence
            machine_config: Optional machine-level configuration
        
        Returns:
            Result dictionary with metrics
        """
        compile_start = time.perf_counter()
        result = {
            'success': False,
            'optimization_type': 'ml_generated',
            'ir_passes': ir_passes,
            'machine_config': machine_config,
            'num_ir_passes': len(ir_passes),
            'compile_time': None,
            'execution_time_avg': None,
            'binary_size': None,
            'error': None
        }
        
        try:
            # Step 1: Compile to unoptimized bitcode
            success, bc_file, error = self.compilation_service.compile_to_bitcode(
                c_file, optimization="-O0"
            )
            if not success:
                result['error'] = error
                return result
            
            # Step 2: Apply IR passes
            success, opt_bc_file, error = self.compilation_service.apply_ir_passes(
                bc_file, ir_passes
            )
            if not success:
                result['error'] = error
                bc_file.unlink(missing_ok=True)
                return result
            
            # Step 3: Generate assembly
            success, asm_file, error = self.compilation_service.generate_assembly(
                opt_bc_file, machine_config
            )
            if not success:
                result['error'] = error
                bc_file.unlink(missing_ok=True)
                opt_bc_file.unlink(missing_ok=True)
                return result
            
            # Step 4: Compile to executable
            success, exe_file, error = self.compilation_service.compile_to_executable(asm_file)
            if not success:
                result['error'] = error
                bc_file.unlink(missing_ok=True)
                opt_bc_file.unlink(missing_ok=True)
                asm_file.unlink(missing_ok=True)
                return result
            
            compile_time = time.perf_counter() - compile_start
            
            # Step 5: Benchmark
            success, metrics, error = self.compilation_service.benchmark_executable(exe_file)
            if not success:
                result['error'] = error
                result['compile_time'] = compile_time
            else:
                result.update({
                    'success': True,
                    'compile_time': compile_time,
                    **metrics
                })
            
            # Cleanup
            bc_file.unlink(missing_ok=True)
            opt_bc_file.unlink(missing_ok=True)
            asm_file.unlink(missing_ok=True)
            exe_file.unlink(missing_ok=True)
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"ML compilation failed: {e}")
        
        return result
    
    def compare_all(
        self,
        c_source: str,
        ir_passes: List[str],
        machine_config: Optional[Dict] = None
    ) -> Dict:
        """
        Run comprehensive comparison: ML passes vs all standard optimization levels.
        
        Args:
            c_source: C source code as string
            ir_passes: ML-generated IR pass sequence
            machine_config: Optional ML-generated machine configuration
        
        Returns:
            Complete comparison results with all metrics
        """
        overall_start = time.perf_counter()
        
        # Create temporary file for C source
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.c',
            delete=False,
            dir=CompilationConfig.TEMP_DIR if Path(CompilationConfig.TEMP_DIR).exists() else None
        ) as tmp:
            tmp.write(c_source)
            tmp_path = Path(tmp.name)
        
        try:
            logger.info(f"Starting comparison for {tmp_path.name}")
            
            results = {
                'target_arch': self.target_arch,
                'ml_optimization': None,
                'standard_optimizations': {},
                'comparison_summary': {},
                'total_time': None
            }
            
            # Run ML optimization
            logger.info("Running ML optimization...")
            ml_result = self.compile_with_ml_passes(tmp_path, ir_passes, machine_config)
            results['ml_optimization'] = ml_result
            
            # Run standard optimizations
            for opt_level in CompilationConfig.STANDARD_OPT_LEVELS:
                logger.info(f"Running standard optimization: {opt_level}")
                std_result = self.compilation_service.compile_with_standard_opt(tmp_path, opt_level)
                results['standard_optimizations'][opt_level] = std_result
            
            # Generate comparison summary
            if ml_result['success']:
                results['comparison_summary'] = self._generate_comparison_summary(
                    ml_result,
                    results['standard_optimizations']
                )
            
            results['total_time'] = time.perf_counter() - overall_start
            logger.info(f"Comparison complete in {results['total_time']:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Comparison failed: {e}")
            return {
                'target_arch': self.target_arch,
                'error': str(e),
                'total_time': time.perf_counter() - overall_start
            }
            
        finally:
            # Cleanup temporary file
            tmp_path.unlink(missing_ok=True)
    
    def _generate_comparison_summary(
        self,
        ml_result: Dict,
        standard_results: Dict
    ) -> Dict:
        """
        Generate comparison summary statistics.
        
        Args:
            ml_result: ML optimization result
            standard_results: Dictionary of standard optimization results
        
        Returns:
            Comparison summary dictionary
        """
        ml_time = ml_result.get('execution_time_avg', float('inf'))
        ml_size = ml_result.get('binary_size', float('inf'))
        
        summary = {
            'ml_beats': [],
            'speedup_vs': {},
            'size_reduction_vs': {},
            'best_standard': None,
            'best_standard_time': None,
            'beats_best_standard': False
        }
        
        best_std_time = float('inf')
        best_std_level = None
        
        for opt_level, std_result in standard_results.items():
            if std_result.get('success'):
                std_time = std_result.get('execution_time_avg', float('inf'))
                std_size = std_result.get('binary_size', float('inf'))
                
                # Track best standard optimization
                if std_time < best_std_time:
                    best_std_time = std_time
                    best_std_level = opt_level
                
                # Calculate speedup and size reduction
                if std_time > 0:
                    speedup = (std_time - ml_time) / std_time * 100
                    summary['speedup_vs'][opt_level] = round(speedup, 2)
                
                if std_size > 0:
                    size_reduction = (std_size - ml_size) / std_size * 100
                    summary['size_reduction_vs'][opt_level] = round(size_reduction, 2)
                
                # Track which levels ML beats
                if ml_time < std_time:
                    summary['ml_beats'].append(opt_level)
        
        summary['best_standard'] = best_std_level
        summary['best_standard_time'] = best_std_time
        summary['beats_best_standard'] = ml_time < best_std_time if best_std_time != float('inf') else False
        
        return summary
    
    def quick_compare(
        self,
        c_file: Path,
        ir_passes: List[str]
    ) -> Dict:
        """
        Quick comparison against -O3 only (faster than full comparison).
        
        Args:
            c_file: Path to C source file
            ir_passes: ML-generated IR pass sequence
        
        Returns:
            Quick comparison results
        """
        logger.info("Running quick comparison (ML vs -O3)")
        
        # Run ML compilation
        ml_result = self.compile_with_ml_passes(c_file, ir_passes)
        
        # Run -O3 compilation
        o3_result = self.compilation_service.compile_with_standard_opt(c_file, '-O3')
        
        results = {
            'ml_optimization': ml_result,
            'o3_optimization': o3_result,
            'comparison': {}
        }
        
        if ml_result['success'] and o3_result['success']:
            ml_time = ml_result['execution_time_avg']
            o3_time = o3_result['execution_time_avg']
            
            results['comparison'] = {
                'speedup_percent': round((o3_time - ml_time) / o3_time * 100, 2),
                'ml_faster': ml_time < o3_time,
                'time_difference': abs(ml_time - o3_time)
            }
        
        return results
