import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

const App = dynamic(() => import('../src/App'), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
      <div className="text-center space-y-3">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-500 mx-auto"></div>
        <p className="text-sm font-semibold tracking-wide text-indigo-400">Loading SupportNova Next.js Intelligence Console...</p>
      </div>
    </div>
  )
});

export default function Home() {
  return <App />;
}
