#!/usr/bin/env python3
"""
Comparison API - Compare ML-generated optimizations vs standard optimization levels
Reuses existing functions from tools folder
"""

import os
import sys
import json
import time
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add tools directory to path
tools_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))
sys.path.insert(0, tools_dir)

# Import existing tools
from feature_extractor import LLVMFeatureExtractor, extract_features_from_c_source
from hybrid_sequence_generator import HybridSequenceGenerator
from machine_flags_generator_v2 import MachineFlagsGeneratorV2


class OptimizationComparator:
    """
    Compare ML-generated optimizations against standard optimization levels.
    Reuses functions from generate_training_data_hybrid.py
    """
    
    def __init__(self, target_arch: str = "riscv64", use_qemu: bool = True):
        """
        Initialize comparator.
        
        Args:
            target_arch: Target architecture (riscv64 or riscv32)
            use_qemu: Use QEMU for execution (required for cross-compilation)
        """
        self.target_arch = target_arch
        self.use_qemu = use_qemu
        
        # Set target-specific configuration
        if target_arch == "riscv64":
            self.target_triple = "riscv64-unknown-linux-gnu"
            self.qemu_binary = "qemu-riscv64"
            self.march = "riscv64"
            self.gcc_cmd = "riscv64-linux-gnu-gcc"
        elif target_arch == "riscv32":
            self.target_triple = "riscv32-unknown-linux-gnu"
            self.qemu_binary = "qemu-riscv32"
            self.march = "riscv32"
            self.gcc_cmd = "riscv32-linux-gnu-gcc"
        else:
            raise ValueError(f"Unsupported target architecture: {target_arch}")
        
        self.feature_extractor = LLVMFeatureExtractor()
        self.hybrid_generator = HybridSequenceGenerator()
        self.machine_generator = MachineFlagsGeneratorV2(target_arch=target_arch)
    
    def compile_to_bitcode(self, c_file: Path, optimization: str = "-O0") -> Path:
        """Compile C source to LLVM bitcode (reused logic)."""
        bc_file = c_file.with_suffix('.bc')
        
        clang_cmd = ['clang', '--target=' + self.target_triple]
        clang_cmd.extend([optimization, '-emit-llvm', '-c', str(c_file), '-o', str(bc_file)])
        
        try:
            subprocess.run(clang_cmd, check=True, capture_output=True, timeout=30)
            return bc_file
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"Failed to compile {c_file}: {str(e)}")
    
    def apply_ir_passes(self, bc_file: Path, ir_passes: List[str]) -> Path:
        """Apply IR-level optimization passes."""
        opt_bc_file = bc_file.with_suffix('.opt.bc')
        
        if ir_passes and len(ir_passes) > 0:
            pass_arg = f"-passes={','.join(ir_passes)}"
        else:
            pass_arg = "-passes=default<O0>"
        
        try:
            subprocess.run(
                ['opt', pass_arg, str(bc_file), '-o', str(opt_bc_file)],
                check=True,
                capture_output=True,
                timeout=60
            )
            return opt_bc_file
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"Failed to apply IR passes: {str(e)}")
    
    def generate_assembly(self, bc_file: Path, machine_config: Dict[str, Any] = None) -> Path:
        """Generate assembly with machine-level optimizations."""
        asm_file = bc_file.with_suffix('.s')
        
        llc_cmd = ['llc', f'-march={self.march}']
        
        # Apply machine config if provided
        if machine_config:
            llc_flags = self.machine_generator.config_to_llc_flags(machine_config, abi=None)
            llc_cmd.extend(llc_flags)
        
        llc_cmd.extend([str(bc_file), '-o', str(asm_file)])
        
        try:
            subprocess.run(llc_cmd, check=True, capture_output=True, timeout=30)
            return asm_file
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"Failed to generate assembly: {str(e)}")
    
    def compile_to_executable(self, asm_file: Path) -> Path:
        """Compile assembly to executable."""
        exe_file = asm_file.with_suffix('.exe')
        
        try:
            subprocess.run(
                [self.gcc_cmd, str(asm_file), '-o', str(exe_file), '-static'],
                check=True,
                capture_output=True,
                timeout=30
            )
            return exe_file
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"Failed to compile to executable: {str(e)}")
    
    def measure_performance(self, exe_file: Path, num_runs: int = 3) -> Dict[str, Any]:
        """Measure execution performance."""
        if not exe_file.exists():
            raise RuntimeError(f"Executable not found: {exe_file}")
        
        times = []
        exec_cmd = [self.qemu_binary, str(exe_file)] if self.use_qemu else [str(exe_file)]
        
        for _ in range(num_runs):
            try:
                start = time.perf_counter()
                result = subprocess.run(exec_cmd, check=True, capture_output=True, timeout=10)
                end = time.perf_counter()
                times.append(end - start)
            except subprocess.TimeoutExpired:
                raise RuntimeError("Execution timeout - program took too long")
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Execution failed: {e.stderr.decode()}")
        
        binary_size = exe_file.stat().st_size
        
        return {
            'execution_time_avg': sum(times) / len(times),
            'execution_time_min': min(times),
            'execution_time_max': max(times),
            'execution_times': times,
            'binary_size': binary_size,
            'num_runs': num_runs
        }
    
    def compile_with_standard_opt(self, c_file: Path, opt_level: str) -> Dict[str, Any]:
        """
        Compile with standard optimization level (-O0, -O1, -O2, -O3).
        Returns comprehensive metrics.
        """
        compile_start = time.perf_counter()
        
        try:
            # Step 1: Compile to bitcode with optimization
            bc_file = self.compile_to_bitcode(c_file, optimization=opt_level)
            
            # Step 2: Generate assembly
            asm_file = self.generate_assembly(bc_file)
            
            # Step 3: Compile to executable
            exe_file = self.compile_to_executable(asm_file)
            
            compile_time = time.perf_counter() - compile_start
            
            # Step 4: Measure performance
            perf_metrics = self.measure_performance(exe_file)
            
            # Cleanup
            bc_file.unlink(missing_ok=True)
            asm_file.unlink(missing_ok=True)
            exe_file.unlink(missing_ok=True)
            
            return {
                'success': True,
                'opt_level': opt_level,
                'compile_time': compile_time,
                **perf_metrics,
                'error': None
            }
        
        except Exception as e:
            return {
                'success': False,
                'opt_level': opt_level,
                'compile_time': None,
                'execution_time_avg': None,
                'binary_size': None,
                'error': str(e)
            }
    
    def compile_with_ml_passes(self, c_file: Path, ir_passes: List[str], 
                                machine_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Compile with ML-generated passes and machine config.
        Returns comprehensive metrics.
        """
        compile_start = time.perf_counter()
        
        try:
            # Step 1: Compile to unoptimized bitcode
            bc_file = self.compile_to_bitcode(c_file, optimization="-O0")
            
            # Step 2: Apply IR passes
            opt_bc_file = self.apply_ir_passes(bc_file, ir_passes)
            
            # Step 3: Generate assembly with machine config
            asm_file = self.generate_assembly(opt_bc_file, machine_config)
            
            # Step 4: Compile to executable
            exe_file = self.compile_to_executable(asm_file)
            
            compile_time = time.perf_counter() - compile_start
            
            # Step 5: Measure performance
            perf_metrics = self.measure_performance(exe_file)
            
            # Cleanup
            bc_file.unlink(missing_ok=True)
            opt_bc_file.unlink(missing_ok=True)
            asm_file.unlink(missing_ok=True)
            exe_file.unlink(missing_ok=True)
            
            return {
                'success': True,
                'optimization_type': 'ml_generated',
                'ir_passes': ir_passes,
                'machine_config': machine_config,
                'num_ir_passes': len(ir_passes),
                'compile_time': compile_time,
                **perf_metrics,
                'error': None
            }
        
        except Exception as e:
            return {
                'success': False,
                'optimization_type': 'ml_generated',
                'ir_passes': ir_passes,
                'machine_config': machine_config,
                'compile_time': None,
                'execution_time_avg': None,
                'binary_size': None,
                'error': str(e)
            }
    
    def compare_all(self, c_source: str, ir_passes: List[str], 
                    machine_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run comprehensive comparison: ML passes vs all standard optimization levels.
        
        Args:
            c_source: C source code as string
            ir_passes: ML-generated IR pass sequence
            machine_config: ML-generated machine configuration
        
        Returns:
            Complete comparison results with all metrics
        """
        overall_start = time.perf_counter()
        
        # Create temporary file for C source
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as tmp:
            tmp.write(c_source)
            tmp_path = Path(tmp.name)
        
        try:
            results = {
                'target_arch': self.target_arch,
                'ml_optimization': None,
                'standard_optimizations': {},
                'comparison_summary': {},
                'total_time': None
            }
            
            # Run ML optimization
            ml_result = self.compile_with_ml_passes(tmp_path, ir_passes, machine_config)
            results['ml_optimization'] = ml_result
            
            # Run standard optimizations
            for opt_level in ['-O0', '-O1', '-O2', '-O3']:
                std_result = self.compile_with_standard_opt(tmp_path, opt_level)
                results['standard_optimizations'][opt_level] = std_result
            
            # Generate comparison summary
            if ml_result['success']:
                ml_time = ml_result['execution_time_avg']
                ml_size = ml_result['binary_size']
                
                summary = {
                    'ml_beats': [],
                    'speedup_vs': {},
                    'size_reduction_vs': {},
                    'best_standard': None,
                    'best_standard_time': None
                }
                
                best_std_time = float('inf')
                best_std_level = None
                
                for opt_level, std_result in results['standard_optimizations'].items():
                    if std_result['success']:
                        std_time = std_result['execution_time_avg']
                        std_size = std_result['binary_size']
                        
                        # Track best standard optimization
                        if std_time < best_std_time:
                            best_std_time = std_time
                            best_std_level = opt_level
                        
                        # Calculate speedup
                        speedup = (std_time - ml_time) / std_time * 100 if std_time > 0 else 0
                        size_reduction = (std_size - ml_size) / std_size * 100 if std_size > 0 else 0
                        
                        summary['speedup_vs'][opt_level] = speedup
                        summary['size_reduction_vs'][opt_level] = size_reduction
                        
                        if ml_time < std_time:
                            summary['ml_beats'].append(opt_level)
                
                summary['best_standard'] = best_std_level
                summary['best_standard_time'] = best_std_time
                summary['beats_best_standard'] = ml_time < best_std_time if best_std_time != float('inf') else False
                
                results['comparison_summary'] = summary
            
            results['total_time'] = time.perf_counter() - overall_start
            
            return results
        
        finally:
            # Cleanup temporary file
            tmp_path.unlink(missing_ok=True)


def create_comparison_routes(app, comparator: OptimizationComparator):
    """Add comparison routes to Flask app."""
    from flask import request, jsonify
    
    @app.route('/api/compare', methods=['POST'])
    def compare_optimizations():
        """
        Compare ML-generated optimizations vs standard levels.
        
        Expected JSON input:
        {
            "source_code": "C source code string",
            "ir_passes": ["pass1", "pass2", ...],
            "machine_config": {"flag1": value1, ...}  // optional
        }
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No JSON data provided'
                }), 400
            
            source_code = data.get('source_code')
            ir_passes = data.get('ir_passes', [])
            machine_config = data.get('machine_config')
            
            if not source_code:
                return jsonify({
                    'success': False,
                    'error': 'source_code is required'
                }), 400
            
            if not ir_passes or len(ir_passes) == 0:
                return jsonify({
                    'success': False,
                    'error': 'ir_passes list is required and cannot be empty'
                }), 400
            
            # Run comparison
            results = comparator.compare_all(source_code, ir_passes, machine_config)
            
            return jsonify({
                'success': True,
                'results': results
            }), 200
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Comparison failed: {str(e)}'
            }), 500
    
    @app.route('/api/compare/file', methods=['POST'])
    def compare_optimizations_file():
        """
        Compare optimizations from uploaded C file.
        
        Form data:
        - source_file: C source file
        - ir_passes: JSON string of pass list
        - machine_config: JSON string of config (optional)
        """
        try:
            if 'source_file' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No source file provided'
                }), 400
            
            file = request.files['source_file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'No selected file'
                }), 400
            
            # Read source code
            source_code = file.read().decode('utf-8')
            
            # Parse IR passes
            ir_passes_json = request.form.get('ir_passes')
            if not ir_passes_json:
                return jsonify({
                    'success': False,
                    'error': 'ir_passes is required'
                }), 400
            
            ir_passes = json.loads(ir_passes_json)
            
            # Parse machine config (optional)
            machine_config = None
            machine_config_json = request.form.get('machine_config')
            if machine_config_json:
                machine_config = json.loads(machine_config_json)
            
            # Run comparison
            results = comparator.compare_all(source_code, ir_passes, machine_config)
            
            return jsonify({
                'success': True,
                'results': results
            }), 200
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Comparison failed: {str(e)}'
            }), 500
