import React, { useState } from 'react';
import { Lock, CheckCircle, Smartphone, Mail, User } from 'lucide-react';
import axios from 'axios';

const LeadForm = ({ analysisData, imageBlob, onSubmitSuccess }) => {
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        age: '',
        gender: '',
        email: '',
        phone: '',
        city: '',
        zip_code: '',
        wants_assessment: false
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const validateForm = () => {
        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            setError("Please enter a valid email address.");
            return false;
        }

        // Phone validation
        // Remove non-digit chars
        const cleanPhone = formData.phone.replace(/\D/g, '');

        if (cleanPhone.length !== 10) {
            setError("Phone number must be exactly 10 digits.");
            return false;
        }

        if (cleanPhone.startsWith('1')) {
            setError("Phone number cannot start with 1.");
            return false;
        }

        return true;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        if (!validateForm()) {
            setLoading(false);
            return;
        }

        try {
            // 1. Send data to backend
            const payload = {
                ...formData,
                analysis_data: analysisData
            };

            const API_URL = import.meta.env.MODE === 'production' ? '/api' : 'http://localhost:8000';
            const response = await axios.post(`${API_URL}/lead`, payload);

            if (response.data.status === 'success') {
                onSubmitSuccess();
            }
        } catch (err) {
            console.error(err);
            setError("Something went wrong. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 backdrop-blur-md overflow-y-auto h-full w-full p-4">
            <div className="glass-panel w-full max-w-lg p-6 sm:p-8 rounded-2xl relative">
                {/* Decorative header */}
                <div className="text-center mb-6">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-studio-gold/20 mb-4 text-studio-gold">
                        <Lock size={24} />
                    </div>
                    <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                        Unlock Full Report
                    </h2>
                    <p className="text-gray-400 text-sm mt-2">
                        Save your results and see your match score.
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">First Name</label>
                            <input
                                type="text"
                                required
                                className="w-full bg-black/40 border border-white/10 rounded-lg py-3.5 px-4 text-white text-base focus:outline-none focus:border-studio-gold transition-colors"
                                placeholder="Jane"
                                value={formData.first_name}
                                onChange={e => setFormData({ ...formData, first_name: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Last Name</label>
                            <input
                                type="text"
                                required
                                className="w-full bg-black/40 border border-white/10 rounded-lg py-3.5 px-4 text-white text-base focus:outline-none focus:border-studio-gold transition-colors"
                                placeholder="Doe"
                                value={formData.last_name}
                                onChange={e => setFormData({ ...formData, last_name: e.target.value })}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Age</label>
                            <input
                                type="number"
                                required
                                className="w-full bg-black/40 border border-white/10 rounded-lg py-3.5 px-4 text-white text-base focus:outline-none focus:border-studio-gold transition-colors"
                                placeholder="25"
                                value={formData.age}
                                onChange={e => setFormData({ ...formData, age: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Gender</label>
                            <select
                                required
                                className="w-full bg-black/40 border border-white/10 rounded-lg py-3.5 px-4 text-white text-base focus:outline-none focus:border-studio-gold transition-colors appearance-none"
                                value={formData.gender}
                                onChange={e => setFormData({ ...formData, gender: e.target.value })}
                            >
                                <option value="" disabled>Select</option>
                                <option value="Female">Female</option>
                                <option value="Male">Male</option>
                                <option value="Non-Binary">Non-Binary</option>
                                <option value="Prefer not to say">Prefer not to say</option>
                            </select>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Email Address</label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-3.5 text-gray-500" size={18} />
                            <input
                                type="email"
                                required
                                className="w-full bg-black/40 border border-white/10 rounded-lg py-3.5 pl-10 pr-4 text-white text-base focus:outline-none focus:border-studio-gold transition-colors"
                                placeholder="jane@example.com"
                                value={formData.email}
                                onChange={e => setFormData({ ...formData, email: e.target.value })}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Phone Number</label>
                        <div className="relative">
                            <Smartphone className="absolute left-3 top-3.5 text-gray-500" size={18} />
                            <input
                                type="tel"
                                required
                                className="w-full bg-black/40 border border-white/10 rounded-lg py-3.5 pl-10 pr-4 text-white text-base focus:outline-none focus:border-studio-gold transition-colors"
                                placeholder="(555) 000-0000"
                                value={formData.phone}
                                onChange={e => setFormData({ ...formData, phone: e.target.value })}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">City</label>
                            <input
                                type="text"
                                required
                                className="w-full bg-black/40 border border-white/10 rounded-lg py-3.5 px-4 text-white text-base focus:outline-none focus:border-studio-gold transition-colors"
                                placeholder="New York"
                                value={formData.city}
                                onChange={e => setFormData({ ...formData, city: e.target.value })}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Zip Code</label>
                            <input
                                type="text"
                                required
                                className="w-full bg-black/40 border border-white/10 rounded-lg py-3.5 px-4 text-white text-base focus:outline-none focus:border-studio-gold transition-colors"
                                placeholder="10001"
                                value={formData.zip_code}
                                onChange={e => setFormData({ ...formData, zip_code: e.target.value })}
                            />
                        </div>
                    </div>

                    <div className="flex items-start space-x-3 pt-2">
                        <div className="flex items-center h-5">
                            <input
                                id="assessment"
                                type="checkbox"
                                className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-studio-gold focus:ring-studio-gold"
                                checked={formData.wants_assessment}
                                onChange={e => setFormData({ ...formData, wants_assessment: e.target.checked })}
                            />
                        </div>
                        <label htmlFor="assessment" className="text-xs text-gray-400">
                            I'd like a local verified studio to review my results for a professional assessment.
                        </label>
                    </div>

                    {error && <p className="text-red-400 text-sm text-center">{error}</p>}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full mt-6 bg-studio-gold hover:bg-yellow-600 text-black font-bold py-4 text-lg rounded-lg transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
                    >
                        {loading ? "Saving..." : "Reveal My Results"}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default LeadForm;
