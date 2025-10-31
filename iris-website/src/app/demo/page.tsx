'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import Layout from '../components/Layout';

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
  const [model, setModel] = useState('transformer');
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
    if (!results || !results.predicted_passes) return;
    const passesString = results.predicted_passes.join(', ');
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

    const formData = new FormData();
    formData.append('source_file', file);
    formData.append('model_selection', model);

    try {
      const res = await fetch('http://localhost:5001/api/optimize', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (res.ok && data.success) {
        setResults(data);
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
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-4 flex items-center justify-center">
        <main className="max-w-2xl w-full mx-auto">
          <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-2xl transition-all duration-300">
            
            {!results && (
              <div className="animate-fade-in">
                <h1 className="text-4xl font-bold mb-6 text-center text-gray-800 dark:text-white">IRis Optimizer</h1>
                
                {/* File Upload Area */}
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors duration-300 ${
                    isDragActive
                      ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                      : 'border-gray-300 dark:border-gray-600 hover:border-indigo-400 dark:hover:border-indigo-500'
                  }`}>
                  <input {...getInputProps()} />
                  {isDragActive ? (
                    <p className="text-indigo-600 dark:text-indigo-300">Drop the file here ...</p>
                  ) : (
                    <p className="text-gray-500 dark:text-gray-400">Drag & drop a C/C++ file here, or click to select</p>
                  )}
                </div>

                {/* File Preview */}
                {file && (
                  <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p className="font-semibold text-gray-700 dark:text-gray-200">Uploaded File:</p>
                    <p className="text-sm text-gray-600 dark:text-gray-300">{file.name} - {(file.size / 1024).toFixed(2)} KB</p>
                  </div>
                )}

                {/* Model Selector */}
                <div className="mt-6">
                  <p className="font-semibold text-gray-700 dark:text-gray-200 mb-2">Select Model:</p>
                  <div className="flex space-x-4">
                    <label className="flex items-center cursor-pointer">
                      <input type="radio" name="model" value="transformer" checked={model === 'transformer'} onChange={() => setModel('transformer')} className="form-radio h-5 w-5 text-indigo-600" />
                      <span className="ml-2 text-gray-700 dark:text-gray-300">Transformer</span>
                    </label>
                    <label className="flex items-center cursor-pointer">
                      <input type="radio" name="model" value="xgboost" checked={model === 'xgboost'} onChange={() => setModel('xgboost')} className="form-radio h-5 w-5 text-indigo-600" />
                      <span className="ml-2 text-gray-700 dark:text-gray-300">XGBoost</span>
                    </label>
                  </div>
                </div>

                {/* Submit Button */}
                <button 
                  onClick={handleSubmit} 
                  disabled={!file || loading}
                  className="w-full mt-8 px-8 py-3 text-lg font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-all duration-300 flex items-center justify-center">
                  {loading ? <Spinner /> : 'Optimize'}
                </button>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="mt-4 p-4 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg animate-fade-in">
                <p><span className="font-bold">Error:</span> {error}</p>
                <button onClick={handleClear} className="mt-4 px-4 py-2 text-sm font-medium text-white bg-gray-600 rounded-md hover:bg-gray-700">
                  Try Again
                </button>
              </div>
            )}

            {/* --- Enhanced Results Display --- */}
            {results && (
              <div className="animate-fade-in">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-2xl font-bold text-gray-800 dark:text-white">Optimization Results</h2>
                  <button onClick={handleClear} className="px-4 py-2 text-sm font-medium text-white bg-gray-600 rounded-md hover:bg-gray-700">
                    Optimize New File
                  </button>
                </div>

                {/* Summary Card */}
                <div className="mb-6">
                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg inline-block">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Model Used</p>
                    <p className="text-lg font-semibold text-indigo-600 dark:text-indigo-300 capitalize">{results.model_used}</p>
                  </div>
                </div>

                {/* Pass Sequence Card */}
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg mb-6">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-semibold">Predicted Pass Sequence</h3>
                    <div className="flex gap-3">
                      <button onClick={copyPasses} className="text-sm font-medium text-green-600 hover:text-green-500 dark:text-green-400 dark:hover:text-green-300">Copy</button>
                      <button onClick={downloadResults} className="text-sm font-medium text-indigo-600 hover:text-indigo-500">Download</button>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {results.predicted_passes.map((pass: string, index: number) => (
                      <div key={index} className="flex items-center px-3 py-1 bg-indigo-100 dark:bg-indigo-900/50 text-indigo-800 dark:text-indigo-200 rounded-full text-sm font-medium">
                        {getPassIcon(pass)}
                        <span>{pass}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Extracted Features Card */}
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-3">Extracted Program Features</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                    {Object.entries(results.features).map(([key, value]) => (
                      <div key={key} className="flex flex-col">
                        <span className="font-medium text-gray-500 dark:text-gray-400 capitalize">{key.replace(/_/g, ' ')}</span>
                        <span className="font-semibold text-lg">{typeof value === 'number' ? value.toFixed(2) : String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </Layout>
  );
}