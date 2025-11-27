import React, { useEffect, useState, useRef } from 'react';
import { PanelRightOpen } from 'lucide-react';
import Sidebar from '../../components/Sidebar';
import ChatInterface from '../../components/ChatInterface';
import { useChatStore } from '../../stores/chatStore';



/* =========================
   Component
========================= */
const Generate: React.FC = () => {

    /* =========================
       Global Store
    ========================= */
    const { addMessage, messages } = useChatStore();
    const hasSentInitialPrompt = useRef(false);



    /* =========================
       State
    ========================= */
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);



    /* =========================
       Effects
    ========================= */
    useEffect(() => {
        const initialPrompt = sessionStorage.getItem('initial_prompt');

        if (initialPrompt && messages.length === 0 && !hasSentInitialPrompt.current) {
            addMessage('user', initialPrompt);
            sessionStorage.removeItem('initial_prompt');
            hasSentInitialPrompt.current = true;
            
            setTimeout(() => {
                const event = new CustomEvent('send-initial-message', {
                    detail: { message: initialPrompt }
                });
                window.dispatchEvent(event);
            }, 500);
        }
    }, [addMessage, messages.length]);



    /* =========================
       Render
    ========================= */
    return (
        <div className="h-screen w-full relative overflow-hidden">

            <div
                className={`h-full transition-all duration-500 ease-in-out ${isSidebarOpen ? 'mr-96' : 'mx-auto max-w-5xl'}`}
            >
                <ChatInterface />
            </div>

            <Sidebar
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
            />

            {!isSidebarOpen && (
                <button
                    onClick={() => setIsSidebarOpen(true)}
                    className="fixed bottom-6 left-6 p-3 bg-white/80 backdrop-blur-md border border-white/40 shadow-lg rounded-full text-gray-600 hover:text-gray-900 hover:scale-105 transition-all z-40 group"
                    title="Open Agent Workflow"
                >
                    <PanelRightOpen className="w-6 h-6" />
                    <span className="absolute left-full ml-3 top-1/2 -translate-y-1/2 bg-black text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                        View Agent Workflow
                    </span>
                </button>
            )}
        </div>
    );
};

export default Generate;