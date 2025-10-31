'use client';

import { useState, useEffect } from 'react';
import Layout from '../components/Layout';

export default function Demo() {
  const [programs, setPrograms] = useState<string[]>([]);
  const [selectedProgram, setSelectedProgram] = useState<string>('');
  const [optimizing, setOptimizing] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    const fetchPrograms = async () => {
      try {
        const res = await fetch('http://localhost:5001/programs');
        if (res.ok) {
          const data = await res.json();
          setPrograms(data);
          if (data.length > 0) {
            setSelectedProgram(data[0]);
          }
        }
      } catch (error) {
        console.error('Error fetching programs:', error);
      }
    };
    fetchPrograms();
  }, []);

  const handleOptimize = async () => {
    if (!selectedProgram) return;

    setOptimizing(true);
    setResult(null);

    try {
      const res = await fetch('http://localhost:5001/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ program: selectedProgram }),
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else {
        console.error('Optimization failed');
      }
    } catch (error) {
      console.error('Error optimizing:', error);
    }

    setOptimizing(false);
  };

  return (
    <Layout>
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-4">
        <main className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold mb-8 text-center">Demo</h1>
          <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md">
            <div className="mb-6">
              <label htmlFor="program-select" className="block text-lg font-medium text-gray-700 dark:text-gray-300">Select a program</label>
              <select id="program-select" value={selectedProgram} onChange={(e) => setSelectedProgram(e.target.value)} className="mt-2 block w-full p-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm">
                {programs.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            <button onClick={handleOptimize} disabled={!selectedProgram || optimizing} className="w-full px-8 py-3 text-lg font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900">
              {optimizing ? 'Optimizing...' : 'Run Optimizer'}
            </button>
          </div>

          {result && (
            <div className="mt-8 bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md">
              <h2 className="text-2xl font-bold mb-4">Results</h2>
              <pre className="bg-gray-200 dark:bg-gray-700 p-4 rounded-md">{JSON.stringify(result, null, 2)}</pre>
            </div>
          )}
        </main>
      </div>
    </Layout>
  );
}

