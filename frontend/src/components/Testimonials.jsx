import React from 'react';
import { Star, User } from 'lucide-react';

const testimonials = [
    {
        id: 1,
        name: "Sarah M.",
        role: "Aspiring Model",
        quote: "I always wondered if I had what it takes. This analysis gave me the confidence to finally apply to agencies!",
        rating: 5
    },
    {
        id: 2,
        name: "James T.",
        role: "New Face",
        quote: "The detailed breakdown of my features was incredible. It helped me understand my market type perfectly.",
        rating: 5
    },
    {
        id: 3,
        name: "Emily R.",
        role: "Freelance Model",
        quote: "Fast, accurate, and super helpful. The insider tips on lighting were a game changer for my portfolio.",
        rating: 5
    }
];

const Testimonials = () => {
    return (
        <div className="w-full max-w-4xl mx-auto mt-12 px-4">
            <h3 className="text-2xl font-bold text-center mb-8">
                Trusted by <span className="text-studio-gold">Thousands</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {testimonials.map((testimonial) => (
                    <div
                        key={testimonial.id}
                        className="glass-panel p-6 rounded-xl flex flex-col relative group hover:border-studio-gold/30 transition-colors"
                    >
                        {/* Quote Icon Decoration */}
                        <div className="absolute top-4 right-4 text-white/5 text-4xl font-serif leading-none select-none">
                            "
                        </div>

                        <div className="flex items-center gap-1 mb-4 text-studio-gold">
                            {[...Array(testimonial.rating)].map((_, i) => (
                                <Star key={i} size={14} fill="currentColor" />
                            ))}
                        </div>

                        <p className="text-gray-300 text-sm italic mb-6 flex-grow">
                            "{testimonial.quote}"
                        </p>

                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center text-gray-400">
                                <User size={20} />
                            </div>
                            <div>
                                <h4 className="text-white font-semibold text-sm">
                                    {testimonial.name}
                                </h4>
                                <p className="text-gray-500 text-xs text-xs">
                                    {testimonial.role}
                                </p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default Testimonials;
