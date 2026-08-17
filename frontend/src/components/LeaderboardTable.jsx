import { useNavigate } from 'react-router-dom'

const ARROW_PATHS = {
  up:   'M12 19V5M12 5l-6 6M12 5l6 6',
  down: 'M12 5v14M12 19l-6-6M12 19l6-6',
  same: 'M5 12h14',
}

const TREND_CONFIG = {
  up:   { className: 'text-emerald-600' },
  down: { className: 'text-rose-600' },
  same: { className: 'text-gray-400' },
}

const RANK_BADGE = {
  1: 'bg-amber-100 text-amber-700',
  2: 'bg-gray-200 text-gray-700',
  3: 'bg-orange-100 text-orange-700',
}

function TrendIndicator({ trend }) {
  const { className } = TREND_CONFIG[trend] ?? TREND_CONFIG.same
  const path = ARROW_PATHS[trend] ?? ARROW_PATHS.same
  return (
    <span className={`inline-flex items-center ${className}`}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d={path} />
      </svg>
    </span>
  )
}

export default function LeaderboardTable({ entries }) {
  const navigate = useNavigate()

  if (!entries || entries.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-500">
        No activity logged yet. Be the first on the board.
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
            <th className="px-6 py-3 w-16">Rank</th>
            <th className="px-6 py-3">Name</th>
            <th className="px-6 py-3 text-right">Points</th>
            <th className="px-6 py-3 w-20 text-center">Trend</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {entries.map((entry) => (
            <tr
              key={entry.userId}
              onClick={() => navigate(`/dashboard/${entry.userId}`)}
              className="cursor-pointer transition-colors hover:bg-indigo-50/50"
            >
              <td className="px-6 py-4">
                <span
                  className={`inline-flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
                    RANK_BADGE[entry.rank] ?? 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {entry.rank}
                </span>
              </td>
              <td className="px-6 py-4 font-medium text-gray-900">{entry.name}</td>
              <td className="px-6 py-4 text-right font-semibold text-gray-900">
                {entry.totalPoints.toLocaleString()}
              </td>
              <td className="px-6 py-4">
                <div className="flex justify-center">
                  <TrendIndicator trend={entry.trend} />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
