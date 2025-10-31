'use client';

const FlowDiagram = () => {
  return (
    <div className="flex flex-wrap items-center justify-center gap-4 md:gap-6 text-sm animate-fade-in">
      <div className="flex flex-col items-center">
        <div className="glass-card p-4 rounded-xl min-w-[120px] text-center transition-all hover:scale-105">
          <span className="text-white font-medium">Source Code</span>
        </div>
      </div>
      
      <div className="text-white/60 self-center">→</div>
      
      <div className="flex flex-col items-center">
        <div className="glass-card p-4 rounded-xl min-w-[120px] text-center transition-all hover:scale-105">
          <span className="text-white font-medium">LLVM IR</span>
        </div>
      </div>
      
      <div className="text-white/60 self-center">→</div>
      
      <div className="flex flex-col items-center">
        <div className="glass-card p-4 rounded-xl min-w-[120px] text-center transition-all hover:scale-105">
          <span className="text-white font-medium">Features</span>
        </div>
      </div>
      
      <div className="text-white/60 self-center">→</div>
      
      <div className="flex flex-col items-center">
        <div className="glass-card p-4 rounded-xl min-w-[120px] text-center bg-indigo-500/20 transition-all hover:scale-105">
          <span className="text-white font-bold">ML Model</span>
        </div>
      </div>
      
      <div className="text-white/60 self-center">→</div>
      
      <div className="flex flex-col items-center">
        <div className="glass-card p-4 rounded-xl min-w-[120px] text-center transition-all hover:scale-105">
          <span className="text-white font-medium">Passes</span>
        </div>
      </div>
      
      <div className="text-white/60 self-center">→</div>
      
      <div className="flex flex-col items-center">
        <div className="glass-card p-4 rounded-xl min-w-[120px] text-center bg-green-500/20 transition-all hover:scale-105">
          <span className="text-white font-bold">Optimized</span>
        </div>
      </div>
    </div>
  );
};

export default FlowDiagram;
