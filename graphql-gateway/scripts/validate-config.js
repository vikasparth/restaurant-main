// mappings: GraphQL response types that correspond to a named schema in backend/openapi.json.
// The validator checks that every field in the GraphQL type also exists in the OpenAPI schema,
// catching the case where the backend removes or renames a field that React is still requesting.
// Add an entry here whenever you add a new GraphQL response type that has an OpenAPI counterpart.
export const mappings = [
  { graphqlType: "MenuItem", openapiSchema: "MenuItem" },
  { graphqlType: "DeliveryValidateResponse", openapiSchema: "DeliveryValidateResponse" },
  
];

// excluded: response types intentionally omitted from field validation.
// These have no direct OpenAPI counterpart — either they are gateway-only wrappers, or the
// backend has not yet documented the response schema in openapi.json.
// The self-check in validate-schema.js warns for any object type not in either list, so every
// type must appear in one of these two arrays. That warning is the mechanism that prevents a
// new type from being silently forgotten.
export const excluded = [
  "MenuCategory",        // nested inside MenuResponse; not a standalone backend model
  "MenuResponse",        // gateway wrapper grouping categories — no single OpenAPI schema for this
  "OrderResponse",       // /api/orders returns empty schema in openapi.json — move to mappings once backend documents it
  "ReservationResponse", // same gap as OrderResponse
  "CateringResponse",   // same gap as OrderResponse — move to mappings once backend documents it
  "CateringResponse",
];
