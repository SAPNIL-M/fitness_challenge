import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getUserDashboard } from '../api/client'
import { getCurrentUser } from '../utils/currentUser'
import StatsSummary from '../components/StatsSummary'
import SportBreakdownChart from '../components/SportBreakdownChart'
import PointsOverTimeChart from '../components/PointsOverTimeChart'
import ActivityHistory from '../components/ActivityHistory'
import LogActivityForm from '../components/LogActivityForm'

export default function Dashboard() {
  const { userId } = useParams()
  const [dashboard, setDashboard] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [isFormOpen, setIsFormOpen] = useState(false)

  const currentUser = getCurrentUser()
  const isOwnDashboard = currentUser && String(currentUser.userId) === String(userId)

  useEffect(() => {
    let isCancelled = false

    async function fetchDashboard() {
      setIsLoading(true)
      setError(null)
      try {
        const data = await getUserDashboard(userId)
        if (!isCancelled) {
          setDashboard(data)
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err.message)
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false)
        }
      }
    }

    fetchDashboard()

    return () => {
      isCancelled = true
    }
  }, [userId, refreshKey])

  function handleActivitySaved() {
    setIsFormOpen(false)
    setRefreshKey((key) => key + 1)
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-500">
        Loading dashboard...
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center text-red-700">
        Failed to load dashboard: {error}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">{dashboard.name}'s Dashboard</h1>
        {isOwnDashboard && (
          <button
            onClick={() => setIsFormOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm rounded-lg px-4 py-2 transition-colors"
          >
            + Add Activity
          </button>
        )}
      </div>

      {isFormOpen && (
        <LogActivityForm
          userId={userId}
          onClose={() => setIsFormOpen(false)}
          onSuccess={handleActivitySaved}
        />
      )}

      <StatsSummary
        totalPoints={dashboard.totalPoints}
        totalActivities={dashboard.totalActivities}
        topSport={dashboard.topSport}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PointsOverTimeChart data={dashboard.pointsOverTime} />
        <SportBreakdownChart breakdown={dashboard.sportBreakdown} />
      </div>

      <ActivityHistory activities={dashboard.activities} />
    </div>
  )
}
