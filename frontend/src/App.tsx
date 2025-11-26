import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Generate from './pages/Generate';

const App: React.FC = () => {
    return (
        <Routes>
            <Route path="/" element={<Layout />}>
                <Route index element={<Home />} />
                <Route path="chat" element={<Generate />} />
                {/* Fallback for unknown routes */}
                <Route path="*" element={<Home />} />
            </Route>
        </Routes>
    );
};

export default App;
