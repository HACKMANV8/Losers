'use client';

import Layout from '../components/Layout';

export default function Team() {
  return (
    <Layout>
      <main className="min-h-screen p-8 max-w-6xl mx-auto text-center">
        <h1 className="text-5xl font-bold mb-8 text-white drop-shadow-lg animate-fade-in">Meet the Team</h1>
        
        <p className="text-xl text-white/90 mb-16 max-w-3xl mx-auto animate-slide-in">
          Passionate researchers and engineers dedicated to pushing the boundaries of compiler technology and machine learning.
        </p>
        
        <section className="grid grid-cols-1 md:grid-cols-3 gap-8 animate-scale-in">
          <article className="glass-card p-8 rounded-2xl hover:bg-white/20 transition-all duration-300 hover:scale-105">
            <h2 className="text-2xl font-bold text-white mb-3">Team Member</h2>
            <p className="text-white/70">Role & Contribution</p>
          </article>
          <article className="glass-card p-8 rounded-2xl hover:bg-white/20 transition-all duration-300 hover:scale-105">
            <h2 className="text-2xl font-bold text-white mb-3">Team Member</h2>
            <p className="text-white/70">Role & Contribution</p>
          </article>
          <article className="glass-card p-8 rounded-2xl hover:bg-white/20 transition-all duration-300 hover:scale-105">
            <h2 className="text-2xl font-bold text-white mb-3">Team Member</h2>
            <p className="text-white/70">Role & Contribution</p>
          </article>
        </section>
        
        <div className="mt-16 animate-fade-in">
          <p className="text-2xl text-white/70">Team profiles coming soon...</p>
          <p className="mt-4 text-white/50">Get to know the brilliant minds behind IRis!</p>
        </div>
      </main>
    </Layout>
  );
}
