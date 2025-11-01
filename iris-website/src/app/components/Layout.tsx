'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useState, useEffect } from 'react';

const StarsBackground = () => {
  useEffect(() => {
    const starsContainer = document.querySelector('.stars');
    if (!starsContainer) return;
    
    // Clear any existing stars
    starsContainer.innerHTML = '';
    
    // Create stars
    const starsCount = 150;
    for (let i = 0; i < starsCount; i++) {
      const star = document.createElement('div');
      star.className = 'star';
      
      // Random position
      const x = Math.random() * 100;
      const y = Math.random() * 100;
      star.style.left = `${x}%`;
      star.style.top = `${y}%`;
      
      // Random size
      const size = Math.random() * 3;
      star.style.width = `${size}px`;
      star.style.height = `${size}px`;
      
      // Random animation duration and delay
      const duration = Math.random() * 5 + 3;
      const delay = Math.random() * 5;
      star.style.setProperty('--duration', `${duration}s`);
      star.style.animationDelay = `${delay}s`;
      
      starsContainer.appendChild(star);
    }
  }, []);

  return <div className="stars" />;
};

const Layout = ({ children }: { children: React.ReactNode }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <>
      <StarsBackground />
      <div className="min-h-screen text-gray-900 dark:text-gray-100">
        <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/30 backdrop-blur-xl">
          <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-3">
                <Image 
                  src="/logo.png" 
                  alt="IRis Logo" 
                  width={40} 
                  height={40} 
                  className="rounded-xl"
                />
                <Link href="/" className="text-2xl font-bold text-white drop-shadow-lg hover:scale-105 transition-transform duration-200">
                  IRis
                </Link>
              </div>
            
            {/* Desktop Navigation */}
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-1">
                <Link href="/demo" className="text-white/90 hover:text-white hover:bg-white/20 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200">
                  Demo
                </Link>
                <Link href="/comparison" className="text-white/90 hover:text-white hover:bg-white/20 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200">
                  Comparison
                </Link>
              </div>
            </div>
            
            {/* Mobile menu button */}
            <div className="md:hidden">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="text-white hover:text-white/80 focus:outline-none focus:ring-2 focus:ring-white/30 rounded-md p-2"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  {mobileMenuOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
            </div>
          
          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="md:hidden glass-card border border-white/20 rounded-xl mt-2 mb-4 p-2">
              <div className="flex flex-col space-y-1">
                <Link href="/demo" className="text-white/90 hover:text-white hover:bg-white/20 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200">
                  Demo
                </Link>
                <Link href="/comparison" className="text-white/90 hover:text-white hover:bg-white/20 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200">
                  Comparison
                </Link>
              </div>
            </div>
          )}
        </div>
      </nav>
    </header>
    <main className="pt-16">{children}</main>
  </div>
</>);
};

export default Layout;