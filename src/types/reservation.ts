export interface ReservationCreateRequest {
  idempotency_key: string;
  customer_name: string;
  customer_email?: string;
  customer_phone: string;
  party_size: number;
  reserved_date: string;   // "YYYY-MM-DD"
  reserved_time: string;   // "HH:MM"
  notes?: string;
}

export interface ReservationCreateResponse {
  reference_number: string;
  status: string;
  party_size: number;
  reserved_date: string;
  reserved_time: string;
}
