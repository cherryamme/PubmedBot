import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

function stripCodeFence(text: string): string {
  // Some LLMs wrap their response in ```markdown ... ```
  const trimmed = text.trim();
  const fencePattern = /^```(?:markdown|md|text)?\s*\n([\s\S]*?)\n```\s*$/;
  const match = trimmed.match(fencePattern);
  if (match) return match[1];
  return trimmed;
}

export default function Markdown({ content }: { content: string }) {
  const cleaned = stripCodeFence(content);
  return (
    <div className="md-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
      >
        {cleaned}
      </ReactMarkdown>
    </div>
  );
}
