import { useEffect, useState } from 'react';
import { XMarkIcon, FolderIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import { getZoteroAccounts, getZoteroCollections, exportToZotero } from '../../api/zotero';
import type { ZoteroAccount, ZoteroCollection } from '../../types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  paperId: number;
  paperTitle: string;
}

export default function ZoteroExportModal({ isOpen, onClose, paperId, paperTitle }: Props) {
  const [accounts, setAccounts] = useState<ZoteroAccount[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null);
  const [collections, setCollections] = useState<ZoteroCollection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const [includeChat, setIncludeChat] = useState(true);

  const [loadingAccounts, setLoadingAccounts] = useState(false);
  const [loadingCollections, setLoadingCollections] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setResult(null);
      setError(null);
      setSelectedAccount(null);
      setCollections([]);
      setSelectedCollection(null);
      loadAccounts();
    }
  }, [isOpen]);

  const loadAccounts = async () => {
    setLoadingAccounts(true);
    try {
      const data = await getZoteroAccounts();
      setAccounts(data);
      if (data.length === 1) {
        setSelectedAccount(data[0].id);
        loadCollectionsForAccount(data[0].id);
      }
    } catch (e: any) {
      setError('获取 Zotero 账户失败');
    }
    setLoadingAccounts(false);
  };

  const loadCollectionsForAccount = async (accountId: number) => {
    setLoadingCollections(true);
    setSelectedCollection(null);
    setError(null);
    try {
      const data = await getZoteroCollections(accountId);
      setCollections(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || '获取文件夹失败');
      setCollections([]);
    }
    setLoadingCollections(false);
  };

  const handleAccountChange = (id: number) => {
    setSelectedAccount(id);
    loadCollectionsForAccount(id);
  };

  const handleExport = async () => {
    if (!selectedAccount) return;
    setIsExporting(true);
    setResult(null);
    try {
      const data = await exportToZotero(paperId, selectedAccount, selectedCollection || undefined, includeChat);
      setResult({ success: data.success, message: data.message });
    } catch (e: any) {
      setResult({ success: false, message: e?.response?.data?.detail || '导出失败' });
    }
    setIsExporting(false);
  };

  if (!isOpen) return null;

  // Build tree from flat list
  const tree: { collection: ZoteroCollection; depth: number }[] = [];
  const childrenMap: Record<string, ZoteroCollection[]> = {};
  const roots: ZoteroCollection[] = [];
  for (const c of collections) {
    if (!c.parent) roots.push(c);
    else {
      if (!childrenMap[c.parent]) childrenMap[c.parent] = [];
      childrenMap[c.parent].push(c);
    }
  }
  const walk = (nodes: ZoteroCollection[], depth: number) => {
    for (const n of nodes) {
      tree.push({ collection: n, depth });
      if (childrenMap[n.key]) walk(childrenMap[n.key], depth + 1);
    }
  };
  walk(roots, 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-800">导出到 Zotero</h3>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600 rounded">
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          {/* Paper title */}
          <div className="text-xs text-gray-500 bg-gray-50 rounded-lg p-3 line-clamp-2">{paperTitle}</div>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2 text-sm text-red-600 bg-red-50 rounded-lg p-3">
              <ExclamationCircleIcon className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Result */}
          {result && (
            <div className={`flex items-start gap-2 text-sm rounded-lg p-3 ${result.success ? 'text-green-700 bg-green-50' : 'text-red-600 bg-red-50'}`}>
              {result.success ? <CheckCircleIcon className="w-5 h-5 shrink-0" /> : <ExclamationCircleIcon className="w-5 h-5 shrink-0" />}
              <span>{result.message}</span>
            </div>
          )}

          {!result?.success && (
            <>
              {/* No accounts */}
              {!loadingAccounts && accounts.length === 0 && (
                <div className="text-sm text-amber-700 bg-amber-50 rounded-lg p-3">
                  尚未添加 Zotero 账户，请在顶部"设置"中添加
                </div>
              )}

              {/* Account selector */}
              {accounts.length > 0 && (
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-2">选择 Zotero 账户</label>
                  <div className="flex flex-wrap gap-2">
                    {accounts.map(acct => (
                      <button key={acct.id}
                        onClick={() => handleAccountChange(acct.id)}
                        className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                          selectedAccount === acct.id
                            ? 'border-blue-400 bg-blue-50 text-blue-700'
                            : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300'
                        }`}>
                        <span className="font-medium">{acct.name}</span>
                        <span className="text-xs text-gray-400 ml-1">
                          ({acct.library_type === 'group' ? '群组' : '个人'})
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Collection picker */}
              {selectedAccount && (
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-2">选择文件夹</label>
                  {loadingCollections ? (
                    <div className="text-sm text-gray-400 py-3 text-center">加载文件夹...</div>
                  ) : (
                    <div className="max-h-48 overflow-y-auto border border-gray-200 rounded-lg">
                      <button onClick={() => setSelectedCollection(null)}
                        className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                          selectedCollection === null ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'
                        }`}>
                        根目录（不放入文件夹）
                      </button>
                      {tree.map(({ collection, depth }) => (
                        <button key={collection.key}
                          onClick={() => setSelectedCollection(collection.key)}
                          className={`w-full text-left px-3 py-2 text-sm flex items-center gap-2 transition-colors ${
                            selectedCollection === collection.key ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-600'
                          }`}
                          style={{ paddingLeft: `${12 + depth * 16}px` }}>
                          <FolderIcon className="w-4 h-4 shrink-0 text-yellow-500" />
                          {collection.name}
                        </button>
                      ))}
                      {collections.length === 0 && !error && (
                        <div className="text-sm text-gray-400 py-3 text-center">此账户暂无文件夹</div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Include chat */}
              {selectedAccount && (
                <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                  <input type="checkbox" checked={includeChat} onChange={e => setIncludeChat(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                  同时导出问答记录
                </label>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">
            {result?.success ? '关闭' : '取消'}
          </button>
          {!result?.success && accounts.length > 0 && (
            <button onClick={handleExport} disabled={isExporting || !selectedAccount}
              className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors">
              {isExporting ? '导出中...' : '导出'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
