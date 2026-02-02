import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import rehypeSanitize from 'rehype-sanitize';
import 'highlight.js/styles/atom-one-dark.css';
import { motion } from 'framer-motion';
import { cn } from "@/lib/utils";
import type { Message, Agent } from "@/types";
import { ArtifactCard } from './ArtifactCard';
import { useChatStore } from '@/store/useChatStore';
import { useUserAvatar } from '@/hooks/useUserAvatar';
import { useAgentAvatars } from '@/hooks/useAgentAvatars';

interface MessageBubbleProps {
    message: Message;
    agent?: Agent;
    isTyping?: boolean;
    isLast?: boolean;
}

export function MessageBubble({ message, agent, isTyping, isLast }: MessageBubbleProps) {
    const isUser = message.role === 'user';
    const isSystem = message.role === 'system';
    const userAvatar = useUserAvatar();
    const agentAvatars = useAgentAvatars();
    const artifacts = useChatStore(state => state.artifacts);

    // Get custom avatar for agent if exists
    const customAgentAvatar = agent?.id ? agentAvatars[agent.id] : null;

    // HUD Colors (Fallbacks)
    const defaultColor = '#00F0C8'; // Cyan
    const activeHexColor = agent?.hexColor || defaultColor;

    if (isSystem) {
        return (
            <div className="flex justify-center my-3 sm:my-4 px-2">
                <div className="bg-midnight/90 border border-surface-highlight text-text-secondary text-[11px] sm:text-xs px-4 py-2 rounded-2xl shadow-md backdrop-blur-md max-w-[85%] text-left whitespace-pre-wrap">
                    <ReactMarkdown
                        rehypePlugins={[rehypeSanitize]}
                        components={{
                            p: ({ children }) => <span>{children}</span>,
                            strong: ({ children }) => <strong className="text-text-primary font-semibold">{children}</strong>
                        }}
                    >
                        {message.content}
                    </ReactMarkdown>
                </div>
            </div>
        );
    }

    return (
        <div className={cn("flex w-full mb-3 sm:mb-4", isUser ? "justify-end" : "justify-start")}>
            <div className={cn("flex max-w-[88%] sm:max-w-[80%] gap-2 sm:gap-3", isUser ? "flex-row-reverse" : "flex-row")}>

                {/* Agent Avatar */}
                {!isUser && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className={cn(
                            "h-7 w-7 sm:h-8 sm:w-8 rounded-full flex items-center justify-center flex-shrink-0 border shadow-sm mt-1 bg-surface transition-colors duration-500 overflow-hidden",
                        )}
                        style={{ borderColor: `${activeHexColor}40` }}
                    >
                        {customAgentAvatar ? (
                            <img src={customAgentAvatar} alt={agent?.name} className="h-full w-full object-cover" />
                        ) : agent ? (
                            <span className={cn("text-[10px] sm:text-xs font-bold", agent.color)}>{agent.avatar}</span>
                        ) : (
                            <span className="text-[10px] sm:text-xs">🤖</span>
                        )}
                    </motion.div>
                )}

                {/* User Avatar */}
                {isUser && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="h-7 w-7 sm:h-8 sm:w-8 rounded-full flex items-center justify-center flex-shrink-0 border border-cyan-500/30 shadow-sm mt-1 bg-gradient-to-br from-indigo-500 to-purple-600 overflow-hidden"
                    >
                        {userAvatar ? (
                            <img src={userAvatar} alt="You" className="h-full w-full object-cover" />
                        ) : (
                            <span className="text-[10px] sm:text-xs font-bold text-white">S</span>
                        )}
                    </motion.div>
                )}

                {/* Bubble - IRON MAN HUD Morphing */}
                <motion.div
                    layout
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{
                        opacity: 1,
                        y: 0,
                        scale: 1,
                        borderColor: isUser ? '#22D3EE20' : `${activeHexColor}50`,
                        boxShadow: isUser ? 'none' : `0 0 15px ${activeHexColor}15`
                    }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                    className={cn(
                        "p-3 sm:p-4 rounded-2xl shadow-lg text-sm leading-relaxed border text-left",
                        isUser
                            ? "bg-user-bubble text-white rounded-tr-sm border-cyan-500/20"
                            : "bg-ai-bubble/95 text-text-primary rounded-tl-sm backdrop-blur-sm relative"
                    )}
                >
                    {!isUser && (
                        <motion.div
                            animate={{ color: activeHexColor }}
                            className="text-[9px] sm:text-[10px] font-bold mb-1 uppercase tracking-widest opacity-80 flex items-center gap-1.5"
                        >
                            <span className="h-1 w-1 rounded-full bg-current animate-pulse" />
                            {agent ? agent.name.split(' ')[0] : 'Sintonizando...'}
                        </motion.div>
                    )}

                    <div className="prose prose-invert prose-sm max-w-none break-words leading-relaxed [&>p]:mb-3 last:[&>p]:mb-0">
                        {/* Process message content, detecting artifact placeholders */}
                        {(() => {
                            const artifactPattern = /\[ARTIFACT:([^:]+):([^\]]+)\]/g;
                            const parts: React.ReactNode[] = [];
                            let lastIndex = 0;
                            let match;
                            let partKey = 0;

                            const content = message.content;

                            // Markdown components Shared Config
                            const markdownComponents = {
                                p: ({ children, ...props }: any) => {
                                    // Hack to prevent hydration errors: if children contain a block element (like pre), don't wrap in p
                                    const hasBlock = React.Children.toArray(children).some(
                                        child => React.isValidElement(child) && ['pre', 'ul', 'ol', 'blockquote'].includes((child.type as any).name || (child.type as any))
                                    );
                                    if (hasBlock) return <>{children}</>;
                                    return <p className="mb-3 last:mb-0 leading-relaxed" {...props}>{children}</p>;
                                },
                                code({ inline, className, children, ...props }: any) {
                                    if (!inline) {
                                        return (
                                            <div className="my-3 overflow-hidden rounded-lg border border-surface-highlight shadow-sm">
                                                <pre className="bg-midnight/80 p-3 overflow-x-auto text-[13px]">
                                                    <code className={cn("font-mono", className)} {...props}>
                                                        {children}
                                                    </code>
                                                </pre>
                                            </div>
                                        );
                                    }
                                    return (
                                        <code className={cn("bg-surface-highlight/50 px-1.5 py-0.5 rounded text-xs font-mono text-electric-cyan border border-electric-cyan/10", className)} {...props}>
                                            {children}
                                        </code>
                                    );
                                },
                                ul: ({ children }: any) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
                                ol: ({ children }: any) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
                                li: ({ children }: any) => <li className="text-text-primary/90">{children}</li>,
                                blockquote: ({ children }: any) => (
                                    <blockquote className="border-l-2 border-electric-cyan/30 pl-4 py-1 my-3 bg-electric-cyan/5 rounded-r text-text-secondary italic">
                                        {children}
                                    </blockquote>
                                ),
                            };

                            while ((match = artifactPattern.exec(content)) !== null) {
                                // Add text before the placeholder
                                if (match.index > lastIndex) {
                                    const textBefore = content.slice(lastIndex, match.index);
                                    if (textBefore.trim()) {
                                        parts.push(
                                            <ReactMarkdown
                                                key={`text-${partKey++}`}
                                                rehypePlugins={[rehypeSanitize, rehypeHighlight]}
                                                components={markdownComponents}
                                            >
                                                {textBefore}
                                            </ReactMarkdown>
                                        );
                                    }
                                }

                                // Add the artifact card
                                const artifactId = match[1];
                                const artifact = artifacts.find(a => a.id === artifactId);
                                if (artifact) {
                                    parts.push(
                                        <ArtifactCard
                                            key={`artifact-${artifactId}`}
                                            content={artifact.content}
                                            language={artifact.language || ''}
                                            title={artifact.title}
                                            artifactId={artifactId}
                                        />
                                    );
                                }

                                lastIndex = match.index + match[0].length;
                            }

                            // Add remaining text after last placeholder
                            if (lastIndex < content.length) {
                                const remaining = content.slice(lastIndex);
                                if (remaining.trim()) {
                                    parts.push(
                                        <ReactMarkdown
                                            key={`text-${partKey++}`}
                                            rehypePlugins={[rehypeSanitize, rehypeHighlight]}
                                            components={markdownComponents}
                                        >
                                            {remaining}
                                        </ReactMarkdown>
                                    );
                                }
                            }

                            // If no placeholders found, render normally
                            if (parts.length === 0) {
                                return (
                                    <ReactMarkdown
                                        rehypePlugins={[rehypeSanitize, rehypeHighlight]}
                                        components={markdownComponents}
                                    >
                                        {message.content}
                                    </ReactMarkdown>
                                );
                            }

                            return parts;
                        })()}
                        {/* Cursor Fantasma */}
                        {isTyping && isLast && !isUser && (
                            <motion.span
                                animate={{ opacity: [1, 0] }}
                                transition={{ repeat: Infinity, duration: 0.8 }}
                                className="inline-block w-1.5 h-4 ml-1 align-middle"
                                style={{ backgroundColor: activeHexColor }}
                            />
                        )}
                    </div>

                    <div className="flex items-center justify-end gap-2 mt-2">
                        {!isUser && (
                            <span className="text-[8px] sm:text-[9px] opacity-30 font-mono tracking-tighter uppercase">
                                freq: {Math.floor(Math.random() * 900 + 100)}mhz
                            </span>
                        )}
                        <span className="text-[9px] sm:text-[10px] opacity-30">
                            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
