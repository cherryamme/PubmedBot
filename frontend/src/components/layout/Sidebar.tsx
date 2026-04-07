import { useEffect } from 'react';
import { ClockIcon, MagnifyingGlassIcon, TrashIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { useSearchStore } from '../../stores/searchStore';
import type { SearchHistoryItem } from '../../types';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { history, loadHistory, loadSearchResults, setQuery, deleteHistory } = useSearchStore();

  useEffect(() => { loadHistory(); }, []);

  const handleClick = (item: SearchHistoryItem) => {
    setQuery(item.query);
    loadSearchResults(item.id);
  };

  const handleDelete = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    deleteHistory(id);
  };

  return (
    <aside className={`bg-gray-50 border-r border-gray-200 flex flex-col h-full overflow-hidden transition-all duration-200 ${
      collapsed ? 'w-10' : 'w-64'
    }`}>
      {/* Header with toggle */}
      <div className="p-2 border-b border-gray-200 flex items-center justify-between">
        {!collapsed && (
          <h2 className="text-sm font-medium text-gray-600 flex items-center gap-2 pl-2">
            <ClockIcon className="w-4 h-4" />
            搜索历史
          </h2>
        )}
        <button
          onClick={onToggle}
          className="p-1 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-200 transition-colors"
          title={collapsed ? '展开侧栏' : '收起侧栏'}
        >
          {collapsed ? <ChevronRightIcon className="w-4 h-4" /> : <ChevronLeftIcon className="w-4 h-4" />}
        </button>
      </div>

      {!collapsed && (
        <div className="flex-1 overflow-y-auto">
          {history.length === 0 ? (
            <div className="p-4 text-sm text-gray-400 text-center">暂无搜索记录</div>
          ) : (
            <ul className="py-1">
              {history.map((item) => (
                <li key={item.id}>
                  <button
                    onClick={() => handleClick(item)}
                    className="w-full text-left px-3 py-2.5 hover:bg-gray-100 transition-colors group relative"
                  >
                    <div className="flex items-start gap-2 pr-6">
                      <MagnifyingGlassIcon className="w-3.5 h-3.5 mt-0.5 text-gray-400 shrink-0" />
                      <div className="min-w-0">
                        <div className="text-sm text-gray-700 truncate group-hover:text-blue-600">
                          {item.query}
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5">
                          {item.result_count} 篇
                          {item.min_year && item.max_year && ` · ${item.min_year}-${item.max_year}`}
                          {item.min_impact_factor != null && item.min_impact_factor > 0 && ` · IF≥${item.min_impact_factor}`}
                        </div>
                      </div>
                    </div>
                    {/* Delete button */}
                    <span
                      onClick={(e) => handleDelete(e, item.id)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                      title="删除"
                    >
                      <TrashIcon className="w-3.5 h-3.5" />
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </aside>
  );
}
