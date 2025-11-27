/* =========================
   Story Display Component
========================= */

import React from 'react';
import { motion } from 'framer-motion';
import { useChatStore } from '../../stores/chatStore';
import { BookOpen, Image as ImageIcon } from 'lucide-react';

/* =========================
   Component
========================= */

const StoryDisplay: React.FC = () => {
    const chapters = useChatStore((state) => state.chapters);
    const storyOutline = useChatStore((state) => state.storyOutline);

    if (chapters.length === 0) {
        return (
            <div className="h-full flex flex-col items-center justify-center text-gray-300 space-y-4">
                <div className="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center">
                    <BookOpen className="w-8 h-8 text-gray-200" />
                </div>
                <p>Story will appear here...</p>
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto p-6 space-y-6">
            {storyOutline && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6 shadow-md"
                >
                    <h2 className="text-xl font-bold text-gray-900 mb-4">Story Outline</h2>
                    {storyOutline.style && (
                        <p className="text-sm text-gray-600 mb-2">
                            <span className="font-semibold">Style:</span> {storyOutline.style}
                        </p>
                    )}
                    {storyOutline.characters && storyOutline.characters.length > 0 && (
                        <p className="text-sm text-gray-600 mb-2">
                            <span className="font-semibold">Characters:</span> {storyOutline.characters.join(', ')}
                        </p>
                    )}
                    {storyOutline.setting && (
                        <p className="text-sm text-gray-600 mb-2">
                            <span className="font-semibold">Setting:</span> {storyOutline.setting}
                        </p>
                    )}
                    {storyOutline.plot_summary && (
                        <p className="text-sm text-gray-600">
                            <span className="font-semibold">Plot:</span> {storyOutline.plot_summary}
                        </p>
                    )}
                </motion.div>
            )}

            {chapters.map((chapter, index) => (
                <motion.div
                    key={chapter.chapter_id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-white/80 backdrop-blur-sm border border-white/40 rounded-2xl p-6 shadow-md"
                >
                    <div className="flex items-start gap-4">
                        {chapter.image_url ? (
                            <div className="w-32 h-32 shrink-0 rounded-xl overflow-hidden border border-gray-200 bg-gray-100">
                                <img
                                    src={chapter.image_url}
                                    alt={chapter.title}
                                    className="w-full h-full object-cover"
                                    onError={(e) => {
                                        console.error('Image load error:', chapter.image_url);
                                        (e.target as HTMLImageElement).style.display = 'none';
                                    }}
                                    onLoad={() => {
                                        console.log('Image loaded successfully:', chapter.image_url);
                                    }}
                                />
                            </div>
                        ) : (
                            <div className="w-32 h-32 shrink-0 rounded-xl bg-gray-100 border border-gray-200 flex items-center justify-center">
                                <ImageIcon className="w-8 h-8 text-gray-300" />
                            </div>
                        )}

                        <div className="flex-1 min-w-0">
                            <h3 className="text-lg font-bold text-gray-900 mb-2">
                                Chapter {chapter.chapter_id}: {chapter.title}
                            </h3>
                            <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                                {chapter.text}
                            </p>
                        </div>
                    </div>
                </motion.div>
            ))}
        </div>
    );
};

export default StoryDisplay;

