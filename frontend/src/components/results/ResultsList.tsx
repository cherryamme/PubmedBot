import { useState } from 'react';
import { useSearchStore } from '../../stores/searchStore';
import { summarizePaper } from '../../api/papers';
import PaperCard from './PaperCard';

export default function ResultsList() {
  const { results, isLoading, isSummarizing, error, statusMessage, doSummarizeAll, updatePaperSummary } = useSearchStore();
  const [summarizingIds, setSummarizingIds] = useState<Set<number>>(new Set());

  const handleSummarize = async (id: number) => {
    setSummarizingIds(prev => new Set(prev).add(id));
    try {
      const result = await summarizePaper(id);
      updatePaperSummary(id, result);
    } catch { /* silent */ }
    finally {
      setSummarizingIds(prev => { const n = new Set(prev); n.delete(id); return n; });
    }
  };

  if (error) return <div className="text-center py-8 text-red-500 text-sm">{error}</div>;
  if (isLoading && results.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex items-center gap-3 text-gray-500">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>{statusMessage || '正在检索 PubMed...'}</span>
        </div>
      </div>
    );
  }
  if (results.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-500">
          {isLoading ? statusMessage : `共 ${results.length} 篇论文`}
        </span>
        {!isLoading && (
          <button
            onClick={doSummarizeAll}
            disabled={isSummarizing}
            className="text-xs px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isSummarizing ? '批量整理中...' : '一键 AI 整理全部'}
          </button>
        )}
      </div>
      {results.map((paper) => (
        <PaperCard key={paper.id} paper={paper} onSummarize={handleSummarize} isSummarizing={summarizingIds.has(paper.id)} />
      ))}
      {isLoading && results.length > 0 && (
        <div className="flex items-center justify-center py-4">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {statusMessage}
          </div>
        </div>
      )}
    </div>
  );
}
