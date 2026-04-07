import { useEffect, useState } from 'react';
import { XMarkIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import { useConfigStore } from '../../stores/configStore';
import { getZoteroAccounts, addZoteroAccount, deleteZoteroAccount } from '../../api/zotero';
import type { ZoteroAccount } from '../../types';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const { config, loadConfig, updateConfig } = useConfigStore();
  const [form, setForm] = useState({
    ncbi_email: '', ncbi_api_key: '', easyscholar_secret_key: '',
    llm_base_url: '', llm_model: '', llm_api_key: '', unpaywall_email: '',
  });

  // Zotero accounts
  const [zoteroAccounts, setZoteroAccounts] = useState<ZoteroAccount[]>([]);
  const [showAddZotero, setShowAddZotero] = useState(false);
  const [newZotero, setNewZotero] = useState({ name: '', library_id: '', library_type: 'user', api_key: '' });
  const [zoteroLoading, setZoteroLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadConfig();
      loadZoteroAccounts();
    }
  }, [isOpen]);

  useEffect(() => {
    if (config) {
      setForm(prev => ({
        ...prev,
        ncbi_email: config.ncbi_email || '',
        llm_base_url: config.llm_base_url || '',
        llm_model: config.llm_model || '',
        unpaywall_email: config.unpaywall_email || '',
      }));
    }
  }, [config]);

  const loadZoteroAccounts = async () => {
    try { setZoteroAccounts(await getZoteroAccounts()); } catch { /* */ }
  };

  const handleSave = async () => {
    const update: Record<string, string> = {};
    for (const [key, value] of Object.entries(form)) {
      if (value) update[key] = value;
    }
    await updateConfig(update);
    onClose();
  };

  const handleAddZotero = async () => {
    if (!newZotero.name || !newZotero.library_id || !newZotero.api_key) return;
    setZoteroLoading(true);
    try {
      await addZoteroAccount(newZotero);
      await loadZoteroAccounts();
      setNewZotero({ name: '', library_id: '', library_type: 'user', api_key: '' });
      setShowAddZotero(false);
    } catch { /* */ }
    setZoteroLoading(false);
  };

  const handleDeleteZotero = async (id: number) => {
    try {
      await deleteZoteroAccount(id);
      setZoteroAccounts(prev => prev.filter(a => a.id !== id));
    } catch { /* */ }
  };

  if (!isOpen) return null;

  const Field = ({ label, name, placeholder, type = 'text' }: { label: string; name: string; placeholder: string; type?: string }) => (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      <input type={type} value={(form as any)[name]}
        onChange={(e) => setForm(prev => ({ ...prev, [name]: e.target.value }))}
        placeholder={placeholder}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-y-auto mx-4">
        <div className="flex items-center justify-between p-5 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-800">设置</h2>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600 rounded"><XMarkIcon className="w-5 h-5" /></button>
        </div>
        <div className="p-5 space-y-5">
          {/* LLM */}
          <Section title="大模型 (LLM)">
            <Field label="API Base URL" name="llm_base_url" placeholder="https://api.openai.com/v1" />
            <Field label="API Key" name="llm_api_key" placeholder={config?.llm_api_key_set ? '已设置 (留空保持不变)' : 'sk-xxx'} type="password" />
            <Field label="模型名称" name="llm_model" placeholder="gpt-4o" />
          </Section>

          {/* NCBI */}
          <Section title="NCBI / PubMed">
            <Field label="邮箱" name="ncbi_email" placeholder="your@email.com" />
            <Field label="API Key (可选)" name="ncbi_api_key" placeholder={config?.ncbi_api_key_set ? '已设置' : '可选，提升速率'} type="password" />
          </Section>

          <Section title="EasyScholar 影响因子">
            <Field label="Secret Key" name="easyscholar_secret_key" placeholder={config?.easyscholar_key_set ? '已设置' : '从 easyscholar.cc 获取'} type="password" />
          </Section>

          <Section title="Unpaywall 全文获取">
            <Field label="邮箱" name="unpaywall_email" placeholder="your@email.com" />
          </Section>

          {/* Zotero multi-account */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-700">Zotero 账户</h3>
              <button onClick={() => setShowAddZotero(!showAddZotero)}
                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700">
                <PlusIcon className="w-3.5 h-3.5" /> 添加账户
              </button>
            </div>

            {/* Existing accounts */}
            {zoteroAccounts.length > 0 && (
              <div className="space-y-2 mb-3">
                {zoteroAccounts.map(acct => (
                  <div key={acct.id} className="flex items-center justify-between px-3 py-2.5 bg-gray-50 rounded-lg border border-gray-200">
                    <div>
                      <span className="text-sm font-medium text-gray-700">{acct.name}</span>
                      <span className="text-xs text-gray-400 ml-2">
                        {acct.library_type === 'group' ? '群组' : '个人'} · {acct.library_id}
                      </span>
                    </div>
                    <button onClick={() => handleDeleteZotero(acct.id)}
                      className="p-1 text-gray-300 hover:text-red-500 transition-colors">
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
            {zoteroAccounts.length === 0 && !showAddZotero && (
              <p className="text-xs text-gray-400 mb-3">尚未添加 Zotero 账户</p>
            )}

            {/* Add form */}
            {showAddZotero && (
              <div className="space-y-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <input value={newZotero.name} onChange={e => setNewZotero(p => ({ ...p, name: e.target.value }))}
                  placeholder="显示名称（如：我的Zotero）"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <div className="flex gap-2">
                  <input value={newZotero.library_id} onChange={e => setNewZotero(p => ({ ...p, library_id: e.target.value }))}
                    placeholder="Library ID" className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  <select value={newZotero.library_type} onChange={e => setNewZotero(p => ({ ...p, library_type: e.target.value }))}
                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="user">个人</option>
                    <option value="group">群组</option>
                  </select>
                </div>
                <input value={newZotero.api_key} onChange={e => setNewZotero(p => ({ ...p, api_key: e.target.value }))}
                  placeholder="API Key" type="password"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <div className="flex justify-end gap-2 pt-1">
                  <button onClick={() => setShowAddZotero(false)} className="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded-lg">取消</button>
                  <button onClick={handleAddZotero} disabled={zoteroLoading || !newZotero.name || !newZotero.library_id || !newZotero.api_key}
                    className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                    {zoteroLoading ? '添加中...' : '添加'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="p-5 border-t border-gray-200 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">取消</button>
          <button onClick={handleSave} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">保存</button>
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-sm font-medium text-gray-700 mb-3">{title}</h3>
      <div className="space-y-3">{children}</div>
    </div>
  );
}
