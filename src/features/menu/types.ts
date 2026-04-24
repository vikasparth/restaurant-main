export interface MenuItem {
  id: string;
  name: string;
  description: string;
  price: number;
  category: string;
  image_url: string;
  is_vegetarian: boolean;
  is_available: boolean;
  catering_available: boolean;
  catering_price_per_tray?: number | null;
  allergens: string[];
  display_order: number;
}

export interface MenuCategory {
  name: string;
  items: MenuItem[];
}

export interface MenuResponse {
  categories: MenuCategory[];
}
