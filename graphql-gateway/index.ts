import { ApolloServer } from "@apollo/server";
import { startStandaloneServer } from "@apollo/server/standalone";
import { readFileSync } from "fs";
import { menuResolvers } from "./resolvers/menu.js";

const typeDefs = readFileSync("./schemas/menu.graphql", "utf-8");

const server = new ApolloServer({ typeDefs, resolvers: menuResolvers });

const { url } = await startStandaloneServer(server, {
  listen: { port: 4000 },
});

console.log(`Gateway running at ${url}`);
