-- ============================================================
-- Migration: Add delivery_zip to catering_orders
-- Reason: CAT-14 — zip code validation added in Slice 5; store validated zip alongside address
-- Phase 2: column retained for geocoding upgrade
-- ============================================================

alter table public.catering_orders
  add column if not exists delivery_zip text;
