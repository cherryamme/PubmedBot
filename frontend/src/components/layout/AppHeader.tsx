import { Cog6ToothIcon } from '@heroicons/react/24/outline';

interface AppHeaderProps {
  onOpenSettings: () => void;
}

export default function AppHeader({ onOpenSettings }: AppHeaderProps) {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-sm">P</span>
        </div>
        <h1 className="text-lg font-semibold text-gray-800">PubMed-Bot</h1>
        <span className="text-xs text-gray-400 hidden sm:block">智能文献检索与整理</span>
      </div>
      <button
        onClick={onOpenSettings}
        className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
        title="设置"
      >
        <Cog6ToothIcon className="w-5 h-5" />
      </button>
    </header>
  );
}
