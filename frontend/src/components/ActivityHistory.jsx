const SPORT_LABELS = {
  running:  'Running',
  walking:  'Walking',
  cycling:  'Cycling',
  gym:      'Gym',
  swimming: 'Swimming',
  steps:    'Daily Steps',
}

function formatMetric(metricType, metricValue) {
  switch (metricType) {
    case 'distance':
      return `${metricValue} km`
    case 'duration':
      return `${metricValue} min`
    case 'count':
      return `${Number(metricValue).toLocaleString()} steps`
    default:
      return metricValue
  }
}

function formatLoggedAt(isoString) {
  const date = new Date(isoString)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export default function ActivityHistory({ activities }) {
  if (!activities || activities.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-500">
        No activities logged yet.
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <h3 className="text-sm font-semibold text-gray-900 px-6 pt-5 pb-1">
        Activity History
      </h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
            <th className="px-6 py-3">Sport</th>
            <th className="px-6 py-3">Metric</th>
            <th className="px-6 py-3 text-right">Points</th>
            <th className="px-6 py-3 text-right">Logged</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {activities.map((activity) => (
            <tr key={activity.id}>
              <td className="px-6 py-3 font-medium text-gray-900">
                {SPORT_LABELS[activity.sport] ?? activity.sport}
              </td>
              <td className="px-6 py-3 text-gray-600">
                {formatMetric(activity.metricType, activity.metricValue)}
              </td>
              <td className="px-6 py-3 text-right font-semibold text-indigo-600">
                +{activity.points}
              </td>
              <td className="px-6 py-3 text-right text-gray-500">
                {formatLoggedAt(activity.loggedAt)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
