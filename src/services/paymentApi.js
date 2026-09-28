import { apiRequest } from "./api";

export function initializePayment(bookingId) {
    return apiRequest(`/payments/${bookingId}/initailize`, {
        method: "POST",
    });
}

export function verifyPayment(bookingId) {
    return apiRequest("/payments/verify", {
        method: "POST",
        body: JSON.stringify({
            transaction_id: transactionId,
        }),
    });
}

export function getPayments() {
    return apiRequest("/payments/");
}