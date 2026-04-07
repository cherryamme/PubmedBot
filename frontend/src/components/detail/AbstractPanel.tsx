import { useState } from 'react';
import type { Paper } from '../../types';

export default function AbstractPanel({ paper }: { paper: Paper }) {
  const [showChinese, setShowChinese] = useState(true);
  const summary = paper.summary;

  return (
    <div className="space-y-4">
      {/* Abstract toggle */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-gray-700">摘要</h3>
          <div className="flex gap-1 bg-gray-100 rounded-lg p-0.5">
            <button
              onClick={() => setShowChinese(true)}
              className={`px-3 py-1 text-xs rounded-md transition-colors ${showChinese ? 'bg-white shadow text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            >
              中文
            </button>
            <button
              onClick={() => setShowChinese(false)}
              className={`px-3 py-1 text-xs rounded-md transition-colors ${!showChinese ? 'bg-white shadow text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            >
              English
            </button>
          </div>
        </div>
        <div className="text-sm text-gray-600 leading-relaxed bg-gray-50 rounded-lg p-4">
          {showChinese && summary?.summary_cn ? summary.summary_cn : (paper.abstract || '暂无摘要')}
        </div>
      </div>

      {/* Innovation + Limitations */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {summary.innovation_points && (
            <div className="bg-green-50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-green-700 mb-2">创新点</h4>
              <div className="text-sm text-green-800 leading-relaxed whitespace-pre-line">
                {summary.innovation_points}
              </div>
            </div>
          )}
          {summary.limitations && (
            <div className="bg-orange-50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-orange-700 mb-2">不足之处</h4>
              <div className="text-sm text-orange-800 leading-relaxed whitespace-pre-line">
                {summary.limitations}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
