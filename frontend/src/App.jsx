import { Routes, Route, NavLink } from 'react-router-dom'
import Leaderboard from './pages/Leaderboard'
import Dashboard from './pages/Dashboard'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">

      {/* ── Navigation ── */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">

          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-sm font-bold">FC</span>
            </div>
            <span className="font-semibold text-gray-900 text-lg">
              Fitness Challenge
            </span>
          </div>

          <div className="flex items-center gap-1">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-600'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`
              }
            >
              Leaderboard
            </NavLink>
            <NavLink
              to="/dashboard/1"
              className={({ isActive }) =>
                `px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-600'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`
              }
            >
              My Dashboard
            </NavLink>
          </div>

        </div>
      </nav>

      {/* ── Page Content ── */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        <Routes>
          <Route path="/"                  element={<Leaderboard />} />
          <Route path="/dashboard/:userId" element={<Dashboard />} />
        </Routes>
      </main>

    </div>
  )
}