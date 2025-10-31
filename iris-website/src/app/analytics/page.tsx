'use client';

import Layout from '../components/Layout';

export default function Analytics() {
  return (
    <Layout>
      <main className="min-h-screen p-8 max-w-6xl mx-auto">
        <h1 className="text-5xl font-bold mb-12 text-center text-white drop-shadow-lg animate-fade-in">Analytics Dashboard</h1>
        
        <section className="grid grid-cols-1 md:grid-cols-3 gap-8 animate-slide-in">
          <article className="glass-card p-8 rounded-2xl hover:bg-white/20 transition-all duration-300 hover:scale-105">
            <h2 className="text-2xl font-bold text-white mb-3">Model Accuracy</h2>
            <p className="text-white/80">Performance metrics and accuracy scores</p>
          </article>
          <article className="glass-card p-8 rounded-2xl hover:bg-white/20 transition-all duration-300 hover:scale-105">
            <h2 className="text-2xl font-bold text-white mb-3">Optimization Gains</h2>
            <p className="text-white/80">Runtime and size improvements</p>
          </article>
          <article className="glass-card p-8 rounded-2xl hover:bg-white/20 transition-all duration-300 hover:scale-105">
            <h2 className="text-2xl font-bold text-white mb-3">Training Progress</h2>
            <p className="text-white/80">Model training statistics</p>
          </article>
        </section>
        
        <div className="mt-16 text-center animate-fade-in">
          <p className="text-2xl text-white/70">Analytics dashboard coming soon...</p>
          <p className="mt-4 text-white/50">Stay tuned for performance metrics and insights!</p>
        </div>
      </main>
    </Layout>
  );
}
