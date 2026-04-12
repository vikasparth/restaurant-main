import type { ReservationCreateRequest, ReservationCreateResponse } from "@/types/reservation";

export async function createReservation(
  payload: ReservationCreateRequest
): Promise<ReservationCreateResponse> {
  const response = await fetch("/api/reservations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok && response.status !== 200) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body?.code ?? "RESERVATION_FAILED");
  }

  return response.json() as Promise<ReservationCreateResponse>;
}
