/* PERSON 2 — FRONTEND DEVELOPER
   One place for every backend call. Nothing in app.js should call
   fetch() directly — it should call a function from here instead. */

const TOKEN_KEY = "tgp_token";
const USER_KEY = "tgp_user";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function isLoggedIn() {
  return !!getToken();
}

function isAdmin() {
  return localStorage.getItem(USER_KEY + "_is_admin") === "true";
}

function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY + "_is_admin");
  window.location.href = "/static/index.html";
}

async function apiRequest(path, { method = "GET", body = null, auth = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (!token) {
      window.location.href = "/static/login.html";
      throw new Error("Not authenticated");
    }
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });

  if (res.status === 401) {
    logout();
    throw new Error("Session expired");
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

const Api = {
  // ---- Auth ----
  async register(payload) {
    const data = await apiRequest("/auth/register", { method: "POST", body: payload });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY + "_is_admin", String(data.is_admin));
    return data;
  },
  async login(email, password) {
    const data = await apiRequest("/auth/login", { method: "POST", body: { email, password } });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY + "_is_admin", String(data.is_admin));
    return data;
  },
  logout,
  isLoggedIn,
  isAdmin,

  // ---- Profile ----
  getMe: () => apiRequest("/users/me", { auth: true }),
  updateMe: (payload) => apiRequest("/users/me", { method: "PUT", body: payload, auth: true }),

  // ---- Trips ----
  searchTrips(mode, { origin, destination, travel_date } = {}) {
    const params = new URLSearchParams();
    if (origin) params.set("origin", origin);
    if (destination) params.set("destination", destination);
    if (travel_date) params.set("travel_date", travel_date);
    const qs = params.toString();
    return apiRequest(`/${mode}${qs ? "?" + qs : ""}`);
  },
  getTrip: (mode, id) => apiRequest(`/${mode}/${id}`),

  // ---- Bookings ----
  createBooking: (payload) => apiRequest("/bookings", { method: "POST", body: payload, auth: true }),
  myBookings: () => apiRequest("/bookings", { auth: true }),
  getBooking: (id) => apiRequest(`/bookings/${id}`, { auth: true }),
  cancelBooking: (id) => apiRequest(`/bookings/${id}/cancel`, { method: "POST", auth: true }),

  // ---- Payments ----
  initiatePayment: (bookingId) =>
    apiRequest("/payments/initiate", { method: "POST", body: { booking_id: bookingId }, auth: true }),
  verifyPayment: (payload) => apiRequest("/payments/verify", { method: "POST", body: payload, auth: true }),

  // ---- Admin ----
  admin: {
    listTrips: () => apiRequest("/admin/trips", { auth: true }),
    createTrip: (payload) => apiRequest("/admin/trips", { method: "POST", body: payload, auth: true }),
    updateTrip: (id, payload) => apiRequest(`/admin/trips/${id}`, { method: "PUT", body: payload, auth: true }),
    deleteTrip: (id) => apiRequest(`/admin/trips/${id}`, { method: "DELETE", auth: true }),
    listBookings: () => apiRequest("/admin/bookings", { auth: true }),
    listPayments: () => apiRequest("/admin/payments", { auth: true }),
    listUsers: () => apiRequest("/admin/users", { auth: true }),
  },
};
