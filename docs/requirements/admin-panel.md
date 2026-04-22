# Requirements: Admin Panel

**REQ Area Code:** ADM
**Status:** Draft
**Author:** AI-assisted
**Date:** 2026-04-21
**Implements spec:** *(to be filled by engineer)*

---

## 1. Context

### Persona
- **Owner** — the restaurant owner. Full admin access: menu management, category management, operational tasks, account management, and audit trail visibility.
- **Manager** — restaurant staff. Operational access only: toggle item availability, view orders, manage reservations.

### User Goal
- **Owner:** manage the menu (add, edit, remove items and categories) without requiring developer involvement.
- **Manager:** handle day-to-day restaurant operations (availability, orders, reservations) through a secure interface.

### Success Metrics
- Owner can add, update, or remove a menu item in under 2 minutes without developer help
- Zero menu update requests to the developer after launch
- Menu changes reflect on the public menu within 5 seconds (target: instant)
- Manager can toggle item availability in under 30 seconds
- Owner receives an email notification within 1 minute of a manager cancelling a reservation or toggling item availability
- Orders and reservations are visible to owner and manager in real time

---

## 2. Functional Behaviour

### Functional Requirements

| ID | Requirement |
|---|---|
| REQ-ADM-001 | System shall provide a login page at `/admin/login` not linked from any public-facing page |
| REQ-ADM-002 | System shall authenticate admin users via Supabase email/password login |
| REQ-ADM-003 | System shall lock an account after 5 consecutive failed login attempts |
| REQ-ADM-004 | System shall expire sessions after a period of inactivity |
| REQ-ADM-005 | System shall enforce role-based access: owner and manager roles with different permissions |
| REQ-ADM-006 | Owner shall be able to add, edit, and remove menu items |
| REQ-ADM-007 | Owner shall be able to manage menu item pricing |
| REQ-ADM-008 | Owner shall be able to add and rename categories |
| REQ-ADM-009 | Owner shall be able to delete a category only if it contains no items |
| REQ-ADM-010 | Owner shall be able to move menu items between categories |
| REQ-ADM-011 | Manager shall be able to toggle menu item availability |
| REQ-ADM-012 | Owner and manager shall be able to view incoming orders in real time |
| REQ-ADM-013 | Owner and manager shall be able to view and manage reservations |
| REQ-ADM-014 | Manager shall be able to cancel a reservation; system shall notify the owner by email |
| REQ-ADM-015 | Owner shall be able to create and deactivate manager accounts |
| REQ-ADM-016 | Owner-set passwords must meet minimum complexity: 8+ characters, one number, one special character |
| REQ-ADM-017 | When a menu item is removed or made unavailable, it shall be immediately disabled in any active customer carts |
| REQ-ADM-018 | Prices locked at time of order shall not be affected by subsequent price changes |
| REQ-ADM-019 | System shall maintain an audit trail of admin actions, visible to owner only |
| REQ-ADM-020 | Owner shall receive an email notification when a manager toggles item availability |

### User Flows / Scenarios

**Happy path — Owner updates a menu item:**
1. Owner navigates directly to `/admin/login`
2. Enters email and password
3. Authenticates via Supabase and lands on admin dashboard
4. Navigates to menu management
5. Edits item name, description, price, or image
6. Saves — change reflects on public menu within 5 seconds

**Happy path — Manager toggles item unavailable:**
1. Manager logs in at `/admin/login`
2. Navigates to menu availability
3. Toggles an item off
4. Item is immediately hidden from public menu
5. Owner receives email notification
6. Any active customer carts show the item as disabled

**Happy path — Manager cancels a reservation:**
1. Manager navigates to reservations
2. Selects a reservation and cancels it
3. System sends email notification to owner
4. Reservation is marked cancelled

**Edge cases:**
- Customer has a disabled item in cart — item shown greyed out, customer cannot proceed to checkout until removed
- All cart items disabled — customer sees empty cart state with prompt to browse menu
- Owner removes a category with items — system blocks deletion and prompts owner to move items first
- Menu save fails — system retries up to 2 times, then shows failure message; no duplicate entries created

### Acceptance Criteria

| ID | Given | When | Then | Verifies |
|---|---|---|---|---|
| AC-ADM-001-01 | A user is on the public website | When they look for an admin login link | Then no admin link is visible | REQ-ADM-001 |
| AC-ADM-002-01 | An admin navigates to `/admin/login` | When they enter valid credentials | Then they are authenticated and redirected to the dashboard | REQ-ADM-002 |
| AC-ADM-003-01 | An admin enters wrong credentials | When they fail 5 consecutive times | Then the account is locked and a clear message is shown | REQ-ADM-003 |
| AC-ADM-005-01 | A manager is logged in | When they view the menu management page | Then add, remove, and price editing options are not available | REQ-ADM-005 |
| AC-ADM-009-01 | An owner tries to delete a category with items | When they attempt deletion | Then the system blocks it and prompts to move items first | REQ-ADM-009 |
| AC-ADM-014-01 | A manager cancels a reservation | When the cancellation is confirmed | Then the owner receives an email notification within 1 minute | REQ-ADM-014 |
| AC-ADM-017-01 | A customer has an item in their cart | When an admin makes that item unavailable | Then the item is immediately shown as disabled in the cart | REQ-ADM-017 |
| AC-ADM-018-01 | A customer places an order at price X | When the owner later changes the price | Then the original order still shows price X | REQ-ADM-018 |
| AC-ADM-019-01 | An owner views the audit trail | When a manager has toggled availability | Then the log shows who made the change, what changed, and when | REQ-ADM-019 |

---

## 3. Data & System Model

### Core Entities
- **AdminUser** — email, role (`owner` | `manager`), active status; managed via Supabase auth
- **MenuItem** — existing entity; extended with availability toggle and category reference
- **Category** — name, display order; new entity
- **AuditLog** — actor, action type, entity affected, old value, new value, timestamp
- **Order** — existing entity; price locked at time of placement
- **Reservation** — existing entity; cancellation triggers owner notification

### State Transitions

**MenuItem availability:**
`available` → `unavailable` (manager or owner) → `available`

**Reservation:**
`pending` → `confirmed` → `cancelled`

---

## 4. Constraints

### Performance
- Menu changes must reflect on the public menu within 5 seconds; instant is the target
- Admin panel supports 2–3 concurrent users maximum

### Security
- Admin login accessible only via direct URL `/admin/login` — not linked from public pages
- Role-based access control: owner and manager permissions enforced server-side
- Account lockout after 5 failed login attempts (Supabase native)
- Session expires after inactivity (Supabase native)
- Passwords must meet: 8+ characters, one number, one special character
- Audit trail visible to owner only — not accessible to manager

### Compliance / Legal
- Restaurant serves US customers — GDPR does not apply
- No CCPA obligations at current scale
- Assumption: revisit if customer base exceeds 100,000 annually

### Compatibility
- Responsive design — works on desktop and mobile browsers
- No native app required

---

## 5. Operational Behaviour

### Error Handling

| Scenario | User-facing message |
|---|---|
| Wrong email or password | "The email or password you entered is incorrect" |
| Account locked after 5 attempts | "Your account has been locked. Please contact the owner to reset access." |
| Menu save fails after 2 retries | "We couldn't save your changes. Please try again." |
| Session expires mid-edit | User is redirected to login page; unsaved changes are lost |
| Category deletion with items | "This category still has items. Move them to another category before deleting." |

### Notifications
- Owner receives email when a manager cancels a reservation
- Owner receives email when a manager toggles item availability

### Audit Trail

The following actions are logged with actor, timestamp, old value, and new value:
1. Menu item added
2. Menu item removed
3. Menu item updated (name, description, price, image)
4. Item availability toggled
5. Manager account created
6. Manager account deactivated
7. Reservation cancelled by manager

Audit trail is visible in the admin panel to the owner only. Backend engineers can access directly via the database.

### Data Retention
- Audit trail retained indefinitely (revisit if storage becomes a cost concern)
- Order prices retained indefinitely to honour historical orders

---

## 6. Boundaries

### Out of Scope
- Manager real-time order notifications in admin panel (nice to have, deferred)
- Bulk menu import via CSV or similar
- Customer-facing account management
- Sales reporting or analytics dashboard
- Removing categories that contain items

### Assumptions
- Supabase project is already provisioned; auth needs to be configured as part of this feature
- Menu items, orders, and reservations already exist in the database schema
- Resend email is configured and working
- Public menu automatically reflects database changes when queried
- CCPA does not apply at current restaurant scale

### Dependencies

**Upstream (must exist before this can be built):**
- Supabase auth configuration (email/password, role field)
- Existing menu items, orders, reservations schema
- Resend email integration

**Downstream (depends on this feature):**
- Ordering flow must handle disabled cart items gracefully
- Catering flow must handle category changes gracefully

---

## 7. Open Questions

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | Should manager account creation send an invite email or rely on owner sharing credentials? | PM | Owner sets password manually — no invite email |
