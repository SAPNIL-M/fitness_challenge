import { useState, useEffect } from 'react'
import { getLeaderboard } from '../api/client'
import LeaderboardTable from '../components/LeaderboardTable'

export default function Leaderboard() {
  const [entries, setEntries] = useState([])
  const [totalUsers, setTotalUsers] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let isCancelled = false

    async function fetchLeaderboard() {
      setIsLoading(true)
      setError(null)
      try {
        const data = await getLeaderboard()
        if (!isCancelled) {
          setEntries(data.leaderboard)
          setTotalUsers(data.totalUsers)
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

    fetchLeaderboard()

    return () => {
      isCancelled = true
    }
  }, [])

  return (
    <div>
      <div className="flex items-baseline justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Global Leaderboard</h1>
        {!isLoading && !error && (
          <span className="text-sm text-gray-500">{totalUsers} competitors</span>
        )}
      </div>

      {isLoading && (
        <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-500">
          Loading leaderboard...
        </div>
      )}

      {!isLoading && error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center text-red-700">
          Failed to load leaderboard: {error}
        </div>
      )}

      {!isLoading && !error && <LeaderboardTable entries={entries} />}
    </div>
  )
}
