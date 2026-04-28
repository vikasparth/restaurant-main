import { ApolloServer, HeaderMap } from "@apollo/server";
import { readFileSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { menuResolvers } from "../resolvers/menu.js";
import { orderResolvers } from "../resolvers/orders.js";
import { reservationResolvers } from "../resolvers/reservations.js";
import { deliveryValidationResolvers } from "../resolvers/delivery.js";
import * as Sentry from "@sentry/node";
import "../config.js";
import type { VercelRequest, VercelResponse } from "@vercel/node";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

if (process.env.SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment: process.env.NODE_ENV ?? "production",
  });
}

const typeDefs = [
  readFileSync(path.join(__dirname, "../schemas/menu.graphql"), "utf-8"),
  readFileSync(path.join(__dirname, "../schemas/orders.graphql"), "utf-8"),
  readFileSync(path.join(__dirname, "../schemas/reservations.graphql"), "utf-8"),
  readFileSync(path.join(__dirname, "../schemas/delivery.graphql"), "utf-8"),
];

const server = new ApolloServer({
  typeDefs,
  resolvers: [menuResolvers, orderResolvers, reservationResolvers, deliveryValidationResolvers],
});

await server.start();

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS preflight
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
  if (req.method === "OPTIONS") {
    res.status(200).end();
    return;
  }

  // Build headers map for Apollo
  const headers = new HeaderMap();
  for (const [key, value] of Object.entries(req.headers)) {
    if (value !== undefined) {
      headers.set(key, Array.isArray(value) ? value.join(", ") : value);
    }
  }

  // Vercel pre-parses JSON bodies — pass directly to Apollo
  const result = await server.executeHTTPGraphQLRequest({
    httpGraphQLRequest: {
      method: req.method ?? "POST",
      headers,
      search: req.url?.includes("?") ? req.url.slice(req.url.indexOf("?")) : "",
      body: req.body,
    },
    context: async () => ({}),
  });

  res.status(result.status ?? 200);
  for (const [key, value] of result.headers) {
    res.setHeader(key, value);
  }

  if (result.body.kind === "complete") {
    res.end(result.body.string);
  } else {
    for await (const chunk of result.body.asyncIterator) {
      res.write(chunk);
    }
    res.end();
  }
}
