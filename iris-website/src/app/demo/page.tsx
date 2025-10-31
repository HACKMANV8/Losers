'use client';

import { useState, useEffect } from 'react';
import Layout from '../components/Layout';

export default function DemoPage() {
  const [programs, setPrograms] = useState<string[]>([]);
  const [selectedProgram, setSelectedProgram] = useState<string>('');
  const [features, setFeatures] = useState<any>(null);
  const [generatedSequence, setGeneratedSequence] = useState<string[]>([]);
  const [referenceSequence, setReferenceSequence] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPrograms() {
      try {
        const res = await fetch('http://127.0.0.1:5001/programs');
        if (!res.ok) {
          throw new Error('Failed to fetch programs');
        }
        const data = await res.json();
        setPrograms(data);
      } catch (err: any) {
        setError(err.message);
      }
    }
    fetchPrograms();
  }, []);

  const handleOptimize = async () => {
    if (!selectedProgram) {
      setError('Please select a program first.');
      return;
    }
    setLoading(true);
    setError(null);
    setGeneratedSequence([]);
    setReferenceSequence([]);
    setFeatures(null);

    try {
      const res = await fetch('http://127.0.0.1:5001/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ program: selectedProgram }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || 'Optimization failed');
      }

      const data = await res.json();
      setFeatures(data.features);
      setGeneratedSequence(data.generated_sequence);
      setReferenceSequence(data.reference_sequence);
    } catch (err: any) {
      setError(err.message || 'An error occurred during optimization.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-8">
        <h1 className="text-4xl font-bold text-center mb-8">AI Optimizer Demo</h1>

        <div className="max-w-4xl mx-auto bg-white dark:bg-gray-800 shadow-lg rounded-lg p-6">
          <div className="mb-6">
            <label htmlFor="program-select" className="block text-lg font-medium mb-2">
              Select a Program:
            </label>
            <select
              id="program-select"
              className="w-full p-3 border border-gray-300 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-indigo-500 focus:border-indigo-500"
              value={selectedProgram}
              onChange={(e) => setSelectedProgram(e.target.value)}
            >
              <option value="">-- Please choose a program --</option>
              {programs.map((program) => (
                <option key={program} value={program}>
                  {program}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleOptimize}
            disabled={loading || !selectedProgram}
            className="w-full px-6 py-3 text-lg font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Optimizing...' : 'Optimize Program'}
          </button>

          {error && (
            <div className="mt-4 text-red-500 text-center">
              {error}
            </div>
          )}

          {features && (
            <div className="mt-8 border-t border-gray-200 dark:border-gray-700 pt-6">
              <h2 className="text-2xl font-semibold mb-4">Optimization Results</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <h3 className="text-xl font-medium mb-2">Program Features:</h3>
                  <ul className="list-disc list-inside bg-gray-50 dark:bg-gray-700 p-4 rounded-md">
                    {Object.entries(features).map(([key, value]) => (
                      <li key={key}>
                        <span className="font-semibold">{key}:</span> {String(value)}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="text-xl font-medium mb-2">Reference Optimal Sequence:</h3>
                  <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-md">
                    <p className="font-mono text-sm break-all">{referenceSequence.join(', ')}</p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-xl font-medium mb-2">Generated Pass Sequence:</h3>
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-md">
                  <p className="font-mono text-sm break-all">{generatedSequence.join(', ')}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}