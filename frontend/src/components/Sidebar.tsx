import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Circle,
    Loader2,
    Terminal,
    Activity,
    ChevronRight,
    X,
    Bot
} from 'lucide-react';
import { useChatStore } from '../stores/chatStore';



/* =========================
   Props Interface
========================= */
interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
}



/* =========================
   Component
========================= */
const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {

    /* =========================
       Global Store Selectors
    ========================= */
    const agentSteps = useChatStore((state) => state.agentSteps);
    const logs = useChatStore((state) => state.logs);
    const workflowBranch = useChatStore((state) => state.workflowBranch);



    /* =========================
       Render
    ========================= */
    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/5 backdrop-blur-[1px] z-40"
                    />

                    <motion.div
                        initial={{ x: '100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '100%' }}
                        transition={{ type: 'spring', damping: 30, stiffness: 300 }}
                        className="absolute right-0 top-0 bottom-0 h-full w-96 bg-white/90 backdrop-blur-xl border-l border-white/20 shadow-2xl z-50 flex flex-col"
                    >

                        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                            <div className="flex items-center gap-2 text-gray-900">
                                <Bot className="w-4 h-4" />
                                <span className="font-semibold text-sm">Agent Workflow</span>
                            </div>
                            <button
                                onClick={onClose}
                                className="p-1.5 hover:bg-gray-100 rounded-full transition-colors"
                            >
                                <X className="w-3.5 h-3.5 text-gray-500" />
                            </button>
                        </div>

                        <div className="p-6 overflow-y-auto max-h-[60%] border-b border-gray-100 relative min-h-[300px]">
                            <div className="flex flex-col items-center">

                                <div className="relative z-10 flex flex-col items-center">
                                    <div className={`
                                        w-12 h-12 rounded-2xl border-2 flex items-center justify-center bg-white shadow-sm transition-all duration-300
                                        ${workflowBranch === 'router' ? 'border-blue-500 scale-110 ring-4 ring-blue-500/10' :
                                            workflowBranch === 'story-graph' ? 'border-blue-500' :
                                                workflowBranch === 'chat' ? 'border-green-500' : 'border-gray-200'}
                                    `}>
                                        <Bot className={`w-6 h-6 ${workflowBranch === 'router' ? 'text-blue-500' :
                                            workflowBranch === 'story-graph' ? 'text-blue-500' :
                                                workflowBranch === 'chat' ? 'text-green-500' : 'text-gray-400'}`} />
                                    </div>
                                    <span className={`mt-2 text-xs font-semibold transition-colors duration-300 ${workflowBranch === 'router' ? 'text-gray-700' :
                                        workflowBranch === 'story-graph' ? 'text-blue-600' :
                                            workflowBranch === 'chat' ? 'text-green-600' : 'text-gray-700'
                                        }`}>Router</span>
                                </div>

                                <div className="relative w-48 h-8">
                                    <div className={`absolute left-1/2 top-0 h-4 w-0.5 -translate-x-1/2 transition-colors duration-300 ${workflowBranch === 'story-graph' ? 'bg-blue-500' :
                                        workflowBranch === 'chat' ? 'bg-green-500' : 'bg-gray-200'
                                        }`} />

                                    <div className={`absolute left-0 right-1/2 top-4 h-0.5 rounded-l-full transition-colors duration-300 ${workflowBranch === 'story-graph' ? 'bg-blue-500' : 'bg-gray-200'
                                        }`} />

                                    <div className={`absolute left-1/2 right-0 top-4 h-0.5 rounded-r-full transition-colors duration-300 ${workflowBranch === 'chat' ? 'bg-green-500' : 'bg-gray-200'
                                        }`} />

                                    <div className={`absolute left-0 top-4 h-4 w-0.5 transition-colors duration-300 ${workflowBranch === 'story-graph' ? 'bg-blue-500' : 'bg-gray-200'}`} />
                                    <div className={`absolute right-0 top-4 h-4 w-0.5 transition-colors duration-300 ${workflowBranch === 'chat' ? 'bg-green-500' : 'bg-gray-200'}`} />
                                </div>

                                <div className="flex justify-between w-full gap-4">

                                    <div className={`flex-1 flex flex-col items-center transition-opacity duration-300 ${workflowBranch === 'chat' ? 'opacity-40 grayscale' : 'opacity-100'}`}>
                                        <div className={`
                                            px-3 py-1.5 rounded-lg border text-xs font-medium mb-4 transition-all
                                            ${workflowBranch === 'story-graph' ? 'bg-blue-50 border-blue-200 text-blue-700 shadow-sm' : 'bg-white border-gray-200 text-gray-500'}
                                        `}>
                                            Story Graph
                                        </div>

                                        {workflowBranch === 'story-graph' && (
                                            <div className="flex flex-col items-center w-full space-y-1">
                                                {agentSteps.filter(s => s.id !== 'router').map((step, index) => (
                                                    <div key={step.id} className="flex flex-col items-center w-full">
                                                        {index > 0 && <div className="h-3 w-0.5 bg-blue-100" />}
                                                        <div className={`
                                                            w-full p-2 rounded-xl border flex items-center gap-3 bg-white shadow-sm transition-all
                                                            ${step.status === 'active' ? 'border-blue-500 ring-2 ring-blue-500/10' :
                                                                step.status === 'completed' ? 'border-green-500/50' :
                                                                    step.status === 'failed' ? 'border-red-500 ring-2 ring-red-500/10' :
                                                                        'border-gray-100'}
                                                        `}>
                                                            <div className={`
                                                                w-6 h-6 rounded-full flex items-center justify-center shrink-0
                                                                ${step.status === 'active' ? 'bg-blue-100 text-blue-600' :
                                                                    step.status === 'completed' ? 'bg-green-100 text-green-600' :
                                                                        step.status === 'failed' ? 'bg-red-100 text-red-600' :
                                                                            'bg-gray-100 text-gray-400'}
                                                            `}>
                                                                {step.status === 'active' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> :
                                                                    step.status === 'completed' ? <Activity className="w-3.5 h-3.5" /> :
                                                                        step.status === 'failed' ? <X className="w-3.5 h-3.5" /> :
                                                                            <Circle className="w-3.5 h-3.5" />}
                                                            </div>
                                                            <div className="flex-1 min-w-0">
                                                                <p className={`text-xs font-medium truncate ${step.status === 'failed' ? 'text-red-900' : 'text-gray-900'}`}>{step.name}</p>
                                                                {step.status === 'active' && <p className="text-[10px] text-blue-500 truncate">{step.details}</p>}
                                                                {step.status === 'failed' && <p className="text-[10px] text-red-500 truncate">{step.details}</p>}
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    <div className={`flex-1 flex flex-col items-center transition-opacity duration-300 ${workflowBranch === 'story-graph' ? 'opacity-40 grayscale' : 'opacity-100'}`}>
                                        <div className={`
                                            px-3 py-1.5 rounded-lg border text-xs font-medium mb-4 transition-all
                                            ${workflowBranch === 'chat' ? 'bg-green-50 border-green-200 text-green-700 shadow-sm' : 'bg-white border-gray-200 text-gray-500'}
                                        `}>
                                            Chat
                                        </div>

                                        {workflowBranch === 'chat' && (
                                            <div className="w-full p-3 rounded-xl border border-green-200 bg-green-50/50 flex flex-col items-center text-center">
                                                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mb-2 text-green-600">
                                                    <Bot className="w-4 h-4" />
                                                </div>
                                                <p className="text-xs font-medium text-green-800">Direct Response</p>
                                                <p className="text-[10px] text-green-600 mt-1">LLM answering directly</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="flex-1 flex flex-col min-h-0 bg-gray-50/50">
                            <div className="p-4 border-b border-gray-100/50 flex items-center gap-2">
                                <Terminal className="w-4 h-4 text-gray-400" />
                                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">System Logs</h3>
                            </div>

                            <div className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-xs">
                                <AnimatePresence initial={false}>
                                    {logs.map((log) => (
                                        <motion.div
                                            key={log.id}
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            className="flex gap-2"
                                        >
                                            <span className="text-gray-300 shrink-0">{log.timestamp}</span>
                                            <span className={`break-all ${log.type === 'error' ? 'text-red-500' :
                                                log.type === 'success' ? 'text-green-600' :
                                                    log.type === 'warning' ? 'text-amber-500' :
                                                        'text-gray-600'
                                                } `}>
                                                {log.type === 'info' && <ChevronRight className="w-3 h-3 inline mr-1 opacity-50" />}
                                                {log.message}
                                            </span>
                                        </motion.div>
                                    ))}
                                    {logs.length === 0 && (
                                        <div className="text-gray-300 italic text-center py-8">
                                            Waiting for events...
                                        </div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};

export default Sidebar;