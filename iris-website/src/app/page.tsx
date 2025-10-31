'use client';

import Link from 'next/link';
import FlowDiagram from './components/FlowDiagram';
import Layout from './components/Layout';

export default function Home() {
  return (
    <Layout>
      <div className="flex flex-col items-center justify-center text-center space-y-8 p-4">
        <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
          IRis — ML-Guided Compiler Optimization
        </h1>
        <p className="mt-3 text-xl text-gray-600 dark:text-gray-300 max-w-2xl">
          Using machine learning to optimize compiler pass sequences for better runtime and binary size.
        </p>
        <div className="mt-10">
          <FlowDiagram />
        </div>
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/demo" className="px-8 py-3 text-lg font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900">
            Try Demo
          </Link>
          <Link href="/analytics" className="px-8 py-3 text-lg font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900">
            View Analytics
          </Link>
          <Link href="/comparison" className="px-8 py-3 text-lg font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900">
            Compare with LLVM
          </Link>
        </div>

        <section className="mt-20 text-center max-w-4xl">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">About the Project</h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
            IRis is a research project aimed at exploring the potential of machine learning in compiler optimization. We leverage state-of-the-art models to predict optimal compiler pass sequences, leading to significant improvements in program performance and size.
          </p>
        </section>

        <section className="mt-20 text-center max-w-4xl">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Meet the Team</h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
            Our team is composed of passionate researchers and engineers dedicated to pushing the boundaries of compiler technology. 
            <Link href="/team" className="text-indigo-600 dark:text-indigo-400 hover:underline">Learn more about us.</Link>
          </p>
        </section>

        <footer className="mt-20 text-gray-500 dark:text-gray-400">
          <p>&copy; {new Date().getFullYear()} IRis. All rights reserved.</p>
        </footer>
      </div>
    </Layout>
  );
}