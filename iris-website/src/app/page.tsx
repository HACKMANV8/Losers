'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100 flex flex-col items-center justify-center p-4">
      <main className="flex flex-col items-center justify-center text-center space-y-8">
        <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
          Welcome to <span className="text-indigo-600 dark:text-indigo-400">IRis</span>
        </h1>
        <p className="mt-3 text-xl text-gray-600 dark:text-gray-300 max-w-2xl">
          Your AI-powered compiler optimization assistant. Discover optimal pass sequences for your programs.
        </p>
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/demo" className="px-8 py-3 text-lg font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900">
            Start Optimizing
          </Link>
          {/* <Link href="/about" className="px-8 py-3 text-lg font-medium text-indigo-600 bg-white rounded-md ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:bg-gray-800 dark:text-indigo-400 dark:ring-gray-700 dark:hover:bg-gray-700 dark:focus:ring-offset-gray-900">
            Learn More
          </Link> */}
        </div>
      </main>

      <footer className="mt-20 text-gray-500 dark:text-gray-400">
        <p>&copy; {new Date().getFullYear()} IRis. All rights reserved.</p>
      </footer>
    </div>
  );
}