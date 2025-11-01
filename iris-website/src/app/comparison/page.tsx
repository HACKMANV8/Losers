'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import Layout from '../components/Layout';
import API_ENDPOINTS from '@/config/api';

const Spinner = () => (
  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
);

export default function Comparison() {
  const [file, setFile] = useState<File | null>(null);
  const [beamSize, setBeamSize] = useState<number>(5); // New state for beam size
  const [targetMetric, setTargetMetric] = useState<string>('execution_time'); // New state for target metric
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [optimizationResults, setOptimizationResults] = useState<any>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setError(null);
      setResults(null);
      setOptimizationResults(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.c', '.cpp'],
    },
    multiple: false,
  });

  const handleOptimize = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      // Read file content
      const code = await file.text();

      // Use transformer model to predict optimal passes
      // Don't send ir_passes - let the backend's transformer model predict them

      // Get comparison results with ML-predicted passes
      const compareRes = await fetch(API_ENDPOINTS.compare, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          // Don't send ir_passes - let transformer predict them
          use_transformer: true,
          opt_level_hint: 'O_2',
          target_arch: 'riscv64',
          beam_size: beamSize, // Pass beamSize to the backend
          target_metric: targetMetric // Pass targetMetric to the backend
        }),
      });

      const compareData = await compareRes.json();

      if (compareRes.ok && compareData.success) {
        setResults(compareData);
        // Get predicted passes from the ML optimization results
        const predicted_passes = compareData.ml_optimization?.ir_passes || [];
        // Store ML optimization results for display
        setOptimizationResults({
          success: true,
          data: {
            predicted_passes: predicted_passes,
            metrics: compareData.ml_optimization
          }
        });
      } else {
        setError(compareData.error || 'Failed to compare optimizations');
      }
    } catch (err) {
      setError('Failed to connect to the server. Please ensure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setFile(null);
    setResults(null);
    setOptimizationResults(null);
    setError(null);
  };

  const formatTime = (time: number) => {
    if (time < 0.001) return `${(time * 1000000).toFixed(2)} µs`;
    if (time < 1) return `${(time * 1000).toFixed(2)} ms`;
    return `${time.toFixed(3)} s`;
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <Layout>
      <main className="min-h-screen p-8 max-w-6xl mx-auto">
        <h1 className="text-5xl font-bold mb-12 text-center text-white drop-shadow-lg animate-fade-in">Performance Comparison</h1>
        
        {!results && (
          <>
            <section className="glass-card p-8 rounded-2xl animate-slide-in mb-8">
              <h2 className="text-2xl font-bold text-white mb-6">Standard LLVM Optimization Levels</h2>
              <p className="text-white/80 mb-8 text-lg">
                Compare ML-predicted pass sequences against standard optimization levels (-O0, -O1, -O2, -O3)
              </p>
              
              <ul className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <li className="glass p-6 rounded-xl text-center hover:bg-white/15 transition-all duration-300 hover:scale-105">
                  <strong className="text-3xl font-bold text-white">-O0</strong>
                  <p className="text-sm text-white/70 mt-2">No optimization</p>
                </li>
                <li className="glass p-6 rounded-xl text-center hover:bg-white/15 transition-all duration-300 hover:scale-105">
                  <strong className="text-3xl font-bold text-white">-O1</strong>
                  <p className="text-sm text-white/70 mt-2">Basic optimization</p>
                </li>
                <li className="glass p-6 rounded-xl text-center hover:bg-white/15 transition-all duration-300 hover:scale-105">
                  <strong className="text-3xl font-bold text-white">-O2</strong>
                  <p className="text-sm text-white/70 mt-2">Moderate optimization</p>
                </li>
                <li className="glass p-6 rounded-xl text-center hover:bg-white/15 transition-all duration-300 hover:scale-105">
                  <strong className="text-3xl font-bold text-white">-O3</strong>
                  <p className="text-sm text-white/70 mt-2">Aggressive optimization</p>
                </li>
              </ul>
            </section>

            <section className="glass-card p-8 rounded-2xl animate-slide-in">
              <h2 className="text-2xl font-bold text-white mb-6">Upload Your Code</h2>
              
              <label
                {...getRootProps()}
                className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all glass block mb-6 ${
                  isDragActive ? 'border-white/60 bg-white/20 scale-105' : 'border-white/30 hover:border-white/50 hover:bg-white/10'
                }`}>
                <input {...getInputProps()} />
                <div className="flex flex-col items-center justify-center">
                  <p className="text-white font-medium text-xl">
                    {isDragActive ? 'Drop the file here...' : 'Drag & drop a C/C++ file, or click to select'}
                  </p>
                </div>
              </label>

              {file && (
                <p className="mb-6 p-5 glass-card rounded-2xl text-white text-center">
                  <strong className="font-bold">{file.name}</strong>
                  <span className="block mt-2 text-white/80">{(file.size / 1024).toFixed(2)} KB</span>
                </p>
              )}

              <div className="mb-6">
                <label htmlFor="beam-size" className="block text-white text-lg font-medium mb-2">Beam Size:</label>
                <input
                  type="number"
                  id="beam-size"
                  min="1"
                  max="20"
                  value={beamSize}
                  onChange={(e) => setBeamSize(parseInt(e.target.value))}
                  className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/20 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                />
              </div>

              <div className="mb-6">
                <label htmlFor="target-metric" className="block text-white text-lg font-medium mb-2">Optimize For:</label>
                <select
                  id="target-metric"
                  value={targetMetric}
                  onChange={(e) => setTargetMetric(e.target.value)}
                  className="w-full p-3 rounded-xl bg-white/10 text-white border border-white/20 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                >
                  <option value="execution_time">Execution Time</option>
                  <option value="binary_size">Binary Size</option>
                </select>
              </div>

              {error && (
                <div className="mb-6 p-5 bg-red-500/20 border border-red-500/50 rounded-2xl text-white">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">Warning:</span>
                    <div className="flex-1">
                      <strong className="font-bold text-lg block mb-2">Error</strong>
                      {error.includes('Compilation failed') || error.includes('compilation errors') ? (
                        <div>
                          <p className="text-white/90 mb-3">Your C code has compilation errors:</p>
                          <pre className="bg-black/40 p-4 rounded-xl overflow-x-auto text-sm font-mono text-red-300 whitespace-pre-wrap max-h-64">
                            {error.replace('Feature extraction failed: Compilation failed: Failed to compile C source: ', '')
                                  .replace('Comparison failed: ', '')
                                  .trim()}
                          </pre>
                          <p className="text-white/70 text-sm mt-3">
                            <strong>Tip:</strong> Please fix the compilation errors in your C code and try again. Make sure your code compiles with standard C compilers.
                          </p>
                        </div>
                      ) : (
                        <p className="text-white/90">{error}</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <div className="flex gap-4 justify-center">
                <button
                  onClick={handleOptimize}
                  disabled={!file || loading}
                  className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:scale-105 shadow-xl">
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <Spinner /> Analyzing...
                    </span>
                  ) : (
                    'Compare Optimizations'
                  )}
                </button>
                {file && (
                  <button
                    onClick={handleClear}
                    className="px-8 py-4 bg-gray-500/30 hover:bg-gray-500/50 text-white font-bold rounded-xl transition-all hover:scale-105">
                    Clear
                  </button>
                )}
              </div>
            </section>
          </>
        )}

        {results && (
          <>
            <button
              onClick={handleClear}
              className="mb-8 px-6 py-3 bg-gray-500/30 hover:bg-gray-500/50 text-white font-bold rounded-xl transition-all hover:scale-105">
              ← New Comparison
            </button>

            {/* Summary */}
            <section className="glass-card p-8 rounded-2xl mb-8 animate-slide-in">
              <h2 className="text-3xl font-bold text-white mb-6">Comparison Summary</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="glass p-6 rounded-xl">
                  <h3 className="text-xl font-bold text-white mb-2">ML Beats Standard Levels</h3>
                  <p className="text-4xl font-bold text-green-400">
                    {(() => {
                      const beatsCount = Object.entries(results.comparison || {}).filter(
                        ([key, val]: [string, any]) => key.startsWith('-O') && val.ml_faster
                      ).length;
                      return `${beatsCount} / 4`;
                    })()}
                  </p>
                  <p className="text-white/60 mt-2">
                    {(() => {
                      const beats = Object.entries(results.comparison || {}).filter(
                        ([key, val]: [string, any]) => key.startsWith('-O') && val.ml_faster
                      ).map(([key]) => key);
                      return beats.length > 0 ? beats.join(', ') : 'None';
                    })()}
                  </p>
                </div>
                <div className="glass p-6 rounded-xl">
                  <h3 className="text-xl font-bold text-white mb-2">Best Performance</h3>
                  <p className="text-4xl font-bold text-purple-400">
                    {results.comparison?.vs_best?.ml_beats_best ? 'ML Wins' : 'Standard Wins'}
                  </p>
                </div>
                <div className="glass p-6 rounded-xl">
                  <h3 className="text-xl font-bold text-white mb-2">ML Smaller Than</h3>
                  <p className="text-4xl font-bold text-blue-400">
                    {(() => {
                      const smallerCount = Object.entries(results.comparison || {}).filter(
                        ([key, val]: [string, any]) => key.startsWith('-O') && val.ml_smaller
                      ).length;
                      return `${smallerCount} / 4`;
                    })()}
                  </p>
                  <p className="text-white/60 mt-2">
                    {(() => {
                      const smaller = Object.entries(results.comparison || {}).filter(
                        ([key, val]: [string, any]) => key.startsWith('-O') && val.ml_smaller
                      ).map(([key]) => key);
                      return smaller.length > 0 ? smaller.join(', ') : 'None';
                    })()}
                  </p>
                </div>
                <div className="glass p-6 rounded-xl">
                  <h3 className="text-xl font-bold text-white mb-2">Best Size Optimization</h3>
                  <p className="text-4xl font-bold text-yellow-400">
                    {results.comparison?.vs_best_size?.ml_beats_best_size ? 'ML Wins' : 'Standard Wins'}
                  </p>
                </div>
              </div>
            </section>

            {/* ML Optimization Results */}
            <section className="glass-card p-8 rounded-2xl mb-8 animate-slide-in">
              <h2 className="text-2xl font-bold text-white mb-6">ML Optimization Results</h2>
              <p className="text-white/80 mb-4">Applied predicted pass sequence to optimize for RISC-V</p>
              {results.ml_optimization?.error ? (
                <div className="bg-red-500/20 border border-red-500/50 rounded-xl p-6">
                  <div className="flex items-start gap-3 mb-3">
                    <span className="text-2xl">Warning:</span>
                    <div className="flex-1">
                      <strong className="font-bold text-white text-lg block mb-2">Compilation Failed</strong>
                      <p className="text-white/90 mb-3">The ML-optimized code failed to compile:</p>
                      <pre className="bg-black/40 p-4 rounded-xl overflow-x-auto text-sm font-mono text-red-300 whitespace-pre-wrap max-h-48">
                        {results.ml_optimization.error}
                      </pre>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="glass p-6 rounded-xl">
                    <p className="text-white/70 text-sm">Execution Time</p>
                    <p className="text-2xl font-bold text-green-400 mt-2">
                      {results.ml_optimization?.execution_time_avg ? formatTime(results.ml_optimization.execution_time_avg) : 'N/A'}
                    </p>
                  </div>
                  <div className="glass p-6 rounded-xl">
                    <p className="text-white/70 text-sm">Binary Size</p>
                    <p className="text-2xl font-bold text-blue-400 mt-2">
                      {results.ml_optimization?.binary_size ? formatSize(results.ml_optimization.binary_size) : 'N/A'}
                    </p>
                  </div>
                  <div className="glass p-6 rounded-xl">
                    <p className="text-white/70 text-sm">Compile Time</p>
                    <p className="text-2xl font-bold text-purple-400 mt-2">
                      {results.ml_optimization?.compile_time ? formatTime(results.ml_optimization.compile_time) : 'N/A'}
                    </p>
                  </div>
                </div>
              )}
            </section>

            {/* Features */}
            <section className="glass-card p-8 rounded-2xl mb-8 animate-slide-in">
              <h2 className="text-2xl font-bold text-white mb-6">LLVM IR Features</h2>
              <p className="text-white/80 mb-4">73 features extracted from source code and fed to ML model</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-h-96 overflow-y-auto">
                {results.features && Object.entries(results.features).map(([key, value]) => (
                  <div key={key} className="glass p-4 rounded-xl hover:bg-white/15">
                    <dt className="text-white/80 capitalize text-sm font-medium">{key.replace(/_/g, ' ')}</dt>
                    <dd className="font-bold text-white text-lg mt-1">{typeof value === 'number' ? value.toFixed(2) : String(value)}</dd>
                  </div>
                ))}
              </div>
            </section>

            {/* Standard Optimizations */}
            <section className="glass-card p-8 rounded-2xl mb-8 animate-slide-in">
              <h2 className="text-2xl font-bold text-white mb-6">Standard LLVM Optimizations</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {['-O0', '-O1', '-O2', '-O3'].map((level) => {
                  const data = results.standard_optimizations?.[level];
                  const comparisonData = results.comparison?.[level];
                  const speedup = comparisonData?.speedup || 0;
                  const sizeReduction = comparisonData?.size_reduction || 0;
                  return (
                    <div key={level} className="glass p-6 rounded-xl">
                      <h3 className="text-xl font-bold text-white mb-4">{level}</h3>
                      <div className="space-y-3">
                        <div>
                          <p className="text-white/70 text-sm">Execution Time</p>
                          <p className="text-lg font-bold text-white">
                            {data?.execution_time_avg ? formatTime(data.execution_time_avg) : 'N/A'}
                          </p>
                        </div>
                        <div>
                          <p className="text-white/70 text-sm">Binary Size</p>
                          <p className="text-lg font-bold text-white">
                            {data?.binary_size ? formatSize(data.binary_size) : 'N/A'}
                          </p>
                        </div>
                        {comparisonData && (
                          <>
                            <div className="pt-2 border-t border-white/10">
                              <p className="text-white/70 text-sm">ML Speedup</p>
                              <p className={`text-lg font-bold ${comparisonData.ml_faster ? 'text-green-400' : 'text-red-400'}`}>
                                {speedup.toFixed(2)}x {comparisonData.ml_faster ? 'Faster' : 'Slower'}
                              </p>
                            </div>
                            <div>
                              <p className="text-white/70 text-sm">ML Size Reduction</p>
                              <p className={`text-lg font-bold ${sizeReduction > 0 ? 'text-blue-400' : 'text-red-400'}`}>
                                {(sizeReduction * 100).toFixed(1)}% {sizeReduction > 0 ? 'Smaller' : 'Larger'}
                              </p>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            {/* Predicted Passes */}
            {optimizationResults?.data?.predicted_passes && (
              <section className="glass-card p-8 rounded-2xl animate-slide-in">
                <h2 className="text-2xl font-bold text-white mb-6">ML Predicted Pass Sequence</h2>
                <ul className="flex flex-wrap gap-3">
                  {optimizationResults.data.predicted_passes.map((pass: string, index: number) => (
                    <li key={index} className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-xl font-medium transition-all hover:scale-105">
                      {pass}
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        )}
      </main>
    </Layout>
  );
}
