import { ApolloClient, InMemoryCache, HttpLink, from } from "@apollo/client";
import { onError } from "@apollo/client/link/error";
import { ServerError, CombinedGraphQLErrors } from "@apollo/client/errors";
import { toast } from "sonner";
import { Kind, OperationTypeNode } from "graphql";

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL;

if (!GATEWAY_URL) {
  throw new Error("VITE_GATEWAY_URL is not set");
}

const errorLink = onError(({ error, operation }) => {
  if (CombinedGraphQLErrors.is(error)) return;

  const isMutation = operation.query.definitions.some(
    (def) => def.kind === Kind.OPERATION_DEFINITION && def.operation === OperationTypeNode.MUTATION
  );

  if (ServerError.is(error) && (error.statusCode === 504 || error.statusCode === 503)) {
    toast.error(
      isMutation
        ? "Your request timed out — we may not have received it. Please try again or contact us directly."
        : "Taking longer than expected — the server may be starting up. Please try again in a moment.",
      { duration: 7000 }
    );
  } else {
    toast.error("Connection problem — please check your connection and try again.");
  }
});

export const apolloClient = new ApolloClient({
  link: from([errorLink, new HttpLink({ uri: GATEWAY_URL })]),
  cache: new InMemoryCache(),
});
