import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';

const Home: React.FC = () => {
    const navigate = useNavigate();
    const [prompt, setPrompt] = useState('');
    const [isFocused, setIsFocused] = useState(false);

    useEffect(() => {
        if (!sessionStorage.getItem('session_id')) {
            sessionStorage.setItem('session_id', crypto.randomUUID());
        }
    }, []);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!prompt.trim()) return;
        sessionStorage.setItem('initial_prompt', prompt);
        navigate('/chat');
    };

    return (
        <div className="min-h-screen flex flex-col items-center relative overflow-hidden">
            {/* Background moved to Layout for global persistence */}

            {/* Main Content Container - Spaced out */}
            <div className="w-full max-w-4xl flex-grow flex flex-col justify-between py-20 px-6 relative z-10">

                {/* Top Section: Title & Copy */}
                <motion.div
                    initial={{ opacity: 0, y: 40 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
                    className="text-center mt-12 space-y-6"
                >
                    <h1 className="text-6xl md:text-8xl font-bold tracking-tighter text-gray-900">
                        In Story Book
                    </h1>
                    <p className="text-2xl md:text-3xl text-gray-500 font-medium tracking-tight max-w-2xl mx-auto leading-tight">
                        Turn your ideas into magical, illustrated bedtime stories in seconds.
                    </p>
                </motion.div>

                {/* Bottom Section: Input */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3, duration: 1, ease: [0.16, 1, 0.3, 1] }}
                    className="mb-12 w-full max-w-xl mx-auto"
                >
                    <form onSubmit={handleSubmit} className="relative group">
                        <div className={`
              flex items-center bg-white/80 backdrop-blur-xl rounded-full p-2 pl-6
              shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-white/50
              transition-all duration-300
              ${isFocused ? 'shadow-[0_20px_50px_rgb(0,0,0,0.1)] scale-[1.02] bg-white/95' : 'hover:shadow-[0_10px_40px_rgb(0,0,0,0.08)]'}
            `}>
                            <input
                                type="text"
                                value={prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                onFocus={() => setIsFocused(true)}
                                onBlur={() => setIsFocused(false)}
                                placeholder="Describe a story..."
                                className="flex-grow bg-transparent border-none outline-none text-lg text-gray-800 placeholder:text-gray-400 font-medium h-12"
                            />

                            <button
                                type="submit"
                                disabled={!prompt.trim()}
                                className={`
                  flex items-center justify-center w-12 h-12 rounded-full transition-all duration-300 ml-2
                  ${prompt.trim()
                                        ? 'bg-black text-white hover:scale-105 active:scale-95'
                                        : 'bg-gray-100 text-gray-300'}
                `}
                            >
                                <ArrowRight className="w-5 h-5" />
                            </button>
                        </div>
                    </form>
                </motion.div>
            </div>
        </div>
    );
};

export default Home;
