/**
 * LLVM Optimization Demo Component
 * Example component showing how to use the simplified LLVM backend
 */

'use client';

import React, { useState, useEffect } from 'react';
import { llvmService } from '@/services/llvmService';

export default function OptimizationDemo() {
  const [code, setCode] = useState('');
  const [selectedPasses, setSelectedPasses] = useState<string[]>(['mem2reg', 'simplifycfg', 'instcombine']);
  const [customPass, setCustomPass] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);

  // Example programs
  const examplePrograms = llvmService.getExamplePrograms();
  const examplePasses = llvmService.getExamplePasses();

  // Check backend health on mount
  useEffect(() => {
    llvmService.checkHealth().then(setBackendHealthy);
  }, []);

  // Load first example program by default
  useEffect(() => {
    if (examplePrograms.length > 0) {
      setCode(examplePrograms[0].code);
    }
  }, []);

  const handleExtractFeatures = async () => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    const result = await llvmService.extractFeatures(code);
    
    setIsLoading(false);
    if (result.success) {
      setResults({
        type: 'features',
        data: result
      });
    } else {
      setError(result.error || 'Feature extraction failed');
    }
  };

  const handleRunOptimization = async () => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    const result = await llvmService.runOptimization(code, selectedPasses);
    
    setIsLoading(false);
    if (result.success) {
      setResults({
        type: 'optimization',
        data: result
      });
    } else {
      setError(result.error || 'Optimization failed');
    }
  };

  const handleCompare = async () => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    const result = await llvmService.compareOptimizations(code, selectedPasses);
    
    setIsLoading(false);
    if (result.success) {
      setResults({
        type: 'comparison',
        data: result
      });
    } else {
      setError(result.error || 'Comparison failed');
    }
  };

  const addCustomPass = () => {
    if (customPass && !selectedPasses.includes(customPass)) {
      setSelectedPasses([...selectedPasses, customPass]);
      setCustomPass('');
    }
  };

  const removePass = (pass: string) => {
    setSelectedPasses(selectedPasses.filter(p => p !== pass));
  };

  const loadExampleProgram = (program: typeof examplePrograms[0]) => {
    setCode(program.code);
    setError(null);
    setResults(null);
  };

  const loadExamplePasses = (passes: string[]) => {
    setSelectedPasses(passes);
    setError(null);
    setResults(null);
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">LLVM Optimization Demo</h2>
        
        {/* Backend Status */}
        <div className="mb-4">
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${
            backendHealthy === true ? 'bg-green-100 text-green-800' :
            backendHealthy === false ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            <span className={`w-2 h-2 rounded-full mr-2 ${
              backendHealthy === true ? 'bg-green-500' :
              backendHealthy === false ? 'bg-red-500' :
              'bg-gray-500'
            }`}></span>
            Backend: {backendHealthy === true ? 'Connected' : backendHealthy === false ? 'Disconnected' : 'Checking...'}
          </div>
        </div>

        {/* Example Programs */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Example Programs</h3>
          <div className="flex gap-2 flex-wrap">
            {examplePrograms.map((program) => (
              <button
                key={program.name}
                onClick={() => loadExampleProgram(program)}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                {program.name}
              </button>
            ))}
          </div>
        </div>

        {/* Code Editor */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">C Source Code</h3>
          <textarea
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="w-full h-64 p-3 border rounded-lg font-mono text-sm"
            placeholder="Enter your C code here..."
          />
        </div>

        {/* Optimization Passes */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-2">Optimization Passes</h3>
          
          {/* Example Pass Sequences */}
          <div className="mb-3">
            <label className="text-sm text-gray-600">Load example sequences:</label>
            <div className="flex gap-2 flex-wrap mt-1">
              {examplePasses.map((passes, idx) => (
                <button
                  key={idx}
                  onClick={() => loadExamplePasses(passes)}
                  className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
                >
                  Sequence {idx + 1} ({passes.length} passes)
                </button>
              ))}
            </div>
          </div>

          {/* Selected Passes */}
          <div className="mb-3">
            <label className="text-sm text-gray-600">Selected passes:</label>
            <div className="flex gap-2 flex-wrap mt-1">
              {selectedPasses.map((pass) => (
                <span
                  key={pass}
                  className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                >
                  {pass}
                  <button
                    onClick={() => removePass(pass)}
                    className="ml-2 text-blue-600 hover:text-blue-800"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Add Custom Pass */}
          <div className="flex gap-2">
            <input
              type="text"
              value={customPass}
              onChange={(e) => setCustomPass(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addCustomPass()}
              placeholder="Add custom pass..."
              className="flex-1 px-3 py-2 border rounded"
            />
            <button
              onClick={addCustomPass}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              Add Pass
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mb-6 flex gap-3">
          <button
            onClick={handleExtractFeatures}
            disabled={isLoading || !code || !backendHealthy}
            className="px-6 py-3 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:bg-gray-400"
          >
            Extract Features
          </button>
          <button
            onClick={handleRunOptimization}
            disabled={isLoading || !code || selectedPasses.length === 0 || !backendHealthy}
            className="px-6 py-3 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-400"
          >
            Run ML Optimization
          </button>
          <button
            onClick={handleCompare}
            disabled={isLoading || !code || selectedPasses.length === 0 || !backendHealthy}
            className="px-6 py-3 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
          >
            Compare with Standard
          </button>
        </div>

        {/* Loading Indicator */}
        {isLoading && (
          <div className="mb-6 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <p className="mt-2 text-gray-600">Processing...</p>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-100 text-red-700 rounded">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Results Display */}
        {results && (
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">
              {results.type === 'features' && 'Feature Extraction Results'}
              {results.type === 'optimization' && 'ML Optimization Results'}
              {results.type === 'comparison' && 'Comparison Results'}
            </h3>

            {/* Features Results */}
            {results.type === 'features' && (
              <div>
                <p className="mb-2">
                  <strong>Features Extracted:</strong> {results.data.feature_count}
                </p>
                <div className="max-h-64 overflow-y-auto">
                  <pre className="text-sm bg-white p-3 rounded">
                    {JSON.stringify(results.data.features, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Optimization Results */}
            {results.type === 'optimization' && results.data.metrics && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <strong>Execution Time:</strong> {results.data.metrics.execution_time_avg.toFixed(6)}s
                </div>
                <div>
                  <strong>Binary Size:</strong> {results.data.metrics.binary_size.toLocaleString()} bytes
                </div>
                <div>
                  <strong>Optimization Time:</strong> {results.data.metrics.optimization_time.toFixed(4)}s
                </div>
                <div>
                  <strong>Pass Count:</strong> {results.data.metrics.pass_count}
                </div>
              </div>
            )}

            {/* Comparison Results */}
            {results.type === 'comparison' && results.data.comparison && (
              <div>
                {/* ML Optimization Metrics */}
                {results.data.ml_optimization && (
                  <div className="mb-4">
                    <h4 className="font-semibold mb-2">ML Optimization</h4>
                    <div className="grid grid-cols-2 gap-2">
                      <div>Execution Time: {results.data.ml_optimization.execution_time_avg?.toFixed(6)}s</div>
                      <div>Binary Size: {results.data.ml_optimization.binary_size?.toLocaleString()} bytes</div>
                    </div>
                  </div>
                )}

                {/* Comparison with Standard */}
                <div>
                  <h4 className="font-semibold mb-2">Comparison with Standard Optimizations</h4>
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="bg-gray-200">
                        <th className="border p-2">Level</th>
                        <th className="border p-2">Speedup</th>
                        <th className="border p-2">Size Reduction</th>
                        <th className="border p-2">ML Faster?</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(results.data.comparison)
                        .filter(([key]) => key !== 'vs_best')
                        .map(([level, comp]: [string, any]) => (
                          <tr key={level}>
                            <td className="border p-2">{level}</td>
                            <td className="border p-2">{comp.speedup?.toFixed(2)}x</td>
                            <td className="border p-2">{(comp.size_reduction * 100)?.toFixed(1)}%</td>
                            <td className="border p-2">
                              <span className={comp.ml_faster ? 'text-green-600' : 'text-red-600'}>
                                {comp.ml_faster ? 'Yes' : 'No'}
                              </span>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>

                  {/* Best Standard Comparison */}
                  {results.data.comparison.vs_best && (
                    <div className="mt-4 p-3 bg-blue-50 rounded">
                      <strong>Best Standard:</strong> {results.data.comparison.vs_best.best_standard} | 
                      <strong> ML Beats Best:</strong> {results.data.comparison.vs_best.ml_beats_best ? 'Yes' : 'No'} | 
                      <strong> Speedup vs Best:</strong> {results.data.comparison.vs_best.speedup_vs_best?.toFixed(2)}x
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
