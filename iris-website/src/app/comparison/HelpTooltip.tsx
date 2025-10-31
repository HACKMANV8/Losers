'use client';

import { useState } from 'react';

interface HelpTooltipProps {
  title: string;
  description: string;
}

export default function HelpTooltip({ title, description }: HelpTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onClick={() => setIsVisible(!isVisible)}
        className="ml-2 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-white/20 hover:bg-white/30 rounded-full transition-all">
        ?
      </button>

      {isVisible && (
        <div className="absolute z-50 left-1/2 transform -translate-x-1/2 bottom-full mb-2 w-64 px-4 py-3 bg-gray-900 text-white text-sm rounded-lg shadow-xl border border-gray-700 animate-fade-in">
          <p className="font-bold mb-1">{title}</p>
          <p className="text-gray-300 text-xs">{description}</p>
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
            <div className="border-8 border-transparent border-t-gray-900"></div>
          </div>
        </div>
      )}
    </div>
  );
}

// Predefined tooltips for common terms
export const TOOLTIPS = {
  binarySize: {
    title: "Binary Size",
    description: "The size of the compiled executable file in bytes. Smaller binaries use less storage and may load faster."
  },
  runtime: {
    title: "Runtime Performance",
    description: "Average execution time over 5 runs. Lower is better. Standard deviation shows consistency."
  },
  mlPredicted: {
    title: "ML-Predicted Passes",
    description: "Custom LLVM pass sequence predicted by our machine learning model based on your program's characteristics."
  },
  llvmO2: {
    title: "LLVM -O2",
    description: "Standard moderate optimization level. Balances compilation time and runtime performance. Widely used in production."
  },
  llvmO3: {
    title: "LLVM -O3",
    description: "Aggressive optimization level. May increase compilation time and binary size for better runtime performance."
  },
  improvement: {
    title: "Improvement Percentage",
    description: "Negative percentages indicate improvements (smaller size or faster runtime). Positive percentages indicate regressions."
  },
  riscv: {
    title: "RISC-V Target",
    description: "All compilations target RISC-V (riscv64) architecture. This is a hardware-specific optimization project."
  },
  passes: {
    title: "Optimization Passes",
    description: "Individual compiler optimizations applied in sequence. Each pass transforms the code to improve performance or size."
  }
};
