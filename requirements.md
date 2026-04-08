# Requirements Document — Aap ki Rasoi
**Version: 1.0**
**Status: APPROVED — Signed off by Vikas, 2026-04-06**
**Last updated: 2026-04-06**
**Reference:** See `architecture.md` for technical design decisions.

---

## 1. Project Overview

**Business name:** Aap ki Rasoi
**Type:** Indian restaurant — USA (Pacific Time)
**Purpose:** A fully functional restaurant website with online ordering, reservations, catering, and an owner admin panel.

---

## 2. Stakeholders

| Role | Person | Responsibilities |
|---|---|---|
| Business Owner / Admin | Vikas | Manages orders, reservations, menu, and business config |
| Customer | General public | Browses menu, places orders, makes reservations, places catering requests |

---

## 3. Functional Requirements

### 3.1 Menu

| ID | Requirement | Priority |
|---|---|---|
| MNU-01 | Customers can browse all active menu items | Must-have |
| MNU-02 | Menu items are grouped by category (Appetizers, Mains, Breads, Desserts, Drinks, Specials) | Must-have |
| MNU-03 | Each menu item displays: name, description, price, image, vegetarian flag, allergens | Must-have |
| MNU-04 | Out-of-stock items are marked unavailable and hidden from the customer-facing menu | Must-have |
| MNU-05 | Owner can add, edit, and delete menu items from the admin panel | Must-have |
| MNU-06 | Owner can mark a menu item as unavailable without deleting it | Must-have |
| MNU-07 | Owner can designate items as daily specials with a date range | Must-have |
| MNU-08 | Menu item images are stored as static files (Phase 1); migrated to Supabase Storage in Phase 2 | Phase 1 / Phase 2 |
| MNU-09 | Menu items include an allergens field (e.g. nuts, gluten, dairy) | Must-have |

---

### 3.2 Shopping Cart

| ID | Requirement | Priority |
|---|---|---|
| CRT-01 | Customers can add items to a cart from the menu | Must-have |
| CRT-02 | Customers can update item quantities in the cart | Must-have |
| CRT-03 | Customers can remove items from the cart | Must-have |
| CRT-04 | Cart persists during the session (not required to persist across browser sessions) | Must-have |
| CRT-05 | Cart displays subtotal, delivery fee (if applicable), and grand total | Must-have |

---

### 3.3 Orders (Pickup & Delivery)

| ID | Requirement | Priority |
|---|---|---|
| ORD-01 | Customers can place orders as guests — no account required | Must-have |
| ORD-02 | Customers can choose between Pickup and Delivery | Must-have |
| ORD-03 | Customers must provide: full name, email, phone number | Must-have |
| ORD-04 | Customers must select a scheduled date and time for the order | Must-have |
| ORD-05 | Delivery orders require a delivery address and zip code | Must-have |
| ORD-06 | Delivery is only available to customers within the approved zip code list | Must-have |
| ORD-07 | A clear error message is shown if the zip code is outside the delivery zone | Must-have |
| ORD-08 | Orders are only accepted during restaurant operating hours (validated server-side) | Must-have |
| ORD-09 | A delivery fee is applied to delivery orders (value from `restaurant_config`) | Must-have |
| ORD-10 | A minimum order value for delivery is enforced (value from `restaurant_config`) | Must-have |
| ORD-11 | On successful order, a unique reference number is generated (format: AKR-YYYYMMDD-XXXX) | Must-have |
| ORD-12 | The order reference number is shown to the customer on the confirmation screen | Must-have |
| ORD-13 | The customer receives a confirmation email with full order summary | Must-have |
| ORD-14 | The owner receives a notification (email + WhatsApp) with full order details | Must-have |
| ORD-15 | Orders are auto-confirmed on placement | Must-have |
| ORD-16 | Only the owner can cancel an order (via admin panel) | Must-have |
| ORD-17 | Item prices are snapshotted at the time of order — changing menu prices does not affect past orders | Must-have |
| ORD-18 | Customers can add special instructions per order (e.g. "no onions", "extra spicy", "ring doorbell") | Must-have |
| ORD-19 | The scheduled time must be in the future and fall within restaurant operating hours (validated server-side) | Must-have |
| ORD-20 | If a duplicate order submission is received (e.g. double-click), only one order is created | Must-have |

---

### 3.4 Reservations

| ID | Requirement | Priority |
|---|---|---|
| RES-01 | Customers can request a table reservation without an account | Must-have |
| RES-02 | Customers must provide: full name, phone number, date, time, party size | Must-have |
| RES-03 | Email is optional but required to receive a confirmation email | Must-have |
| RES-04 | Maximum party size is 20 guests (value from `restaurant_config`) | Must-have |
| RES-05 | Reservations are auto-confirmed on submission | Must-have |
| RES-06 | The customer receives a confirmation email (if email provided) | Must-have |
| RES-07 | The owner receives a notification (email + WhatsApp) for every new reservation | Must-have |
| RES-08 | The customer receives a reminder email 24 hours before their reservation | Must-have |
| RES-09 | The reminder is sent via a Supabase pg_cron job running daily at 9am Pacific Time | Must-have |
| RES-10 | Only the owner can cancel a reservation (via admin panel) | Must-have |
| RES-11 | A unique reference number is generated for each reservation (format: AKR-YYYYMMDD-XXXX) | Must-have |
| RES-12 | The reference number is shown to the customer on the confirmation screen | Must-have |

---

### 3.5 Catering Orders

| ID | Requirement | Priority |
|---|---|---|
| CAT-01 | Customers can place catering orders for events without an account | Must-have |
| CAT-02 | Customers must provide: full name, email, phone, event date, event time, delivery address | Must-have |
| CAT-03 | Catering orders must be placed at least 48 hours in advance (validated server-side) | Must-have |
| CAT-04 | A minimum order value of $100 is enforced (value from `restaurant_config`) | Must-have |
| CAT-05 | Only menu items marked `catering_available = true` are shown on the catering page | Must-have |
| CAT-06 | Customers select items by number of trays; each item has a per-tray price | Must-have |
| CAT-07 | On successful submission, a reference number is generated and shown to the customer | Must-have |
| CAT-08 | The customer receives a confirmation email with full order summary | Must-have |
| CAT-09 | The owner receives a notification (email + WhatsApp) with full catering order details | Must-have |
| CAT-10 | Catering orders are auto-confirmed on placement | Must-have |
| CAT-11 | Only the owner can cancel a catering order (via admin panel) | Must-have |
| CAT-12 | Customers can add special instructions to a catering order (e.g. "vegetarian guests only", "no nuts") | Must-have |
| CAT-13 | A 40% deposit amount is calculated and shown in the confirmation email and success screen — e.g. "A deposit of $X is required. Our team will contact you within 24 hours to arrange payment." Online payment collection is Phase 2 (Stripe). | Must-have |

---

### 3.6 Delivery Zone Validation

| ID | Requirement | Priority |
|---|---|---|
| DLV-01 | Delivery is restricted to a predefined list of zip codes stored in the database | Must-have |
| DLV-02 | Zip code validation happens server-side before the order is accepted | Must-have |
| DLV-03 | A clear, friendly error message is shown to customers outside the delivery zone | Must-have |
| DLV-04 | Owner can add or remove zip codes from the delivery zone via admin panel | Must-have |
| DLV-05 | Phase 2: upgrade to real geocoding (exact distance) if zip code approach proves insufficient | Phase 2 |

---

### 3.7 Notifications

| ID | Requirement | Priority |
|---|---|---|
| NOT-01 | Customer order confirmation email includes: reference number, items, quantities, prices, total, scheduled time | Must-have |
| NOT-02 | Customer reservation confirmation email includes: date, time, party size, reference | Must-have |
| NOT-03 | Customer catering confirmation email includes: reference, event date/time, items, total | Must-have |
| NOT-04 | Owner order notification (email + WhatsApp) includes full order details | Must-have |
| NOT-05 | Owner reservation notification (email + WhatsApp) includes full booking details | Must-have |
| NOT-06 | Owner catering notification (email + WhatsApp) includes full catering details | Must-have |
| NOT-07 | Customer reservation reminder email sent 24 hours before the reservation | Must-have |
| NOT-08 | Emails sent via Resend (sandbox in development, custom domain in production) | Must-have |
| NOT-09 | WhatsApp messages sent via Twilio WhatsApp API | Must-have |
| NOT-10 | Owner WhatsApp number: +1 425-439-8426 | Must-have |
| NOT-11 | Owner notification email: vikasparth@gmail.com | Must-have |

---

### 3.8 Admin Panel (API only — UI built separately in Lovable)

| ID | Requirement | Priority |
|---|---|---|
| ADM-01 | Owner can log in securely via Supabase Auth | Must-have |
| ADM-02 | No public sign-up — admin account created manually in Supabase | Must-have |
| ADM-03 | Owner can view all orders with status, customer details, and items | Must-have |
| ADM-04 | Owner can update order status (confirmed → preparing → ready → delivered) | Must-have |
| ADM-05 | Owner can cancel any order | Must-have |
| ADM-06 | Owner can view all reservations | Must-have |
| ADM-07 | Owner can cancel any reservation | Must-have |
| ADM-08 | Owner can view all catering orders | Must-have |
| ADM-09 | Owner can cancel any catering order | Must-have |
| ADM-10 | Owner can add, edit, and delete menu items | Must-have |
| ADM-11 | Owner can mark menu items as unavailable | Must-have |
| ADM-12 | Owner can manage delivery zone zip codes | Must-have |
| ADM-13 | Owner can update restaurant config (hours, delivery fee, minimums, timezone) | Must-have |
| ADM-14 | Admin panel shows: monthly online order revenue, pickup vs delivery count, top 5 items | Must-have |
| ADM-15 | Staff logins with role-based permissions | Phase 2 |

---

### 3.9 Restaurant Configuration (Admin-Managed)

All of the following are stored in the database and editable by the owner. Nothing is hardcoded.

| Config Key | Description | Default |
|---|---|---|
| `timezone` | Restaurant timezone | America/Los_Angeles (Pacific) |
| `operating_hours` | Opening and closing times per day of week | As per current `menu.ts` |
| `closed_days` | Days the restaurant is closed | None by default |
| `delivery_fee` | Flat delivery fee | $4.99 |
| `min_delivery_order` | Minimum order value for delivery | TBD by owner |
| `min_catering_order` | Minimum catering order value | $100 |
| `catering_advance_hours` | Hours in advance required for catering | 48 |
| `catering_deposit_percent` | Deposit percentage shown to customer on catering confirmation | 40 |
| `max_reservation_party_size` | Maximum guests for online reservation | 20 |
| `delivery_radius_miles` | Informational only (zip code list is the enforcer) | 15 |

---

## 4. Non-Functional Requirements

### 4.1 Performance
| ID | Requirement |
|---|---|
| PRF-01 | API responses must complete within 2 seconds under normal load |
| PRF-02 | Menu page must load within 3 seconds on a standard connection |
| PRF-03 | Render free tier cold start (~3 seconds) is acceptable for Phase 1 |

### 4.2 Security
| ID | Requirement |
|---|---|
| SEC-01 | All API communication over HTTPS |
| SEC-02 | Admin endpoints protected by Supabase JWT verification |
| SEC-03 | All secrets stored in environment variables — never hardcoded, never committed to git |
| SEC-04 | Customer data (name, email, phone) stored securely in Supabase |
| SEC-05 | No public sign-up — admin account managed directly in Supabase dashboard |
| SEC-06 | Input validation on all API endpoints via Pydantic models |
| SEC-07 | CORS restricted to known frontend origin (Vercel URL) in production |
| SEC-08 | Rate limiting on all public POST endpoints: max 10 requests per IP per hour (via slowapi) |
| SEC-09 | Free-text fields (name, address, special instructions) sanitized before storage to prevent injection |
| SEC-10 | No PII (personal phone numbers, emails) committed to git or documentation files |

### 4.3 Reliability
| ID | Requirement |
|---|---|
| REL-01 | Reservation reminder cron job runs via Supabase pg_cron — independent of Render sleep |
| REL-02 | If email sending fails, the order is still saved and the error is logged |
| REL-03 | If WhatsApp notification fails, the order is still saved and the error is logged |

### 4.4 Scalability
| ID | Requirement |
|---|---|
| SCA-01 | Database schema supports multiple locations from day one (`location_id` on all relevant tables) |
| SCA-02 | Restaurant config is per-location — each location can have its own hours, fees, and zones |
| SCA-03 | Upgrading from Render free to paid tier eliminates cold starts without code changes |

### 4.5 Maintainability
| ID | Requirement |
|---|---|
| MNT-01 | No single file exceeds 500 lines |
| MNT-02 | Business logic is in service layer — not in routers or models |
| MNT-03 | All business rule values come from `restaurant_config` — changing a rule requires no code change |
| MNT-04 | Database changes are versioned as SQL migration files in `supabase/migrations/` |
| MNT-05 | Environment variables documented in `.env.example` |

### 4.6 Cost
| ID | Requirement |
|---|---|
| CST-01 | Monthly infrastructure cost must be ~$0 during Phase 1 |
| CST-02 | Only costs incurred on usage: Twilio (~$0.005/WhatsApp message) |
| CST-03 | Domain (~$10–15/year) required before go-live — not a monthly cost |

---

## 5. Out of Scope (Phase 1)

The following are explicitly excluded from Phase 1 and documented for Phase 2:

| Feature | Phase |
|---|---|
| Stripe payment integration (catering deposit collection online) | Phase 2 — currently deposit amount is shown in confirmation email; owner collects manually |
| Customer order status tracking page | Phase 2 |
| Real geocoding (exact distance validation) | Phase 2 |
| Staff logins with role-based permissions | Phase 2 |
| Supabase Storage for menu item images | Phase 2 |
| Loyalty / rewards program | Phase 2+ |
| QR code table ordering | Phase 2+ |
| Multi-location activation | Phase 2+ |
| Customer accounts / login | Phase 2+ |

---

## 6. Pre-Launch Checklist (not Phase 1 blockers, but required before real customers)

- [ ] Upgrade Render to Starter tier ($7/mo) — eliminates cold start delays on order flow
- [ ] Purchase domain name (~$10–15/year)
- [ ] Configure Resend with custom domain — prevents confirmation emails landing in spam
- [ ] Replace Twilio WhatsApp sandbox with approved production number
- [ ] Review CCPA privacy requirements (applies if serving California customers)
- [ ] Define data retention policy for customer orders and personal data

---

## 7. Assumptions

1. The restaurant operates from a single USA location during Phase 1.
2. The owner will personally manage all orders and reservations via the admin panel.
3. Customers are expected to pay on pickup/delivery during Phase 1 (no online payment).
4. The owner will purchase a domain before going live.
5. All monetary values are in USD.
6. The frontend (React/Vite) is already built and will be updated in Lovable for missing fields.

---

## 8. Sign-off

| Role | Name | Status |
|---|---|---|
| Business Owner | Vikas | ✅ Approved 2026-04-06 |
