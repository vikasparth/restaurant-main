import type { CateringCreateRequest, CateringCreateResponse } from "@/types/catering";

export async function createCateringOrder(
  payload: CateringCreateRequest
): Promise<CateringCreateResponse> {
  const response = await fetch("/api/catering", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok && response.status !== 200) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body?.code ?? "CATERING_FAILED");
  }

  return response.json() as Promise<CateringCreateResponse>;
}
