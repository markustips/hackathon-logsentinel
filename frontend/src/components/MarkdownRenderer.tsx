import { useMemo } from 'react'

interface MarkdownRendererProps {
  content: string
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const formattedContent = useMemo(() => {
    // Simple markdown parser for basic formatting
    let html = content

    // Code blocks (```)
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (_, _lang, code) => {
      return `<pre class="bg-gray-900 p-3 rounded-lg my-2 overflow-x-auto"><code class="text-sm text-gray-300">${escapeHtml(code.trim())}</code></pre>`
    })

    // Inline code (`)
    html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-900 px-1.5 py-0.5 rounded text-sm text-blue-400">$1</code>')

    // Bold (**text**)
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold text-white">$1</strong>')

    // Italic (*text*)
    html = html.replace(/\*([^*]+)\*/g, '<em class="italic">$1</em>')

    // Headers (## text)
    html = html.replace(/^### (.+)$/gm, '<h3 class="text-base font-semibold text-white mt-3 mb-2">$1</h3>')
    html = html.replace(/^## (.+)$/gm, '<h2 class="text-lg font-semibold text-white mt-4 mb-2">$1</h2>')
    html = html.replace(/^# (.+)$/gm, '<h1 class="text-xl font-bold text-white mt-4 mb-3">$1</h1>')

    // Unordered lists (- item)
    html = html.replace(/^- (.+)$/gm, '<li class="ml-4 mb-1">• $1</li>')
    html = html.replace(/(<li[^>]*>.*<\/li>\n?)+/g, '<ul class="my-2">$&</ul>')

    // Ordered lists (1. item)
    html = html.replace(/^\d+\. (.+)$/gm, '<li class="ml-4 mb-1 list-decimal">$1</li>')
    html = html.replace(/(<li[^>]*class="ml-4 mb-1 list-decimal"[^>]*>.*<\/li>\n?)+/g, '<ol class="my-2 ml-4">$&</ol>')

    // Links [text](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 underline">$1</a>')

    // MITRE technique references (T####)
    html = html.replace(/\b(T\d{4}(?:\.\d{3})?)\b/g, '<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-900/40 text-purple-300">$1</span>')

    // Line breaks
    html = html.replace(/\n\n/g, '<br/><br/>')
    html = html.replace(/\n/g, '<br/>')

    return html
  }, [content])

  const escapeHtml = (text: string) => {
    const div = document.createElement('div')
    div.textContent = text
    return div.innerHTML
  }

  return (
    <div
      className="prose prose-sm max-w-none text-gray-200"
      dangerouslySetInnerHTML={{ __html: formattedContent }}
    />
  )
}
