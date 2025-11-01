#!/usr/bin/env python3
"""
Compilation Service - Handles compilation, optimization, and benchmarking
"""

import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import (
    CompilationConfig,
    ErrorMessages,
    get_target_triple,
    get_gcc_command,
    get_qemu_command
)
from utils.logger import get_logger

logger = get_logger(__name__)


class CompilationService:
    """Service for compilation and optimization operations"""
    
    def __init__(self, target_arch: str = CompilationConfig.DEFAULT_TARGET_ARCH):
        """
        Initialize compilation service.
        
        Args:
            target_arch: Target architecture (riscv64 or riscv32)
        """
        self.target_arch = target_arch
        self.target_triple = get_target_triple(target_arch)
        self.gcc_cmd = get_gcc_command(target_arch)
        self.qemu_cmd = get_qemu_command(target_arch)
        self.use_qemu = CompilationConfig.USE_QEMU
        
        logger.info(f"CompilationService initialized for {target_arch}")
        logger.debug(f"Target triple: {self.target_triple}")
        logger.debug(f"GCC command: {self.gcc_cmd}")
        logger.debug(f"QEMU command: {self.qemu_cmd}")
    
    def compile_to_bitcode(
        self,
        c_file: Path,
        optimization: str = "-O0"
    ) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Compile C source to LLVM bitcode.
        
        Args:
            c_file: Path to C source file
            optimization: Optimization level
        
        Returns:
            Tuple of (success, bitcode_file_path, error_message)
        """
        bc_file = c_file.with_suffix('.bc')
        
        clang_cmd = [
            CompilationConfig.CLANG_CMD,
            f'--target={self.target_triple}',
            optimization,
            '-emit-llvm',
            '-c',
            str(c_file),
            '-o',
            str(bc_file)
        ]
        
        try:
            logger.debug(f"Compiling to bitcode: {' '.join(clang_cmd)}")
            
            result = subprocess.run(
                clang_cmd,
                check=True,
                capture_output=True,
                timeout=CompilationConfig.COMPILE_TIMEOUT
            )
            
            logger.info(f"Successfully compiled to bitcode: {bc_file}")
            return True, bc_file, None
            
        except subprocess.CalledProcessError as e:
            error_msg = ErrorMessages.COMPILATION_FAILED.format(
                e.stderr.decode() if e.stderr else str(e)
            )
            logger.error(error_msg)
            return False, None, error_msg
            
        except subprocess.TimeoutExpired:
            error_msg = ErrorMessages.TIMEOUT_ERROR.format(CompilationConfig.COMPILE_TIMEOUT)
            logger.error(error_msg)
            return False, None, error_msg
            
        except Exception as e:
            error_msg = ErrorMessages.COMPILATION_FAILED.format(str(e))
            logger.error(error_msg)
            return False, None, error_msg
    
    def apply_ir_passes(
        self,
        bc_file: Path,
        ir_passes: List[str]
    ) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Apply IR-level optimization passes.
        
        Args:
            bc_file: Path to input bitcode file
            ir_passes: List of LLVM pass names
        
        Returns:
            Tuple of (success, optimized_bitcode_path, error_message)
        """
        opt_bc_file = bc_file.with_suffix('.opt.bc')
        
        # Format passes for opt command
        if ir_passes and len(ir_passes) > 0:
            pass_arg = f"-passes={','.join(ir_passes)}"
        else:
            pass_arg = "-passes=default<O0>"
        
        opt_cmd = [
            CompilationConfig.OPT_CMD,
            pass_arg,
            str(bc_file),
            '-o',
            str(opt_bc_file)
        ]
        
        try:
            logger.debug(f"Applying IR passes: {' '.join(opt_cmd)}")
            
            result = subprocess.run(
                opt_cmd,
                check=True,
                capture_output=True,
                timeout=CompilationConfig.OPT_TIMEOUT
            )
            
            logger.info(f"Successfully applied {len(ir_passes)} IR passes")
            return True, opt_bc_file, None
            
        except subprocess.CalledProcessError as e:
            error_msg = ErrorMessages.OPTIMIZATION_FAILED.format(
                e.stderr.decode() if e.stderr else str(e)
            )
            logger.error(error_msg)
            return False, None, error_msg
            
        except subprocess.TimeoutExpired:
            error_msg = ErrorMessages.TIMEOUT_ERROR.format(CompilationConfig.OPT_TIMEOUT)
            logger.error(error_msg)
            return False, None, error_msg
            
        except Exception as e:
            error_msg = ErrorMessages.OPTIMIZATION_FAILED.format(str(e))
            logger.error(error_msg)
            return False, None, error_msg
    
    def generate_assembly(
        self,
        bc_file: Path,
        machine_config: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Generate assembly from bitcode.
        
        Args:
            bc_file: Path to bitcode file
            machine_config: Optional machine-level optimization config
        
        Returns:
            Tuple of (success, assembly_file_path, error_message)
        """
        asm_file = bc_file.with_suffix('.s')
        
        llc_cmd = [
            CompilationConfig.LLC_CMD,
            f'-march={self.target_arch}',
            str(bc_file),
            '-o',
            str(asm_file)
        ]
        
        # TODO: Apply machine config if provided
        # This would require integration with machine_flags_generator_v2.py
        
        try:
            logger.debug(f"Generating assembly: {' '.join(llc_cmd)}")
            
            result = subprocess.run(
                llc_cmd,
                check=True,
                capture_output=True,
                timeout=CompilationConfig.COMPILE_TIMEOUT
            )
            
            logger.info(f"Successfully generated assembly: {asm_file}")
            return True, asm_file, None
            
        except subprocess.CalledProcessError as e:
            error_msg = ErrorMessages.COMPILATION_FAILED.format(
                e.stderr.decode() if e.stderr else str(e)
            )
            logger.error(error_msg)
            return False, None, error_msg
            
        except subprocess.TimeoutExpired:
            error_msg = ErrorMessages.TIMEOUT_ERROR.format(CompilationConfig.COMPILE_TIMEOUT)
            logger.error(error_msg)
            return False, None, error_msg
            
        except Exception as e:
            error_msg = ErrorMessages.COMPILATION_FAILED.format(str(e))
            logger.error(error_msg)
            return False, None, error_msg
    
    def compile_to_executable(
        self,
        asm_file: Path
    ) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Compile assembly to executable.
        
        Args:
            asm_file: Path to assembly file
        
        Returns:
            Tuple of (success, executable_path, error_message)
        """
        exe_file = asm_file.with_suffix('.exe')
        
        # Use correct RISC-V ABI to avoid floating-point extension errors
        # lp64 = 64-bit long and pointers, soft-float ABI (no 'd' extension required)
        abi_flag = '-mabi=lp64' if self.target_arch == 'riscv64' else '-mabi=ilp32'
        
        gcc_cmd = [
            self.gcc_cmd,
            abi_flag,
            '-march=rv64gc' if self.target_arch == 'riscv64' else '-march=rv32gc',
            str(asm_file),
            '-o',
            str(exe_file),
            '-static'
        ]
        
        try:
            logger.debug(f"Compiling to executable: {' '.join(gcc_cmd)}")
            
            result = subprocess.run(
                gcc_cmd,
                check=True,
                capture_output=True,
                timeout=CompilationConfig.COMPILE_TIMEOUT
            )
            
            logger.info(f"Successfully compiled to executable: {exe_file}")
            return True, exe_file, None
            
        except subprocess.CalledProcessError as e:
            error_msg = ErrorMessages.COMPILATION_FAILED.format(
                e.stderr.decode() if e.stderr else str(e)
            )
            logger.error(error_msg)
            return False, None, error_msg
            
        except subprocess.TimeoutExpired:
            error_msg = ErrorMessages.TIMEOUT_ERROR.format(CompilationConfig.COMPILE_TIMEOUT)
            logger.error(error_msg)
            return False, None, error_msg
            
        except Exception as e:
            error_msg = ErrorMessages.COMPILATION_FAILED.format(str(e))
            logger.error(error_msg)
            return False, None, error_msg
    
    def benchmark_executable(
        self,
        exe_file: Path,
        num_runs: int = CompilationConfig.DEFAULT_NUM_RUNS
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Benchmark executable performance.
        
        Args:
            exe_file: Path to executable
            num_runs: Number of runs for benchmarking
        
        Returns:
            Tuple of (success, metrics_dict, error_message)
        """
        if not exe_file.exists():
            return False, None, f"Executable not found: {exe_file}"
        
        exec_cmd = [self.qemu_cmd, str(exe_file)] if self.use_qemu else [str(exe_file)]
        times = []
        
        try:
            logger.debug(f"Benchmarking with {num_runs} runs")
            
            for i in range(num_runs):
                start = time.perf_counter()
                
                result = subprocess.run(
                    exec_cmd,
                    check=True,
                    capture_output=True,
                    timeout=CompilationConfig.EXECUTION_TIMEOUT
                )
                
                end = time.perf_counter()
                times.append(end - start)
                logger.debug(f"Run {i+1}: {times[-1]:.6f}s")
            
            binary_size = exe_file.stat().st_size
            
            metrics = {
                'execution_time_avg': sum(times) / len(times),
                'execution_time_min': min(times),
                'execution_time_max': max(times),
                'execution_times': times,
                'binary_size': binary_size,
                'num_runs': num_runs
            }
            
            logger.info(f"Benchmark complete: avg={metrics['execution_time_avg']:.6f}s, size={binary_size} bytes")
            return True, metrics, None
            
        except subprocess.TimeoutExpired:
            error_msg = ErrorMessages.TIMEOUT_ERROR.format(CompilationConfig.EXECUTION_TIMEOUT)
            logger.error(error_msg)
            return False, None, error_msg
            
        except subprocess.CalledProcessError as e:
            error_msg = ErrorMessages.EXECUTION_FAILED.format(
                e.stderr.decode() if e.stderr else str(e)
            )
            logger.error(error_msg)
            return False, None, error_msg
            
        except Exception as e:
            error_msg = ErrorMessages.EXECUTION_FAILED.format(str(e))
            logger.error(error_msg)
            return False, None, error_msg
    
    def compile_with_standard_opt(
        self,
        c_file: Path,
        opt_level: str
    ) -> Dict:
        """
        Full compilation pipeline with standard optimization level.
        
        Args:
            c_file: Path to C source file
            opt_level: Standard optimization level (-O0, -O1, -O2, -O3)
        
        Returns:
            Result dictionary with all metrics
        """
        compile_start = time.perf_counter()
        result = {
            'success': False,
            'opt_level': opt_level,
            'compile_time': None,
            'execution_time_avg': None,
            'binary_size': None,
            'error': None
        }
        
        try:
            # Compile to bitcode with optimization
            success, bc_file, error = self.compile_to_bitcode(c_file, optimization=opt_level)
            if not success:
                result['error'] = error
                return result
            
            # Generate assembly
            success, asm_file, error = self.generate_assembly(bc_file)
            if not success:
                result['error'] = error
                bc_file.unlink(missing_ok=True)
                return result
            
            # Compile to executable
            success, exe_file, error = self.compile_to_executable(asm_file)
            if not success:
                result['error'] = error
                bc_file.unlink(missing_ok=True)
                asm_file.unlink(missing_ok=True)
                return result
            
            compile_time = time.perf_counter() - compile_start
            
            # Benchmark
            success, metrics, error = self.benchmark_executable(exe_file)
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
            asm_file.unlink(missing_ok=True)
            exe_file.unlink(missing_ok=True)
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
