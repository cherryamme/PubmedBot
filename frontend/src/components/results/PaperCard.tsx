import { useNavigate } from 'react-router-dom';
import { IFBadge, OABadge } from '../common/Badge';
import type { Paper } from '../../types';

interface PaperCardProps {
  paper: Paper;
  onSummarize?: (id: number) => void;
  isSummarizing?: boolean;
}

export default function PaperCard({ paper, onSummarize, isSummarizing }: PaperCardProps) {
  const navigate = useNavigate();

  const authorStr = paper.authors.length > 3
    ? `${paper.authors.slice(0, 3).map(a => a.name).join(', ')} et al.`
    : paper.authors.map(a => a.name).join(', ');

  return (
    <div
      onClick={() => navigate(`/paper/${paper.id}`)}
      className="bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer overflow-hidden"
    >
      <div className="flex">
        {/* Left: Metadata */}
        <div className="flex-1 p-4 min-w-0">
          <h3 className="text-sm font-semibold text-gray-800 leading-snug line-clamp-2">
            {paper.title}
          </h3>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {paper.journal && (
              <span className="text-xs text-gray-500 italic truncate max-w-[200px]">{paper.journal}</span>
            )}
            <IFBadge value={paper.impact_factor} partition={paper.sci_partition} />
            {paper.has_fulltext && <OABadge />}
          </div>
          <div className="mt-1.5 text-xs text-gray-400">
            {authorStr && <span>{authorStr}</span>}
            {paper.year && <span className="ml-2">({paper.year})</span>}
          </div>
          <div className="mt-1 text-xs text-gray-400">
            PMID: {paper.pmid}
            {paper.doi && <span className="ml-2">DOI: {paper.doi}</span>}
          </div>
        </div>

        {/* Right: Summary */}
        <div className="w-[40%] shrink-0 p-4 bg-gray-50/50 border-l border-gray-100">
          {paper.summary ? (
            <div className="space-y-1.5">
              <p className="text-sm text-gray-600 line-clamp-3">{paper.summary.summary_cn}</p>
              {paper.summary.innovation_points && (
                <div>
                  <span className="text-xs font-medium text-green-700">创新点</span>
                  <p className="text-xs text-gray-500 line-clamp-2 mt-0.5 whitespace-pre-line">
                    {paper.summary.innovation_points}
                  </p>
                </div>
              )}
              {paper.summary.limitations && (
                <div>
                  <span className="text-xs font-medium text-orange-600">不足</span>
                  <p className="text-xs text-gray-500 line-clamp-2 mt-0.5 whitespace-pre-line">
                    {paper.summary.limitations}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full min-h-[60px]">
              <button
                onClick={(e) => { e.stopPropagation(); onSummarize?.(paper.id); }}
                disabled={isSummarizing}
                className="text-xs px-3 py-1.5 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 disabled:opacity-50 transition-colors"
              >
                {isSummarizing ? '整理中...' : '生成 AI 摘要'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
