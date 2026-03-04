import React, { useState } from 'react';
import translations from '../translations';

const BROWN_DARK = '#5C3D1E';
const BROWN_GOLD = '#8B6914';
const CREAM = '#F5F0EA';

const LanguageSelector = ({ onSelectLanguage }) => {
    const [selected, setSelected] = useState('en');
    const t = translations[selected];

    const languages = [
        { code: 'en', name: 'English' },
        { code: 'fr', name: 'Français' },
        { code: 'rw', name: 'Kinyarwanda' },
    ];

    return (
        <div className="phone-frame">
            <div className="phone-notch"></div>
            <div className="phone-screen p-6 justify-center items-center">

                {/* Main Content Card */}
                <div className="premium-card w-full text-center">
                    <h1 className="text-2xl font-bold mb-2 leading-tight">
                        {t.appTitle}
                    </h1>
                    <p className="text-museum-brown-medium text-sm leading-relaxed mb-8">
                        {t.appSubtitle}
                    </p>

                    <p className="text-museum-brown-dark text-sm font-semibold mb-4">
                        {t.selectLanguage}
                    </p>

                    <div className="flex flex-col gap-3 mb-8">
                        {languages.map((lang) => (
                            <button
                                key={lang.code}
                                onClick={() => setSelected(lang.code)}
                                className={`w-full py-3.5 px-4 rounded-2xl border-2 transition-all duration-300 text-[15px] font-medium ${selected === lang.code
                                        ? 'bg-museum-brown-medium border-museum-brown-medium text-white shadow-md scale-[1.02]'
                                        : 'bg-white border-museum-cream-dark text-museum-brown-dark hover:bg-museum-cream-light hover:border-museum-brown-light'
                                    }`}
                            >
                                {lang.name}
                            </button>
                        ))}
                    </div>

                    <button
                        onClick={() => onSelectLanguage(selected)}
                        className="museum-button-primary w-full text-base py-4 mb-6 shadow-[0_8px_20px_rgba(74,55,40,0.25)]"
                    >
                        {t.start}
                    </button>

                    {/* Pagination Indicator */}
                    <div className="flex justify-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full bg-museum-brown-medium"></div>
                        <div className="w-2.5 h-2.5 rounded-full bg-museum-brown-light/40"></div>
                        <div className="w-2.5 h-2.5 rounded-full bg-museum-brown-light/20"></div>
                    </div>
                </div>
            </div>
            {/* Home bar */}
            <div className="w-16 h-1.5 bg-white/20 rounded-full mx-auto my-3"></div>
        </div>
    );
};

export default LanguageSelector;
