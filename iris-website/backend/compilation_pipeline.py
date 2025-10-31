"""
Compilation Pipeline for ML-Predicted Pass Sequences
Reuses existing tools from /home/yash/hackman/tools
"""

import os
import sys
import time
import tempfile
import subprocess
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add tools directory to path to import existing utilities
tools_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))
sys.path.insert(0, tools_dir)

# Import existing compilation utilities
from generate_training_data_hybrid import HybridTrainingDataGenerator


class CompilationPipeline:
    """
    Wrapper around existing compilation tools for API usage.
    Compiles C programs with ML-predicted passes targeting RISC-V.
    """
    
    def __init__(self, target_arch: str = "riscv64", use_qemu: bool = True):
        """
        Initialize compilation pipeline.
        
        Args:
            target_arch: Target architecture (riscv64, riscv32, or native)
            use_qemu: Use QEMU for execution measurement
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
            self.target_triple = None
            self.qemu_binary = None
            self.march = None
            self.gcc_cmd = "gcc"
    
    def compile_with_ml_passes(
        self,
        source_code: str,
        predicted_passes: List[str],
        num_runs: int = 5,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Compile C source with ML-predicted pass sequence and measure performance.
        
        This is the main function that orchestrates the entire compilation pipeline.
        
        Args:
            source_code: C source code as string
            predicted_passes: List of LLVM pass names (e.g., ["mem2reg", "inline", "gvn"])
            num_runs: Number of runtime measurement runs for averaging
            timeout: Timeout per run in seconds
        
        Returns:
            Dictionary with compilation results:
            {
                'success': bool,
                'binary_size': int (bytes),
                'binary_size_human': str,
                'runtime_mean': float,
                'runtime_std': float,
                'runtime_min': float,
                'runtime_max': float,
                'passes_used': List[str],
                'num_passes': int,
                'compilation_time': float,
                'error': str (if failed)
            }
        """
        start_time = time.time()
        
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                # Step 1: Save source code to file
                c_file = temp_path / "program.c"
                c_file.write_text(source_code)
                
                # Step 2: Compile C to LLVM bitcode
                bc_file = self._compile_to_bitcode(c_file, temp_path)
                if bc_file is None:
                    return {
                        'success': False,
                        'error': 'Failed to compile C source to LLVM bitcode',
                        'compilation_time': time.time() - start_time
                    }
                
                # Step 3: Apply ML-predicted passes
                opt_bc_file = self._apply_passes(bc_file, predicted_passes, temp_path)
                if opt_bc_file is None:
                    return {
                        'success': False,
                        'error': 'Failed to apply optimization passes',
                        'passes_used': predicted_passes,
                        'compilation_time': time.time() - start_time
                    }
                
                # Step 4: Compile to assembly (RISC-V)
                asm_file = self._compile_to_assembly(opt_bc_file, temp_path)
                if asm_file is None:
                    return {
                        'success': False,
                        'error': 'Failed to compile bitcode to assembly',
                        'passes_used': predicted_passes,
                        'compilation_time': time.time() - start_time
                    }
                
                # Step 5: Compile to executable
                exe_file = self._compile_to_executable(asm_file, temp_path)
                if exe_file is None:
                    return {
                        'success': False,
                        'error': 'Failed to link executable',
                        'passes_used': predicted_passes,
                        'compilation_time': time.time() - start_time
                    }
                
                compilation_time = time.time() - start_time
                
                # Step 6: Measure binary size
                binary_size = exe_file.stat().st_size
                
                # Step 7: Measure runtime performance
                runtime_results = self._measure_runtime(
                    exe_file, 
                    num_runs=num_runs, 
                    timeout=timeout
                )
                
                if not runtime_results['success']:
                    return {
                        'success': False,
                        'error': runtime_results['error'],
                        'binary_size': binary_size,
                        'binary_size_human': self._format_size(binary_size),
                        'passes_used': predicted_passes,
                        'num_passes': len(predicted_passes),
                        'compilation_time': compilation_time
                    }
                
                # Success - return all metrics
                return {
                    'success': True,
                    'binary_size': binary_size,
                    'binary_size_human': self._format_size(binary_size),
                    'runtime_mean': runtime_results['mean'],
                    'runtime_std': runtime_results['std'],
                    'runtime_min': runtime_results['min'],
                    'runtime_max': runtime_results['max'],
                    'passes_used': predicted_passes,
                    'num_passes': len(predicted_passes),
                    'compilation_time': compilation_time,
                    'error': None
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Unexpected error: {str(e)}',
                    'compilation_time': time.time() - start_time
                }
    
    def compile_with_optimization_level(
        self,
        source_code: str,
        opt_level: str,
        num_runs: int = 5,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Compile with standard LLVM optimization level (-O0, -O1, -O2, -O3).
        Uses the same working approach as generate_training_data_hybrid.py:
        C -> bitcode (clang) -> assembly (llc) -> executable (gcc)
        
        Args:
            source_code: C source code as string
            opt_level: Optimization level (-O0, -O1, -O2, -O3)
            num_runs: Number of execution runs for performance measurement
            timeout: Timeout in seconds for each execution run
        
        Returns:
            Dictionary with compilation results and metrics
        """
        start_time = time.time()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                temp_path = Path(temp_dir)
                c_file = temp_path / "program.c"
                c_file.write_text(source_code)
                
                # Step 1: Compile C to bitcode
                bc_file = temp_path / "program.bc"
                clang_cmd = ['clang']
                if self.target_triple:
                    clang_cmd.extend(['--target=' + self.target_triple])
                clang_cmd.extend([opt_level, '-emit-llvm', '-c', str(c_file), '-o', str(bc_file)])
                
                try:
                    subprocess.run(
                        clang_cmd,
                        check=True,
                        capture_output=True,
                        timeout=30
                    )
                except subprocess.CalledProcessError as e:
                    return {
                        'success': False,
                        'error': f'Compilation to bitcode failed: {e.stderr.decode()}',
                        'passes_used': [opt_level],
                        'compilation_time': time.time() - start_time
                    }
                except subprocess.TimeoutExpired:
                    return {
                        'success': False,
                        'error': 'Compilation timeout',
                        'passes_used': [opt_level],
                        'compilation_time': time.time() - start_time
                    }
                
                # Step 2: Convert bitcode to assembly using llc (GNU-compatible assembly)
                asm_file = temp_path / "program.s"
                if self.target_arch in ['riscv64', 'riscv32']:
                    # Use proper RISC-V ABI flags to match gcc defaults
                    mabi = 'lp64d' if self.target_arch == 'riscv64' else 'ilp32d'
                    llc_cmd = ['llc', f'-march={self.target_arch}', f'-mabi={mabi}', 
                               '-mattr=+m,+a,+f,+d,+c', str(bc_file), '-o', str(asm_file)]
                    try:
                        subprocess.run(
                            llc_cmd,
                            check=True,
                            capture_output=True,
                            timeout=30
                        )
                    except subprocess.CalledProcessError as e:
                        return {
                            'success': False,
                            'error': f'Assembly generation failed: {e.stderr.decode()}',
                            'passes_used': [opt_level],
                            'compilation_time': time.time() - start_time
                        }
                    except subprocess.TimeoutExpired:
                        return {
                            'success': False,
                            'error': 'Assembly generation timeout',
                            'passes_used': [opt_level],
                            'compilation_time': time.time() - start_time
                        }
                
                # Step 3: Link assembly to executable with RISC-V GCC
                exe_file = temp_path / "program.exe"
                try:
                    # Use rv64gc (general compute) which includes imafdc extensions
                    march_flag = 'rv64gc' if self.target_arch == 'riscv64' else 'rv32gc'
                    subprocess.run(
                        [self.gcc_cmd, '-march=' + march_flag, str(asm_file), '-o', str(exe_file), '-static'],
                        check=True,
                        capture_output=True,
                        timeout=30
                    )
                except subprocess.CalledProcessError as e:
                    return {
                        'success': False,
                        'error': f'Linking failed: {e.stderr.decode()}',
                        'passes_used': [opt_level],
                        'compilation_time': time.time() - start_time
                    }
                except subprocess.TimeoutExpired:
                    return {
                        'success': False,
                        'error': 'Linking timeout',
                        'passes_used': [opt_level],
                        'compilation_time': time.time() - start_time
                    }
                
                compilation_time = time.time() - start_time
                
                # Measure binary size
                binary_size = exe_file.stat().st_size
                
                # Measure runtime
                runtime_results = self._measure_runtime(exe_file, num_runs, timeout)
                
                if not runtime_results['success']:
                    return {
                        'success': False,
                        'error': runtime_results['error'],
                        'binary_size': binary_size,
                        'binary_size_human': self._format_size(binary_size),
                        'passes_used': [opt_level],
                        'num_passes': 1,
                        'compilation_time': compilation_time
                    }
                
                return {
                    'success': True,
                    'binary_size': binary_size,
                    'binary_size_human': self._format_size(binary_size),
                    'runtime_mean': runtime_results['mean'],
                    'runtime_std': runtime_results['std'],
                    'runtime_min': runtime_results['min'],
                    'runtime_max': runtime_results['max'],
                    'passes_used': [opt_level],
                    'num_passes': 1,
                    'compilation_time': compilation_time,
                    'error': None
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Unexpected error: {str(e)}',
                    'compilation_time': time.time() - start_time
                }
    
    # ==================== Internal Helper Methods ====================
    
    def _compile_to_bitcode(self, c_file: Path, output_dir: Path) -> Optional[Path]:
        """Compile C source to LLVM bitcode (RISC-V target)."""
        bc_file = output_dir / "program.bc"
        
        clang_cmd = ['clang']
        if self.target_triple:
            clang_cmd.extend(['--target=' + self.target_triple])
        clang_cmd.extend(['-O0', '-emit-llvm', '-c', str(c_file), '-o', str(bc_file)])
        
        try:
            subprocess.run(clang_cmd, check=True, capture_output=True, timeout=30)
            return bc_file
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None
    
    def _apply_passes(self, bc_file: Path, passes: List[str], output_dir: Path) -> Optional[Path]:
        """Apply LLVM optimization passes using opt."""
        opt_bc_file = output_dir / "program_opt.bc"
        
        if not passes:
            # No passes - just copy the file
            import shutil
            shutil.copy(bc_file, opt_bc_file)
            return opt_bc_file
        
        # Build opt command with pass sequence
        pass_arg = f"-passes={','.join(passes)}"
        
        try:
            subprocess.run(
                ['opt', pass_arg, str(bc_file), '-o', str(opt_bc_file)],
                check=True,
                capture_output=True,
                timeout=60
            )
            return opt_bc_file
        except subprocess.CalledProcessError as e:
            # Could be invalid pass name
            return None
        except subprocess.TimeoutExpired:
            return None
    
    def _compile_to_assembly(self, bc_file: Path, output_dir: Path) -> Optional[Path]:
        """Compile LLVM bitcode to assembly (RISC-V target)."""
        asm_file = output_dir / "program.s"
        
        if not self.march:
            # Native compilation - skip llc, go straight to executable
            return bc_file  # Return bitcode for native compilation
        
        # Use proper RISC-V ABI flags to match gcc defaults
        mabi = 'lp64d' if self.target_arch == 'riscv64' else 'ilp32d'
        llc_cmd = ['llc', f'-march={self.march}', f'-mabi={mabi}',
                   '-mattr=+m,+a,+f,+d,+c', str(bc_file), '-o', str(asm_file)]
        
        try:
            subprocess.run(llc_cmd, check=True, capture_output=True, timeout=30)
            return asm_file
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None
    
    def _compile_to_executable(self, input_file: Path, output_dir: Path) -> Optional[Path]:
        """Compile assembly (or bitcode for native) to executable."""
        exe_file = output_dir / "program.exe"
        
        if self.target_arch in ['riscv64', 'riscv32']:
            # RISC-V cross-compilation with proper -march flag
            try:
                march_flag = 'rv64gc' if self.target_arch == 'riscv64' else 'rv32gc'
                subprocess.run(
                    [self.gcc_cmd, '-march=' + march_flag, str(input_file), '-o', str(exe_file), '-static'],
                    check=True,
                    capture_output=True,
                    timeout=30
                )
                return exe_file
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                return None
        else:
            # Native compilation from bitcode
            try:
                subprocess.run(
                    ['clang', str(input_file), '-o', str(exe_file)],
                    check=True,
                    capture_output=True,
                    timeout=30
                )
                return exe_file
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                return None
    
    def _measure_runtime(
        self, 
        exe_file: Path, 
        num_runs: int = 5, 
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Measure execution runtime with multiple runs and statistical analysis.
        
        Uses QEMU for RISC-V execution.
        """
        times = []
        
        # Build execution command
        if self.use_qemu and self.qemu_binary:
            exec_cmd = [self.qemu_binary, str(exe_file)]
        else:
            exec_cmd = [str(exe_file)]
        
        # Run multiple times for statistical reliability
        for run_idx in range(num_runs):
            try:
                start = time.perf_counter()
                subprocess.run(
                    exec_cmd,
                    check=True,
                    capture_output=True,
                    timeout=timeout,
                    stdin=subprocess.DEVNULL  # Empty stdin
                )
                end = time.perf_counter()
                times.append(end - start)
                
            except subprocess.TimeoutExpired:
                return {
                    'success': False,
                    'error': f'Runtime timeout: Program exceeded {timeout}s limit (run {run_idx + 1}/{num_runs})',
                    'runs_completed': len(times)
                }
            except subprocess.CalledProcessError as e:
                return {
                    'success': False,
                    'error': f'Program crashed with exit code {e.returncode}',
                    'stderr': e.stderr.decode() if e.stderr else '',
                    'runs_completed': len(times)
                }
        
        # Calculate statistics
        return {
            'success': True,
            'mean': statistics.mean(times),
            'std': statistics.stdev(times) if len(times) > 1 else 0.0,
            'min': min(times),
            'max': max(times),
            'runs': len(times)
        }
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format byte size as human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"


# ==================== Standalone Helper Functions ====================

def calculate_improvements(ml_result: Dict, baseline_result: Dict) -> Dict[str, Any]:
    """
    Calculate improvement metrics comparing ML-predicted vs baseline.
    
    Args:
        ml_result: Results from compile_with_ml_passes()
        baseline_result: Results from compile_with_optimization_level()
    
    Returns:
        Dictionary with improvement metrics
    """
    if not ml_result['success'] or not baseline_result['success']:
        return {
            'binary_size_reduction_percent': None,
            'binary_size_reduction_bytes': None,
            'runtime_reduction_percent': None,
            'runtime_reduction_seconds': None,
            'winner_binary': None,
            'winner_runtime': None
        }
    
    # Binary size comparison
    ml_size = ml_result['binary_size']
    baseline_size = baseline_result['binary_size']
    size_reduction_bytes = ml_size - baseline_size
    size_reduction_percent = (size_reduction_bytes / baseline_size) * 100
    
    # Runtime comparison
    ml_time = ml_result['runtime_mean']
    baseline_time = baseline_result['runtime_mean']
    time_reduction_seconds = ml_time - baseline_time
    time_reduction_percent = (time_reduction_seconds / baseline_time) * 100
    
    return {
        'binary_size_reduction_percent': size_reduction_percent,
        'binary_size_reduction_bytes': size_reduction_bytes,
        'runtime_reduction_percent': time_reduction_percent,
        'runtime_reduction_seconds': time_reduction_seconds,
        'winner_binary': 'ml_predicted' if size_reduction_bytes < 0 else 'baseline',
        'winner_runtime': 'ml_predicted' if time_reduction_seconds < 0 else 'baseline'
    }
