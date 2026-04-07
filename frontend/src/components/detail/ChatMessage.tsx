import Markdown from '../common/Markdown';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === 'user';
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium shrink-0 ${
        isUser ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
      }`}>
        {isUser ? '你' : 'AI'}
      </div>
      <div className={`max-w-[80%] rounded-xl px-4 py-2.5 ${
        isUser
          ? 'bg-blue-600 text-white text-sm'
          : 'bg-gray-100 text-gray-700'
      }`}>
        {isUser ? (
          <p className="text-sm">{content}</p>
        ) : (
          <Markdown content={content} />
        )}
      </div>
    </div>
  );
}
