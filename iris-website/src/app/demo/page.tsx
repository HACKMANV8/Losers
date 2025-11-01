'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import Layout from '../components/Layout';
import API_ENDPOINTS from '@/config/api';

// --- Icon Components ---
const MemoryIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4-4 4 4m0 6l-4 4-4-4" /></svg>
);
const SimplifyIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
);
const InlineIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" /></svg>
);
const GVNIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
);
const DefaultPassIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
);

const getPassIcon = (passName: string) => {
  if (passName.includes('mem')) return <MemoryIcon />;
  if (passName.includes('simplify') || passName.includes('sccp')) return <SimplifyIcon />;
  if (passName.includes('inline')) return <InlineIcon />;
  if (passName.includes('gvn')) return <GVNIcon />;
  return <DefaultPassIcon />;
};

// A simple spinner component
const Spinner = () => (
  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
);

export default function Demo() {
  const [file, setFile] = useState<File | null>(null);
  const [beamSize, setBeamSize] = useState<number>(5); // New state for beam size
  const [targetMetric, setTargetMetric] = useState<string>('execution_time'); // New state for target metric
  // Model selection is removed from the UI. Always use transformer on frontend.
  const model = 'transformer';
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setError(null);
      setResults(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.c', '.cpp'],
    },
    multiple: false,
  });

  const downloadResults = () => {
    if (!results) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(results, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "iris_results.json");
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  const copyPasses = () => {
    if (!results || !results.data?.predicted_passes) return;
    const passesString = results.data.predicted_passes.join(', ');
    navigator.clipboard.writeText(passesString).then(() => {
      // Optional: Show a brief success message
      alert('Passes copied to clipboard!');
    }).catch(err => {
      console.error('Failed to copy passes:', err);
    });
  };

  const handleClear = () => {
    setFile(null);
    setResults(null);
    setError(null);
  };

  const handleSubmit = async () => {
    if (!file) return;

    setLoading(true);
    setResults(null);
    setError(null);

    try {
      // Read file content
      const code = await file.text();

      // Step 1: Extract features
      const featuresRes = await fetch(API_ENDPOINTS.features, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          target_arch: 'riscv64'
        }),
      });

      const featuresData = await featuresRes.json();

      if (!featuresRes.ok || !featuresData.success) {
        setError(featuresData.error || 'Failed to extract features');
        setLoading(false);
        return;
      }

      // Step 2: Use transformer model to predict optimal passes
      // By not sending ir_passes, the backend will use the transformer model
      // to predict passes based on the extracted features

      // Step 3: Apply ML-predicted optimization passes
      const res = await fetch(API_ENDPOINTS.optimize, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code,
          // Don't send ir_passes - let transformer predict them
          use_transformer: true,
          opt_level_hint: 'O_2', // Can be customized based on UI selection
          target_arch: 'riscv64',
          beam_size: beamSize, // Pass beamSize to the backend
          target_metric: targetMetric // Pass targetMetric to the backend
        }),
      });

      const data = await res.json();

      if (res.ok && data.success) {
        // Get predicted passes from the response
        const predicted_passes = data.passes_used || data.metrics?.ir_passes || [];
        
        // Format results to match expected structure with features
        setResults({
          success: true,
          data: {
            predicted_passes: predicted_passes,
            metrics: data.metrics,
            model: model,
            features: featuresData.features
          }
        });
      } else {
        setError(data.error || 'An unknown error occurred during optimization.');
      }
    } catch (err) {
      setError('Failed to connect to the server. Please ensure the backend is running and accessible.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <main className="min-h-screen p-6 flex items-center justify-center">
        <article className="max-w-2xl w-full glass-strong p-8 animate-scale-in">
            
            {!results && (
              <>
                <h1 className="text-4xl font-bold mb-8 text-center text-white drop-shadow-lg">IRis Optimizer</h1>
                
                <label
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all glass block ${
                    isDragActive ? 'border-white/60 bg-white/20 scale-105' : 'border-white/30 hover:border-white/50 hover:bg-white/10'
                  }`}>
                  <input {...getInputProps()} />
                  <div className="flex flex-col items-center justify-center">
                    <p className="text-white font-medium text-xl">
                      {isDragActive ? 'Drop the file here...' : 'Drag & drop a C/C++ file, or click to select'}
                    </p>
                  </div>
                </label>

                {error && (
                  <div className="mt-6 p-5 bg-red-500/20 border border-red-500/50 rounded-2xl text-white">
                    <div className="flex items-start gap-3 mb-3">
                      <span className="text-2xl">Warning:</span>
                      <div className="flex-1">
                        <strong className="font-bold text-lg block mb-2">Error</strong>
                        {error.includes('Compilation failed') ? (
                          <div>
                            <p className="text-white/90 mb-3">Your C code has compilation errors:</p>
                            <pre className="bg-black/40 p-4 rounded-xl overflow-x-auto text-sm font-mono text-red-300 whitespace-pre-wrap">
                              {error.replace('Feature extraction failed: Compilation failed: Failed to compile C source: ', '').trim()}
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

                {file && (
                  <p className="mt-6 p-5 glass-card rounded-2xl text-white text-center">
                    <strong className="font-bold">{file.name}</strong>
                    <span className="block mt-2 text-white/80">{(file.size / 1024).toFixed(2)} KB</span>
                  </p>
                )}

                <div className="mt-6">
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

                <div className="mt-6">
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

                <button 
                  onClick={handleSubmit} 
                  disabled={!file || loading}
                  className="w-full mt-10 px-8 py-5 text-xl font-bold text-white bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-2xl hover:scale-105 transition-all duration-300">
                  {loading ? <Spinner /> : 'Optimize Code'}
                </button>
              </>
            )}

            {error && (
              <aside className="p-8 glass-card rounded-2xl border-2 border-red-400/50 animate-fade-in">
                <div className="text-center">
                  <span className="text-2xl block mb-4">Warning</span>
                  <h2 className="text-2xl font-bold text-white mb-2">Error</h2>
                  <p className="text-white mb-6">{error}</p>
                  <button onClick={handleClear} className="px-8 py-3 font-bold text-white bg-white/20 rounded-xl hover:bg-white/30 transition-all">
                    Try Again
                  </button>
                </div>
              </aside>
            )}

            {results && (
              <>
                <header className="flex justify-between items-center mb-8 animate-slide-in">
                  <h2 className="text-3xl font-bold text-white">Optimization Results</h2>
                  <button onClick={handleClear} className="px-6 py-3 font-bold text-white bg-white/20 rounded-xl hover:bg-white/30 transition-all hover:scale-105">
                    New File
                  </button>
                </header>

                <div className="glass-card p-6 rounded-2xl mb-6 animate-fade-in">
                  <h3 className="text-xl font-bold text-white mb-3">Model Used</h3>
                  <p className="text-2xl font-bold text-white capitalize">{results.model_used || results.data?.model || 'transformer'}</p>
                </div>

                <section className="glass-card p-6 rounded-2xl mb-6 animate-slide-in">
                  <header className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-bold text-white">ML Predicted Pass Sequence</h3>
                    <nav className="flex gap-3">
                      <button onClick={copyPasses} className="font-bold text-white bg-green-500/30 hover:bg-green-500/50 px-4 py-2 rounded-xl transition-all hover:scale-105">Copy</button>
                      <button onClick={downloadResults} className="font-bold text-white bg-indigo-500/30 hover:bg-indigo-500/50 px-4 py-2 rounded-xl transition-all hover:scale-105">Download</button>
                    </nav>
                  </header>
                  <p className="text-white/80 mb-4">Generated by feeding extracted features to ML model</p>
                  <ul className="flex flex-wrap gap-3">
                    {results.data?.predicted_passes?.map((pass: string, index: number) => (
                      <li key={index} className="flex items-center px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-xl font-medium transition-all hover:scale-105">
                        {getPassIcon(pass)}
                        <span className="ml-2">{pass}</span>
                      </li>
                    ))}
                  </ul>
                </section>

                <section className="glass-card p-6 rounded-2xl animate-slide-in">
                  <h3 className="text-xl font-bold text-white mb-4">LLVM IR Features Extracted</h3>
                  <p className="text-white/80 mb-4">Features used as input to ML model for pass prediction</p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-h-64 overflow-y-auto">
                    {results.data?.features && Object.entries(results.data.features).map(([key, value]) => (
                      <div key={key} className="glass p-3 rounded-lg">
                        <dt className="text-white/80 capitalize text-xs font-medium">{key.replace(/_/g, ' ')}</dt>
                        <dd className="font-bold text-white text-sm mt-1">{typeof value === 'number' ? value.toFixed(2) : String(value)}</dd>
                      </div>
                    ))}
                  </div>
                </section>
              </>
            )}
        </article>
      </main>
    </Layout>
  );
}