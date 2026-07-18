import { useState } from 'react';

/**
 * Full-featured dashboard that integrates all components.
 * (Used as an alternative single-page entry point.)
 */
export default function Dashboard({ children }) {
  return (
    <div className="min-h-screen bg-dark text-slate-100">
      {children}
    </div>
  );
}
