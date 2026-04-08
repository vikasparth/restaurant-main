import type { DeliveryValidateResponse } from "@/types/delivery";

export async function validateZip(zipCode: string): Promise<DeliveryValidateResponse> {
  const response = await fetch("/api/delivery/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ zip_code: zipCode }),
  });

  if (!response.ok && response.status !== 422) {
    throw new Error("Failed to validate zip code");
  }

  return response.json() as Promise<DeliveryValidateResponse>;
}
