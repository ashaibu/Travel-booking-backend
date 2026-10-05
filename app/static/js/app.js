/* PERSON 2 — FRONTEND DEVELOPER
   One file for every page's logic. Each HTML page sets
   <body data-page="..."> and the matching init_* function below runs
   on load. Shared nav is rendered into <div id="navbar"> on every page. */

function renderNav() {
  const el = document.getElementById("navbar");
  if (!el) return;

  const loggedIn = Api.isLoggedIn();
  const admin = Api.isAdmin();

  el.innerHTML = `
    <nav class="tg-surface border-b py-4 px-6 md:px-10 flex justify-between items-center sticky top-0 z-50">
      <a href="/static/index.html" class="text-xl font-bold flex items-center gap-2" style="color: var(--accent)">
        ✈️ TravelGroup
      </a>
      <div class="flex items-center gap-5 text-sm font-medium tg-text-dim">
        ${
          loggedIn
            ? `
              <a href="/static/my-tickets.html" class="hover:text-white transition">My Tickets</a>
              <a href="/static/profile.html" class="hover:text-white transition">Profile</a>
              ${admin ? `<a href="/static/admin.html" class="hover:text-white transition">Admin</a>` : ""}
              <button onclick="Api.logout()" class="tg-accent px-3 py-1.5 rounded-lg font-semibold">Logout</button>
            `
            : `
              <a href="/static/login.html" class="hover:text-white transition">Login</a>
              <a href="/static/register.html" class="tg-accent px-3 py-1.5 rounded-lg font-semibold">Register</a>
            `
        }
      </div>
    </nav>
  `;
}

function qs(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function money(n) {
  return "₦" + Number(n).toLocaleString();
}

function requireAuth() {
  if (!Api.isLoggedIn()) window.location.href = "/static/login.html";
}

function requireAdmin() {
  if (!Api.isLoggedIn() || !Api.isAdmin()) window.location.href = "/static/login.html";
}

// ---- Home ------------------------------------------------------------
function init_home() {
  let mode = "flights";
  document.querySelectorAll("[data-mode-tab]").forEach((btn) => {
    btn.addEventListener("click", () => {
      mode = btn.dataset.modeTab;
      document.querySelectorAll("[data-mode-tab]").forEach((b) => b.classList.remove("tg-accent"));
      btn.classList.add("tg-accent");
    });
  });
  document.querySelectorAll("[data-mode-tab]")[0]?.classList.add("tg-accent");

  document.getElementById("searchForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const origin = document.getElementById("origin").value.trim();
    const destination = document.getElementById("destination").value.trim();
    const date = document.getElementById("travelDate").value;
    const params = new URLSearchParams({ mode, origin, destination, date });
    window.location.href = `/static/search.html?${params.toString()}`;
  });
}

// ---- Search results ----------------------------------------------------
function init_search() {
  const mode = qs("mode") || "flights";
  const origin = qs("origin") || "";
  const destination = qs("destination") || "";
  const date = qs("date") || "";

  document.getElementById("searchSummary").innerText =
    `${origin || "Anywhere"} → ${destination || "Anywhere"}` + (date ? ` · ${date}` : "");

  Api.searchTrips(mode, { origin, destination, travel_date: date || undefined })
    .then((trips) => {
      const list = document.getElementById("resultsList");
      if (!trips.length) {
        list.innerHTML = `<p class="tg-text-dim text-center py-10">No trips found for this search.</p>`;
        return;
      }
      list.innerHTML = trips
        .map(
          (t) => `
            <a href="/static/trip-details.html?mode=${mode}&id=${t.id}"
               class="tg-surface block rounded-xl p-5 mb-4 hover:border-yellow-500 transition">
              <div class="flex justify-between items-center">
                <div>
                  <div class="font-bold text-lg">${t.operator_name}</div>
                  <div class="tg-text-dim text-sm">${t.origin} → ${t.destination}</div>
                  <div class="tg-text-dim text-xs mt-1">${new Date(t.departure_time).toLocaleString()}</div>
                </div>
                <div class="text-right">
                  <div class="font-bold text-xl" style="color: var(--accent)">${money(t.price)}</div>
                  <div class="tg-text-dim text-xs">${t.available_seats} seats left</div>
                </div>
              </div>
            </a>
          `
        )
        .join("");
    })
    .catch((e) => {
      document.getElementById("resultsList").innerHTML = `<p class="text-red-400">${e.message}</p>`;
    });
}

// ---- Trip details --------------------------------------------------
function init_tripDetails() {
  const mode = qs("mode") || "flights";
  const id = qs("id");

  Api.getTrip(mode, id).then((t) => {
    document.getElementById("tripInfo").innerHTML = `
      <h1 class="text-2xl font-bold mb-1">${t.operator_name}</h1>
      <p class="tg-text-dim mb-6">${t.origin} → ${t.destination}</p>
      <div class="grid grid-cols-2 gap-4 text-sm mb-6">
        <div><span class="tg-text-dim">Departure</span><br>${new Date(t.departure_time).toLocaleString()}</div>
        <div><span class="tg-text-dim">Seats left</span><br>${t.available_seats} / ${t.total_seats}</div>
      </div>
      <div class="text-3xl font-bold mb-6" style="color: var(--accent)">${money(t.price)}</div>
    `;
    document.getElementById("bookBtn").href = `/static/checkout.html?mode=${mode}&id=${t.id}`;
  });
}

// ---- Login / Register -------------------------------------------------
function init_login() {
  document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const data = await Api.login(
        document.getElementById("email").value,
        document.getElementById("password").value
      );
      window.location.href = data.is_admin ? "/static/admin.html" : "/static/index.html";
    } catch (err) {
      alert(err.message);
    }
  });
}

function init_register() {
  document.getElementById("registerForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await Api.register({
        name: document.getElementById("name").value,
        email: document.getElementById("email").value,
        phone: document.getElementById("phone").value,
        password: document.getElementById("password").value,
      });
      window.location.href = "/static/index.html";
    } catch (err) {
      alert(err.message);
    }
  });
}

// ---- Checkout (booking + payment) --------------------------------
function init_checkout() {
  requireAuth();
  const mode = qs("mode") || "flights";
  const tripId = qs("id");
  let trip = null;

  Api.getTrip(mode, tripId).then((t) => {
    trip = t;
    document.getElementById("checkoutSummary").innerHTML = `
      <div class="font-bold">${t.operator_name}</div>
      <div class="tg-text-dim text-sm">${t.origin} → ${t.destination}</div>
      <div class="font-bold text-xl mt-2" style="color: var(--accent)">${money(t.price)}</div>
    `;
  });

  document.getElementById("checkoutForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const passenger_name = document.getElementById("passengerName").value;
    const passenger_phone = document.getElementById("passengerPhone").value;
    const seat_number = document.getElementById("seatNumber").value;

    try {
      const booking = await Api.createBooking({
        trip_id: Number(tripId),
        seat_number,
        passenger_name,
        passenger_phone,
      });
      const payment = await Api.initiatePayment(booking.id);

      FlutterwaveCheckout({
        public_key: payment.public_key,
        tx_ref: payment.tx_ref,
        amount: payment.amount,
        currency: payment.currency,
        payment_options: "card, banktransfer, ussd, account",
        customer: { email: (await Api.getMe()).email, phone_number: passenger_phone, name: passenger_name },
        customizations: {
          title: "TravelGroup Booking",
          description: `Booking ${booking.booking_ref}`,
        },
        callback: async function (data) {
          try {
            await Api.verifyPayment({
              booking_id: booking.id,
              tx_ref: payment.tx_ref,
              transaction_id: String(data.transaction_id),
            });
            window.location.href = `/static/booking-confirmation.html?id=${booking.id}`;
          } catch (err) {
            alert("Payment could not be verified: " + err.message);
          }
        },
      });
    } catch (err) {
      alert(err.message);
    }
  });
}

// ---- Booking confirmation -------------------------------------------
function init_bookingConfirmation() {
  requireAuth();
  const id = qs("id");
  Api.getBooking(id).then((b) => {
    document.getElementById("confirmation").innerHTML = `
      <div class="text-5xl mb-4">🎟️</div>
      <h1 class="text-2xl font-bold mb-2">Booking ${b.status === "confirmed" ? "Confirmed" : "Received"}</h1>
      <p class="tg-text-dim mb-6">Reference: <span class="font-mono text-white">${b.booking_ref}</span></p>
      <div class="tg-surface rounded-xl p-6 text-left max-w-sm mx-auto">
        <div class="flex justify-between py-1"><span class="tg-text-dim">Route</span><span>${b.trip.origin} → ${b.trip.destination}</span></div>
        <div class="flex justify-between py-1"><span class="tg-text-dim">Seat</span><span>${b.seat_number}</span></div>
        <div class="flex justify-between py-1"><span class="tg-text-dim">Amount</span><span>${money(b.amount)}</span></div>
        <div class="flex justify-between py-1"><span class="tg-text-dim">Status</span><span class="capitalize">${b.status.replace("_", " ")}</span></div>
      </div>
    `;
  });
}

// ---- My Tickets --------------------------------------------------------
function init_myTickets() {
  requireAuth();
  Api.myBookings().then((bookings) => {
    const list = document.getElementById("ticketsList");
    if (!bookings.length) {
      list.innerHTML = `<p class="tg-text-dim text-center py-10">No bookings yet. <a href="/static/index.html" class="underline" style="color: var(--accent)">Book a trip</a>.</p>`;
      return;
    }
    list.innerHTML = bookings
      .map(
        (b) => `
          <div class="tg-surface rounded-xl p-5 mb-4 flex justify-between items-center">
            <div>
              <div class="font-bold">${b.trip.operator_name} — ${b.trip.origin} → ${b.trip.destination}</div>
              <div class="tg-text-dim text-xs mt-1">Ref ${b.booking_ref} · Seat ${b.seat_number}</div>
            </div>
            <div class="text-right">
              <div class="font-bold" style="color: var(--accent)">${money(b.amount)}</div>
              <div class="text-xs capitalize tg-text-dim">${b.status.replace("_", " ")}</div>
              ${
                b.status !== "cancelled"
                  ? `<button onclick="cancelBooking(${b.id})" class="text-xs text-red-400 underline mt-1">Cancel</button>`
                  : ""
              }
            </div>
          </div>
        `
      )
      .join("");
  });
}

function cancelBooking(id) {
  if (!confirm("Cancel this booking?")) return;
  Api.cancelBooking(id).then(() => init_myTickets());
}

// ---- Profile -------------------------------------------------------
function init_profile() {
  requireAuth();
  Api.getMe().then((u) => {
    document.getElementById("profileName").value = u.name;
    document.getElementById("profileEmail").value = u.email;
    document.getElementById("profilePhone").value = u.phone || "";
  });

  document.getElementById("profileForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await Api.updateMe({
        name: document.getElementById("profileName").value,
        phone: document.getElementById("profilePhone").value,
      });
      alert("Profile updated.");
    } catch (err) {
      alert(err.message);
    }
  });
}

// ---- Admin -----------------------------------------------------------
function init_admin() {
  requireAdmin();

  function loadTrips() {
    Api.admin.listTrips().then((trips) => {
      document.getElementById("tripsTable").innerHTML = trips
        .map(
          (t) => `
            <tr class="border-b tg-text-dim">
              <td class="p-2 capitalize">${t.mode}</td>
              <td class="p-2 text-white">${t.operator_name}</td>
              <td class="p-2">${t.origin} → ${t.destination}</td>
              <td class="p-2">${money(t.price)}</td>
              <td class="p-2">${t.available_seats}/${t.total_seats}</td>
              <td class="p-2"><button onclick="deleteTrip(${t.id})" class="text-red-400 underline text-xs">Delete</button></td>
            </tr>
          `
        )
        .join("");
    });
  }

  document.getElementById("tripForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await Api.admin.createTrip({
        mode: document.getElementById("tMode").value,
        operator_name: document.getElementById("tOperator").value,
        origin: document.getElementById("tOrigin").value,
        destination: document.getElementById("tDestination").value,
        departure_time: document.getElementById("tDeparture").value,
        price: parseFloat(document.getElementById("tPrice").value),
        total_seats: parseInt(document.getElementById("tSeats").value, 10),
      });
      e.target.reset();
      loadTrips();
    } catch (err) {
      alert(err.message);
    }
  });

  window.deleteTrip = (id) => {
    if (!confirm("Delete this trip?")) return;
    Api.admin.deleteTrip(id).then(loadTrips);
  };

  function loadBookings() {
    Api.admin.listBookings().then((bookings) => {
      document.getElementById("bookingsTable").innerHTML = bookings
        .map(
          (b) => `
            <tr class="border-b tg-text-dim">
              <td class="p-2 text-white">${b.booking_ref}</td>
              <td class="p-2">${b.passenger_name}</td>
              <td class="p-2">${b.trip.origin} → ${b.trip.destination}</td>
              <td class="p-2">${money(b.amount)}</td>
              <td class="p-2 capitalize">${b.status.replace("_", " ")}</td>
            </tr>
          `
        )
        .join("");
    });
  }

  loadTrips();
  loadBookings();
}

// ---- Dispatch on load --------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  renderNav();
  const page = document.body.dataset.page;
  const initFns = {
    home: init_home,
    search: init_search,
    "trip-details": init_tripDetails,
    login: init_login,
    register: init_register,
    checkout: init_checkout,
    "booking-confirmation": init_bookingConfirmation,
    "my-tickets": init_myTickets,
    profile: init_profile,
    admin: init_admin,
  };
  if (initFns[page]) initFns[page]();
});
