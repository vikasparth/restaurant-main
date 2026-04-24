import { ApolloServer } from "@apollo/server";
import { startStandaloneServer } from "@apollo/server/standalone";
import { readFileSync } from "fs";

const typeDefs = readFileSync("./schema.graphql", "utf-8");

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const API_PATHS = {
  menu: "/api/menu",
} as const;

const resolvers = {
  Query: {
    menu: async () => {
      const response = await fetch(`${BACKEND_URL}${API_PATHS.menu}`);
      return response.json();
    },
  },
};

const server = new ApolloServer({ typeDefs, resolvers });

const { url } = await startStandaloneServer(server, {
  listen: { port: 4000 },
});

console.log(`Gateway running at ${url}`);
