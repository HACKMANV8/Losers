'use client';

import { useState } from 'react';

interface PassSequenceComparisonProps {
  mlPasses: string[];
}

// Common LLVM optimization passes by level
const LLVM_O2_PASSES = [
  'mem2reg', 'simplifycfg', 'sroa', 'early-cse', 'lower-expect',
  'inline', 'function-attrs', 'argpromotion', 'sroa', 'jump-threading',
  'correlated-propagation', 'tailcallelim', 'reassociate', 'loop-rotate',
  'licm', 'loop-unswitch', 'indvars', 'loop-deletion', 'loop-unroll',
  'gvn', 'memcpyopt', 'sccp', 'bdce', 'adce', 'dse', 'loop-vectorize',
  'slp-vectorizer', 'alignment-from-assumptions', 'strip-dead-prototypes',
  'globaldce', 'constmerge', 'cgscc'
];

const LLVM_O3_PASSES = [
  ...LLVM_O2_PASSES,
  'aggressive-instcombine', 'loop-unroll-and-jam', 'loop-distribute',
  'loop-load-elim', 'callsite-splitting', 'partial-inliner',
  'gvn-hoist', 'div-rem-pairs', 'speculative-execution'
];

// Pass descriptions for tooltips
const PASS_DESCRIPTIONS: Record<string, string> = {
  'mem2reg': 'Promote memory to register - converts stack allocations to SSA form',
  'simplifycfg': 'Simplify control flow graph - removes unnecessary branches',
  'sroa': 'Scalar replacement of aggregates - breaks down structures',
  'inline': 'Function inlining - replaces function calls with function body',
  'gvn': 'Global value numbering - eliminates redundant computations',
  'dce': 'Dead code elimination - removes unused code',
  'adce': 'Aggressive dead code elimination - more thorough dead code removal',
  'dse': 'Dead store elimination - removes unnecessary writes',
  'sccp': 'Sparse conditional constant propagation',
  'licm': 'Loop invariant code motion - moves computations out of loops',
  'loop-unroll': 'Loop unrolling - duplicates loop body for performance',
  'loop-vectorize': 'Loop vectorization - SIMD optimization',
  'slp-vectorizer': 'Superword level parallelism vectorization',
  'tailcallelim': 'Tail call elimination - optimizes recursive calls',
  'reassociate': 'Expression reassociation - reorders operations',
  'jump-threading': 'Thread jumps through conditionals',
  'correlated-propagation': 'Propagate information from conditionals',
  'indvars': 'Induction variable simplification',
  'loop-deletion': 'Delete dead loops',
  'loop-rotate': 'Rotate loops to canonical form',
  'loop-unswitch': 'Unswitch loops - move conditionals outside loops',
  'memcpyopt': 'Memory copy optimization',
  'bdce': 'Bit-tracking dead code elimination',
  'constmerge': 'Merge duplicate constants',
  'globaldce': 'Global dead code elimination',
  'argpromotion': 'Promote arguments from pointers to values',
  'function-attrs': 'Deduce function attributes',
  'early-cse': 'Early common subexpression elimination',
  'lower-expect': 'Lower expect intrinsics',
  'alignment-from-assumptions': 'Compute alignments from assumptions',
  'strip-dead-prototypes': 'Strip unused function declarations',
  'cgscc': 'Call graph SCC pass manager',
  'aggressive-instcombine': 'Aggressive instruction combining',
  'loop-unroll-and-jam': 'Loop unroll and jam fusion',
  'loop-distribute': 'Loop distribution for vectorization',
  'loop-load-elim': 'Loop load elimination',
  'callsite-splitting': 'Split call sites for optimization',
  'partial-inliner': 'Partial function inlining',
  'gvn-hoist': 'Global value numbering hoisting',
  'div-rem-pairs': 'Optimize division/remainder pairs',
  'speculative-execution': 'Speculative execution optimization'
};

export default function PassSequenceComparison({ mlPasses }: PassSequenceComparisonProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [hoveredPass, setHoveredPass] = useState<string | null>(null);

  // Analyze pass differences
  const mlSet = new Set(mlPasses.map(p => p.toLowerCase()));
  const o2Set = new Set(LLVM_O2_PASSES);
  const o3Set = new Set(LLVM_O3_PASSES);

  const mlOnlyPasses = mlPasses.filter(p => !o2Set.has(p.toLowerCase()) && !o3Set.has(p.toLowerCase()));
  const o2OnlyPasses = LLVM_O2_PASSES.filter(p => !mlSet.has(p));
  const o3OnlyPasses = LLVM_O3_PASSES.filter(p => !mlSet.has(p) && !o2Set.has(p));
  const commonPasses = mlPasses.filter(p => o2Set.has(p.toLowerCase()) || o3Set.has(p.toLowerCase()));

  return (
    <div className="glass-card p-6 rounded-2xl animate-fade-in mb-8">
      {/* Header with expand/collapse button */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-2xl font-bold text-white">🔍 Pass Sequence Analysis</h3>
          <p className="text-white/60 text-sm mt-1">
            Compare optimization passes used by ML vs standard LLVM levels
          </p>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-all flex items-center gap-2">
          <span className="text-white font-medium">{isExpanded ? 'Collapse' : 'Expand'}</span>
          <span className="text-white text-xl">{isExpanded ? '▲' : '▼'}</span>
        </button>
      </div>

      {/* Summary Stats (Always Visible) */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <StatCard 
          label="ML Passes" 
          value={mlPasses.length} 
          color="bg-indigo-500/20 border-indigo-500/30"
        />
        <StatCard 
          label="Common with -O2/-O3" 
          value={commonPasses.length} 
          color="bg-green-500/20 border-green-500/30"
        />
        <StatCard 
          label="ML Unique" 
          value={mlOnlyPasses.length} 
          color="bg-yellow-500/20 border-yellow-500/30"
        />
        <StatCard 
          label="LLVM Unique" 
          value={o2OnlyPasses.length + o3OnlyPasses.length} 
          color="bg-blue-500/20 border-blue-500/30"
        />
      </div>

      {/* Detailed Comparison (Collapsible) */}
      {isExpanded && (
        <div className="space-y-6 mt-6 animate-fade-in">
          {/* ML-Predicted Passes */}
          <PassSection
            title="ML-Predicted Passes"
            icon="🤖"
            color="indigo"
            passes={mlPasses}
            hoveredPass={hoveredPass}
            setHoveredPass={setHoveredPass}
            highlightCommon={true}
            commonSet={new Set([...o2Set, ...o3Set])}
          />

          {/* Common Passes */}
          {commonPasses.length > 0 && (
            <PassSection
              title="Passes Common to ML and LLVM"
              icon="✓"
              color="green"
              passes={commonPasses}
              hoveredPass={hoveredPass}
              setHoveredPass={setHoveredPass}
            />
          )}

          {/* ML-Only Passes */}
          {mlOnlyPasses.length > 0 && (
            <PassSection
              title="Passes Unique to ML"
              icon="⚡"
              color="yellow"
              passes={mlOnlyPasses}
              hoveredPass={hoveredPass}
              setHoveredPass={setHoveredPass}
              badge="ML ONLY"
            />
          )}

          {/* LLVM -O2 Info */}
          <div className="glass p-4 rounded-xl">
            <h4 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <span>🔧</span> LLVM -O2 Typical Passes
            </h4>
            <p className="text-white/70 text-sm mb-3">
              Standard -O2 typically includes ~{LLVM_O2_PASSES.length} passes focused on moderate optimization
            </p>
            <div className="flex flex-wrap gap-2">
              {LLVM_O2_PASSES.slice(0, 10).map((pass, idx) => (
                <PassBadge
                  key={idx}
                  pass={pass}
                  included={mlSet.has(pass)}
                  hoveredPass={hoveredPass}
                  setHoveredPass={setHoveredPass}
                />
              ))}
              <span className="px-3 py-1 bg-white/10 text-white/50 rounded-lg text-xs">
                +{LLVM_O2_PASSES.length - 10} more...
              </span>
            </div>
          </div>

          {/* LLVM -O3 Info */}
          <div className="glass p-4 rounded-xl">
            <h4 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <span>⚙️</span> LLVM -O3 Typical Passes
            </h4>
            <p className="text-white/70 text-sm mb-3">
              Standard -O3 includes all -O2 passes plus ~{LLVM_O3_PASSES.length - LLVM_O2_PASSES.length} additional aggressive optimizations
            </p>
            <div className="flex flex-wrap gap-2">
              {o3OnlyPasses.slice(0, 8).map((pass, idx) => (
                <PassBadge
                  key={idx}
                  pass={pass}
                  included={mlSet.has(pass)}
                  hoveredPass={hoveredPass}
                  setHoveredPass={setHoveredPass}
                />
              ))}
              {o3OnlyPasses.length > 8 && (
                <span className="px-3 py-1 bg-white/10 text-white/50 rounded-lg text-xs">
                  +{o3OnlyPasses.length - 8} more...
                </span>
              )}
            </div>
          </div>

          {/* Insight Box */}
          <div className="glass p-6 rounded-xl bg-blue-500/10 border-2 border-blue-500/30">
            <h4 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <span>💡</span> Insight
            </h4>
            <p className="text-white/80 text-sm">
              {mlOnlyPasses.length > 0 ? (
                <>
                  ML predicted <strong>{mlOnlyPasses.length} unique pass{mlOnlyPasses.length > 1 ? 'es' : ''}</strong> not 
                  typically used in standard -O2/-O3. This custom sequence is tailored to your program's specific characteristics.
                </>
              ) : (
                <>
                  ML's predicted passes align closely with standard LLVM optimization levels, 
                  suggesting your program benefits from well-established optimization strategies.
                </>
              )}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// Stat Card Component
function StatCard({ label, value, color }: { label: string, value: number, color: string }) {
  return (
    <div className={`glass p-4 rounded-xl border-2 ${color}`}>
      <p className="text-white/60 text-xs mb-1">{label}</p>
      <p className="text-white text-3xl font-bold">{value}</p>
    </div>
  );
}

// Pass Section Component
function PassSection({ 
  title, 
  icon, 
  color, 
  passes, 
  hoveredPass, 
  setHoveredPass,
  highlightCommon = false,
  commonSet = new Set(),
  badge
}: any) {
  const colorClasses = {
    indigo: 'border-indigo-500/30 bg-indigo-500/10',
    green: 'border-green-500/30 bg-green-500/10',
    yellow: 'border-yellow-500/30 bg-yellow-500/10',
    purple: 'border-purple-500/30 bg-purple-500/10'
  };

  return (
    <div className={`glass p-4 rounded-xl border-2 ${colorClasses[color as keyof typeof colorClasses]}`}>
      <div className="flex justify-between items-center mb-3">
        <h4 className="text-lg font-bold text-white flex items-center gap-2">
          <span>{icon}</span> {title}
        </h4>
        {badge && (
          <span className="px-2 py-1 bg-yellow-500/30 text-yellow-100 rounded text-xs font-bold">
            {badge}
          </span>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        {passes.map((pass: string, idx: number) => (
          <PassBadge
            key={idx}
            pass={pass}
            included={true}
            hoveredPass={hoveredPass}
            setHoveredPass={setHoveredPass}
            isCommon={highlightCommon && commonSet.has(pass.toLowerCase())}
          />
        ))}
      </div>
    </div>
  );
}

// Pass Badge Component with Tooltip
function PassBadge({ 
  pass, 
  included, 
  hoveredPass, 
  setHoveredPass,
  isCommon = false
}: {
  pass: string;
  included: boolean;
  hoveredPass: string | null;
  setHoveredPass: (pass: string | null) => void;
  isCommon?: boolean;
}) {
  const description = PASS_DESCRIPTIONS[pass.toLowerCase()] || 'LLVM optimization pass';
  const isHovered = hoveredPass === pass;

  return (
    <div className="relative inline-block">
      <button
        onMouseEnter={() => setHoveredPass(pass)}
        onMouseLeave={() => setHoveredPass(null)}
        className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
          included
            ? isCommon
              ? 'bg-green-500/30 text-green-100 border border-green-500/50'
              : 'bg-indigo-500/30 text-indigo-100 border border-indigo-500/50'
            : 'bg-white/10 text-white/50 border border-white/20'
        } hover:scale-105`}>
        {included ? '✓' : '✗'} {pass}
      </button>
      
      {/* Tooltip */}
      {isHovered && (
        <div className="absolute z-50 bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-xl border border-gray-700 w-64 animate-fade-in">
          <p className="font-bold mb-1">{pass}</p>
          <p className="text-gray-300">{description}</p>
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
            <div className="border-8 border-transparent border-t-gray-900"></div>
          </div>
        </div>
      )}
    </div>
  );
}
