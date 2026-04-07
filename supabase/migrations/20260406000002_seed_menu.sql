-- ============================================================
-- Migration: Seed Menu Items
-- Migrated from src/data/menu.ts
-- Images reference the static assets already in the frontend.
-- When you add a CDN or Supabase Storage later, update image_url values.
-- ============================================================

insert into public.menu_items
  (id, name, description, ingredients, price, image_url, category, is_vegetarian, catering_available, catering_price_per_tray, display_order)
values
  ('samosa', 'Samosa',
   'Crispy golden pastry stuffed with spiced potatoes and peas, served with mint and tamarind chutney.',
   array['Potatoes','Peas','Cumin','Coriander','Green Chili','Pastry Dough'],
   6.99, '/assets/food/samosa.jpg', 'appetizers', true, true, 45.99, 1),

  ('butter-chicken', 'Butter Chicken',
   'Tender chicken pieces simmered in a rich, creamy tomato sauce with aromatic spices. Our most beloved dish.',
   array['Chicken','Tomatoes','Butter','Cream','Garam Masala','Fenugreek'],
   16.99, '/assets/food/butter-chicken.jpg', 'mains', false, true, 89.99, 2),

  ('palak-paneer', 'Palak Paneer',
   'Fresh cottage cheese cubes in a velvety spinach gravy, seasoned with garlic and aromatic spices.',
   array['Paneer','Spinach','Garlic','Onion','Cumin','Cream'],
   14.99, '/assets/food/palak-paneer.jpg', 'mains', true, true, 79.99, 3),

  ('biryani', 'Chicken Biryani',
   'Fragrant basmati rice layered with tender chicken, saffron, and aromatic spices, slow-cooked to perfection.',
   array['Basmati Rice','Chicken','Saffron','Cardamom','Bay Leaf','Yogurt','Onion'],
   17.99, '/assets/food/biryani.jpg', 'mains', false, true, 99.99, 4),

  ('dal-makhani', 'Dal Makhani',
   'Creamy black lentils slow-cooked overnight with butter and aromatic spices. A true taste of Punjab.',
   array['Black Lentils','Kidney Beans','Butter','Cream','Tomatoes','Ginger','Garlic'],
   13.99, '/assets/food/dal-makhani.jpg', 'mains', true, true, 69.99, 5),

  ('tandoori-chicken', 'Tandoori Chicken',
   'Chicken marinated in yogurt and traditional tandoori spices, roasted in a clay oven until charred and juicy.',
   array['Chicken','Yogurt','Tandoori Masala','Lemon','Ginger','Garlic'],
   15.99, '/assets/food/tandoori-chicken.jpg', 'mains', false, true, 85.99, 6),

  ('chole-bhature', 'Chole Bhature',
   'Spiced chickpea curry served with fluffy deep-fried bread. A classic North Indian comfort meal.',
   array['Chickpeas','Onion','Tomatoes','Chole Masala','Flour','Yogurt'],
   13.99, '/assets/food/chole-bhature.jpg', 'mains', true, true, 74.99, 7),

  ('aloo-gobi', 'Aloo Gobi',
   'Tender potatoes and cauliflower florets cooked with turmeric, cumin, and fresh herbs.',
   array['Potatoes','Cauliflower','Turmeric','Cumin','Tomatoes','Ginger'],
   12.99, '/assets/food/aloo-gobi.jpg', 'mains', true, true, 64.99, 8),

  ('masala-dosa', 'Masala Dosa',
   'Crispy fermented rice and lentil crepe filled with spiced potato masala, served with sambar and chutneys.',
   array['Rice','Urad Dal','Potatoes','Mustard Seeds','Curry Leaves','Turmeric'],
   12.99, '/assets/food/masala-dosa.jpg', 'specials', true, false, null, 9),

  ('naan', 'Butter Naan',
   'Soft and fluffy leavened bread baked in a tandoor, brushed with melted butter.',
   array['Flour','Yogurt','Butter','Yeast'],
   3.99, '/assets/food/naan.jpg', 'breads', true, true, 29.99, 10),

  ('gulab-jamun', 'Gulab Jamun',
   'Golden fried milk dumplings soaked in rose-scented cardamom sugar syrup. A heavenly dessert.',
   array['Milk Powder','Flour','Cardamom','Rose Water','Sugar'],
   7.99, '/assets/food/gulab-jamun.jpg', 'desserts', true, true, 49.99, 11),

  ('mango-lassi', 'Mango Lassi',
   'Refreshing yogurt-based drink blended with sweet Alphonso mangoes and a touch of cardamom.',
   array['Yogurt','Mango Pulp','Sugar','Cardamom'],
   5.99, '/assets/food/mango-lassi.jpg', 'drinks', true, false, null, 12);

-- ============================================================
-- Seed: Delivery Zip Codes
-- Replace these with actual zip codes near your restaurant.
-- These are placeholders — update before going live.
-- ============================================================
insert into public.delivery_zones (zip_code, city) values
  ('00001', 'Placeholder City 1'),
  ('00002', 'Placeholder City 2'),
  ('00003', 'Placeholder City 3');
