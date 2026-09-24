/**
 * API Layer — Travel Booking FastAPI Backend
 * Base backend: FastAPI app in main.py, routers: flights, buses, ships, auth, bookings, users, payments
 *
 * IMPORTANT: Every path and field name below is a best guess based on FastAPI
 * naming conventions and your router filenames — NOT confirmed against the
 * actual code. Open http://127.0.0.1:8000/docs and check each endpoint marked
 * // VERIFY before relying on this. Wrong field names will fail silently
 * (empty results, not obvious errors).
 */

const API_BASE_URL = 'http://127.0.0.1:8000'; // VERIFY: confirm no further /api prefix in /docs

// FastAPI validation errors return detail as an array of objects, e.g.
// { detail: [{ loc: [...], msg: "field required", type: "..." }] }
// This turns that (or a plain string detail) into readable text.
function formatApiError(err, fallbackMessage) {
    if (!err || !err.detail) return fallbackMessage;
    if (typeof err.detail === 'string') return err.detail;
    if (Array.isArray(err.detail)) {
        return err.detail.map(e => e.msg || JSON.stringify(e)).join('; ');
    }
    return JSON.stringify(err.detail);
}

const ApiService = {
    async register(userData) {
        // VERIFY: exact path — likely /auth/register — and field names (name/email/password?)
        const res = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(formatApiError(err, `Registration failed (${res.status})`));
        }
        return await res.json();
    },

    async login(credentials) {
        // VERIFY: exact path — likely /auth/login — and whether it expects JSON
        // or OAuth2 form-data (FastAPI's default login often expects
        // 'username'/'password' as form fields, not JSON, when using
        // OAuth2PasswordRequestForm — check /docs for this specifically)
        const res = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(credentials)
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(formatApiError(err, `Login failed (${res.status})`));
        }
        const data = await res.json();
        // VERIFY: confirm the token field is actually called 'access_token'
        if (data.access_token) {
            localStorage.setItem('authToken', data.access_token);
        }
        return data;
    },

    async getTrips(mode, origin, destination) {
        // VERIFY: each router's real path and query param names
        // (origin/destination assumed — could be departure_city/arrival_city etc)
        const routeByMode = {
            air: 'flights',
            land: 'buses',
            sea: 'ships'
        };
        const route = routeByMode[mode];
        if (!route) {
            throw new Error(`Unknown mode: ${mode}`);
        }

        const params = new URLSearchParams({ origin, destination });
        const res = await fetch(`${API_BASE_URL}/${route}?${params.toString()}`);
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(formatApiError(err, `Trip search failed (${res.status})`));
        }
        return await res.json();
    },

    async createBooking(bookingData) {
        // VERIFY: exact path (/bookings?) and required field names,
        // and whether this route requires the Authorization header
        const token = localStorage.getItem('authToken');
        const res = await fetch(`${API_BASE_URL}/bookings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { Authorization: `Bearer ${token}` } : {})
            },
            body: JSON.stringify(bookingData)
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(formatApiError(err, `Booking failed (${res.status})`));
        }
        return await res.json();
    },

    async createPayment(paymentData) {
        // VERIFY: exact path (/payments?) and field names — this router
        // wasn't referenced in the original mock file at all, so it's
        // entirely unverified
        const token = localStorage.getItem('authToken');
        const res = await fetch(`${API_BASE_URL}/payments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token ? { Authorization: `Bearer ${token}` } : {})
            },
            body: JSON.stringify(paymentData)
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(formatApiError(err, `Payment failed (${res.status})`));
        }
        return await res.json();
    }
};