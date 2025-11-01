'use client';

import Link from 'next/link';
import FlowDiagram from './components/FlowDiagram';
import Layout from './components/Layout';

export default function Home() {
  return (
    <Layout>
      <main className="flex flex-col items-center justify-center text-center space-y-16 p-8 min-h-screen max-w-6xl mx-auto">
        
        <h1 className="text-5xl md:text-6xl font-bold text-white drop-shadow-2xl animate-fade-in">
          IRis
          <span className="block text-3xl md:text-4xl font-normal mt-2 text-white/80">ML-Guided Compiler Optimization</span>
        </h1>
        
        <p className="text-xl md:text-2xl text-white/90 max-w-3xl font-medium animate-slide-in">
          Using machine learning to optimize compiler pass sequences for better runtime and binary size.
        </p>

        <div className="animate-float">
          <FlowDiagram />
        </div>

        <nav className="flex flex-wrap justify-center gap-4 animate-scale-in">
          <Link href="/demo" className="px-8 py-4 text-lg font-bold text-white bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl hover:from-indigo-600 hover:to-purple-700 shadow-xl hover:scale-105 transition-all duration-300">
            Try Demo
          </Link>
          <Link href="/analytics" className="px-8 py-4 text-lg font-bold text-white bg-gradient-to-r from-purple-500 to-pink-600 rounded-2xl hover:from-purple-600 hover:to-pink-700 shadow-xl hover:scale-105 transition-all duration-300">
            Analytics
          </Link>
          <Link href="/comparison" className="px-8 py-4 text-lg font-bold text-white bg-gradient-to-r from-pink-500 to-rose-600 rounded-2xl hover:from-pink-600 hover:to-rose-700 shadow-xl hover:scale-105 transition-all duration-300">
            Compare
          </Link>
        </nav>

        <section className="glass-card p-10 rounded-3xl max-w-4xl w-full animate-fade-in">
          <h2 className="text-3xl font-bold text-white mb-6">About the Project</h2>
          <p className="text-lg text-white/90 leading-relaxed">
            IRis is a research project that leverages state-of-the-art machine learning models to predict optimal compiler pass sequences, leading to significant improvements in program performance and binary size.
          </p>
        </section>

        <footer className="text-white/60 text-sm pt-8 animate-fade-in">
          <p>© {new Date().getFullYear()} IRis. All rights reserved. | <Link href="/team" className="underline hover:text-white/80">Meet the Team</Link></p>
        </footer>
      </main>
    </Layout>
  );
}