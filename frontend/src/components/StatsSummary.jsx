const SPORT_LABELS = {
  running:  'Running',
  walking:  'Walking',
  cycling:  'Cycling',
  gym:      'Gym',
  swimming: 'Swimming',
  steps:    'Daily Steps',
}

function StatCard({ label, value, accent }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className={`mt-2 text-3xl font-bold ${accent}`}>{value}</p>
    </div>
  )
}

export default function StatsSummary({ totalPoints, totalActivities, topSport }) {
  const topSportLabel = topSport ? SPORT_LABELS[topSport] ?? topSport : '—'

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <StatCard
        label="Total Points"
        value={totalPoints.toLocaleString()}
        accent="text-indigo-600"
      />
      <StatCard
        label="Total Activities"
        value={totalActivities.toLocaleString()}
        accent="text-gray-900"
      />
      <StatCard
        label="Top Sport"
        value={topSportLabel}
        accent="text-gray-900"
      />
    </div>
  )
}
