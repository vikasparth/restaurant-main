import type { OrderCreateRequest, OrderCreateResponse } from "@/types/order";

export async function createOrder(
  payload: OrderCreateRequest
): Promise<OrderCreateResponse> {
  const response = await fetch("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok && response.status !== 200) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body?.code ?? "ORDER_FAILED");
  }

  return response.json() as Promise<OrderCreateResponse>;
}
