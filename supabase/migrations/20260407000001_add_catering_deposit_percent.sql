-- ============================================================
-- Migration: Add catering_deposit_percent to restaurant_config
-- Reason: CAT-13 — show 40% deposit requirement on catering confirmation
-- Phase 1: deposit amount shown only; online collection is Phase 2 (Stripe)
-- ============================================================

alter table public.restaurant_config
  add column if not exists catering_deposit_percent integer not null default 40;
