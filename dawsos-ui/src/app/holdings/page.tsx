'use client';

import { HoldingsDetail } from '@/components/HoldingsDetail';

// Force dynamic rendering
export const dynamic = 'force-dynamic'

export default function HoldingsPage() {
  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('/api/v1/portfolios/main-portfolio/upload-holdings', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      const result = await response.json();
      alert(`Upload complete: ${result.successful} successful, ${result.failed} failed`);
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              Holdings Detail
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Detailed analysis of individual holdings and positions
            </p>
          </div>
          
          <label className="px-6 py-3 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700">
            Upload CSV
            <input
              type="file"
              accept=".csv,.xlsx"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
            />
          </label>
        </div>
        
        <HoldingsDetail portfolioId="main-portfolio" />
      </div>
    </div>
  );
}
