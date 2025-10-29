interface Report {
  id: string
  portfolio_id: string
  template_name: string
  generated_at: string
  file_size: number
  download_url: string
  attributions: string[]
  watermark: string | null
}

interface ReportHistoryProps {
  reports: Report[]
}

export function ReportHistory({ reports }: ReportHistoryProps) {
  const formatFileSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024)
    return `${mb.toFixed(1)} MB`
  }

  const formatTemplateName = (template: string) => {
    return template.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  return (
    <div className="metric-card">
      <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Report History</h3>
      
      <div className="space-y-fib4">
        {reports.map((report) => (
          <div key={report.id} className="border border-slate-200 rounded-fib3 p-fib4">
            <div className="flex items-start justify-between mb-fib3">
              <div>
                <h4 className="text-sm font-medium text-slate-900">
                  {formatTemplateName(report.template_name)}
                </h4>
                <div className="text-xs text-slate-600">
                  {new Date(report.generated_at).toLocaleString()}
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-600">{formatFileSize(report.file_size)}</div>
                <div className="text-xs text-slate-500">{report.portfolio_id}</div>
              </div>
            </div>

            {/* Attributions */}
            {report.attributions.length > 0 && (
              <div className="mb-fib3">
                <div className="text-xs text-slate-600 mb-fib1">Attributions:</div>
                <div className="space-y-fib1">
                  {report.attributions.map((attribution, index) => (
                    <div key={index} className="text-xs text-slate-500">
                      • {attribution}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Watermark */}
            {report.watermark && (
              <div className="mb-fib3">
                <div className="text-xs text-slate-600 mb-fib1">Watermark:</div>
                <div className="text-xs text-slate-500">{report.watermark}</div>
              </div>
            )}

            {/* Download Button */}
            <div className="flex items-center justify-between pt-fib3 border-t border-slate-200">
              <div className="text-xs text-slate-500">
                Generated {new Date(report.generated_at).toLocaleDateString()}
              </div>
              <button className="text-xs text-primary-500 hover:text-primary-600 font-medium">
                Download PDF
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-fib5 pt-fib4 border-t border-slate-200">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-900">Total Reports</span>
          <span className="text-sm font-medium text-slate-900">{reports.length}</span>
        </div>
        <div className="flex items-center justify-between mt-fib1">
          <span className="text-sm font-medium text-slate-900">Total Size</span>
          <span className="text-sm font-medium text-slate-900">
            {formatFileSize(reports.reduce((sum, report) => sum + report.file_size, 0))}
          </span>
        </div>
      </div>
    </div>
  )
}
