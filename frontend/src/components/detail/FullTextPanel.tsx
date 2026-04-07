import { usePaperStore } from '../../stores/paperStore';
import Markdown from '../common/Markdown';
import Loading from '../common/Loading';

const externalLLMs = [
  { name: 'Gemini', url: 'https://gemini.google.com/app', color: 'bg-blue-500 hover:bg-blue-600', icon: '✦' },
  { name: 'ChatGPT', url: 'https://chatgpt.com/', color: 'bg-emerald-600 hover:bg-emerald-700', icon: '◉' },
  { name: '豆包', url: 'https://www.doubao.com/chat/', color: 'bg-sky-500 hover:bg-sky-600', icon: '豆' },
  { name: 'DeepSeek', url: 'https://chat.deepseek.com/', color: 'bg-violet-600 hover:bg-violet-700', icon: 'D' },
];

export default function FullTextPanel() {
  const { fulltext, fulltextAnalysis, isLoadingFulltext, isAnalyzing, analyzeError, doAnalyzeFulltext, paper } = usePaperStore();

  if (isLoadingFulltext) return <Loading text="获取全文中..." />;

  const hasFulltext = fulltext?.available && fulltext?.content;
  const sourceLabel = fulltext?.source === 'pmc_bioc' ? 'PMC 开放获取'
    : fulltext?.source === 'unpaywall_pdf' ? 'Unpaywall PDF'
    : fulltext?.available ? 'OA 链接' : null;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-gray-700">全文深度分析</h3>
          {sourceLabel && <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full">{sourceLabel}</span>}
          {!hasFulltext && <span className="text-xs text-gray-400">(将基于摘要分析)</span>}
        </div>
        <div className="flex gap-2">
          {fulltext?.oa_url && (
            <a href={fulltext.oa_url} target="_blank" rel="noopener"
              className="text-xs px-3 py-1.5 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors">
              查看原文
            </a>
          )}
          {!fulltextAnalysis && (
            <button
              onClick={() => paper && doAnalyzeFulltext(paper.id)}
              disabled={isAnalyzing}
              className="text-xs px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isAnalyzing ? 'AI 分析中...' : 'AI 深度分析'}
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {analyzeError && (
        <div className="text-sm text-red-500 bg-red-50 rounded-lg p-3">{analyzeError}</div>
      )}

      {/* Analysis result */}
      {fulltextAnalysis && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-5 border border-blue-100">
          <Markdown content={fulltextAnalysis} />
        </div>
      )}

      {/* Placeholder when no analysis yet */}
      {!fulltextAnalysis && !isAnalyzing && !analyzeError && (
        <div className="text-center py-6 text-sm text-gray-400 bg-gray-50 rounded-lg">
          点击"AI 深度分析"对论文进行全面解读
        </div>
      )}

      {/* Analyzing indicator */}
      {isAnalyzing && <Loading text="AI 正在深度分析论文..." />}

      {/* External LLM buttons */}
      <div className="border-t border-gray-200 pt-4">
        <p className="text-xs text-gray-400 mb-2">使用其他 AI 平台分析（手动上传 PDF 后开始对话）</p>
        <div className="flex flex-wrap gap-2">
          {externalLLMs.map((llm) => (
            <a
              key={llm.name}
              href={llm.url}
              target="_blank"
              rel="noopener noreferrer"
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-white rounded-lg transition-colors ${llm.color}`}
            >
              <span className="text-xs font-bold">{llm.icon}</span>
              {llm.name}
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
