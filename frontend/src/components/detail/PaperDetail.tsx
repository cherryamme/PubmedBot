import { useEffect, useState } from 'react';
import { ArrowLeftIcon, BookmarkIcon } from '@heroicons/react/24/outline';
import { usePaperStore } from '../../stores/paperStore';
import { IFBadge, OABadge } from '../common/Badge';
import Loading from '../common/Loading';
import AbstractPanel from './AbstractPanel';
import FullTextPanel from './FullTextPanel';
import ChatPanel from './ChatPanel';
import ZoteroExportModal from './ZoteroExportModal';

interface PaperDetailProps {
  paperId: number;
  onBack: () => void;
}

export default function PaperDetail({ paperId, onBack }: PaperDetailProps) {
  const { paper, isLoadingPaper, isSummarizing, loadPaper, loadFulltext, doSummarize, reset } = usePaperStore();
  const [showZoteroModal, setShowZoteroModal] = useState(false);

  useEffect(() => {
    reset();
    loadPaper(paperId);
    loadFulltext(paperId);
    return () => reset();
  }, [paperId]);

  if (isLoadingPaper) return <Loading text="加载论文信息..." />;
  if (!paper) return <div className="text-center py-8 text-red-500">论文不存在</div>;

  const authorStr = paper.authors.map(a => a.name).join(', ');

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <button onClick={onBack} className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 shrink-0 mt-1">
          <ArrowLeftIcon className="w-5 h-5" />
        </button>
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-semibold text-gray-800 leading-snug">{paper.title}</h2>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {paper.journal && <span className="text-sm text-gray-500 italic">{paper.journal}</span>}
            <IFBadge value={paper.impact_factor} partition={paper.sci_partition} />
            {paper.has_fulltext && <OABadge />}
            {paper.year && <span className="text-sm text-gray-400">({paper.year})</span>}
          </div>
          {authorStr && <p className="text-xs text-gray-400 mt-1">{authorStr}</p>}
          <p className="text-xs text-gray-400 mt-0.5">
            PMID: {paper.pmid}
            {paper.doi && <span className="ml-2">DOI: {paper.doi}</span>}
          </p>
        </div>
        <div className="flex gap-2 shrink-0">
          {!paper.summary && (
            <button
              onClick={() => doSummarize(paper.id)}
              disabled={isSummarizing}
              className="text-xs px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isSummarizing ? 'AI 整理中...' : 'AI 整理'}
            </button>
          )}
          <button
            onClick={() => setShowZoteroModal(true)}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <BookmarkIcon className="w-3.5 h-3.5" />
            导出 Zotero
          </button>
        </div>
      </div>

      {/* Abstract + Summary */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <AbstractPanel paper={paper} />
      </div>

      {/* Full text analysis */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <FullTextPanel />
      </div>

      {/* Chat */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <ChatPanel paperId={paper.id} />
      </div>

      {/* Zotero export modal */}
      <ZoteroExportModal
        isOpen={showZoteroModal}
        onClose={() => setShowZoteroModal(false)}
        paperId={paper.id}
        paperTitle={paper.title}
      />
    </div>
  );
}
