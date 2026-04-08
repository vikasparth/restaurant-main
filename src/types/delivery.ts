export interface DeliveryValidateRequest {
  zip_code: string;
}

export interface DeliveryValidateResponse {
  is_covered: boolean;
  city: string | null;
}
