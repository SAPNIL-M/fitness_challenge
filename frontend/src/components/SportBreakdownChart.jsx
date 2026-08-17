import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const SPORT_LABELS = {
  running:  'Running',
  walking:  'Walking',
  cycling:  'Cycling',
  gym:      'Gym',
  swimming: 'Swimming',
  steps:    'Daily Steps',
}

const SPORT_COLORS = {
  running:  '#4f46e5',
  walking:  '#0ea5e9',
  cycling:  '#f59e0b',
  gym:      '#ef4444',
  swimming: '#14b8a6',
  steps:    '#a855f7',
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload || payload.length === 0) return null

  const { sport, totalPoints, percentage } = payload[0].payload
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm px-3 py-2 text-sm">
      <p className="font-medium text-gray-900">{SPORT_LABELS[sport] ?? sport}</p>
      <p className="text-gray-500">
        {totalPoints.toLocaleString()} pts &middot; {percentage.toFixed(1)}%
      </p>
    </div>
  )
}

export default function SportBreakdownChart({ breakdown }) {
  if (!breakdown || breakdown.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 h-80 flex items-center justify-center text-gray-500">
        No activity data yet
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-4">Sport Breakdown</h3>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie
            data={breakdown}
            dataKey="totalPoints"
            nameKey="sport"
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
          >
            {breakdown.map((entry) => (
              <Cell
                key={entry.sport}
                fill={SPORT_COLORS[entry.sport] ?? '#9ca3af'}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            formatter={(value) => SPORT_LABELS[value] ?? value}
            wrapperStyle={{ fontSize: '13px' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
