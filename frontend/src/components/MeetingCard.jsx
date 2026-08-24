import { Link } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import StatusBadge from './StatusBadge'

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function getFileIcon(filename) {
  const ext = (filename || '').split('.').pop().toLowerCase()
  if (['mp3', 'wav', 'm4a', 'flac', 'ogg'].includes(ext)) {
    return (
      <span className="p-2 bg-blue-100 text-blue-600 rounded-lg group-hover:bg-blue-600 group-hover:text-white transition-colors">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
      </span>
    )
  }
  if (['mp4', 'webm', 'mov'].includes(ext)) {
    return (
      <span className="p-2 bg-purple-100 text-purple-600 rounded-lg group-hover:bg-purple-600 group-hover:text-white transition-colors">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      </span>
    )
  }
  return (
    <span className="p-2 bg-indigo-100 text-indigo-600 rounded-lg group-hover:bg-indigo-600 group-hover:text-white transition-colors">
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    </span>
  )
}

export default function MeetingCard({ meeting }) {
  return (
    <RouterLink
      to={`/meetings/${meeting.id}`}
      className="block card hover:shadow-lg hover:border-primary-300 transition-all duration-200 group bg-white rounded-xl border border-gray-200/80 p-5"
    >
      <div className="flex items-start gap-3.5">
        {getFileIcon(meeting.original_filename)}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-semibold text-gray-900 truncate group-hover:text-primary-600 transition-colors text-base">
              {meeting.title}
            </h3>
            <StatusBadge status={meeting.status} className="shrink-0" />
          </div>
          <p className="text-xs text-gray-500 truncate mt-1 flex items-center gap-1">
            <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            {meeting.original_filename}
          </p>
        </div>
      </div>

      {meeting.status === 'failed' && meeting.error_message && (
        <p className="mt-3 text-xs text-red-700 bg-red-50/80 border border-red-100 rounded-lg p-2.5 line-clamp-2">
          {meeting.error_message}
        </p>
      )}

      <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {formatDate(meeting.created_at)}
        </span>
        <span className="text-primary-600 font-medium group-hover:translate-x-0.5 transition-transform flex items-center gap-0.5">
          View Summary &rarr;
        </span>
      </div>
    </RouterLink>
  )
}
