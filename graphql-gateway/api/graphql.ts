import { ApolloServer } from "@apollo/server";
import { expressMiddleware } from "@apollo/server/express4";
import express from "express";
import cors from "cors";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { menuResolvers } from "../resolvers/menu.js";
import { orderResolvers } from "../resolvers/orders.js";
import { reservationResolvers } from "../resolvers/reservations.js";
import { deliveryValidationResolvers } from "../resolvers/delivery.js";
import * as Sentry from "@sentry/node";
import "../config.js";

if (process.env.SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment: process.env.NODE_ENV ?? "production",
  });
}

const __dirname = dirname(fileURLToPath(import.meta.url));

const typeDefs = [
  readFileSync(join(__dirname, "../schemas/menu.graphql"), "utf-8"),
  readFileSync(join(__dirname, "../schemas/orders.graphql"), "utf-8"),
  readFileSync(join(__dirname, "../schemas/reservations.graphql"), "utf-8"),
  readFileSync(join(__dirname, "../schemas/delivery.graphql"), "utf-8"),
];

const server = new ApolloServer({
  typeDefs,
  resolvers: [menuResolvers, orderResolvers, reservationResolvers, deliveryValidationResolvers],
});

await server.start();

const app = express();
app.use(cors<cors.CorsRequest>());
app.use(express.json());
app.use(expressMiddleware(server));

export default app;
