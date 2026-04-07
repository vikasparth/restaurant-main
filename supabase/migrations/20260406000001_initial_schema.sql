-- ============================================================
-- Migration: Initial Schema — Aap ki Rasoi
-- ============================================================

-- Enable UUID generation
create extension if not exists "uuid-ossp";

-- ============================================================
-- LOCATIONS
-- Supports multi-location from day one. Phase 1 uses 1 location.
-- ============================================================
create table public.locations (
  id          uuid primary key default uuid_generate_v4(),
  name        text not null,
  address     text not null,
  city        text not null,
  state       text not null,
  zip_code    text not null,
  phone       text not null,
  is_active   boolean not null default true,
  created_at  timestamptz not null default now()
);

-- ============================================================
-- RESTAURANT CONFIG
-- All business rules stored here — no hardcoded values in code.
-- operating_hours format: {"monday": {"open": "11:00", "close": "21:00"}, ...}
-- ============================================================
create table public.restaurant_config (
  id                          uuid primary key default uuid_generate_v4(),
  location_id                 uuid not null references public.locations(id),
  timezone                    text not null default 'America/Los_Angeles',
  operating_hours             jsonb not null,
  closed_days                 text[] not null default '{}',
  delivery_fee                numeric(10,2) not null default 4.99,
  min_delivery_order          numeric(10,2) not null default 25.00,
  min_catering_order          numeric(10,2) not null default 100.00,
  catering_advance_hours      integer not null default 48,
  max_reservation_party_size  integer not null default 20,
  delivery_radius_miles       numeric(5,2) not null default 15.00,
  updated_at                  timestamptz not null default now(),
  unique(location_id)
);

-- ============================================================
-- REFERENCE NUMBER SEQUENCE
-- Format: AKR-YYYYMMDD-XXXX (e.g. AKR-20260406-0001)
-- Global sequence — unique across orders, reservations, catering.
-- ============================================================
create sequence public.reference_number_seq start 1;

create or replace function public.generate_reference_number()
returns text language plpgsql as $$
begin
  return 'AKR-' || to_char(now(), 'YYYYMMDD') || '-' ||
         lpad(nextval('public.reference_number_seq')::text, 4, '0');
end;
$$;

-- ============================================================
-- MENU ITEMS
-- ============================================================
create table public.menu_items (
  id                      text primary key,
  location_id             uuid not null references public.locations(id),
  name                    text not null,
  description             text not null,
  price                   numeric(10,2) not null,
  image_url               text not null,
  category                text not null check (category in (
                            'appetizers','mains','breads','desserts','drinks','specials')),
  allergens               text[] not null default '{}',
  is_vegetarian           boolean not null default false,
  is_available            boolean not null default true,
  catering_available      boolean not null default false,
  catering_price_per_tray numeric(10,2),
  display_order           integer not null default 0,
  created_at              timestamptz not null default now(),
  updated_at              timestamptz not null default now()
);

-- ============================================================
-- DAILY SPECIALS
-- Items marked as special for a date range.
-- ============================================================
create table public.daily_specials (
  id           uuid primary key default uuid_generate_v4(),
  menu_item_id text not null references public.menu_items(id) on delete cascade,
  location_id  uuid not null references public.locations(id),
  start_date   date not null,
  end_date     date not null,
  created_at   timestamptz not null default now(),
  check (end_date >= start_date)
);

-- ============================================================
-- DELIVERY ZONES
-- Approved zip codes per location.
-- ============================================================
create table public.delivery_zones (
  id          uuid primary key default uuid_generate_v4(),
  location_id uuid not null references public.locations(id),
  zip_code    text not null,
  city        text not null,
  is_active   boolean not null default true,
  unique(location_id, zip_code)
);

-- ============================================================
-- ORDERS (pickup / delivery)
-- ============================================================
create table public.orders (
  id                   uuid primary key default uuid_generate_v4(),
  location_id          uuid not null references public.locations(id),
  reference_number     text not null unique default public.generate_reference_number(),
  idempotency_key      uuid not null unique,
  customer_name        text not null,
  customer_email       text not null,
  customer_phone       text not null,
  order_type           text not null check (order_type in ('pickup','delivery')),
  status               text not null default 'confirmed'
                         check (status in ('confirmed','preparing','ready','delivered','cancelled')),
  scheduled_date       date not null,
  scheduled_time       text not null,
  delivery_address     text,
  delivery_zip         text,
  subtotal             numeric(10,2) not null,
  delivery_fee         numeric(10,2) not null default 0,
  total                numeric(10,2) not null,
  special_instructions text,
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now()
);

create table public.order_items (
  id           uuid primary key default uuid_generate_v4(),
  order_id     uuid not null references public.orders(id) on delete cascade,
  menu_item_id text not null,
  name         text not null,           -- snapshot at time of order
  price        numeric(10,2) not null,  -- snapshot at time of order
  quantity     integer not null check (quantity > 0)
);

-- ============================================================
-- RESERVATIONS
-- ============================================================
create table public.reservations (
  id               uuid primary key default uuid_generate_v4(),
  location_id      uuid not null references public.locations(id),
  reference_number text not null unique default public.generate_reference_number(),
  idempotency_key  uuid not null unique,
  customer_name    text not null,
  customer_email   text,
  customer_phone   text not null,
  party_size       integer not null check (party_size > 0),
  reserved_date    date not null,
  reserved_time    text not null,
  status           text not null default 'confirmed'
                     check (status in ('confirmed','cancelled','completed')),
  notes            text,
  reminder_sent    boolean not null default false,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

-- ============================================================
-- CATERING ORDERS
-- ============================================================
create table public.catering_orders (
  id                   uuid primary key default uuid_generate_v4(),
  location_id          uuid not null references public.locations(id),
  reference_number     text not null unique default public.generate_reference_number(),
  idempotency_key      uuid not null unique,
  customer_name        text not null,
  customer_email       text not null,
  customer_phone       text not null,
  event_date           date not null,
  event_time           text not null,
  delivery_address     text not null,
  total                numeric(10,2) not null,
  status               text not null default 'confirmed'
                         check (status in ('confirmed','cancelled','completed')),
  special_instructions text,
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now()
);

create table public.catering_order_items (
  id                uuid primary key default uuid_generate_v4(),
  catering_order_id uuid not null references public.catering_orders(id) on delete cascade,
  menu_item_id      text not null,
  name              text not null,            -- snapshot at time of order
  price_per_tray    numeric(10,2) not null,   -- snapshot at time of order
  trays             integer not null check (trays > 0)
);

-- ============================================================
-- AUTO-UPDATE updated_at TRIGGER
-- ============================================================
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger trg_menu_items_updated_at
  before update on public.menu_items
  for each row execute function public.set_updated_at();

create trigger trg_restaurant_config_updated_at
  before update on public.restaurant_config
  for each row execute function public.set_updated_at();

create trigger trg_orders_updated_at
  before update on public.orders
  for each row execute function public.set_updated_at();

create trigger trg_reservations_updated_at
  before update on public.reservations
  for each row execute function public.set_updated_at();

create trigger trg_catering_orders_updated_at
  before update on public.catering_orders
  for each row execute function public.set_updated_at();

-- ============================================================
-- ROW LEVEL SECURITY (defence-in-depth)
-- Backend uses direct Postgres connection (bypasses RLS).
-- These policies protect against accidental direct access.
-- ============================================================

alter table public.locations enable row level security;
create policy "Public can read locations" on public.locations
  for select using (true);

alter table public.restaurant_config enable row level security;
create policy "Public can read config" on public.restaurant_config
  for select using (true);

alter table public.menu_items enable row level security;
create policy "Public can read menu" on public.menu_items
  for select using (true);
create policy "Admin can manage menu" on public.menu_items
  for all using (auth.role() = 'authenticated');

alter table public.daily_specials enable row level security;
create policy "Public can read daily specials" on public.daily_specials
  for select using (true);

alter table public.delivery_zones enable row level security;
create policy "Public can read delivery zones" on public.delivery_zones
  for select using (true);
create policy "Admin can manage delivery zones" on public.delivery_zones
  for all using (auth.role() = 'authenticated');

alter table public.orders enable row level security;
create policy "Public can place orders" on public.orders
  for insert with check (true);
create policy "Admin can read all orders" on public.orders
  for select using (auth.role() = 'authenticated');
create policy "Admin can update orders" on public.orders
  for update using (auth.role() = 'authenticated');

alter table public.order_items enable row level security;
create policy "Public can insert order items" on public.order_items
  for insert with check (true);
create policy "Admin can read order items" on public.order_items
  for select using (auth.role() = 'authenticated');

alter table public.reservations enable row level security;
create policy "Public can make reservations" on public.reservations
  for insert with check (true);
create policy "Admin can read reservations" on public.reservations
  for select using (auth.role() = 'authenticated');
create policy "Admin can update reservations" on public.reservations
  for update using (auth.role() = 'authenticated');

alter table public.catering_orders enable row level security;
create policy "Public can place catering orders" on public.catering_orders
  for insert with check (true);
create policy "Admin can read catering orders" on public.catering_orders
  for select using (auth.role() = 'authenticated');
create policy "Admin can update catering orders" on public.catering_orders
  for update using (auth.role() = 'authenticated');

alter table public.catering_order_items enable row level security;
create policy "Public can insert catering items" on public.catering_order_items
  for insert with check (true);
create policy "Admin can read catering items" on public.catering_order_items
  for select using (auth.role() = 'authenticated');
