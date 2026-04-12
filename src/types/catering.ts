export interface CateringItemRequest {
  item_id: string;
  trays: number;
}

export interface CateringCreateRequest {
  idempotency_key: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  event_date: string;        // "YYYY-MM-DD"
  event_time: string;        // "HH:MM"
  delivery_address: string;
  zip_code: string;
  items: CateringItemRequest[];
  special_instructions?: string;
}

export interface CateringCreateResponse {
  reference_number: string;
  status: string;
  total_amount: number;
  deposit_amount: number;
  event_date: string;
  event_time: string;
}
