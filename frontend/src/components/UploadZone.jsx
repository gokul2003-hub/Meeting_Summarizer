import { useRef, useState } from 'react'
import { uploadMeeting, uploadMeetingFromUrl } from '../api/client'

const ALLOWED_EXTENSIONS = ['.mp3', '.mp4', '.wav', '.m4a', '.ogg', '.flac', '.webm', '.vtt', '.srt', '.txt', '.json']
const MAX_SIZE_MB = 500

function validateFile(file) {
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return `File type "${ext}" not supported. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`
  }
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    return `File exceeds maximum size of ${MAX_SIZE_MB}MB`
  }
  return null
}

export default function UploadZone({ onSuccess }) {
  const [mode, setMode] = useState('file') // 'file' | 'url'

  // File mode state
  const [isDragging, setIsDragging] = useState(false)
  const [file, setFile] = useState(null)
  const [fileTitle, setFileTitle] = useState('')
  const [summaryStyle, setSummaryStyle] = useState('concise')
  const inputRef = useRef(null)

  // URL mode state
  const [url, setUrl] = useState('')
  const [urlTitle, setUrlTitle] = useState('')

  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  const handleFile = (f) => {
    const err = validateFile(f)
    if (err) { setError(err); return }
    setFile(f)
    setFileTitle(f.name.replace(/\.[^/.]+$/, ''))
    setError('')
  }

  const handleDragOver = (e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true) }
  const handleDragLeave = (e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false) }
  const handleDrop = (e) => {
    e.preventDefault(); e.stopPropagation(); setIsDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) handleFile(dropped)
  }
  const handleInputChange = (e) => {
    const selected = e.target.files[0]
    if (selected) handleFile(selected)
  }

  const switchMode = (next) => {
    setMode(next)
    setError('')
    setFile(null)
    setFileTitle('')
    setUrl('')
    setUrlTitle('')
  }

  const handleSubmitFile = async (e) => {
    e.preventDefault()
    if (!file) return
    setUploading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', fileTitle || file.name)
      formData.append('style', summaryStyle)
      await uploadMeeting(formData)
      setFile(null)
      setFileTitle('')
      onSuccess?.()
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const handleSubmitUrl = async (e) => {
    e.preventDefault()
    if (!url.trim()) return
    setUploading(true)
    setError('')
    try {
      await uploadMeetingFromUrl(url.trim(), urlTitle.trim() || url.trim(), summaryStyle)
      setUrl('')
      setUrlTitle('')
      onSuccess?.()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process URL. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="card">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">New Meeting</h2>

      {/* Mode tabs */}
      <div className="flex rounded-lg border border-gray-200 p-1 mb-4 bg-gray-50">
        <button
          type="button"
          onClick={() => switchMode('file')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm font-medium transition-colors
            ${mode === 'file' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          Upload Audio / Transcript
        </button>
        <button
          type="button"
          onClick={() => switchMode('url')}
          className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md text-sm font-medium transition-colors
            ${mode === 'url' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          YouTube URL
        </button>
      </div>

      {mode === 'file' ? (
        <>
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => !file && inputRef.current?.click()}
            className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer
              ${isDragging ? 'border-primary-400 bg-primary-50' : 'border-gray-300 hover:border-primary-300 hover:bg-gray-50'}
              ${file ? 'cursor-default' : ''}`}
          >
            <input
              ref={inputRef}
              type="file"
              accept={ALLOWED_EXTENSIONS.join(',')}
              onChange={handleInputChange}
              className="hidden"
            />

            {file ? (
              <div className="flex items-center justify-center gap-3">
                <svg className="w-8 h-8 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <div className="text-left">
                  <p className="font-medium text-gray-900">{file.name}</p>
                  <p className="text-sm text-gray-500">{(file.size / (1024 * 1024)).toFixed(1)} MB</p>
                </div>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setFile(null); setFileTitle('') }}
                  className="ml-auto text-gray-400 hover:text-red-500 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ) : (
              <>
                <svg className="mx-auto w-12 h-12 text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="text-gray-600 font-medium">Drop audio (.mp3, .wav) or transcript (.vtt, .srt, .txt, .json) here</p>
                <p className="text-sm text-gray-400 mt-1">or click to browse</p>
              </>
            )}
          </div>

          {file && (
            <form onSubmit={handleSubmitFile} className="mt-4 space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Meeting title</label>
                <input
                  type="text"
                  value={fileTitle}
                  onChange={(e) => setFileTitle(e.target.value)}
                  placeholder="Enter a title for this meeting"
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Summary Style</label>
                <select
                  value={summaryStyle}
                  onChange={(e) => setSummaryStyle(e.target.value)}
                  className="input-field"
                >
                  <option value="concise">Concise Summary</option>
                  <option value="detailed">Detailed Summary</option>
                  <option value="executive">Executive Brief</option>
                  <option value="four_section">Four-Section Recap (Summary, Decisions, Actions, Questions)</option>
                </select>
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <button type="submit" disabled={uploading} className="btn-primary w-full">
                {uploading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Uploading…
                  </span>
                ) : 'Upload & Process'}
              </button>
            </form>
          )}
          {!file && error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        </>
      ) : (
        <form onSubmit={handleSubmitUrl} className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">YouTube URL</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="input-field"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Meeting title</label>
            <input
              type="text"
              value={urlTitle}
              onChange={(e) => setUrlTitle(e.target.value)}
              placeholder="Enter a title for this meeting"
              className="input-field"
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={uploading || !url.trim()} className="btn-primary w-full">
            {uploading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Downloading…
              </span>
            ) : 'Import & Process'}
          </button>
        </form>
      )}
    </div>
  )
}
