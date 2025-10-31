'use client';

import { SparklesIcon, ChipIcon, FileIcon, ClockIcon, TrendingUpIcon, TrendingDownIcon } from './icons';
import ComparisonCharts from './ComparisonCharts';
import PassSequenceComparison from './PassSequenceComparison';

interface MethodResult {
  success: boolean;
  binary_size?: number;
  binary_size_human?: string;
  runtime_mean?: number;
  runtime_std?: number;
  passes_used?: string[];
  num_passes?: number;
  error?: string;
}

interface Improvement {
  binary_size_reduction_percent: number;
  binary_size_reduction_bytes: number;
  runtime_reduction_percent: number;
  runtime_reduction_seconds: number;
  winner_binary: string;
  winner_runtime: string;
}

interface ComparisonResults {
  ml_predicted: MethodResult;
  llvm_o2?: MethodResult;
  llvm_o3?: MethodResult;
  improvements: Record<string, Improvement>;
  summary: {
    ml_wins: {
      binary_size: number;
      runtime: number;
      total: number;
      out_of: number;
    };
    best_binary_size?: {
      method: string;
      size: number;
      size_human: string;
    };
    best_runtime?: {
      method: string;
      time: number;
    };
  };
  total_processing_time?: number;
}

interface ComparisonUIProps {
  results: ComparisonResults;
  fileName: string;
  onBackClick: () => void;
  onDownloadReport?: () => void;
  onTryAnother?: () => void;
}

export default function ComparisonUI({ results, fileName, onBackClick, onDownloadReport, onTryAnother }: ComparisonUIProps) {
  return (
    <>
      {/* Header */}
      <section className="glass-card p-6 rounded-2xl mb-6 animate-fade-in">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Comparison Results</h2>
            <p className="text-white/60 text-sm">
              File: <span className="text-white">{fileName}</span> | Target: <span className="text-white">RISC-V (riscv64)</span>
            </p>
          </div>
          <button
            onClick={onBackClick}
            className="px-6 py-3 font-bold text-white bg-white/20 rounded-xl hover:bg-white/30 transition-all hover:scale-105">
            ← Back
          </button>
        </div>
      </section>

      {/* Results Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* ML-Predicted Card */}
        <ResultCard
          title="ML-Predicted"
          icon={<SparklesIcon />}
          iconBg="bg-indigo-500/30"
          borderColor="border-indigo-500/50"
          result={results.ml_predicted}
          showPasses={true}
        />

        {/* LLVM -O2 Card */}
        {results.llvm_o2 && (
          <ResultCard
            title="LLVM -O2"
            icon={<ChipIcon />}
            iconBg="bg-purple-500/30"
            borderColor="border-purple-500/50"
            result={results.llvm_o2}
            description="Moderate optimization level"
          />
        )}

        {/* LLVM -O3 Card */}
        {results.llvm_o3 && (
          <ResultCard
            title="LLVM -O3"
            icon={<ChipIcon />}
            iconBg="bg-pink-500/30"
            borderColor="border-pink-500/50"
            result={results.llvm_o3}
            description="Aggressive optimization level"
          />
        )}
      </div>

      {/* Pass Sequence Comparison */}
      <PassSequenceComparison mlPasses={results.ml_predicted.passes_used || []} />

      {/* Visual Charts */}
      {Object.keys(results.improvements).length > 0 && (
        <ComparisonCharts
          binarySizes={{
            ml: results.ml_predicted.binary_size || 0,
            o2: results.llvm_o2?.binary_size,
            o3: results.llvm_o3?.binary_size
          }}
          runtimes={{
            ml: results.ml_predicted.runtime_mean || 0,
            o2: results.llvm_o2?.runtime_mean,
            o3: results.llvm_o3?.runtime_mean
          }}
          improvements={results.improvements}
        />
      )}

      {/* Improvement Summary */}
      {Object.keys(results.improvements).length > 0 && (
        <ImprovementSummary improvements={results.improvements} summary={results.summary} />
      )}

      {/* Action Buttons Footer */}
      <section className="glass-card p-8 rounded-2xl animate-fade-in">
        <div className="flex flex-col md:flex-row gap-4 justify-center items-center">
          {onDownloadReport && (
            <button
              onClick={onDownloadReport}
              className="w-full md:w-auto px-8 py-4 text-lg font-bold text-white bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl hover:from-green-600 hover:to-emerald-700 shadow-xl hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download Report (JSON)
            </button>
          )}
          {onTryAnother && (
            <button
              onClick={onTryAnother}
              className="w-full md:w-auto px-8 py-4 text-lg font-bold text-white bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl hover:from-indigo-600 hover:to-purple-700 shadow-xl hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Try Another Program
            </button>
          )}
          <button
            onClick={onBackClick}
            className="w-full md:w-auto px-8 py-4 text-lg font-bold text-white bg-white/20 rounded-2xl hover:bg-white/30 shadow-xl hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Demo
          </button>
        </div>
        
        <div className="mt-6 text-center">
          <p className="text-white/50 text-sm">
            Total processing time: <span className="text-white font-bold">{results.total_processing_time?.toFixed(2)}s</span>
          </p>
          <p className="text-white/40 text-xs mt-1">
            All measurements performed on RISC-V (riscv64) architecture
          </p>
        </div>
      </section>
    </>
  );
}

// Result Card Component
function ResultCard({ title, icon, iconBg, borderColor, result, showPasses = false, description }: any) {
  return (
    <div className={`glass-card p-6 rounded-2xl border-2 ${borderColor} animate-scale-in`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={`p-2 ${iconBg} rounded-lg`}>
            {icon}
          </div>
          <h3 className="text-xl font-bold text-white">{title}</h3>
        </div>
        {result.success && (
          <span className="px-3 py-1 bg-green-500/30 text-green-100 rounded-lg text-sm font-medium">✓</span>
        )}
      </div>
      
      {result.success ? (
        <>
          <div className="space-y-4 mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/10 rounded-lg">
                <FileIcon />
              </div>
              <div>
                <p className="text-white/60 text-sm">Binary Size</p>
                <p className="text-white text-2xl font-bold">{result.binary_size_human}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/10 rounded-lg">
                <ClockIcon />
              </div>
              <div>
                <p className="text-white/60 text-sm">Runtime</p>
                <p className="text-white text-2xl font-bold">{result.runtime_mean?.toFixed(4)}s</p>
              </div>
            </div>
            {showPasses && result.num_passes && (
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/10 rounded-lg">
                  <ChipIcon />
                </div>
                <div>
                  <p className="text-white/60 text-sm">Passes Used</p>
                  <p className="text-white text-lg font-bold">{result.num_passes} passes</p>
                </div>
              </div>
            )}
          </div>
          {showPasses && result.passes_used && (
            <div className="bg-black/30 p-3 rounded-lg">
              <p className="text-white/50 text-xs mb-1">Pass sequence:</p>
              <p className="text-white/80 text-xs font-mono break-all">
                {result.passes_used.join(', ')}
              </p>
            </div>
          )}
          {description && (
            <div className="bg-black/30 p-3 rounded-lg mt-4">
              <p className="text-white/80 text-sm font-medium">Standard {title} optimization</p>
              <p className="text-white/60 text-xs mt-1">{description}</p>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-8">
          <p className="text-red-400 font-medium">{result.error}</p>
        </div>
      )}
    </div>
  );
}

// Improvement Summary Component
function ImprovementSummary({ improvements, summary }: { improvements: Record<string, Improvement>, summary: any }) {
  return (
    <section className="glass-card p-8 rounded-2xl mb-8 animate-fade-in">
      <h2 className="text-3xl font-bold text-white mb-6 text-center">📊 Improvement Summary</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* vs -O2 */}
        {improvements.vs_o2 && (
          <ImprovementCard title="ML vs -O2" improvement={improvements.vs_o2} />
        )}
        
        {/* vs -O3 */}
        {improvements.vs_o3 && (
          <ImprovementCard title="ML vs -O3" improvement={improvements.vs_o3} />
        )}
      </div>

      {/* Overall Summary */}
      <div className="glass p-6 rounded-xl text-center">
        <h3 className="text-2xl font-bold text-white mb-4">Overall Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-white/60 text-sm mb-2">ML Wins</p>
            <p className="text-4xl font-bold text-white">
              {summary.ml_wins.total}/{summary.ml_wins.out_of}
            </p>
          </div>
          <div>
            <p className="text-white/60 text-sm mb-2">Best Binary Size</p>
            <p className="text-lg font-bold text-white capitalize">{summary.best_binary_size?.method.replace('_', ' ')}</p>
            <p className="text-sm text-white/70">{summary.best_binary_size?.size_human}</p>
          </div>
          <div>
            <p className="text-white/60 text-sm mb-2">Best Runtime</p>
            <p className="text-lg font-bold text-white capitalize">{summary.best_runtime?.method.replace('_', ' ')}</p>
            <p className="text-sm text-white/70">{summary.best_runtime?.time.toFixed(4)}s</p>
          </div>
        </div>
      </div>
    </section>
  );
}

// Improvement Card Component
function ImprovementCard({ title, improvement }: { title: string, improvement: Improvement }) {
  return (
    <div className="glass p-6 rounded-xl">
      <h3 className="text-xl font-bold text-white mb-4">{title}</h3>
      <div className="space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-white/70 text-sm">Binary Size</span>
            <div className="flex items-center gap-2">
              {improvement.binary_size_reduction_percent < 0 ? <TrendingDownIcon /> : <TrendingUpIcon />}
              <span className={`text-3xl font-bold ${improvement.binary_size_reduction_percent < 0 ? 'text-green-400' : 'text-red-400'}`}>
                {improvement.binary_size_reduction_percent.toFixed(1)}%
              </span>
            </div>
          </div>
          <p className="text-white/50 text-xs">
            {improvement.binary_size_reduction_bytes < 0 ? 'Reduced by' : 'Increased by'} {Math.abs(improvement.binary_size_reduction_bytes)} bytes
          </p>
        </div>
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-white/70 text-sm">Runtime</span>
            <div className="flex items-center gap-2">
              {improvement.runtime_reduction_percent < 0 ? <TrendingDownIcon /> : <TrendingUpIcon />}
              <span className={`text-3xl font-bold ${improvement.runtime_reduction_percent < 0 ? 'text-green-400' : 'text-red-400'}`}>
                {improvement.runtime_reduction_percent.toFixed(1)}%
              </span>
            </div>
          </div>
          <p className="text-white/50 text-xs">
            {improvement.runtime_reduction_seconds < 0 ? 'Faster by' : 'Slower by'} {Math.abs(improvement.runtime_reduction_seconds).toFixed(4)}s
          </p>
        </div>
      </div>
    </div>
  );
}
