#!/usr/bin/env python3
"""
Core LLVM Optimization Service - Handles feature extraction, ML pass application, and metrics comparison
"""

import subprocess
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import sys
import json

# Add tools directory to path for feature extraction
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'tools'))
from feature_extractor import LLVMFeatureExtractor

from utils.logger import get_logger

logger = get_logger(__name__)


class LLVMOptimizationService:
    """Core service for LLVM optimization operations with RISC-V target."""
    
    def __init__(self, target_arch: str = "riscv64", use_qemu: bool = True):
        """
        Initialize LLVM optimization service for RISC-V.
        
        Args:
            target_arch: Target architecture (riscv64, riscv32)
            use_qemu: Use QEMU emulation for cross-compiled binaries
        """
        self.target_arch = target_arch
        self.use_qemu = use_qemu
        
        # Set RISC-V specific configurations
        if target_arch == "riscv64":
            self.target_triple = "riscv64-unknown-linux-gnu"
            self.qemu_binary = "qemu-riscv64"
            self.march = "riscv64"
            self.gcc_cmd = "riscv64-linux-gnu-gcc"
            self.abi = "lp64"
        elif target_arch == "riscv32":
            self.target_triple = "riscv32-unknown-linux-gnu"
            self.qemu_binary = "qemu-riscv32"
            self.march = "riscv32"
            self.gcc_cmd = "riscv32-linux-gnu-gcc"
            self.abi = "ilp32"
        else:
            raise ValueError(f"Unsupported target architecture: {target_arch}")
        
        self.feature_extractor = LLVMFeatureExtractor()
        
        logger.info(f"LLVMOptimizationService initialized for {target_arch}")
        logger.debug(f"Target triple: {self.target_triple}")
        logger.debug(f"GCC command: {self.gcc_cmd}")
        logger.debug(f"QEMU binary: {self.qemu_binary}")
    
    def extract_features_from_c(self, c_code: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Extract features from C source code using feature_extractor module.
        
        Args:
            c_code: C source code as string
        
        Returns:
            Tuple of (success, features_dict, error_message)
        """
        try:
            # Create temporary C file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                f.write(c_code)
                c_file = Path(f.name)
            
            # Use the extract_features_from_c_source function directly
            from feature_extractor import extract_features_from_c_source
            
            # Extract features with proper RISC-V target
            features = extract_features_from_c_source(
                str(c_file),
                output_bc=None,  # Will use default .bc file
                target_arch=self.target_arch
            )
            
            # Cleanup
            c_file.unlink(missing_ok=True)
            bc_file = c_file.with_suffix('.bc')
            bc_file.unlink(missing_ok=True)
            
            logger.info(f"Successfully extracted {len(features)} features")
            return True, features, None
            
        except RuntimeError as e:
            # From compilation failure
            error = str(e)
            logger.error(f"Feature extraction error: {error}")
            return False, None, error
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return False, None, str(e)
    
    def run_ml_passes(
        self,
        c_code: str,
        ir_passes: List[str],
        machine_config: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Apply ML-generated optimization passes and measure metrics.
        
        Args:
            c_code: C source code
            ir_passes: List of LLVM IR passes to apply
            machine_config: Optional machine-level optimization config
        
        Returns:
            Tuple of (success, metrics_dict, error_message)
        """
        temp_files = []
        
        try:
            # Create temporary C file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                f.write(c_code)
                c_file = Path(f.name)
                temp_files.append(c_file)
            
            # Step 1: Compile to unoptimized bitcode
            bc_file = c_file.with_suffix('.bc')
            temp_files.append(bc_file)
            
            clang_cmd = [
                'clang',
                f'--target={self.target_triple}',
                '-O0',
                '-emit-llvm',
                '-c',
                str(c_file),
                '-o',
                str(bc_file)
            ]
            
            logger.debug(f"Compiling: {' '.join(clang_cmd)}")
            result = subprocess.run(clang_cmd, capture_output=True, timeout=30)
            
            if result.returncode != 0:
                error = result.stderr.decode() if result.stderr else "Compilation failed"
                self._cleanup_files(temp_files)
                return False, None, error
            
            # Step 2: Apply IR passes
            opt_bc_file = bc_file.with_suffix('.opt.bc')
            temp_files.append(opt_bc_file)
            
            if ir_passes and len(ir_passes) > 0:
                pass_arg = f"-passes={','.join(ir_passes)}"
            else:
                pass_arg = "-passes=default<O0>"
            
            opt_cmd = ['opt', pass_arg, str(bc_file), '-o', str(opt_bc_file)]
            
            logger.debug(f"Applying passes: {' '.join(opt_cmd)}")
            opt_start = time.perf_counter()
            result = subprocess.run(opt_cmd, capture_output=True, timeout=60)
            opt_time = time.perf_counter() - opt_start
            
            if result.returncode != 0:
                error = result.stderr.decode() if result.stderr else "Optimization failed"
                self._cleanup_files(temp_files)
                return False, None, error
            
            # Step 3: Generate assembly
            asm_file = opt_bc_file.with_suffix('.s')
            temp_files.append(asm_file)
            
            # Use consistent floating-point ABI
            llc_cmd = ['llc', f'-march={self.march}', '-mattr=+d,+f']
            
            # Apply machine config if provided
            if machine_config:
                llc_flags = self._convert_machine_config_to_flags(machine_config)
                llc_cmd.extend(llc_flags)
            
            llc_cmd.extend([str(opt_bc_file), '-o', str(asm_file)])
            
            logger.debug(f"Generating assembly: {' '.join(llc_cmd)}")
            result = subprocess.run(llc_cmd, capture_output=True, timeout=30)
            
            if result.returncode != 0:
                error = result.stderr.decode() if result.stderr else "Assembly generation failed"
                self._cleanup_files(temp_files)
                return False, None, error
            
            # Step 4: Compile to executable
            exe_file = asm_file.with_suffix('.exe')
            temp_files.append(exe_file)
            
            # Use lp64d ABI for double-precision floating point support
            gcc_cmd = [
                self.gcc_cmd,
                '-mabi=lp64d' if self.target_arch == 'riscv64' else '-mabi=ilp32d',
                '-march=rv64gc' if self.target_arch == 'riscv64' else '-march=rv32gc',
                str(asm_file),
                '-o',
                str(exe_file),
                '-static',
                '-lm'  # Link math library for sqrt and other math functions
            ]
            
            logger.debug(f"Compiling executable: {' '.join(gcc_cmd)}")
            compile_start = time.perf_counter()
            result = subprocess.run(gcc_cmd, capture_output=True, timeout=30)
            compile_time = time.perf_counter() - compile_start
            
            if result.returncode != 0:
                error = result.stderr.decode() if result.stderr else "Executable compilation failed"
                self._cleanup_files(temp_files)
                return False, None, error
            
            # Step 5: Measure performance
            exec_cmd = [self.qemu_binary, str(exe_file)] if self.use_qemu else [str(exe_file)]
            
            times = []
            num_runs = 5
            for _ in range(num_runs):
                start = time.perf_counter()
                result = subprocess.run(exec_cmd, capture_output=True, timeout=10)
                if result.returncode != 0:
                    error = "Execution failed"
                    self._cleanup_files(temp_files)
                    return False, None, error
                times.append(time.perf_counter() - start)
            
            binary_size = exe_file.stat().st_size
            
            metrics = {
                'execution_time_avg': sum(times) / len(times),
                'execution_time_min': min(times),
                'execution_time_max': max(times),
                'binary_size': binary_size,
                'optimization_time': opt_time,
                'compile_time': compile_time,
                'num_runs': num_runs,
                'ir_passes': ir_passes,
                'pass_count': len(ir_passes),
                'machine_config': machine_config or {}
            }
            
            # Cleanup
            self._cleanup_files(temp_files)
            
            logger.info(f"ML passes applied successfully. Avg execution: {metrics['execution_time_avg']:.6f}s")
            return True, metrics, None
            
        except Exception as e:
            self._cleanup_files(temp_files)
            logger.error(f"Error in run_ml_passes: {e}")
            return False, None, str(e)
    
    def run_standard_optimizations(
        self,
        c_code: str,
        opt_levels: List[str] = ["-O0", "-O1", "-O2", "-O3"]
    ) -> Dict[str, Dict]:
        """
        Run standard optimization levels for comparison.
        
        Args:
            c_code: C source code
            opt_levels: List of optimization levels to test
        
        Returns:
            Dictionary mapping opt_level to metrics
        """
        results = {}
        
        for opt_level in opt_levels:
            logger.info(f"Running standard optimization {opt_level}")
            
            temp_files = []
            
            try:
                # Create temporary C file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                    f.write(c_code)
                    c_file = Path(f.name)
                    temp_files.append(c_file)
                
                # Compile with optimization level using RISC-V GCC
                exe_file = c_file.with_suffix('.exe')
                temp_files.append(exe_file)
                
                # Use RISC-V GCC directly for better compatibility
                gcc_cmd = [
                    self.gcc_cmd,
                    '-mabi=lp64d' if self.target_arch == 'riscv64' else '-mabi=ilp32d',
                    '-march=rv64gc' if self.target_arch == 'riscv64' else '-march=rv32gc',
                    opt_level,
                    str(c_file),
                    '-o',
                    str(exe_file),
                    '-static',
                    '-lm'
                ]
                
                logger.debug(f"Compiling with {opt_level}: {' '.join(gcc_cmd)}")
                compile_start = time.perf_counter()
                result = subprocess.run(gcc_cmd, capture_output=True, timeout=30)
                compile_time = time.perf_counter() - compile_start
                
                if result.returncode != 0:
                    error = result.stderr.decode() if result.stderr else "Compilation failed"
                    results[opt_level] = {'success': False, 'error': error}
                    self._cleanup_files(temp_files)
                    continue
                
                # Measure performance
                exec_cmd = [self.qemu_binary, str(exe_file)] if self.use_qemu else [str(exe_file)]
                
                times = []
                num_runs = 5
                for _ in range(num_runs):
                    start = time.perf_counter()
                    result = subprocess.run(exec_cmd, capture_output=True, timeout=10)
                    if result.returncode != 0:
                        break
                    times.append(time.perf_counter() - start)
                
                if times:
                    binary_size = exe_file.stat().st_size
                    
                    results[opt_level] = {
                        'success': True,
                        'execution_time_avg': sum(times) / len(times),
                        'execution_time_min': min(times),
                        'execution_time_max': max(times),
                        'binary_size': binary_size,
                        'compile_time': compile_time,
                        'num_runs': len(times)
                    }
                else:
                    results[opt_level] = {'success': False, 'error': 'Execution failed'}
                
                # Cleanup
                self._cleanup_files(temp_files)
                
            except Exception as e:
                self._cleanup_files(temp_files)
                results[opt_level] = {'success': False, 'error': str(e)}
        
        logger.info(f"Standard optimizations complete. Tested {len(results)} levels")
        return results
    
    def compare_with_standard(
        self,
        c_code: str,
        ir_passes: List[str],
        machine_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Run ML passes and compare with standard optimizations.
        
        Args:
            c_code: C source code
            ir_passes: ML-generated IR passes
            machine_config: Optional machine-level config
        
        Returns:
            Comparison results dictionary
        """
        results = {
            'ml_optimization': None,
            'standard_optimizations': {},
            'comparison': {},
            'features': None
        }
        
        # Extract features
        success, features, error = self.extract_features_from_c(c_code)
        if success:
            results['features'] = features
        
        # Run ML optimization
        success, ml_metrics, error = self.run_ml_passes(c_code, ir_passes, machine_config)
        if success:
            results['ml_optimization'] = ml_metrics
        else:
            results['ml_optimization'] = {'success': False, 'error': error}
        
        # Run standard optimizations
        results['standard_optimizations'] = self.run_standard_optimizations(c_code)
        
        # Compute comparison if ML optimization succeeded
        if ml_metrics:
            ml_exec_time = ml_metrics['execution_time_avg']
            ml_binary_size = ml_metrics['binary_size']
            
            comparisons = {}
            for opt_level, std_metrics in results['standard_optimizations'].items():
                if std_metrics.get('success'):
                    std_exec_time = std_metrics['execution_time_avg']
                    std_binary_size = std_metrics['binary_size']
                    
                    comparisons[opt_level] = {
                        'speedup': std_exec_time / ml_exec_time if ml_exec_time > 0 else 0,
                        'size_reduction': 1 - (ml_binary_size / std_binary_size) if std_binary_size > 0 else 0,
                        'ml_faster': ml_exec_time < std_exec_time,
                        'ml_smaller': ml_binary_size < std_binary_size
                    }
            
            results['comparison'] = comparisons
            
            # Find best standard optimization
            best_std = None
            best_time = float('inf')
            for opt_level, metrics in results['standard_optimizations'].items():
                if metrics.get('success') and metrics['execution_time_avg'] < best_time:
                    best_time = metrics['execution_time_avg']
                    best_std = opt_level
            
            if best_std:
                results['comparison']['vs_best'] = {
                    'best_standard': best_std,
                    'ml_beats_best': ml_exec_time < best_time,
                    'speedup_vs_best': best_time / ml_exec_time if ml_exec_time > 0 else 0
                }
        
        return results
    
    def _convert_machine_config_to_flags(self, machine_config: Dict) -> List[str]:
        """
        Convert machine configuration to LLC flags.
        
        Args:
            machine_config: Dictionary with machine-level settings
        
        Returns:
            List of LLC command-line flags
        """
        flags = []
        
        # Map common machine config options to LLC flags
        if machine_config.get('fast_isel'):
            flags.append('-fast-isel')
        
        if machine_config.get('enable_machine_outliner'):
            flags.append('-enable-machine-outliner')
        
        if 'mcpu' in machine_config:
            flags.append(f"-mcpu={machine_config['mcpu']}")
        
        if 'mattr' in machine_config:
            attrs = machine_config['mattr']
            if isinstance(attrs, list):
                attrs = ','.join(attrs)
            flags.append(f"-mattr={attrs}")
        
        return flags
    
    def _cleanup_files(self, files: List[Path]):
        """Clean up temporary files."""
        for file in files:
            if file and file.exists():
                file.unlink(missing_ok=True)
