import "dotenv/config";

if (!process.env.BACKEND_URL) {
  throw new Error("BACKEND_URL environment variable is not set");
}

export const BACKEND_URL = process.env.BACKEND_URL;

export const API_PATHS = {
  menu: "/api/menu",
  orders: "/api/orders",
  reservations: "/api/reservations",
  deliveryValidate: "/api/delivery/validate",
  catering: "/api/catering",
} as const;
