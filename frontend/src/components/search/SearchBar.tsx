import { MagnifyingGlassIcon } from '@heroicons/react/24/solid';
import { useSearchStore } from '../../stores/searchStore';

export default function SearchBar() {
  const {
    query, minYear, maxYear, minIF, maxResults, autoSummarize,
    setQuery, setMinYear, setMaxYear, setMinIF, setMaxResults, setAutoSummarize,
    doSearch, isLoading,
  } = useSearchStore();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    doSearch();
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="输入检索关键词，如 telomere aging"
            className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              检索中
            </>
          ) : '检索'}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-4 mt-3 pt-3 border-t border-gray-100">
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500 whitespace-nowrap">年份</label>
          <input type="number" value={minYear} onChange={(e) => setMinYear(Number(e.target.value))}
            className="w-20 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
          <span className="text-gray-400">-</span>
          <input type="number" value={maxYear} onChange={(e) => setMaxYear(Number(e.target.value))}
            className="w-20 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500 whitespace-nowrap">IF ≥</label>
          <input type="number" step="0.1" value={minIF} onChange={(e) => setMinIF(Number(e.target.value))}
            className="w-20 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-500 whitespace-nowrap">数量</label>
          <input type="number" value={maxResults} onChange={(e) => setMaxResults(Number(e.target.value))}
            className="w-20 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
            min={1} max={200} />
        </div>

        {/* Auto-summarize toggle */}
        <div className="flex items-center gap-2 ml-auto">
          <label className="text-xs text-gray-500 whitespace-nowrap">自动 AI 总结</label>
          <button
            type="button"
            onClick={() => setAutoSummarize(!autoSummarize)}
            className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
              autoSummarize ? 'bg-blue-600' : 'bg-gray-300'
            }`}
          >
            <span className={`inline-block h-3.5 w-3.5 rounded-full bg-white transition-transform ${
              autoSummarize ? 'translate-x-4.5' : 'translate-x-0.5'
            }`} />
          </button>
        </div>
      </div>
    </form>
  );
}
