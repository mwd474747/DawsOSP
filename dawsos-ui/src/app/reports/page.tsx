'use client'

import { useState } from 'react'
import { FileText, Download, Clock, CheckCircle, Calendar, Filter, FileDown } from 'lucide-react'

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState('generate')
  const [reportType, setReportType] = useState('comprehensive')
  const [dateRange, setDateRange] = useState('MTD')
  const [generating, setGenerating] = useState(false)

  const generateReport = async () => {
    setGenerating(true)
    // Simulate report generation
    setTimeout(() => {
      setGenerating(false)
      alert('Report generated successfully!')
    }, 3000)
  }

  // Sample report history
  const reportHistory = [
    {
      id: 1,
      name: 'October 2025 Portfolio Report',
      type: 'Monthly',
      generated: '2025-10-31 09:00:00',
      size: '2.4 MB',
      pages: 28,
      status: 'ready'
    },
    {
      id: 2,
      name: 'Q3 2025 Performance Analysis',
      type: 'Quarterly',
      generated: '2025-10-01 12:00:00',
      size: '4.8 MB',
      pages: 45,
      status: 'ready'
    },
    {
      id: 3,
      name: 'Risk Assessment Report',
      type: 'Risk',
      generated: '2025-10-28 15:30:00',
      size: '1.8 MB',
      pages: 18,
      status: 'ready'
    },
    {
      id: 4,
      name: 'Tax Optimization Report',
      type: 'Tax',
      generated: '2025-10-15 10:15:00',
      size: '3.2 MB',
      pages: 35,
      status: 'ready'
    }
  ]

  // Report templates
  const reportTemplates = [
    {
      name: 'Comprehensive Portfolio Report',
      id: 'comprehensive',
      description: 'Full portfolio analysis including performance, risk, attribution, and holdings',
      sections: ['Performance', 'Risk Analytics', 'Attribution', 'Holdings', 'Transactions'],
      pages: '25-30'
    },
    {
      name: 'Executive Summary',
      id: 'executive',
      description: 'High-level overview for executive review',
      sections: ['KPIs', 'Performance Summary', 'Key Risks', 'Recommendations'],
      pages: '5-8'
    },
    {
      name: 'Risk Analysis Report',
      id: 'risk',
      description: 'Detailed risk metrics and exposure analysis',
      sections: ['VaR Analysis', 'Stress Tests', 'Factor Exposures', 'Concentration'],
      pages: '15-20'
    },
    {
      name: 'Tax Report',
      id: 'tax',
      description: 'Tax-loss harvesting and realized gains/losses',
      sections: ['Realized Gains/Losses', 'Tax Lots', 'Harvesting Opportunities'],
      pages: '10-15'
    },
    {
      name: 'Compliance Report',
      id: 'compliance',
      description: 'Regulatory compliance and audit trail',
      sections: ['Position Limits', 'Trade Compliance', 'Audit Trail', 'Violations'],
      pages: '12-18'
    }
  ]

  // Export formats
  const exportFormats = [
    { format: 'PDF', icon: '📄', description: 'Portable Document Format' },
    { format: 'Excel', icon: '📊', description: 'Microsoft Excel Workbook' },
    { format: 'CSV', icon: '📁', description: 'Comma-Separated Values' },
    { format: 'JSON', icon: '{ }', description: 'JavaScript Object Notation' }
  ]

  return (
    <div className="space-y-6">
      <header className="glass-card-dark">
        <h1 className="text-2xl font-bold text-blue-400">REPORT GENERATION CENTER</h1>
        <p className="text-slate-400 mt-2">
          Generate comprehensive portfolio reports and export data in multiple formats
        </p>
      </header>

      {/* Report Statistics */}
      <div className="grid grid-cols-5 gap-4">
        <div className="data-cell">
          <div className="data-label">Reports Generated</div>
          <div className="data-value">48</div>
          <div className="text-xs text-slate-500 mt-1">This month</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Last Report</div>
          <div className="data-value text-blue-400">Today</div>
          <div className="text-xs text-slate-500 mt-1">09:00 AM</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Scheduled</div>
          <div className="data-value">12</div>
          <div className="text-xs text-slate-500 mt-1">Automated</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Storage Used</div>
          <div className="data-value">124 MB</div>
          <div className="text-xs text-slate-500 mt-1">Of 1 GB</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Avg Generation</div>
          <div className="data-value profit">8.2s</div>
          <div className="text-xs text-slate-500 mt-1">Time</div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 p-1 glass-card-dark w-fit rounded-lg">
        {['generate', 'templates', 'history', 'scheduled', 'export'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm uppercase tracking-wider transition-all ${
              activeTab === tab
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Generate Report */}
      {activeTab === 'generate' && (
        <div className="grid grid-cols-2 gap-6">
          <div className="glass-card-dark">
            <h2 className="terminal-title mb-4">REPORT CONFIGURATION</h2>
            <div className="space-y-4">
              <div>
                <label className="data-label">Report Type</label>
                <select 
                  className="terminal-input w-full"
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                >
                  {reportTemplates.map(template => (
                    <option key={template.id} value={template.id}>
                      {template.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="data-label">Date Range</label>
                <div className="grid grid-cols-3 gap-2">
                  {['MTD', 'QTD', 'YTD', '1M', '3M', '1Y'].map(range => (
                    <button
                      key={range}
                      onClick={() => setDateRange(range)}
                      className={`py-2 rounded text-sm ${
                        dateRange === range
                          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          : 'bg-slate-800/30 text-slate-400 hover:bg-slate-800/50'
                      }`}
                    >
                      {range}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="data-label">Custom Date Range</label>
                <div className="flex gap-2">
                  <input type="date" className="terminal-input flex-1" defaultValue="2025-10-01" />
                  <input type="date" className="terminal-input flex-1" defaultValue="2025-10-31" />
                </div>
              </div>

              <div>
                <label className="data-label">Include Sections</label>
                <div className="space-y-2">
                  {['Performance Analysis', 'Risk Metrics', 'Holdings Detail', 'Transaction History', 'Attribution', 'Benchmarks'].map(section => (
                    <label key={section} className="flex items-center gap-2">
                      <input type="checkbox" defaultChecked />
                      <span className="text-sm">{section}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="data-label">Format</label>
                <select className="terminal-input w-full">
                  <option>PDF - Professional Report</option>
                  <option>Excel - Data Workbook</option>
                  <option>PowerPoint - Presentation</option>
                </select>
              </div>

              <button 
                onClick={generateReport}
                disabled={generating}
                className="btn-terminal w-full"
              >
                {generating ? 'GENERATING...' : 'GENERATE REPORT'}
              </button>
            </div>
          </div>

          <div className="glass-card-dark">
            <h2 className="terminal-title mb-4">PREVIEW</h2>
            <div className="bg-slate-800/30 rounded-lg p-6 h-[500px] flex flex-col">
              <div className="text-center mb-4">
                <FileText size={48} className="text-blue-400 mx-auto mb-2" />
                <h3 className="text-lg font-bold">
                  {reportTemplates.find(t => t.id === reportType)?.name}
                </h3>
                <p className="text-sm text-slate-400 mt-2">
                  {reportTemplates.find(t => t.id === reportType)?.description}
                </p>
              </div>

              <div className="flex-1 space-y-3">
                <h4 className="text-sm font-semibold text-slate-400">SECTIONS TO INCLUDE:</h4>
                {reportTemplates.find(t => t.id === reportType)?.sections.map(section => (
                  <div key={section} className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-400" />
                    <span className="text-sm">{section}</span>
                  </div>
                ))}
              </div>

              <div className="pt-4 border-t border-slate-700">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Estimated Pages:</span>
                  <span>{reportTemplates.find(t => t.id === reportType)?.pages}</span>
                </div>
                <div className="flex justify-between text-sm mt-2">
                  <span className="text-slate-400">Generation Time:</span>
                  <span>~10 seconds</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Report Templates */}
      {activeTab === 'templates' && (
        <div className="glass-card-dark">
          <div className="terminal-header">
            <h2 className="terminal-title">Available Report Templates</h2>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {reportTemplates.map(template => (
              <div key={template.id} className="p-4 bg-slate-800/30 rounded-lg hover:bg-slate-800/50 transition-colors">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-blue-400">{template.name}</h3>
                  <span className="text-xs text-slate-500">{template.pages} pages</span>
                </div>
                <p className="text-sm text-slate-400 mb-3">{template.description}</p>
                <div className="space-y-1 mb-4">
                  {template.sections.slice(0, 3).map(section => (
                    <div key={section} className="text-xs text-slate-500">• {section}</div>
                  ))}
                  {template.sections.length > 3 && (
                    <div className="text-xs text-slate-500">• +{template.sections.length - 3} more sections</div>
                  )}
                </div>
                <div className="flex gap-2">
                  <button className="btn-terminal text-xs flex-1">USE TEMPLATE</button>
                  <button className="text-blue-400 hover:text-blue-300 text-xs">CUSTOMIZE</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Report History */}
      {activeTab === 'history' && (
        <div className="glass-card-dark">
          <div className="terminal-header">
            <h2 className="terminal-title">Report History</h2>
            <div className="flex gap-2">
              <button className="text-blue-400 hover:text-blue-300 text-xs uppercase">
                <Filter size={14} className="inline mr-1" />
                Filter
              </button>
            </div>
          </div>
          <table className="terminal-table">
            <thead>
              <tr>
                <th>Report Name</th>
                <th>Type</th>
                <th>Generated</th>
                <th>Size</th>
                <th>Pages</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {reportHistory.map(report => (
                <tr key={report.id}>
                  <td className="font-semibold">{report.name}</td>
                  <td>
                    <span className="badge badge-info">{report.type}</span>
                  </td>
                  <td className="text-xs">{report.generated}</td>
                  <td>{report.size}</td>
                  <td>{report.pages}</td>
                  <td>
                    <span className="badge badge-success">READY</span>
                  </td>
                  <td>
                    <div className="flex gap-2">
                      <button className="text-blue-400 hover:text-blue-300 text-xs">
                        <Download size={14} className="inline" />
                      </button>
                      <button className="text-blue-400 hover:text-blue-300 text-xs">VIEW</button>
                      <button className="text-red-400 hover:text-red-300 text-xs">DELETE</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Scheduled Reports */}
      {activeTab === 'scheduled' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Scheduled Reports</h2>
              <button className="btn-terminal">ADD SCHEDULE</button>
            </div>
            <table className="terminal-table">
              <thead>
                <tr>
                  <th>Report</th>
                  <th>Frequency</th>
                  <th>Next Run</th>
                  <th>Recipients</th>
                  <th>Format</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Monthly Portfolio Report</td>
                  <td>Monthly (1st)</td>
                  <td>2025-11-01 09:00</td>
                  <td>3 recipients</td>
                  <td>PDF</td>
                  <td><span className="badge badge-success">ACTIVE</span></td>
                  <td>
                    <button className="text-blue-400 hover:text-blue-300 text-xs">EDIT</button>
                  </td>
                </tr>
                <tr>
                  <td>Weekly Risk Summary</td>
                  <td>Weekly (Monday)</td>
                  <td>2025-11-04 08:00</td>
                  <td>5 recipients</td>
                  <td>PDF</td>
                  <td><span className="badge badge-success">ACTIVE</span></td>
                  <td>
                    <button className="text-blue-400 hover:text-blue-300 text-xs">EDIT</button>
                  </td>
                </tr>
                <tr>
                  <td>Daily NAV Report</td>
                  <td>Daily (16:00)</td>
                  <td>2025-10-31 16:00</td>
                  <td>2 recipients</td>
                  <td>Excel</td>
                  <td><span className="badge badge-success">ACTIVE</span></td>
                  <td>
                    <button className="text-blue-400 hover:text-blue-300 text-xs">EDIT</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="glass-card-dark">
            <h3 className="terminal-title mb-4">Schedule Configuration</h3>
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="data-label">Report Template</label>
                  <select className="terminal-input w-full">
                    <option>Monthly Portfolio Report</option>
                    <option>Executive Summary</option>
                    <option>Risk Analysis</option>
                  </select>
                </div>
                <div>
                  <label className="data-label">Frequency</label>
                  <select className="terminal-input w-full">
                    <option>Daily</option>
                    <option>Weekly</option>
                    <option>Monthly</option>
                    <option>Quarterly</option>
                  </select>
                </div>
                <div>
                  <label className="data-label">Time</label>
                  <input type="time" className="terminal-input w-full" defaultValue="09:00" />
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="data-label">Recipients</label>
                  <textarea 
                    className="terminal-input w-full h-24" 
                    placeholder="Enter email addresses (one per line)"
                  />
                </div>
                <div>
                  <label className="data-label">Format</label>
                  <select className="terminal-input w-full">
                    <option>PDF</option>
                    <option>Excel</option>
                    <option>Both</option>
                  </select>
                </div>
                <button className="btn-terminal w-full">CREATE SCHEDULE</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Data Export */}
      {activeTab === 'export' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Data Export Center</h2>
            </div>
            <div className="grid grid-cols-3 gap-6">
              <div>
                <h3 className="text-sm font-semibold text-slate-400 mb-4">DATA SELECTION</h3>
                <div className="space-y-3">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" defaultChecked />
                    <span className="text-sm">Portfolio Holdings</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" defaultChecked />
                    <span className="text-sm">Transaction History</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" />
                    <span className="text-sm">Performance Metrics</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" />
                    <span className="text-sm">Risk Analytics</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" />
                    <span className="text-sm">Attribution Data</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" />
                    <span className="text-sm">Market Data</span>
                  </label>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-slate-400 mb-4">EXPORT FORMAT</h3>
                <div className="space-y-3">
                  {['CSV', 'Excel', 'JSON', 'XML', 'SQL'].map(format => (
                    <button
                      key={format}
                      className="w-full p-3 bg-slate-800/30 rounded-lg hover:bg-slate-800/50 text-left flex items-center justify-between"
                    >
                      <span>{format}</span>
                      <FileDown size={16} className="text-slate-400" />
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-slate-400 mb-4">EXPORT OPTIONS</h3>
                <div className="space-y-4">
                  <div>
                    <label className="data-label">Date Range</label>
                    <select className="terminal-input w-full">
                      <option>Last 30 Days</option>
                      <option>Last 90 Days</option>
                      <option>Year to Date</option>
                      <option>All Time</option>
                    </select>
                  </div>
                  <div>
                    <label className="data-label">Compression</label>
                    <select className="terminal-input w-full">
                      <option>None</option>
                      <option>ZIP</option>
                      <option>GZIP</option>
                    </select>
                  </div>
                  <button className="btn-terminal w-full">
                    <Download size={16} className="inline mr-2" />
                    EXPORT DATA
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="glass-card-dark">
            <h3 className="terminal-title mb-4">Recent Exports</h3>
            <table className="terminal-table">
              <thead>
                <tr>
                  <th>Export Name</th>
                  <th>Data Type</th>
                  <th>Format</th>
                  <th>Size</th>
                  <th>Created</th>
                  <th>Download</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Holdings_20251031.csv</td>
                  <td>Portfolio Holdings</td>
                  <td>CSV</td>
                  <td>245 KB</td>
                  <td>Today, 10:30 AM</td>
                  <td>
                    <button className="text-blue-400 hover:text-blue-300">
                      <Download size={16} />
                    </button>
                  </td>
                </tr>
                <tr>
                  <td>Transactions_Q3_2025.xlsx</td>
                  <td>Transactions</td>
                  <td>Excel</td>
                  <td>1.2 MB</td>
                  <td>Oct 30, 2:15 PM</td>
                  <td>
                    <button className="text-blue-400 hover:text-blue-300">
                      <Download size={16} />
                    </button>
                  </td>
                </tr>
                <tr>
                  <td>Performance_YTD.json</td>
                  <td>Performance Metrics</td>
                  <td>JSON</td>
                  <td>89 KB</td>
                  <td>Oct 29, 4:45 PM</td>
                  <td>
                    <button className="text-blue-400 hover:text-blue-300">
                      <Download size={16} />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}