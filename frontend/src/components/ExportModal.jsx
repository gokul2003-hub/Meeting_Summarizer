import { useState } from 'react'
import { exportMeetingReport, exportToLinear } from '../api/client'

export default function ExportModal({ meeting, onClose }) {
  const [format, setFormat] = useState('markdown')
  const [downloading, setDownloading] = useState(false)
  const [linearSyncing, setLinearSyncing] = useState(false)
  const [message, setMessage] = useState('')

  const handleDownload = async () => {
    setDownloading(true)
    setMessage('')
    try {
      const response = await exportMeetingReport(meeting.id, format)
      const blob = new Blob([response.data], {
        type: format === 'pdf' ? 'application/pdf' : (format === 'json' ? 'application/json' : 'text/markdown'),
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `meeting_${meeting.id.slice(0, 6)}.${format === 'markdown' ? 'md' : format}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
      setMessage('Export downloaded successfully!')
    } catch (err) {
      setMessage('Failed to download export.')
    } finally {
      setDownloading(false)
    }
  }

  const handleLinearSync = async () => {
    setLinearSyncing(true)
    setMessage('')
    try {
      const res = await exportToLinear(meeting.id)
      setMessage(`Synced ${res.data.synced_issues.length} action items to Linear!`)
    } catch (err) {
      setMessage('Failed to sync with Linear.')
    } finally {
      setLinearSyncing(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
        <div className="flex justify-between items-center border-b pb-3">
          <h3 className="text-lg font-semibold text-gray-900">Export Meeting Report</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Export Format</label>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="input-field w-full"
          >
            <option value="markdown">Markdown (.md)</option>
            <option value="json">JSON (.json)</option>
            <option value="pdf">PDF Document (.pdf)</option>
          </select>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="btn-primary flex-1"
          >
            {downloading ? 'Downloading...' : `Download ${format.toUpperCase()}`}
          </button>

          <button
            onClick={handleLinearSync}
            disabled={linearSyncing}
            className="btn-secondary flex-1"
          >
            {linearSyncing ? 'Syncing...' : 'Sync to Linear'}
          </button>
        </div>

        {message && <p className="text-sm text-center text-primary-600 font-medium">{message}</p>}
      </div>
    </div>
  )
}
