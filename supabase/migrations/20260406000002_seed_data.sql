-- ============================================================
-- Migration: Seed Data — Aap ki Rasoi
-- Development seed only. Update with real values before go-live.
-- ============================================================

-- ============================================================
-- LOCATION (1 location for Phase 1)
-- Update address with real USA address before go-live.
-- ============================================================
insert into public.locations (id, name, address, city, state, zip_code, phone)
values (
  '00000000-0000-0000-0000-000000000001',
  'Aap ki Rasoi',
  '123 Main Street',
  'Bellevue',
  'WA',
  '98004',
  '+1-425-000-0000'
);

-- ============================================================
-- RESTAURANT CONFIG
-- Update hours, fees, and timezone with real values before go-live.
-- operating_hours: 24h format, null means closed that day.
-- ============================================================
insert into public.restaurant_config (
  location_id,
  timezone,
  operating_hours,
  delivery_fee,
  min_delivery_order,
  min_catering_order,
  catering_advance_hours,
  max_reservation_party_size,
  delivery_radius_miles
)
values (
  '00000000-0000-0000-0000-000000000001',
  'America/Los_Angeles',
  '{
    "monday":    {"open": "11:00", "close": "21:00"},
    "tuesday":   {"open": "11:00", "close": "21:00"},
    "wednesday": {"open": "11:00", "close": "21:00"},
    "thursday":  {"open": "11:00", "close": "21:00"},
    "friday":    {"open": "11:00", "close": "22:00"},
    "saturday":  {"open": "11:00", "close": "22:00"},
    "sunday":    {"open": "12:00", "close": "20:00"}
  }',
  4.99,
  25.00,
  100.00,
  48,
  20,
  15.00
);

-- ============================================================
-- SAMPLE MENU ITEMS
-- Replace with real menu items before go-live.
-- ============================================================
insert into public.menu_items (id, location_id, name, description, price, image_url, category, allergens, is_vegetarian, is_available, catering_available, catering_price_per_tray, display_order)
values
  ('samosa',          '00000000-0000-0000-0000-000000000001', 'Samosa',          'Crispy pastry filled with spiced potatoes and peas',                   5.99,  '/images/samosa.jpg',          'appetizers', '{gluten}',          true,  true, true,  35.00, 1),
  ('chicken-tikka',   '00000000-0000-0000-0000-000000000001', 'Chicken Tikka',   'Tender chicken marinated in yogurt and spices, grilled in tandoor',    14.99, '/images/chicken-tikka.jpg',   'appetizers', '{dairy}',           false, true, true,  75.00, 2),
  ('butter-chicken',  '00000000-0000-0000-0000-000000000001', 'Butter Chicken',  'Classic creamy tomato curry with tender chicken',                      16.99, '/images/butter-chicken.jpg',  'mains',      '{dairy}',           false, true, true,  85.00, 1),
  ('dal-makhani',     '00000000-0000-0000-0000-000000000001', 'Dal Makhani',     'Slow-cooked black lentils in rich buttery sauce',                      13.99, '/images/dal-makhani.jpg',     'mains',      '{dairy}',           true,  true, true,  65.00, 2),
  ('palak-paneer',    '00000000-0000-0000-0000-000000000001', 'Palak Paneer',    'Fresh cottage cheese in a smooth spinach gravy',                       14.99, '/images/palak-paneer.jpg',    'mains',      '{dairy}',           true,  true, true,  70.00, 3),
  ('garlic-naan',     '00000000-0000-0000-0000-000000000001', 'Garlic Naan',     'Soft leavened bread with garlic and butter, baked in tandoor',          3.99, '/images/garlic-naan.jpg',     'breads',     '{gluten,dairy}',    true,  true, true,  25.00, 1),
  ('gulab-jamun',     '00000000-0000-0000-0000-000000000001', 'Gulab Jamun',     'Soft milk-solid dumplings soaked in rose-flavoured sugar syrup',        6.99, '/images/gulab-jamun.jpg',     'desserts',   '{dairy,gluten}',    true,  true, true,  40.00, 1),
  ('mango-lassi',     '00000000-0000-0000-0000-000000000001', 'Mango Lassi',     'Chilled yogurt-based drink blended with sweet Alphonso mango',          4.99, '/images/mango-lassi.jpg',     'drinks',     '{dairy}',           true,  true, false, null,  1);

-- ============================================================
-- SAMPLE DELIVERY ZONES
-- Replace with real zip codes before go-live.
-- ============================================================
insert into public.delivery_zones (location_id, zip_code, city)
values
  ('00000000-0000-0000-0000-000000000001', '98004', 'Bellevue'),
  ('00000000-0000-0000-0000-000000000001', '98005', 'Bellevue'),
  ('00000000-0000-0000-0000-000000000001', '98006', 'Bellevue'),
  ('00000000-0000-0000-0000-000000000001', '98007', 'Bellevue'),
  ('00000000-0000-0000-0000-000000000001', '98008', 'Bellevue'),
  ('00000000-0000-0000-0000-000000000001', '98033', 'Kirkland'),
  ('00000000-0000-0000-0000-000000000001', '98034', 'Kirkland'),
  ('00000000-0000-0000-0000-000000000001', '98052', 'Redmond'),
  ('00000000-0000-0000-0000-000000000001', '98053', 'Redmond');
