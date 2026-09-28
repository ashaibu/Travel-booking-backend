import { initializePayment } from "./paymentApi";

import { createBooking } from "./bookingApi";
import { initializePayment } from "./paymentsApi";

export async function startBookingPayment(transportType, transportId) {
    const booking = await createBooking(transportType, transportId);

    const payment = await initializePayment(booking.id);

    return {
        booking,
        payment,
    };
}