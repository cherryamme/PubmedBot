import { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';
import { usePaperStore } from '../../stores/paperStore';
import ChatMessage from './ChatMessage';
import Markdown from '../common/Markdown';

export default function ChatPanel({ paperId }: { paperId: number }) {
  const {
    chatMessages, streamingContent, isChatting,
    sendMessage, loadChatHistory,
  } = usePaperStore();
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadChatHistory(paperId);
  }, [paperId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatMessages, streamingContent]);

  const handleSend = () => {
    if (!input.trim() || isChatting) return;
    sendMessage(paperId, input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[400px]">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">智能问答</h3>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-3 mb-3">
        {chatMessages.length === 0 && !streamingContent && (
          <div className="text-center py-8 text-sm text-gray-400">
            <p>对这篇论文有什么疑问？</p>
            <div className="flex flex-wrap justify-center gap-2 mt-3">
              {['这篇文章的主要发现是什么？', '用了什么实验方法？', '有哪些未来研究方向？'].map(q => (
                <button
                  key={q}
                  onClick={() => { setInput(q); }}
                  className="text-xs px-3 py-1.5 bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {chatMessages.map((msg) => (
          <ChatMessage key={msg.id} role={msg.role} content={msg.content} />
        ))}

        {/* Streaming response */}
        {streamingContent && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-gray-100 text-gray-600 flex items-center justify-center text-xs font-medium shrink-0">
              AI
            </div>
            <div className="max-w-[80%] bg-gray-100 rounded-xl px-4 py-2.5">
              <Markdown content={streamingContent} />
              <span className="inline-block w-1.5 h-4 bg-gray-400 animate-pulse ml-0.5" />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-2 border-t border-gray-200 pt-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入问题..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isChatting}
        />
        <button
          onClick={handleSend}
          disabled={isChatting || !input.trim()}
          className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <PaperAirplaneIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
