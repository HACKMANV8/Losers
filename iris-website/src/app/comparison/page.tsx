'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import Layout from '../components/Layout';
import ComparisonUI from './ComparisonUI';

interface ComparisonData {
  sourceCode: string;
  fileName: string;
  predictedPasses: string[];
  features: Record<string, number>;
  modelUsed: string;
  processingTime: number;
  timestamp: number;
}

interface MethodResult {
  success: boolean;
  binary_size?: number;
  binary_size_human?: string;
  runtime_mean?: number;
  runtime_std?: number;
  runtime_min?: number;
  runtime_max?: number;
  passes_used?: string[];
  num_passes?: number;
  compilation_time?: number;
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
  success: boolean;
  ml_predicted: MethodResult;
  llvm_o0?: MethodResult;
  llvm_o2?: MethodResult;
  llvm_o3?: MethodResult;
  llvm_oz?: MethodResult;
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
  total_processing_time: number;
}

// Loading spinner component
const LoadingSpinner = () => (
  <div className="flex flex-col items-center justify-center min-h-[60vh]">
    <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-white mb-4"></div>
    <p className="text-white text-xl">Loading comparison data...</p>
  </div>
);

export default function Comparison() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [comparisonResults, setComparisonResults] = useState<ComparisonResults | null>(null);

  useEffect(() => {
    // Check if we came from demo page
    const fromDemo = searchParams.get('from') === 'demo';
    
    // Try to load data from sessionStorage
    const storedData = sessionStorage.getItem('iris_comparison_data');
    
    if (!storedData) {
      setError('No comparison data found. Please run the optimizer first.');
      setLoading(false);
      return;
    }
    
    try {
      const data: ComparisonData = JSON.parse(storedData);
      
      // Validate required fields
      if (!data.sourceCode || !data.fileName || !data.predictedPasses || !data.features) {
        setError('Invalid comparison data. Please run the optimizer again.');
        setLoading(false);
        return;
      }
      
      // Check if data is not too old (24 hours)
      const dataAge = Date.now() - data.timestamp;
      const maxAge = 24 * 60 * 60 * 1000; // 24 hours
      if (dataAge > maxAge) {
        setError('Comparison data is too old. Please run the optimizer again.');
        setLoading(false);
        return;
      }
      
      // Data is valid
      setComparisonData(data);
      setLoading(false);
    } catch (err) {
      setError('Failed to parse comparison data. Please run the optimizer again.');
      setLoading(false);
    }
  }, [searchParams]);

  // Auto-trigger comparison when data is loaded
  useEffect(() => {
    if (comparisonData && !comparing && !comparisonResults && !error) {
      // Automatically start comparison
      handleRunComparison();
    }
  }, [comparisonData]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleGoBack = () => {
    router.push('/demo');
  };

  const handleRunComparison = async () => {
    if (!comparisonData) return;
    
    setComparing(true);
    setError(null);
    
    try {
      // Prepare form data
      const formData = new FormData();
      
      // Convert source code string to File object
      const blob = new Blob([comparisonData.sourceCode], { type: 'text/plain' });
      const file = new File([blob], comparisonData.fileName, { type: 'text/plain' });
      
      formData.append('source_file', file);
      formData.append('predicted_passes', JSON.stringify(comparisonData.predictedPasses));
      formData.append('optimization_levels', JSON.stringify(["-O2", "-O3"]));
      formData.append('num_runs', '5');
      
      // Call backend API
      const response = await fetch('http://localhost:5001/api/compare', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        setComparisonResults(data);
        setComparing(false);
      } else {
        throw new Error(data.error || 'Comparison failed');
      }
    } catch (err: any) {
      console.error('Comparison error:', err);
      setError(err.message || 'Failed to run comparison. Make sure the backend is running on http://localhost:5001');
      setComparing(false);
    }
  };

  const handleTryAnother = () => {
    // Clear all data and go back to demo
    sessionStorage.removeItem('iris_comparison_data');
    router.push('/demo');
  };

  const handleDownloadReport = () => {
    if (!comparisonResults || !comparisonData) return;
    
    const report = {
      metadata: {
        fileName: comparisonData.fileName,
        timestamp: new Date().toISOString(),
        targetArchitecture: 'riscv64',
        modelUsed: comparisonData.modelUsed
      },
      results: comparisonResults,
      sourceCode: comparisonData.sourceCode
    };
    
    // Create JSON blob and download
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `iris-comparison-${comparisonData.fileName.replace('.c', '')}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Layout>
      <main className="min-h-screen p-8 max-w-6xl mx-auto">
        <h1 className="text-5xl font-bold mb-12 text-center text-white drop-shadow-lg animate-fade-in">
          Performance Comparison
        </h1>
        
        {loading && <LoadingSpinner />}
        
        {error && (
          <div className="glass-card p-12 rounded-2xl border-2 border-red-400/50 animate-fade-in">
            <div className="text-center">
              <span className="text-6xl block mb-6">⚠️</span>
              <h2 className="text-3xl font-bold text-white mb-4">{comparisonData ? 'Comparison Failed' : 'No Data Available'}</h2>
              <p className="text-white/80 text-lg mb-8">{error}</p>
              <div className="flex gap-4 justify-center">
                {comparisonData && (
                  <button
                    onClick={handleRunComparison}
                    disabled={comparing}
                    className="px-8 py-4 text-lg font-bold text-white bg-gradient-to-r from-pink-500 to-rose-600 rounded-2xl hover:from-pink-600 hover:to-rose-700 shadow-xl hover:scale-105 transition-all duration-300 disabled:opacity-50">
                    {comparing ? 'Retrying...' : '🔄 Retry Comparison'}
                  </button>
                )}
                <Link 
                  href="/demo"
                  className="px-8 py-4 text-lg font-bold text-white bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl hover:from-indigo-600 hover:to-purple-700 shadow-xl hover:scale-105 transition-all duration-300">
                  Go to Demo
                </Link>
                <Link 
                  href="/"
                  className="px-8 py-4 text-lg font-bold text-white bg-white/20 rounded-2xl hover:bg-white/30 shadow-xl hover:scale-105 transition-all duration-300">
                  Go Home
                </Link>
              </div>
            </div>
          </div>
        )}
        
        {/* Comparing State */}
        {comparing && (
          <div className="flex flex-col items-center justify-center min-h-[60vh]">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-white mb-4"></div>
            <p className="text-white text-2xl font-bold mb-2">Running Comparison...</p>
            <p className="text-white/60 text-sm">Compiling and measuring performance on RISC-V</p>
            <p className="text-white/60 text-sm mt-1">This may take 10-20 seconds</p>
          </div>
        )}

        {!loading && !error && !comparing && comparisonData && !comparisonResults && (
          <>
            {/* File Information */}
            <section className="glass-card p-6 rounded-2xl mb-6 animate-fade-in">
              <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">Source File</h2>
                  <p className="text-white/80 text-lg">
                    <strong className="text-white">{comparisonData.fileName}</strong>
                  </p>
                  <p className="text-white/60 text-sm mt-1">
                    Model: <span className="text-white capitalize">{comparisonData.modelUsed}</span> | 
                    Processed: {new Date(comparisonData.timestamp).toLocaleString()}
                  </p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleRunComparison}
                    className="px-8 py-4 text-lg font-bold text-white bg-gradient-to-r from-pink-500 to-rose-600 rounded-2xl hover:from-pink-600 hover:to-rose-700 shadow-xl hover:scale-105 transition-all duration-300">
                    ⚡ Run Comparison
                  </button>
                  <button
                    onClick={handleGoBack}
                    className="px-6 py-3 font-bold text-white bg-white/20 rounded-xl hover:bg-white/30 transition-all hover:scale-105">
                    ← Back
                  </button>
                </div>
              </div>
            </section>

            {/* ML Predicted Passes */}
            <section className="glass-card p-6 rounded-2xl mb-6 animate-slide-in">
              <h2 className="text-2xl font-bold text-white mb-4">ML-Predicted Pass Sequence</h2>
              <div className="bg-black/30 p-4 rounded-xl">
                <p className="text-white/70 text-sm mb-2">Passes ({comparisonData.predictedPasses.length}):</p>
                <div className="flex flex-wrap gap-2">
                  {comparisonData.predictedPasses.map((pass, index) => (
                    <span key={index} className="px-3 py-1 bg-indigo-500/30 text-white rounded-lg text-sm font-medium">
                      {pass}
                    </span>
                  ))}
                </div>
              </div>
            </section>
            
            {/* Ready to compare message */}
            <div className="mt-8 text-center animate-fade-in glass-card p-12 rounded-2xl">
              <span className="text-6xl block mb-6">🚀</span>
              <p className="text-2xl text-white/90 font-bold mb-4">Ready to Compare!</p>
              <p className="text-white/70 text-lg mb-8">
                Click "Run Comparison" to see how ML-predicted passes perform against standard LLVM optimization levels.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="glass p-6 rounded-xl">
                  <p className="text-white/60 text-sm mb-2">Source Lines</p>
                  <p className="text-white text-2xl font-bold">{comparisonData.sourceCode.split('\n').length}</p>
                </div>
                <div className="glass p-6 rounded-xl">
                  <p className="text-white/60 text-sm mb-2">Predicted Passes</p>
                  <p className="text-white text-2xl font-bold">{comparisonData.predictedPasses.length}</p>
                </div>
                <div className="glass p-6 rounded-xl">
                  <p className="text-white/60 text-sm mb-2">Model Used</p>
                  <p className="text-white text-2xl font-bold capitalize">{comparisonData.modelUsed}</p>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Comparison Results */}
        {!loading && !error && !comparing && comparisonResults && comparisonData && (
          <ComparisonUI
            results={comparisonResults}
            fileName={comparisonData.fileName}
            onBackClick={handleGoBack}
            onDownloadReport={handleDownloadReport}
            onTryAnother={handleTryAnother}
          />
        )}
      </main>
    </Layout>
  );
}
