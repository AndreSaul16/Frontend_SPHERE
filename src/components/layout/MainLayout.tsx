import { type ReactNode, useState, useCallback, useEffect } from "react";
import { Menu, X, GripVertical } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { useChatStore } from "@/store/useChatStore";

interface MainLayoutProps {
    sidebar: ReactNode;
    chat: ReactNode;
    artifactPanel?: ReactNode;
    className?: string;
}

// Min/Max widths for the artifact panel (in pixels)
const MIN_PANEL_WIDTH = 350;
const MAX_PANEL_WIDTH = 800;
const DEFAULT_PANEL_WIDTH = 450;

export function MainLayout({ sidebar, chat, artifactPanel, className }: MainLayoutProps) {
    const { isSidebarOpen, toggleSidebar, isArtifactPanelOpen } = useChatStore();

    // Panel width state (desktop only)
    const [panelWidth, setPanelWidth] = useState(DEFAULT_PANEL_WIDTH);
    const [isResizing, setIsResizing] = useState(false);

    // Handle mouse drag for resizing
    const handleMouseDown = useCallback((e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizing(true);
    }, []);

    const handleMouseMove = useCallback((e: MouseEvent) => {
        if (!isResizing) return;

        // Calculate new width from right edge of window
        const newWidth = window.innerWidth - e.clientX;

        // Clamp to min/max
        if (newWidth >= MIN_PANEL_WIDTH && newWidth <= MAX_PANEL_WIDTH) {
            setPanelWidth(newWidth);
        }
    }, [isResizing]);

    const handleMouseUp = useCallback(() => {
        setIsResizing(false);
    }, []);

    // Attach/detach global mouse listeners for drag
    useEffect(() => {
        if (isResizing) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        } else {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
    }, [isResizing, handleMouseMove, handleMouseUp]);

    return (
        <div className={cn("flex h-[100dvh] w-full bg-transparent overflow-hidden", className)}>
            {/* Mobile Menu Button - Dynamic Position */}
            <button
                onClick={() => toggleSidebar()}
                className={cn(
                    "lg:hidden fixed top-3.5 z-50 p-2.5 bg-surface/80 backdrop-blur-md border border-white/5 rounded-xl text-white hover:bg-surface transition-all duration-300 shadow-xl",
                    isSidebarOpen ? "left-[240px]" : "left-4"
                )}
            >
                {isSidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>

            {/* Left Sidebar - Responsive */}
            <aside className={cn(
                "fixed lg:relative inset-y-0 left-0 z-40 w-[280px] lg:w-[320px] h-full border-r border-white/5 flex-shrink-0 glass-panel transform transition-transform duration-300 ease-in-out",
                isSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
            )}>
                {sidebar}
            </aside>

            {/* Mobile Backdrop for Sidebar */}
            {isSidebarOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="lg:hidden fixed inset-0 z-30 bg-midnight/60 backdrop-blur-sm"
                    onClick={() => toggleSidebar(false)}
                />
            )}

            {/* Center Chat - Flexible */}
            <main className="flex-1 h-full relative flex flex-col min-w-0 z-10 bg-transparent">
                {chat}
            </main>

            {/* Right Artifact Panel */}
            {artifactPanel && (
                <aside
                    className={cn(
                        "h-full border-l border-white/5 glass-panel shadow-2xl transition-all",
                        "fixed inset-0 z-[60] xl:relative xl:inset-auto xl:z-20",
                        isArtifactPanelOpen ? "translate-x-0 opacity-100" : "translate-x-full opacity-0 pointer-events-none xl:hidden",
                        isResizing ? "transition-none" : "duration-300"
                    )}
                    style={{ width: window.innerWidth >= 1280 ? `${panelWidth}px` : undefined }}
                >
                    {/* Resize Handle - Desktop Only */}
                    <div
                        onMouseDown={handleMouseDown}
                        className={cn(
                            "hidden xl:flex absolute left-0 top-0 bottom-0 w-3 cursor-col-resize items-center justify-center group hover:bg-electric-cyan/10 transition-colors z-10",
                            isResizing && "bg-electric-cyan/20"
                        )}
                    >
                        <GripVertical className={cn(
                            "h-6 w-4 text-white/20 group-hover:text-electric-cyan transition-colors",
                            isResizing && "text-electric-cyan"
                        )} />
                    </div>

                    {/* Panel Content */}
                    <div className="h-full xl:pl-3">
                        {artifactPanel}
                    </div>
                </aside>
            )}
        </div>
    );
}
