export interface OrderItem {
  menu_item_id: string;
  quantity: number;
}

export interface OrderCreateRequest {
  idempotency_key: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  order_type: 'pickup' | 'delivery';
  scheduled_date: string;
  scheduled_time: string;
  items: OrderItem[];
  delivery_address?: string;
  delivery_zip?: string;
  special_instructions?: string;
}

export interface OrderCreateResponse {
  reference_number: string;
  status: string;
  order_type: string;
  scheduled_date: string;
  scheduled_time: string;
  subtotal: number;
  delivery_fee: number;
  total: number;
}
