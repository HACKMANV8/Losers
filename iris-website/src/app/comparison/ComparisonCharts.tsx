'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

interface ChartData {
  name: string;
  value: number;
  color: string;
  label: string;
}

interface ComparisonChartsProps {
  binarySizes: {
    ml: number;
    o2?: number;
    o3?: number;
  };
  runtimes: {
    ml: number;
    o2?: number;
    o3?: number;
  };
  improvements: {
    vs_o2?: {
      binary_size_reduction_percent: number;
      runtime_reduction_percent: number;
    };
    vs_o3?: {
      binary_size_reduction_percent: number;
      runtime_reduction_percent: number;
    };
  };
}

export default function ComparisonCharts({ binarySizes, runtimes, improvements }: ComparisonChartsProps) {
  // Prepare binary size data
  const binarySizeData: ChartData[] = [
    { name: 'ML-Predicted', value: binarySizes.ml, color: '#6366f1', label: formatBytes(binarySizes.ml) }
  ];
  if (binarySizes.o2) {
    binarySizeData.push({ name: 'LLVM -O2', value: binarySizes.o2, color: '#a855f7', label: formatBytes(binarySizes.o2) });
  }
  if (binarySizes.o3) {
    binarySizeData.push({ name: 'LLVM -O3', value: binarySizes.o3, color: '#ec4899', label: formatBytes(binarySizes.o3) });
  }

  // Prepare runtime data
  const runtimeData: ChartData[] = [
    { name: 'ML-Predicted', value: runtimes.ml * 1000, color: '#6366f1', label: `${(runtimes.ml * 1000).toFixed(2)} ms` }
  ];
  if (runtimes.o2) {
    runtimeData.push({ name: 'LLVM -O2', value: runtimes.o2 * 1000, color: '#a855f7', label: `${(runtimes.o2 * 1000).toFixed(2)} ms` });
  }
  if (runtimes.o3) {
    runtimeData.push({ name: 'LLVM -O3', value: runtimes.o3 * 1000, color: '#ec4899', label: `${(runtimes.o3 * 1000).toFixed(2)} ms` });
  }

  // Find winners
  const binaryWinner = binarySizeData.reduce((min, curr) => curr.value < min.value ? curr : min);
  const runtimeWinner = runtimeData.reduce((min, curr) => curr.value < min.value ? curr : min);

  return (
    <div className="space-y-8">
      {/* Binary Size Chart */}
      <div className="glass-card p-6 rounded-2xl animate-fade-in">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-2xl font-bold text-white">📦 Binary Size Comparison</h3>
          <div className="flex items-center gap-2">
            <span className="text-sm text-white/60">Winner:</span>
            <span className="px-3 py-1 bg-green-500/30 text-green-100 rounded-lg text-sm font-bold">
              {binaryWinner.name}
            </span>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={binarySizeData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
            <XAxis 
              dataKey="name" 
              stroke="#ffffff80"
              tick={{ fill: '#ffffff80' }}
            />
            <YAxis 
              stroke="#ffffff80"
              tick={{ fill: '#ffffff80' }}
              label={{ value: 'Size (bytes)', angle: -90, position: 'insideLeft', fill: '#ffffff80' }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1f2937', 
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#fff'
              }}
              formatter={(value: number) => [formatBytes(value), 'Size']}
            />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              {binarySizeData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Improvement Badges for Binary Size */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          {improvements.vs_o2 && (
            <ImprovementBadge
              title="vs -O2"
              percentage={improvements.vs_o2.binary_size_reduction_percent}
              metric="binary size"
            />
          )}
          {improvements.vs_o3 && (
            <ImprovementBadge
              title="vs -O3"
              percentage={improvements.vs_o3.binary_size_reduction_percent}
              metric="binary size"
            />
          )}
        </div>
      </div>

      {/* Runtime Chart */}
      <div className="glass-card p-6 rounded-2xl animate-fade-in">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-2xl font-bold text-white">⚡ Runtime Comparison</h3>
          <div className="flex items-center gap-2">
            <span className="text-sm text-white/60">Winner:</span>
            <span className="px-3 py-1 bg-green-500/30 text-green-100 rounded-lg text-sm font-bold">
              {runtimeWinner.name}
            </span>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={runtimeData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
            <XAxis 
              dataKey="name" 
              stroke="#ffffff80"
              tick={{ fill: '#ffffff80' }}
            />
            <YAxis 
              stroke="#ffffff80"
              tick={{ fill: '#ffffff80' }}
              label={{ value: 'Time (ms)', angle: -90, position: 'insideLeft', fill: '#ffffff80' }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1f2937', 
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#fff'
              }}
              formatter={(value: number) => [value.toFixed(2) + ' ms', 'Runtime']}
            />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              {runtimeData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Improvement Badges for Runtime */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          {improvements.vs_o2 && (
            <ImprovementBadge
              title="vs -O2"
              percentage={improvements.vs_o2.runtime_reduction_percent}
              metric="runtime"
            />
          )}
          {improvements.vs_o3 && (
            <ImprovementBadge
              title="vs -O3"
              percentage={improvements.vs_o3.runtime_reduction_percent}
              metric="runtime"
            />
          )}
        </div>
      </div>

      {/* Overall Winner Card */}
      <OverallWinnerCard
        binaryWinner={binaryWinner.name}
        runtimeWinner={runtimeWinner.name}
        improvements={improvements}
      />
    </div>
  );
}

// Improvement Badge Component
function ImprovementBadge({ title, percentage, metric }: { title: string, percentage: number, metric: string }) {
  const isImprovement = percentage < 0;
  const displayPercent = Math.abs(percentage).toFixed(1);
  
  return (
    <div className={`glass p-4 rounded-xl border-2 ${
      isImprovement ? 'border-green-500/30 bg-green-500/10' : 'border-red-500/30 bg-red-500/10'
    }`}>
      <p className="text-white/70 text-sm mb-1">{title}</p>
      <div className="flex items-center gap-2">
        <span className={`text-3xl font-bold ${isImprovement ? 'text-green-400' : 'text-red-400'}`}>
          {isImprovement ? '↓' : '↑'} {displayPercent}%
        </span>
        <span className="text-white/80 text-sm">
          {isImprovement ? 'smaller' : 'larger'}
        </span>
      </div>
      <p className="text-white/50 text-xs mt-1">
        ML is {isImprovement ? 'better' : 'worse'} for {metric}
      </p>
    </div>
  );
}

// Overall Winner Card Component
function OverallWinnerCard({ 
  binaryWinner, 
  runtimeWinner, 
  improvements 
}: { 
  binaryWinner: string, 
  runtimeWinner: string,
  improvements: any 
}) {
  // Calculate overall score (50% binary, 50% runtime)
  let mlScore = 0;
  let totalComparisons = 0;

  if (improvements.vs_o2) {
    if (improvements.vs_o2.binary_size_reduction_percent < 0) mlScore += 0.5;
    if (improvements.vs_o2.runtime_reduction_percent < 0) mlScore += 0.5;
    totalComparisons += 1;
  }
  if (improvements.vs_o3) {
    if (improvements.vs_o3.binary_size_reduction_percent < 0) mlScore += 0.5;
    if (improvements.vs_o3.runtime_reduction_percent < 0) mlScore += 0.5;
    totalComparisons += 1;
  }

  const mlWinRate = totalComparisons > 0 ? (mlScore / totalComparisons) * 100 : 0;
  const overallWinner = mlWinRate >= 50 ? 'ML-Predicted' : 'LLVM';

  return (
    <div className="glass-card p-8 rounded-2xl animate-scale-in border-2 border-yellow-500/50">
      <div className="text-center">
        <h3 className="text-3xl font-bold text-white mb-4">🏆 Overall Winner</h3>
        <div className="inline-block px-8 py-4 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 rounded-2xl border-2 border-yellow-500/50 mb-4">
          <p className="text-5xl font-bold text-yellow-400 mb-2">{overallWinner}</p>
          <p className="text-white/70 text-sm">
            Win rate: {mlWinRate.toFixed(0)}%
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <div className="glass p-4 rounded-xl">
            <p className="text-white/60 text-sm mb-2">Binary Size Champion</p>
            <p className="text-white text-xl font-bold">{binaryWinner}</p>
          </div>
          <div className="glass p-4 rounded-xl">
            <p className="text-white/60 text-sm mb-2">Runtime Champion</p>
            <p className="text-white text-xl font-bold">{runtimeWinner}</p>
          </div>
        </div>

        <p className="text-white/50 text-sm mt-4">
          Scoring: 50% binary size + 50% runtime performance
        </p>
      </div>
    </div>
  );
}

// Helper function to format bytes
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
