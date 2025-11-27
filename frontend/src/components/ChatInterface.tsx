import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Send, Sparkles, User } from 'lucide-react';
import { useChatStore } from '../stores/chatStore';
import { useWebSocket, WebSocketMessage } from '../hooks/useWebSocket';


/* =========================
   Typewriter Component
========================= */
const TypewriterText = ({ text, messageId, onComplete }: { text: string; messageId: string; onComplete?: () => void }) => {
    const [displayedText, setDisplayedText] = useState('');
    const indexRef = useRef(0);
    const textRef = useRef(text);
    const messageIdRef = useRef(messageId);
    const completedRef = useRef(false);

    // Reset when messageId changes
    useEffect(() => {
        if (messageIdRef.current !== messageId) {
            messageIdRef.current = messageId;
            textRef.current = text;
            indexRef.current = 0;
            setDisplayedText('');
            completedRef.current = false;
        } else if (textRef.current !== text) {
            // Text updated but same message - update ref but don't reset
            textRef.current = text;
        }
    }, [text, messageId]);

    useEffect(() => {
        if (completedRef.current) return;
        
        const timer = setInterval(() => {
            if (indexRef.current < textRef.current.length) {
                setDisplayedText(textRef.current.substring(0, indexRef.current + 1));
                indexRef.current++;
            } else {
                clearInterval(timer);
                if (!completedRef.current && onComplete) {
                    completedRef.current = true;
                    onComplete();
                }
            }
        }, 15); // Faster speed: 15ms per character

        return () => clearInterval(timer);
    }, [text, messageId, onComplete]);
    
    return <div className="whitespace-pre-wrap" dangerouslySetInnerHTML={{
        __html: displayedText
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n---\n/g, '\n<hr class="my-4 border-gray-200" />\n')
            .replace(/\n/g, '<br />')
    }} />;
};



/* =========================
   Component
========================= */
const ChatInterface: React.FC = () => {

    /* =========================
       Global Store Selectors
    ========================= */
    const messages = useChatStore((state) => state.messages);
    const isGenerating = useChatStore((state) => state.isGenerating);
    const getOrCreateSessionId = useChatStore((state) => state.getOrCreateSessionId);
    const handleWebSocketEvent = useChatStore((state) => state.handleWebSocketEvent);
    const addMessage = useChatStore((state) => state.addMessage);
    const setIsGenerating = useChatStore((state) => state.setIsGenerating);
    const setWsConnected = useChatStore((state) => state.setWsConnected);



    /* =========================
       Local State
    ========================= */
    const [input, setInput] = useState('');
    const [typingMessageIds, setTypingMessageIds] = useState<Set<string>>(new Set());
    const [selectedImage, setSelectedImage] = useState<{ url: string; title: string } | null>(null);
    
    /* =========================
       Session ID
    ========================= */
    const sessionId = getOrCreateSessionId();
    console.log('ChatInterface: sessionId:', sessionId);

    /* =========================
       WebSocket Connection
    ========================= */
    const { sendMessage, isConnected, status } = useWebSocket({
        sessionId,
        onMessage: (message: WebSocketMessage) => {
            console.log('ChatInterface: Received WebSocket message:', message.type, `[timestamp: ${message.timestamp}]`);
            handleWebSocketEvent(message.type, message.data, message.timestamp);
        },
        onConnect: () => {
            console.log('ChatInterface: WebSocket connected successfully');
            setWsConnected(true);
        },
        onDisconnect: () => {
            console.log('ChatInterface: WebSocket disconnected');
            setWsConnected(false);
        },
        onError: (error) => {
            console.error('ChatInterface: WebSocket error:', error);
            setWsConnected(false);
        },
    });

    useEffect(() => {
        console.log('ChatInterface: WebSocket status changed:', status, 'isConnected:', isConnected, 'sessionId:', sessionId);
    }, [status, isConnected, sessionId]);



    /* =========================
       Refs
    ========================= */
    const messagesEndRef = useRef<HTMLDivElement>(null);



    /* =========================
       Helpers
    ========================= */
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };



    /* =========================
       Effects
    ========================= */
    useEffect(() => {
        scrollToBottom();
    }, [messages, isGenerating, typingMessageIds]);

    // Auto-start typewriter for messages with needsTypewriter flag
    useEffect(() => {
        messages.forEach(msg => {
            if (msg.needsTypewriter && !typingMessageIds.has(msg.id)) {
                setTypingMessageIds(prev => new Set(prev).add(msg.id));
            }
        });
    }, [messages, typingMessageIds]);

    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && selectedImage) {
                setSelectedImage(null);
            }
        };
        window.addEventListener('keydown', handleEscape);
        return () => window.removeEventListener('keydown', handleEscape);
    }, [selectedImage]);

    useEffect(() => {
        const handleInitialMessage = (event: CustomEvent<{ message: string }>) => {
            if (isConnected && event.detail.message) {
                setIsGenerating(true);
                sendMessage('message', { theme: event.detail.message });
            }
        };

        window.addEventListener('send-initial-message', handleInitialMessage as EventListener);
        return () => {
            window.removeEventListener('send-initial-message', handleInitialMessage as EventListener);
        };
    }, [isConnected, sendMessage, setIsGenerating]);



    /* =========================
       Callbacks
    ========================= */
    const handleTypingComplete = useCallback((messageId: string) => {
        setTypingMessageIds((prev) => {
            const next = new Set(prev);
            next.delete(messageId);
            return next;
        });
    }, []);



    /* =========================
       Handlers
    ========================= */
    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isGenerating || typingMessageIds.size > 0 || !isConnected) return;

        const userMessage = input.trim();
        setInput('');
        addMessage('user', userMessage);
        setIsGenerating(true);

        const success = sendMessage('message', { theme: userMessage });
        if (!success) {
            console.error('Failed to send message');
            setIsGenerating(false);
        }
    };



    /* =========================
       Render
    ========================= */
    return (
        <div className="flex-1 flex flex-col h-full relative">

            <div className="flex-1 overflow-y-auto p-6 space-y-8 no-scrollbar">
                {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-300 space-y-4">
                        <div className="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center">
                            <Sparkles className="w-8 h-8 text-gray-200" />
                        </div>
                        <p>Start your story journey...</p>
                    </div>
                ) : (
                    messages.map((msg) => (
                        <div key={msg.id} className="space-y-3">
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                            >
                                <div className={`
                                    w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-lg ring-2 ring-white
                                    ${msg.role === 'user'
                                        ? 'bg-gray-900 text-white'
                                        : 'bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white'}
                                `}>
                                    {msg.role === 'user' ? <User className="w-5 h-5" /> : <Sparkles className="w-5 h-5" />}
                                </div>

                                <div className={`
                                    max-w-[80%] rounded-2xl p-5 shadow-sm leading-relaxed
                                    ${msg.role === 'user'
                                        ? 'bg-white text-gray-900 rounded-tr-sm border border-gray-100'
                                        : 'bg-white/80 backdrop-blur-sm border border-white/40 text-gray-800 rounded-tl-sm shadow-md'}
                                `}>
                                    {msg.role === 'assistant' && (msg.needsTypewriter || typingMessageIds.has(msg.id)) ? (
                                        <TypewriterText 
                                            text={msg.content}
                                            messageId={msg.id}
                                            onComplete={() => {
                                                handleTypingComplete(msg.id);
                                                if (msg.needsTypewriter) {
                                                    useChatStore.setState((state) => ({
                                                        messages: state.messages.map(m => 
                                                            m.id === msg.id ? { ...m, needsTypewriter: false } : m
                                                        )
                                                    }));
                                                }
                                            }}
                                        />
                                    ) : (
                                        <div 
                                            className="whitespace-pre-wrap"
                                            dangerouslySetInnerHTML={{
                                                __html: msg.content
                                                    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                                                    .replace(/\n---\n/g, '\n<hr class="my-4 border-gray-200" />\n')
                                                    .replace(/\n/g, '<br />')
                                            }}
                                        />
                                    )}
                                </div>
                            </motion.div>
                            
                            {msg.role === 'assistant' && msg.storyChapters && msg.storyChapters.length > 0 && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.2 }}
                                    className={`ml-14 max-w-[80%] rounded-xl bg-white/60 backdrop-blur-sm border border-white/30 shadow-sm overflow-hidden`}
                                >
                                    <div className="overflow-x-auto no-scrollbar">
                                        <div className="flex gap-3 p-3" style={{ width: 'max-content' }}>
                                            {msg.storyChapters
                                                .sort((a, b) => a.chapter_id - b.chapter_id)
                                                .map((chapter) => (
                                                    <div 
                                                        key={chapter.chapter_id} 
                                                        className="flex-shrink-0 w-56 rounded-lg overflow-hidden border border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow"
                                                        onClick={() => {
                                                            if (chapter.image_url) {
                                                                setSelectedImage({ 
                                                                    url: chapter.image_url, 
                                                                    title: chapter.title || `Chapter ${chapter.chapter_id}` 
                                                                });
                                                            }
                                                        }}
                                                    >
                                                        {chapter.image_url ? (
                                                            <>
                                                                <img
                                                                    src={chapter.image_url}
                                                                    alt={chapter.title || `Chapter ${chapter.chapter_id}`}
                                                                    className="w-full h-40 object-cover cursor-pointer"
                                                                    onError={(e) => {
                                                                        console.error('Image load error:', chapter.image_url);
                                                                        (e.target as HTMLImageElement).style.display = 'none';
                                                                    }}
                                                                    onLoad={() => {
                                                                        console.log('Image loaded:', chapter.image_url);
                                                                    }}
                                                                />
                                                                <p className="text-xs text-gray-600 p-2 text-center font-medium truncate">
                                                                    {chapter.title || `Chapter ${chapter.chapter_id}`}
                                                                </p>
                                                            </>
                                                        ) : (
                                                            <>
                                                                <div className="w-full h-40 bg-gray-100 flex items-center justify-center">
                                                                    <div className="flex flex-col items-center gap-2">
                                                                        <div className="w-8 h-8 border-2 border-gray-300 border-t-purple-500 rounded-full animate-spin" />
                                                                        <span className="text-xs text-gray-500">Loading image...</span>
                                                                    </div>
                                                                </div>
                                                                <p className="text-xs text-gray-600 p-2 text-center font-medium truncate">
                                                                    {chapter.title || `Chapter ${chapter.chapter_id}`}
                                                                </p>
                                                            </>
                                                        )}
                                                    </div>
                                                ))}
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </div>
                    ))
                )}

                {isGenerating && (() => {
                    // Don't show "Thinking..." if the last message already has content
                    // (text is generated, only waiting for images)
                    const lastMessage = messages[messages.length - 1];
                    const hasTextContent = lastMessage && lastMessage.role === 'assistant' && lastMessage.content && lastMessage.content.trim().length > 0;
                    
                    // Only show "Thinking..." if there's no text content yet
                    if (hasTextContent) {
                        return null;
                    }
                    
                    return (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex gap-4"
                        >
                            <div className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-lg ring-2 ring-white bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white">
                                <Sparkles className="w-5 h-5 animate-pulse" />
                            </div>
                            <div className="bg-white/80 backdrop-blur-sm border border-white/40 text-gray-500 rounded-2xl rounded-tl-sm p-5 shadow-md flex items-center gap-3">
                                <div className="flex gap-1">
                                    <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                    <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                    <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                </div>
                                <span className="text-sm font-medium">Thinking...</span>
                            </div>
                        </motion.div>
                    );
                })()}

                <div ref={messagesEndRef} />
            </div>

            <div className="p-6">
                <form onSubmit={handleSend} className="max-w-4xl mx-auto relative group">
                    <div className={`
                        relative bg-white/80 backdrop-blur-xl rounded-2xl p-2
                        shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-white/40
                        transition-all duration-300
                        ${isGenerating || typingMessageIds.size > 0 ? 'opacity-80' : 'hover:shadow-[0_10px_40px_rgb(0,0,0,0.08)]'}
                    `}>
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={!isConnected ? "Connecting to server..." : typingMessageIds.size > 0 ? "AI is typing..." : "What happens next?"}
                            className="w-full h-12 pl-4 pr-14 bg-transparent border-none outline-none text-gray-900 placeholder:text-gray-400 text-lg font-light"
                            disabled={isGenerating || typingMessageIds.size > 0 || !isConnected}
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isGenerating || typingMessageIds.size > 0 || !isConnected}
                            className={`
                                absolute right-2 top-2 bottom-2 w-10 h-10 rounded-xl flex items-center justify-center transition-all
                                ${!input.trim() || isGenerating || typingMessageIds.size > 0 || !isConnected
                                    ? 'bg-gray-100 text-gray-300 cursor-not-allowed'
                                    : 'bg-black text-white hover:scale-105 active:scale-95 shadow-md'}
                            `}
                        >
                            {isGenerating || typingMessageIds.size > 0 ? (
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <Send className="w-4 h-4" />
                            )}
                        </button>
                    </div>
                </form>
            </div>

            {/* Image Modal */}
            {selectedImage && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
                    onClick={() => setSelectedImage(null)}
                >
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.9, opacity: 0 }}
                        className="relative max-w-4xl max-h-[90vh] p-4"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <button
                            onClick={() => setSelectedImage(null)}
                            className="absolute -top-2 -right-2 w-10 h-10 rounded-full bg-white/90 backdrop-blur-sm border border-white/40 shadow-lg flex items-center justify-center text-gray-600 hover:text-gray-900 hover:scale-110 transition-all z-10"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                        <img
                            src={selectedImage.url}
                            alt={selectedImage.title}
                            className="max-w-full max-h-[90vh] rounded-xl shadow-2xl object-contain"
                        />
                        <p className="mt-4 text-center text-white text-sm font-medium bg-black/50 backdrop-blur-sm rounded-lg px-4 py-2 inline-block">
                            {selectedImage.title}
                        </p>
                    </motion.div>
                </motion.div>
            )}
        </div>
    );
};

export default ChatInterface;