import { readFileSync } from "fs";
import { buildSchema, isObjectType } from "graphql";
import { mappings, excluded } from "./validate-config.js";

const SCHEMA_PATH = process.env.SCHEMA_PATH ?? "graphql-gateway/schemas/menu.graphql";
const OPENAPI_PATH = process.env.OPENAPI_PATH ?? "backend/openapi.json";

const schemaText = readFileSync(SCHEMA_PATH, "utf8");
const openapi = JSON.parse(readFileSync(OPENAPI_PATH, "utf8"));

const schema = buildSchema(schemaText);
let failed = false;

// Field-level validation: for each mapped type, every GraphQL field must exist in the
// corresponding OpenAPI schema. This catches the case where the backend removes or renames
// a field after the GraphQL schema was written.
// Types not present in this schema file are silently skipped — they are validated when
// CI runs this script against their own schema file.
for (const { graphqlType, openapiSchema } of mappings) {
  const gqlType = schema.getType(graphqlType);
  if (!gqlType) continue;

  const graphqlFields = Object.keys(gqlType.getFields());
  const openapiFields = Object.keys(openapi.components.schemas[openapiSchema].properties);

  const missing = graphqlFields.filter(field => !openapiFields.includes(field));

  if (missing.length > 0) {
    console.error(`Validation failed for ${graphqlType}. Fields not found in openapi.json:`);
    missing.forEach(field => console.error(`  - ${field}`));
    failed = true;
  } else {
    console.log(`${graphqlType} — all fields match openapi.json.`);
  }
}

// Self-check: warn for any object type in this schema that is not listed in either mappings
// or excluded. This is the mechanism that catches a new type being added to the schema without
// updating validate-config.js — the mistake that caused us to miss OrderResponse and
// ReservationResponse after the orders/reservations migration.
// Emits a warning (not a failure) because a type may legitimately have no OpenAPI counterpart;
// the developer must decide which list it belongs in.
const ROOT_TYPES = new Set(["Query", "Mutation", "Subscription"]);
const MAPPED = new Set(mappings.map(m => m.graphqlType));
const EXCLUDED = new Set(excluded);

const unmapped = Object.entries(schema.getTypeMap())
  .filter(([name, type]) =>
    !name.startsWith("__") &&
    !ROOT_TYPES.has(name) &&
    isObjectType(type) &&
    !MAPPED.has(name) &&
    !EXCLUDED.has(name)
  )
  .map(([name]) => name);

// Fail so CI blocks the PR — a warning is ignorable, a failure is not.
// Start strict; relax later based on real blocking experience.
if (unmapped.length > 0) {
  console.error(`\nValidation failed: response types in ${SCHEMA_PATH} not listed in validate-config.js:`);
  unmapped.forEach(t => console.error(`  - ${t}  →  add to mappings (has OpenAPI schema) or excluded (does not)`));
  failed = true;
}

if (failed) process.exit(1);
