import { ApolloServer } from "@apollo/server";
import { startStandaloneServer } from "@apollo/server/standalone";
import { readFileSync } from "fs";
import { menuResolvers } from "./resolvers/menu.js";
import { orderResolvers } from "./resolvers/orders.js";
import { reservationResolvers } from "./resolvers/reservations.js";
import { deliveryValidationResolvers } from "./resolvers/delivery.js";
import * as Sentry from "@sentry/node";

if (process.env.GATEWAY_SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.GATEWAY_SENTRY_DSN,
    environment: process.env.NODE_ENV ?? "development",
    release: process.env.GATEWAY_SENTRY_RELEASE,
  });
}

const typeDefs = [
  readFileSync("./schemas/menu.graphql", "utf-8"),
  readFileSync("./schemas/orders.graphql", "utf-8"),
  readFileSync("./schemas/reservations.graphql", "utf-8"),
  readFileSync("./schemas/delivery.graphql", "utf-8"),
];

const server = new ApolloServer({
  typeDefs,
  resolvers: [menuResolvers, orderResolvers, reservationResolvers, deliveryValidationResolvers],
});

const { url } = await startStandaloneServer(server, {
  listen: { port: 4000 },
});

console.log(`Gateway running at ${url}`);
