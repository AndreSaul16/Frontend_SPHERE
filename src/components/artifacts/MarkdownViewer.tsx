import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Download, FileText } from 'lucide-react';
import type { Artifact } from '@/types/artifact';

interface MarkdownViewerProps {
    artifact: Artifact;
}

export function MarkdownViewer({ artifact }: MarkdownViewerProps) {
    const handleDownload = () => {
        const filename = `${artifact.title.replace(/\s+/g, '_').toLowerCase()}.md`;
        const blob = new Blob([artifact.content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="flex flex-col h-full bg-[#0d0d12]">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-3 bg-white/[0.02] border-b border-white/5">
                <div className="flex items-center gap-3">
                    <FileText className="h-4 w-4 text-gray-500" />
                    <span className="text-[10px] font-mono text-gray-500 uppercase tracking-widest">
                        Document Preview
                    </span>
                </div>
                <button
                    onClick={handleDownload}
                    className="p-2 rounded-xl hover:bg-white/5 transition-all text-gray-400 hover:text-electric-cyan"
                    title="Descargar .md"
                >
                    <Download className="h-4 w-4" />
                </button>
            </div>

            {/* Markdown Content */}
            <div className="flex-1 overflow-auto p-8 sm:p-12 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                <div className="max-w-3xl mx-auto">
                    <div className="prose prose-invert prose-sm 
                        prose-headings:text-white prose-headings:font-bold prose-headings:tracking-tight
                        prose-p:text-gray-400 prose-p:leading-relaxed prose-p:mb-6
                        prose-a:text-luxury-purple prose-a:no-underline hover:prose-a:underline
                        prose-code:text-electric-cyan prose-code:bg-white/5 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:before:content-none prose-code:after:content-none
                        prose-pre:bg-white/[0.03] prose-pre:border prose-pre:border-white/5 prose-pre:rounded-2xl
                        prose-strong:text-white prose-strong:font-bold
                        prose-ul:text-gray-400 prose-ol:text-gray-400
                        prose-blockquote:border-l-luxury-purple prose-blockquote:bg-luxury-purple/5 prose-blockquote:py-1 prose-blockquote:px-6 prose-blockquote:rounded-r-xl
                        prose-img:rounded-2xl prose-img:border prose-img:border-white/5
                    ">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {artifact.content}
                        </ReactMarkdown>
                    </div>
                </div>
            </div>
        </div>
    );
}
