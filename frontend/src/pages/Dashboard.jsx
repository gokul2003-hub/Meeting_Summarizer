import { useCallback, useEffect, useState } from 'react'
import { getMeetings } from '../api/client'
import UploadZone from '../components/UploadZone'
import MeetingCard from '../components/MeetingCard'

function AnalyticsBar({ meetings }) {
  const total = meetings.length
  const completed = meetings.filter((m) => m.status === 'completed').length
  const processing = meetings.filter((m) => ['pending', 'processing'].includes(m.status)).length

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-8">
      <div className="bg-white border border-gray-200/80 rounded-xl p-4 shadow-sm flex items-center gap-3.5">
        <span className="p-3 bg-blue-50 text-blue-600 rounded-xl">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        </span>
        <div>
          <p className="text-2xl font-bold text-gray-900">{total}</p>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Meetings</p>
        </div>
      </div>

      <div className="bg-white border border-gray-200/80 rounded-xl p-4 shadow-sm flex items-center gap-3.5">
        <span className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </span>
        <div>
          <p className="text-2xl font-bold text-gray-900">{completed}</p>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Completed Recaps</p>
        </div>
      </div>

      <div className="bg-white border border-gray-200/80 rounded-xl p-4 shadow-sm flex items-center gap-3.5 col-span-2 sm:col-span-1">
        <span className="p-3 bg-amber-50 text-amber-600 rounded-xl">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </span>
        <div>
          <p className="text-2xl font-bold text-gray-900">{processing}</p>
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">In Progress</p>
        </div>
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="bg-white border border-gray-200/80 rounded-xl p-12 text-center shadow-sm">
      <div className="w-16 h-16 mx-auto bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mb-4">
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
      </div>
      <h3 className="text-lg font-bold text-gray-900 mb-1">No meetings added yet</h3>
      <p className="text-gray-500 text-sm max-w-md mx-auto">
        Upload an audio recording (.mp3, .wav) or transcript file (.vtt, .srt, .txt, .json) to generate automatic summaries and action items.
      </p>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="card animate-pulse bg-white p-5 rounded-xl border border-gray-200">
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-3 bg-gray-200 rounded w-1/2" />
        </div>
        <div className="h-5 w-20 bg-gray-200 rounded-full" />
      </div>
      <div className="mt-4 h-3 bg-gray-200 rounded w-1/3" />
    </div>
  )
}

export default function Dashboard() {
  const [meetings, setMeetings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  const fetchMeetings = useCallback(async () => {
    try {
      const res = await getMeetings()
      setMeetings(res.data)
    } catch {
      setError('Failed to load meetings')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMeetings()
  }, [fetchMeetings])

  const filteredMeetings = meetings.filter((m) =>
    m.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    m.original_filename.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Meeting Intelligence Hub</h1>
        <p className="text-gray-500 mt-1 text-sm">Transcribe, summarize, and extract action items automatically with AI</p>
      </div>

      {/* Analytics Counter Bar */}
      {!loading && <AnalyticsBar meetings={meetings} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Panel */}
        <div className="lg:col-span-1">
          <UploadZone onSuccess={fetchMeetings} />
        </div>

        {/* Meetings Grid */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              Recent Meetings
              {!loading && meetings.length > 0 && (
                <span className="text-xs bg-blue-100 text-blue-700 font-semibold px-2 py-0.5 rounded-full">
                  {meetings.length}
                </span>
              )}
            </h2>

            {!loading && meetings.length > 0 && (
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <input
                  type="text"
                  placeholder="Search meetings..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="input-field text-xs py-1.5 w-full sm:w-48"
                />
                <button onClick={fetchMeetings} className="btn-secondary text-xs px-3 py-1.5 shrink-0">
                  Refresh
                </button>
              </div>
            )}
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-600 font-medium">{error}</p>
            </div>
          )}

          {loading ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
            </div>
          ) : meetings.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {filteredMeetings.map((meeting) => (
                <MeetingCard key={meeting.id} meeting={meeting} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
