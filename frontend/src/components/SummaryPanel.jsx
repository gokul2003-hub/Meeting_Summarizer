export default function SummaryPanel({ summary }) {
  if (!summary) {
    return (
      <div className="text-center py-12 text-gray-400 bg-white rounded-xl border border-gray-200">
        <svg className="mx-auto w-10 h-10 mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6h16M4 10h16M4 14h10" />
        </svg>
        <p className="font-medium text-gray-500">Summary not available yet</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Executive Summary Box */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-xl p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-2">
          <span className="p-1.5 bg-blue-600 text-white rounded-lg">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </span>
          <h3 className="text-sm font-bold text-blue-900 uppercase tracking-wider">Executive Summary</h3>
        </div>
        <p className="text-gray-800 leading-relaxed font-normal text-base">{summary.summary}</p>
      </div>

      {/* Decisions Made */}
      {summary.decisions?.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <span className="p-1.5 bg-emerald-100 text-emerald-700 rounded-lg">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </span>
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">Key Decisions Made</h3>
          </div>
          <ul className="space-y-2.5">
            {summary.decisions.map((decision, i) => (
              <li key={i} className="flex items-start gap-3 bg-emerald-50/50 p-2.5 rounded-lg border border-emerald-100/60">
                <svg className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-gray-800 text-sm font-medium">{decision}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Key Discussion Points */}
      {summary.key_points?.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <span className="p-1.5 bg-indigo-100 text-indigo-700 rounded-lg">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </span>
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">Key Discussion Topics</h3>
          </div>
          <ul className="space-y-2.5">
            {summary.key_points.map((point, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className="shrink-0 w-6 h-6 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold flex items-center justify-center border border-indigo-200 mt-0.5">
                  {i + 1}
                </span>
                <span className="text-gray-700 text-sm">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Open Questions */}
      {summary.open_questions?.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <span className="p-1.5 bg-amber-100 text-amber-700 rounded-lg">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </span>
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">Open Questions</h3>
          </div>
          <ul className="space-y-2">
            {summary.open_questions.map((q, i) => (
              <li key={i} className="flex items-start gap-2.5 bg-amber-50/50 p-2.5 rounded-lg border border-amber-100/60 text-sm text-gray-800">
                <span className="text-amber-600 font-bold">?</span>
                <span>{q}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
