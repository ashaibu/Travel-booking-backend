import { apiRequest }  from "./api";

export function createBooking(transportType, transportId) {
    return apiRequest("/bookings", {
        method: "POST",
        body: JSON.stringify({
            transport_type: transportType,
            transport_id: transportId,
        }),
    });
}

export function getMyBookings() {
    return apiRequest("/bookings");
}

export function getBooking(bookingId) {
    return apiRequest(`/bookings/${bookingId}`);
}

export function cancelBooking(bookingId) {
    return apiRequest(`/booking/${bookingId}`, {
        method: "DELETE",
    });
}