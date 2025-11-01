'use client';

import OptimizationDemo from '@/components/OptimizationDemo';

export default function LLVMDemoPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="container mx-auto py-8">
        <h1 className="text-4xl font-bold text-center mb-2 text-gray-800">
          IRIS - LLVM Optimization Demo
        </h1>
        <p className="text-center text-gray-600 mb-8">
          ML-Guided Compiler Optimization for RISC-V Architecture
        </p>
        <OptimizationDemo />
      </div>
    </div>
  );
}
