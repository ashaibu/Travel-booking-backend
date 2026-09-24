/**
 * Core Application Logic & UI Handlers
 */

let currentMode = 'air';
let currentTrips = [];       // replaces reliance on the old mockTripsData
let selectedTrip = null;
let selectedSeat = null;
let bookedTickets = JSON.parse(localStorage.getItem('my_tickets') || '[]');

document.addEventListener('DOMContentLoaded', () => {
    // Set default departure date to today
    document.getElementById('date-input').valueAsDate = new Date();
    // Perform initial query
    renderTrips();
    updateUserUI();
});

function switchMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-tab').forEach(tab => {
        tab.className = 'mode-tab flex items-center justify-center gap-2 py-3 rounded-lg font-bold text-sm transition-all text-slate-400 hover:text-white hover:bg-slate-800';
    });

    const activeTab = document.getElementById(`tab-${mode}`);
    if (activeTab) {
        activeTab.className = 'mode-tab flex items-center justify-center gap-2 py-3 rounded-lg font-bold text-sm transition-all bg-gradient-to-r from-sky-500 to-blue-600 text-white shadow-md';
    }

    renderTrips();
}

async function handleSearch(e) {
    e.preventDefault();
    renderTrips();
}

async function renderTrips() {
    const origin = document.getElementById('origin-select').value;
    const destination = document.getElementById('destination-select').value;
    const container = document.getElementById('trips-container');

    container.innerHTML = `<div class="text-center py-8 text-slate-500">Loading trips...</div>`;

    let trips;
    try {
        trips = await ApiService.getTrips(currentMode, origin, destination);
        // VERIFY: confirm the response is a plain array. If the backend
        // wraps it (e.g. { results: [...] }), use trips = trips.results here.
    } catch (err) {
        container.innerHTML = `
            <div class="bg-red-900/30 border border-red-700/50 rounded-xl p-8 text-center">
                <p class="text-red-300 font-semibold">Couldn't load trips</p>
                <p class="text-xs text-red-400/80 mt-1">${err.message}</p>
            </div>
        `;
        document.getElementById('results-count').textContent = '0 Available';
        return;
    }

    currentTrips = trips; // keep a reference so seat selection can find the trip later

    document.getElementById('results-count').textContent = `${trips.length} Available`;

    if (trips.length === 0) {
        container.innerHTML = `
            <div class="bg-slate-800/50 rounded-xl p-8 text-center border border-slate-700/60">
                <i data-lucide="info" class="w-8 h-8 text-slate-500 mx-auto mb-2"></i>
                <p class="text-slate-300 font-semibold">No direct trips found for this route</p>
                <p class="text-xs text-slate-500 mt-1">Try switching travel modes or picking a different route.</p>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    // VERIFY: confirm each trip object actually has these exact field names
    // (id, operator, code, origin, destination, duration, price, seatsAvailable, mode)
    // — real backend records may use different names.
    container.innerHTML = trips.map(trip => `
        <div class="bg-slate-800/90 hover:border-sky-500/50 transition-all border border-slate-700/80 rounded-xl p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-lg animate-fade-in">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 font-bold">
                    <i data-lucide="${trip.mode === 'air' ? 'plane' : trip.mode === 'land' ? 'bus' : 'ship'}" class="w-6 h-6"></i>
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <h4 class="font-bold text-white text-base">${trip.operator}</h4>
                        <span class="text-[10px] px-2 py-0.5 rounded bg-slate-700 text-slate-300 font-mono">${trip.code}</span>
                    </div>
                    <div class="flex items-center gap-2 text-xs text-slate-400 mt-1">
                        <span>${trip.origin}</span>
                        <i data-lucide="arrow-right" class="w-3 h-3"></i>
                        <span>${trip.destination}</span>
                        <span class="text-slate-600">•</span>
                        <span>${trip.duration}</span>
                    </div>
                </div>
            </div>

            <div class="flex items-center justify-between w-full md:w-auto md:gap-8 border-t md:border-t-0 border-slate-700/60 pt-3 md:pt-0">
                <div>
                    <div class="text-2xl font-black text-sky-400">₦${trip.price.toLocaleString()}</div>
                    <div class="text-[11px] text-slate-500">${trip.seatsAvailable} seats left</div>
                </div>
                <button onclick="openSeatSelection('${trip.id}')" class="px-5 py-2.5 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-400 hover:to-amber-400 text-white font-bold text-sm rounded-lg shadow-md transition-all">
                    Select Seats
                </button>
            </div>
        </div>
    `).join('');

    lucide.createIcons();
}

function openSeatSelection(tripId) {
    // now looks up the trip from the last real API response instead of mock data
    selectedTrip = currentTrips.find(t => t.id === tripId);
    if (!selectedTrip) {
        console.error('Could not find trip with id', tripId);
        return;
    }
    selectedSeat = null;
    document.getElementById('selected-seat-label').textContent = 'None';
    document.getElementById('confirm-seat-btn').disabled = true;

    const grid = document.getElementById('seat-grid');
    grid.innerHTML = '';

    const seats = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C1', 'C2', 'C3', 'C4'];
    seats.forEach(seat => {
        const seatBtn = document.createElement('button');
        seatBtn.className = 'seat-btn p-3 rounded-lg border border-slate-700 bg-slate-900 text-xs font-mono font-bold text-slate-300 hover:border-sky-500 transition-all';
        seatBtn.textContent = seat;
        seatBtn.onclick = () => selectSeat(seat, seatBtn);
        grid.appendChild(seatBtn);
    });

    openModal('seat-modal');
}

function selectSeat(seat, element) {
    selectedSeat = seat;
    document.querySelectorAll('.seat-btn').forEach(btn => btn.classList.remove('bg-sky-500', 'text-white', 'border-sky-400'));
    element.classList.add('bg-sky-500', 'text-white', 'border-sky-400');
    document.getElementById('selected-seat-label').textContent = seat;
    document.getElementById('confirm-seat-btn').disabled = false;
}

function proceedToCheckout() {
    closeModal('seat-modal');
    document.getElementById('summary-fare').textContent = `₦${selectedTrip.price.toLocaleString()}`;
    document.getElementById('summary-total').textContent = `₦${(selectedTrip.price + 1500).toLocaleString()}`;
    openModal('checkout-modal');
}

async function handlePayment(e) {
    e.preventDefault();

    const bookingPayload = {
        tripId: selectedTrip.id,
        passengerName: document.getElementById('passenger-name').value,
        passengerEmail: document.getElementById('passenger-email').value,
        passengerPhone: document.getElementById('passenger-phone').value,
        seatNumber: selectedSeat,
        totalAmount: selectedTrip.price + 1500,
        mode: selectedTrip.mode,
        route: `${selectedTrip.origin} → ${selectedTrip.destination}`
    };
    // VERIFY: confirm these field names match what the /bookings endpoint expects

    let response;
    try {
        response = await ApiService.createBooking(bookingPayload);
        // api.js now throws on failure, so reaching here means it succeeded —
        // the old `if (response.success)` check is no longer needed
    } catch (err) {
        alert(`Booking failed: ${err.message}`); // consider a nicer in-page error instead of alert()
        return;
    }

    // VERIFY: confirm the real response actually contains bookingRef,
    // passengerName, seatNumber, route, totalAmount — or adjust to whatever
    // field names the backend actually returns
    bookedTickets.push(response);
    localStorage.setItem('my_tickets', JSON.stringify(bookedTickets));

    document.getElementById('ticket-ref').textContent = response.bookingRef;
    document.getElementById('ticket-passenger').textContent = response.passengerName;
    document.getElementById('ticket-seat').textContent = response.seatNumber;
    document.getElementById('ticket-route').textContent = response.route;
    document.getElementById('ticket-time').textContent = selectedTrip.departureTime;

    closeModal('checkout-modal');
    openModal('ticket-modal');
    renderMyTickets();
}

function showSection(sectionId) {
    document.getElementById('home-section').classList.add('hidden');
    document.getElementById('results-section').classList.add('hidden');
    document.getElementById('my-tickets-section').classList.add('hidden');
    document.getElementById('freight-section').classList.add('hidden');

    if (sectionId === 'home') {
        document.getElementById('home-section').classList.remove('hidden');
        document.getElementById('results-section').classList.remove('hidden');
    } else if (sectionId === 'my-tickets') {
        document.getElementById('my-tickets-section').classList.remove('hidden');
        renderMyTickets();
    } else if (sectionId === 'freight') {
        document.getElementById('freight-section').classList.remove('hidden');
    }
}

function renderMyTickets() {
    const container = document.getElementById('my-tickets-list');
    if (bookedTickets.length === 0) {
        container.innerHTML = `<div class="p-8 text-center text-slate-500 bg-slate-800/50 rounded-xl">No booked tickets found yet.</div>`;
        return;
    }

    container.innerHTML = bookedTickets.map(t => `
        <div class="bg-slate-800 p-5 rounded-xl border border-slate-700 flex justify-between items-center">
            <div>
                <span class="text-xs font-mono px-2 py-0.5 rounded bg-sky-500/20 text-sky-400 border border-sky-500/30 font-bold">${t.bookingRef}</span>
                <h4 class="font-bold text-white mt-1">${t.route}</h4>
                <p class="text-xs text-slate-400">Passenger: ${t.passengerName} • Seat: ${t.seatNumber}</p>
            </div>
            <div class="text-right">
                <span class="text-xs px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 font-semibold border border-emerald-500/30">CONFIRMED</span>
                <p class="text-sm font-bold text-sky-400 mt-1">₦${t.totalAmount.toLocaleString()}</p>
            </div>
        </div>
    `).join('');
}

function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    // VERIFY: does your login form actually have a password input? If so,
    // give it an id like 'login-password' and read it here — real auth
    // endpoints almost always require a password, not just an email.
    const password = document.getElementById('login-password')?.value;

    try {
        const res = await ApiService.login({ email, password });
        localStorage.setItem('user', JSON.stringify(res.user));
        updateUserUI();
        closeModal('login-modal');
    } catch (err) {
        alert(`Login failed: ${err.message}`);
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('reg-name').value;
    const email = document.getElementById('reg-email').value;
    // VERIFY: same as above — add a password input to the register form
    // if it doesn't already have one, with id 'reg-password'
    const password = document.getElementById('reg-password')?.value;

    try {
        const res = await ApiService.register({ name, email, password });
        localStorage.setItem('user', JSON.stringify(res.user));
        updateUserUI();
        closeModal('register-modal');
    } catch (err) {
        alert(`Registration failed: ${err.message}`);
    }
}

function logout() {
    localStorage.removeItem('user');
    updateUserUI();
}

function updateUserUI() {
    const user = JSON.parse(localStorage.getItem('user'));
    if (user) {
        document.getElementById('auth-buttons').classList.add('hidden');
        document.getElementById('user-profile').classList.remove('hidden');
        document.getElementById('user-name-display').textContent = user.name || user.email;
    } else {
        document.getElementById('auth-buttons').classList.remove('hidden');
        document.getElementById('user-profile').classList.add('hidden');
    }
}