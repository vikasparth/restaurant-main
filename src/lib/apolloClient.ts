import { ApolloClient, InMemoryCache, HttpLink } from "@apollo/client";

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL;

if (!GATEWAY_URL) {
  throw new Error("VITE_GATEWAY_URL is not set");
}

export const apolloClient = new ApolloClient({
  link: new HttpLink({ uri: GATEWAY_URL }),
  cache: new InMemoryCache(),
});
