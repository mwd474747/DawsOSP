import { BuffettRating } from '@/types'

interface BuffettRatingCardProps {
  rating: BuffettRating
}

export function BuffettRatingCard({ rating }: BuffettRatingCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'bg-accent-100 text-accent-800 border-accent-200'
    if (score >= 6) return 'bg-primary-100 text-primary-800 border-primary-200'
    if (score >= 4) return 'bg-warning-100 text-warning-800 border-warning-200'
    return 'bg-red-100 text-red-800 border-red-200'
  }

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'buy': return 'bg-accent-100 text-accent-800 border-accent-200'
      case 'hold': return 'bg-primary-100 text-primary-800 border-primary-200'
      case 'sell': return 'bg-red-100 text-red-800 border-red-200'
      default: return 'bg-slate-100 text-slate-800 border-slate-200'
    }
  }

  const getScoreLabel = (score: number) => {
    if (score >= 8) return 'Excellent'
    if (score >= 6) return 'Good'
    if (score >= 4) return 'Fair'
    return 'Poor'
  }

  return (
    <div className="metric-card">
      <div className="flex items-start justify-between mb-fib6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 mb-fib1">{rating.symbol}</h2>
          <p className="text-slate-600">Buffett Quality Framework Analysis</p>
        </div>
        <div className={`rating-badge ${getRecommendationColor(rating.recommendation)}`}>
          {rating.recommendation.toUpperCase()}
        </div>
      </div>

      {/* Overall Score */}
      <div className="text-center mb-fib8">
        <div className="text-4xl font-bold text-slate-900 mb-fib2">{rating.overall_score.toFixed(1)}</div>
        <div className={`rating-badge ${getScoreColor(rating.overall_score)}`}>
          {getScoreLabel(rating.overall_score)}
        </div>
      </div>

      {/* Individual Scores */}
      <div className="grid grid-cols-3 gap-fib5 mb-fib8">
        <div className="text-center">
          <div className="text-2xl font-bold text-slate-900 mb-fib1">{rating.dividend_safety.toFixed(1)}</div>
          <div className="text-sm text-slate-600 mb-fib2">Dividend Safety</div>
          <div className="w-full bg-slate-200 rounded-full h-fib2">
            <div 
              className="h-fib2 rounded-full bg-accent-500"
              style={{ width: `${(rating.dividend_safety / 10) * 100}%` }}
            ></div>
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-slate-900 mb-fib1">{rating.moat_strength.toFixed(1)}</div>
          <div className="text-sm text-slate-600 mb-fib2">Moat Strength</div>
          <div className="w-full bg-slate-200 rounded-full h-fib2">
            <div 
              className="h-fib2 rounded-full bg-primary-500"
              style={{ width: `${(rating.moat_strength / 10) * 100}%` }}
            ></div>
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-slate-900 mb-fib1">{rating.resilience.toFixed(1)}</div>
          <div className="text-sm text-slate-600 mb-fib2">Resilience</div>
          <div className="w-full bg-slate-200 rounded-full h-fib2">
            <div 
              className="h-fib2 rounded-full bg-warning-500"
              style={{ width: `${(rating.resilience / 10) * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Rationale */}
      <div className="border-t border-slate-200 pt-fib6">
        <h4 className="text-sm font-medium text-slate-900 mb-fib3">Analysis Rationale</h4>
        <p className="text-sm text-slate-600 leading-relaxed">{rating.rationale}</p>
      </div>
    </div>
  )
}
