import { useState } from 'react'
import { logActivity } from '../api/client'

const SPORT_METRIC_MAP = {
  running:  'distance',
  walking:  'distance',
  cycling:  'distance',
  gym:      'duration',
  swimming: 'duration',
  steps:    'count',
}

const SPORT_LABELS = {
  running:  'Running',
  walking:  'Walking',
  cycling:  'Cycling',
  gym:      'Gym',
  swimming: 'Swimming',
  steps:    'Daily Steps',
}

export default function LogActivityForm({ onClose, onSuccess }) {
  const [sport, setSport] = useState('running')
  const [distance, setDistance] = useState('')
  const [minutes, setMinutes] = useState('')
  const [seconds, setSeconds] = useState('')
  const [steps, setSteps] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const metricType = SPORT_METRIC_MAP[sport]

  function buildMetricValue() {
    if (metricType === 'distance') return distance
    if (metricType === 'duration') return `${minutes || 0}:${String(seconds || 0).padStart(2, '0')}`
    if (metricType === 'count') return steps
    return null
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setIsSubmitting(true)
    setError(null)

    try {
      const payload = {
        sport,
        metricType,
        metricValue: buildMetricValue(),
      }
      await logActivity(payload)
      onSuccess()
    } catch (err) {
      setError(err.message)
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-20 px-4">
      <div className="bg-white rounded-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-900">Log Activity</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
            aria-label="Close"
          >
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="sport" className="block text-sm font-medium text-gray-700 mb-1">
              Sport
            </label>
            <select
              id="sport"
              value={sport}
              onChange={(e) => setSport(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {Object.keys(SPORT_METRIC_MAP).map((key) => (
                <option key={key} value={key}>
                  {SPORT_LABELS[key]}
                </option>
              ))}
            </select>
          </div>

          {metricType === 'distance' && (
            <div>
              <label htmlFor="distance" className="block text-sm font-medium text-gray-700 mb-1">
                Distance (km)
              </label>
              <input
                id="distance"
                type="number"
                step="0.1"
                min="0.1"
                required
                value={distance}
                onChange={(e) => setDistance(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="5.0"
              />
            </div>
          )}

          {metricType === 'duration' && (
            <div className="flex gap-3">
              <div className="flex-1">
                <label htmlFor="minutes" className="block text-sm font-medium text-gray-700 mb-1">
                  Minutes
                </label>
                <input
                  id="minutes"
                  type="number"
                  min="0"
                  required
                  value={minutes}
                  onChange={(e) => setMinutes(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="30"
                />
              </div>
              <div className="flex-1">
                <label htmlFor="seconds" className="block text-sm font-medium text-gray-700 mb-1">
                  Seconds
                </label>
                <input
                  id="seconds"
                  type="number"
                  min="0"
                  max="59"
                  value={seconds}
                  onChange={(e) => setSeconds(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="0"
                />
              </div>
            </div>
          )}

          {metricType === 'count' && (
            <div>
              <label htmlFor="steps" className="block text-sm font-medium text-gray-700 mb-1">
                Steps
              </label>
              <input
                id="steps"
                type="number"
                step="1"
                min="1"
                required
                value={steps}
                onChange={(e) => setSteps(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="8000"
              />
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-gray-300 text-gray-700 font-medium text-sm rounded-lg px-4 py-2.5 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-medium text-sm rounded-lg px-4 py-2.5 transition-colors"
            >
              {isSubmitting ? 'Saving...' : 'Save Activity'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
