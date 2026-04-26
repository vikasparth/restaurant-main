import "dotenv/config";

if (!process.env.BACKEND_URL) {
  throw new Error("BACKEND_URL environment variable is not set");
}

export const BACKEND_URL = process.env.BACKEND_URL;

export const API_PATHS = {
  menu: "/api/menu",
  orders: "/api/orders",
} as const;
