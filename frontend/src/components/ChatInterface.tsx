import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Send, Sparkles, User } from 'lucide-react';
import { useChatStore } from '../stores/chatStore';

// Typewriter Component for Streaming Effect
const Typewriter = ({ text, onComplete }: { text: string; onComplete?: () => void }) => {
    const [displayedText, setDisplayedText] = useState('');
    const indexRef = useRef(0);

    useEffect(() => {
        indexRef.current = 0;
        setDisplayedText('');

        const timer = setInterval(() => {
            if (indexRef.current < text.length) {
                setDisplayedText((prev) => prev + text.charAt(indexRef.current));
                indexRef.current++;
            } else {
                clearInterval(timer);
                if (onComplete) onComplete();
            }
        }, 30); // Adjust speed here (lower = faster)

        return () => clearInterval(timer);
    }, [text, onComplete]);

    return <p className="whitespace-pre-wrap">{displayedText}</p>;
};

const ChatInterface: React.FC = () => {
    const messages = useChatStore((state) => state.messages);
    const isGenerating = useChatStore((state) => state.isGenerating);
    const addMessage = useChatStore((state) => state.addMessage);
    const setIsGenerating = useChatStore((state) => state.setIsGenerating);
    const addLog = useChatStore((state) => state.addLog);
    const updateAgentStep = useChatStore((state) => state.updateAgentStep);
    const setWorkflowBranch = useChatStore((state) => state.setWorkflowBranch);
    const setAgentSteps = useChatStore((state) => state.setAgentSteps);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isGenerating, isTyping]); // Scroll on new messages or state change

    const handleTypingComplete = useCallback(() => {
        setIsTyping(false);
    }, []);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isGenerating || isTyping) return;

        const userMessage = input;
        setInput('');
        addMessage('user', userMessage);
        setIsGenerating(true);

        // Reset Workflow
        setWorkflowBranch('router');
        setAgentSteps([{ id: 'router', name: 'Router', status: 'active', details: 'Analyzing intent...' }]);
        addLog('Received user prompt: ' + userMessage);

        // Simulate Router Delay
        await new Promise(r => setTimeout(r, 1000));

        // Router Decision Logic (Mock)
        if (userMessage.toLowerCase().includes('story')) {
            // Branch: Story Graph
            setWorkflowBranch('story-graph');
            updateAgentStep('router', 'completed', 'Route: Story Graph');
            addLog('Router: Detected story intent. Routing to Story Graph.', 'success');

            // Initialize Story Steps
            setAgentSteps([
                { id: 'router', name: 'Router', status: 'completed', details: 'Route: Story Graph' },
                { id: 'planning', name: 'Planning Story', status: 'pending' },
                { id: 'writing', name: 'Writing Content', status: 'pending' },
                { id: 'illustrating', name: 'Generating Illustrations', status: 'pending' },
            ]);

            // Step 1: Planning
            updateAgentStep('planning', 'active', 'Analyzing story requirements...');
            await new Promise(r => setTimeout(r, 1500));
            updateAgentStep('planning', 'completed', 'Story arc generated.');
            addLog('Story planning complete.', 'success');

            // Step 2: Writing
            updateAgentStep('writing', 'active', 'Drafting story content...');
            await new Promise(r => setTimeout(r, 2000));

            // Add assistant message (Typewriter will handle the visual streaming)
            addMessage('assistant', "Here is a story based on your idea: \n\nOnce upon a time, in a land far away, there lived a brave little toaster who dreamed of exploring the world beyond the kitchen counter. Every morning, as the sun peeked through the curtains, the toaster would watch the birds fly high in the sky and wonder what it would be like to feel the wind against its chrome finish. One day, the toaster decided that it was time to leave the safety of the countertop and embark on a grand adventure. It packed a few slices of bread for the journey and set off into the unknown, ready to face whatever challenges lay ahead. Along the way, it met a wise old blender who taught it the secrets of mixing and mingling with different appliances. Together, they traveled through dense forests of tangled cords and crossed vast deserts of dusty floorboards, always looking for the legendary power outlet that was said to grant eternal energy to any appliance that found it.");

            setIsTyping(true); // Lock input for streaming
            updateAgentStep('writing', 'completed', 'First draft ready.');
            addLog('Content generation complete.', 'success');

            // Step 3: Illustrating (Mock start)
            updateAgentStep('illustrating', 'active', 'Generating scenes...');
            addLog('Starting image generation pipeline...');

        } else {
            // Branch: Chat
            setWorkflowBranch('chat');
            updateAgentStep('router', 'completed', 'Route: Chat');
            addLog('Router: Detected chat intent. Routing to Chat.', 'info');

            await new Promise(r => setTimeout(r, 500));

            addMessage('assistant', "I can help you with that! I'm an AI assistant designed to help you create stories. Try asking me to 'write a story'!");
            setIsTyping(true);
        }

        setIsGenerating(false);
    };

    return (
        <div className="flex-1 flex flex-col h-full relative">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8 no-scrollbar">
                {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-300 space-y-4">
                        <div className="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center">
                            <Sparkles className="w-8 h-8 text-gray-200" />
                        </div>
                        <p>Start your story journey...</p>
                    </div>
                ) : (
                    messages.map((msg, index) => (
                        <motion.div
                            key={msg.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                        >
                            {/* Avatar */}
                            <div className={`
                w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-lg ring-2 ring-white
                ${msg.role === 'user'
                                    ? 'bg-gray-900 text-white'
                                    : 'bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white'}
              `}>
                                {msg.role === 'user' ? <User className="w-5 h-5" /> : <Sparkles className="w-5 h-5" />}
                            </div>

                            {/* Bubble */}
                            <div className={`
                max-w-[80%] rounded-2xl p-5 shadow-sm leading-relaxed
                ${msg.role === 'user'
                                    ? 'bg-white text-gray-900 rounded-tr-sm border border-gray-100'
                                    : 'bg-white/80 backdrop-blur-sm border border-white/40 text-gray-800 rounded-tl-sm shadow-md'}
              `}>
                                {msg.role === 'assistant' && index === messages.length - 1 && isTyping ? (
                                    <Typewriter text={msg.content} onComplete={handleTypingComplete} />
                                ) : (
                                    <p className="whitespace-pre-wrap">{msg.content}</p>
                                )}
                            </div>
                        </motion.div>
                    ))
                )}

                {/* Loading Indicator */}
                {isGenerating && (
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
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-6">
                <form onSubmit={handleSend} className="max-w-4xl mx-auto relative group">
                    <div className={`
            relative bg-white/80 backdrop-blur-xl rounded-2xl p-2
            shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-white/40
            transition-all duration-300
            ${isGenerating || isTyping ? 'opacity-80' : 'hover:shadow-[0_10px_40px_rgb(0,0,0,0.08)]'}
          `}>
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={isTyping ? "AI is typing..." : "What happens next?"}
                            className="w-full h-12 pl-4 pr-14 bg-transparent border-none outline-none text-gray-900 placeholder:text-gray-400 text-lg font-light"
                            disabled={isGenerating || isTyping}
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isGenerating || isTyping}
                            className={`
                absolute right-2 top-2 bottom-2 w-10 h-10 rounded-xl flex items-center justify-center transition-all
                ${!input.trim() || isGenerating || isTyping
                                    ? 'bg-gray-100 text-gray-300 cursor-not-allowed'
                                    : 'bg-black text-white hover:scale-105 active:scale-95 shadow-md'}
              `}
                        >
                            {isGenerating || isTyping ? (
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <Send className="w-4 h-4" />
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ChatInterface;
