import React, { useState } from 'react';
import { Lock, CheckCircle, Smartphone, Mail, User, X } from 'lucide-react';
import axios from 'axios';

const LeadForm = ({ analysisData, imageBlob, onSubmitSuccess, onCancel }) => {
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
        const cleanPhone = formData.phone.replace(/\D/g, '');

        if (cleanPhone.length !== 10) {
            setError("Phone number must be exactly 10 digits.");
            return false;
        }

        if (cleanPhone.startsWith('1')) {
            setError("Phone number cannot start with 1.");
            return false;
        }

        // Zip Code Format Validation
        const zipRegex = /^\d{5}$/;
        if (!zipRegex.test(formData.zip_code)) {
            setError("Zip Code must be exactly 5 digits.");
            return false;
        }

        return true;
    };

    // Campaign Code Logic
    const TARGET_CITIES = {
        'Boston': { code: '#BOFB3', lat: 42.3601, lon: -71.0589 },
        'New York': { code: '#NYFB3', lat: 40.7128, lon: -74.0060 },
        'Dallas': { code: '#DALFB3', lat: 32.7767, lon: -96.7970 },
        'Houston': { code: '#HOUFB3', lat: 29.7604, lon: -95.3698 },
        'Nashville': { code: '#NAFB3', lat: 36.1627, lon: -86.7816 },
        'Miami': { code: '#FLFB3', lat: 25.7617, lon: -80.1918 },
        'Chicago': { code: '#CHIFB3', lat: 41.8781, lon: -87.6298 },
        'Orlando': { code: '#ORLFB3', lat: 28.5383, lon: -81.3792 }
    };

    const getDistanceFromLatLonInKm = (lat1, lon1, lat2, lon2) => {
        const R = 6371; // Radius of the earth in km
        const dLat = (lat2 - lat1) * (Math.PI / 180);
        const dLon = (lon2 - lon1) * (Math.PI / 180);
        const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }

    // States that should always route to Boston
    const BOSTON_STATES = ['CT', 'MA', 'NH', 'RI', 'NY'];

    // Allowed zip code prefixes (first 3 digits) — everything else is blocked
    const ALLOWED_ZIP_PREFIXES = [
        // New England (MA, CT, RI, NH, VT, ME)
        '010', '011', '012', '013', '014', '015', '016', '017', '018', '019',
        '020', '021', '022', '023', '024', '025', '026', '027', '028', '029',
        '030', '031', '032', '033', '034', '035', '036', '037', '038', '039',
        '040', '041', '042', '043', '045', '046',
        '050', '051', '052', '053',
        '060', '061', '062', '063', '064', '065', '066', '067', '068', '069',
        // NJ / NY metro
        '070', '071', '072', '073', '074', '075', '076', '077', '078', '079',
        '080', '081', '082', '083', '084', '085', '086', '087', '088', '089',
        '100', '101', '102', '103', '104', '105', '106', '107', '108', '109',
        '110', '111', '112', '113', '114', '115', '116', '117', '118', '119',
        '120', '121', '122', '123', '124', '125', '126', '127',
        // PA / MD / DE / DC
        '170', '171', '172', '173', '174', '175', '176', '178', '179',
        '180', '182', '185', '189',
        '190', '191', '192', '193', '194', '197', '198', '199',
        '210', '211', '212', '214', '215',
        // GA (parts)
        '306', '307', '314',
        // Florida
        '320', '321', '322', '323', '325', '326', '327', '328', '329',
        '330', '331', '332', '333', '334', '335', '336', '337', '338', '339',
        '340', '341', '342', '344', '346', '347', '349',
        // AL / TN / KY
        '350', '351', '352', '353', '356', '357', '358', '359',
        '363', '364',
        '370', '371', '372', '373', '374', '375', '376', '377', '379',
        '380', '381', '382', '383', '384', '385', '386', '387',
        '397',
        '400', '401', '402', '403', '404', '405', '407', '408', '409',
        '411', '412', '413', '415', '416', '417',
        '421', '422', '423', '425', '426',
        // IN / MI
        '460', '461', '462', '463', '464', '465', '466', '467', '468', '469',
        '473', '474', '475', '476', '477', '478',
        '486', '487', '488', '489', '490', '491', '492', '496',
        // IA / WI / MN
        '525', '526', '528',
        '530', '531', '532', '534', '535', '537', '538', '539',
        '541', '542', '543', '547', '549',
        // IL / MO
        '600', '601', '602', '603', '604', '605', '606', '607', '608', '609',
        '610', '611', '612', '613', '614', '615', '616', '617',
        '620', '621', '623', '625', '626', '627', '628', '629',
        '638',
        // LA (Shreveport)
        '710', '711',
        // OK
        '730', '731', '734', '735', '736', '738',
        // TX
        '744', '745', '747', '748',
        '750', '751', '752', '753', '754', '755', '756', '757', '758', '759',
        '760', '761', '762', '763', '764', '766', '768', '769',
        '770', '771', '772', '773', '774', '775', '776', '777', '778', '779',
        '780', '781', '782', '783', '784', '786', '787'
    ];

    // Tampa latitude — the horizontal cutoff line across Florida
    const TAMPA_LAT = 27.95;

    const calculateCampaignCode = async (zip, age, gender) => {
        try {
            // 0. Only allow approved zip prefixes
            const zipPrefix = zip.substring(0, 3);
            if (!ALLOWED_ZIP_PREFIXES.includes(zipPrefix)) {
                throw new Error("We're not currently accepting applications from your area. Stay tuned!");
            }

            // 1. Get Lat/Lon and City from Zip
            const response = await axios.get(`https://api.zippopotam.us/us/${zip}`);
            const place = response.data.places[0];
            const userLat = parseFloat(place.latitude);
            const userLon = parseFloat(place.longitude);
            const cityName = place['place name'];
            const stateAbbr = place['state abbreviation'];

            // 2. State/region overrides
            let cityCode;
            if (BOSTON_STATES.includes(stateAbbr)) {
                // CT, MA, NH, RI, NY → Boston
                cityCode = TARGET_CITIES['Boston'].code;
            } else if (stateAbbr === 'FL' && userLat < TAMPA_LAT) {
                // South Florida (below Tampa line) → Miami
                cityCode = TARGET_CITIES['Miami'].code;
            } else {
                // 3. Find Nearest City by distance
                let nearestCity = null;
                let minDistance = Infinity;

                for (const [city, data] of Object.entries(TARGET_CITIES)) {
                    const distance = getDistanceFromLatLonInKm(userLat, userLon, data.lat, data.lon);
                    if (distance < minDistance) {
                        minDistance = distance;
                        nearestCity = data.code;
                    }
                }
                cityCode = nearestCity || '#NYFB3';
            }

            // 3. Age Code + Gender Code
            const ageNum = parseInt(age);
            const genderCode = gender === 'Female' ? 'F' : 'M';

            let ageCode;
            const isFlorida = cityCode === TARGET_CITIES['Miami'].code || cityCode === TARGET_CITIES['Orlando'].code;

            if (isFlorida) {
                // Florida-specific age codes
                if (genderCode === 'M') {
                    // Males: all ages → 1
                    ageCode = '1';
                } else {
                    // Females: 0-34 → 1, 35+ → 2
                    ageCode = ageNum >= 35 ? '2' : '1';
                }
            } else {
                // Default age codes for all other cities
                ageCode = '1';
                if (ageNum >= 35 && ageNum <= 44) ageCode = '2';
                if (ageNum >= 45) ageCode = '3';
            }

            return { code: `${cityCode}${ageCode}${genderCode}`, city: cityName };

        } catch (error) {
            console.error("Error calculating campaign code:", error);
            // Preserve blocked-state messages, fallback for zip errors
            throw new Error(error.message || "Invalid Zip Code");
        }
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
            // Calculate Campaign Code & Detect City
            const { code: campaignCode, city: detectedCity } = await calculateCampaignCode(
                formData.zip_code,
                formData.age,
                formData.gender
            );
            console.log("Generated Campaign Code:", campaignCode, "City:", detectedCity);

            // 1. Send data to backend as FormData
            const payload = new FormData();

            // Append simple fields
            Object.keys(formData).forEach(key => {
                if (key !== 'city') { // Skip manual city
                    payload.append(key, formData[key]);
                }
            });

            // Append Auto-Detected City
            payload.append('city', detectedCity);

            // Append Calculated Campaign
            payload.append('campaign', campaignCode);

            // Append Analysis Data as JSON string
            payload.append('analysis_data', JSON.stringify(analysisData));

            // Append Image File
            if (imageBlob) {
                payload.append('file', imageBlob);
            }

            const API_URL = import.meta.env.MODE === 'production' ? '/api' : 'http://localhost:8000';
            const response = await axios.post(`${API_URL}/lead`, payload, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            if (response.data.status === 'success') {
                console.log("Form submission success. Tracking Lead event...");
                // Track Meta Pixel Lead Event
                if (window.fbq) {
                    try {
                        window.fbq('track', 'Lead');
                        console.log("Meta Pixel 'Lead' event fired.");
                    } catch (e) {
                        console.error("Meta Pixel tracking failed:", e);
                    }
                } else {
                    console.warn("window.fbq is not defined. Pixel not tracking.");
                }

                // Small delay to ensure tracking fires before component unmount
                setTimeout(() => {
                    onSubmitSuccess();
                }, 500);
            }
        } catch (err) {
            console.error(err);
            if (err.message === "Invalid Zip Code") {
                setError("Invalid Zip Code. Please enter a valid US Zip Code.");
            } else if (err.response && err.response.data && err.response.data.message) {
                setError(err.response.data.message);
            } else {
                setError("Something went wrong. Please try again.");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] overflow-y-auto bg-black/90 backdrop-blur-md">
            <div className="min-h-screen flex items-center justify-center p-4">
                <div className="glass-panel w-full max-w-lg p-6 sm:p-8 rounded-2xl relative">
                    {/* Close Button */}
                    {onCancel && (
                        <button
                            onClick={onCancel}
                            className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors p-2 z-50"
                            type="button"
                        >
                            <X size={24} />
                        </button>
                    )}
                    {/* Decorative header */}
                    <div className="text-center mb-6">
                        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-studio-gold/20 mb-4 text-studio-gold">
                            <Lock size={24} />
                        </div>
                        <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                            Claim Your Spot
                        </h2>
                        <p className="text-gray-400 text-sm mt-2">
                            Enter your details below if you'd like to start modeling.
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">First Name *</label>
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
                                <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Last Name *</label>
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
                                <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Age *</label>
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
                                <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Gender *</label>
                                <select
                                    required
                                    className="w-full bg-black/40 border border-white/10 rounded-lg py-3.5 px-4 text-white text-base focus:outline-none focus:border-studio-gold transition-colors appearance-none"
                                    value={formData.gender}
                                    onChange={e => setFormData({ ...formData, gender: e.target.value })}
                                >
                                    <option value="" disabled>Select</option>
                                    <option value="Female">Female</option>
                                    <option value="Male">Male</option>
                                </select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Email Address *</label>
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
                            <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Phone Number *</label>
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

                        <div className="space-y-2">
                            <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Zip Code *</label>
                            <input
                                type="text"
                                required
                                className="w-full bg-black/40 border border-white/10 rounded-lg py-3.5 px-4 text-white text-base focus:outline-none focus:border-studio-gold transition-colors"
                                placeholder="10001"
                                value={formData.zip_code}
                                onChange={e => setFormData({ ...formData, zip_code: e.target.value })}
                            />
                        </div>

                        {/* Checkbox Removed as per request
                    <div className="flex items-start space-x-3 pt-2">
                         ...
                    </div> */}

                        {error && <p className="text-red-400 text-sm text-center">{error}</p>}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full mt-6 bg-studio-gold hover:bg-yellow-600 text-black font-bold py-4 text-lg rounded-lg transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
                        >
                            {loading ? "Saving..." : "Reveal My Results"}
                        </button>
                        <p className="text-center text-xs text-gray-500 mt-4">
                            Talent Scouted is not an agency
                        </p>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default LeadForm;
