import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';

const Layout: React.FC = () => {
    const location = useLocation();
    const isHome = location.pathname === '/';
    const isChat = location.pathname === '/chat';
    const hideChrome = isHome || isChat;

    return (
        <div className="min-h-screen flex flex-col bg-gray-50 text-gray-900 font-sans selection:bg-blue-100 selection:text-blue-900 relative overflow-hidden">
            {/* Global High Visibility Floating Background Elements (Optimized) */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
                <div
                    className="absolute top-[10%] left-[10%] w-[400px] h-[400px] bg-blue-500/40 rounded-full blur-[60px] animate-blob-1 will-change-transform"
                />
                <div
                    className="absolute bottom-[10%] right-[5%] w-[500px] h-[500px] bg-purple-500/40 rounded-full blur-[70px] animate-blob-2 will-change-transform"
                />
                <div
                    className="absolute top-[40%] left-[40%] w-[300px] h-[300px] bg-amber-400/40 rounded-full blur-[50px] animate-blob-3 will-change-transform"
                />
            </div>

            {/* Header - Hidden on Home & Chat */}
            {!hideChrome && (
                <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-white/70 backdrop-blur-md border-b border-white/20 shadow-sm transition-all duration-300">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg shadow-md flex items-center justify-center text-white font-bold text-lg">
                                I
                            </div>
                            <span className="text-xl font-semibold tracking-tight text-gray-900">InStoryBook</span>
                        </div>
                        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-gray-500">
                            {/* <a href="#" className="hover:text-gray-900 transition-colors">About</a> */}
                        </nav>
                    </div>
                </header>
            )}

            {/* Main Content Area */}
            <main className={`flex-grow relative z-10 ${!hideChrome ? 'pt-16' : ''}`}>
                <Outlet />
            </main>

            {/* Footer - Minimalist (Hidden on Home & Chat) */}
            {!hideChrome && (
                <footer className="py-8 text-center text-sm text-gray-400 border-t border-gray-100 bg-white/50 backdrop-blur-sm relative z-10">
                    <p>© {new Date().getFullYear()} InStoryBook. Designed for creativity.</p>
                </footer>
            )}
        </div>
    );
};

export default Layout;
