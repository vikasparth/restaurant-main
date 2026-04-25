import { readFileSync } from "fs";
import { buildSchema } from "graphql";
import mappings from "./validate-config.js";

const SCHEMA_PATH = process.env.SCHEMA_PATH ?? "graphql-gateway/schemas/menu.graphql";
const OPENAPI_PATH = process.env.OPENAPI_PATH ?? "backend/openapi.json";

const schemaText = readFileSync(SCHEMA_PATH, "utf8");
const openapi = JSON.parse(readFileSync(OPENAPI_PATH, "utf8"));

const schema = buildSchema(schemaText);
let failed = false;

for (const { graphqlType, openapiSchema } of mappings) {
  const gqlType = schema.getType(graphqlType);
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

if (failed) process.exit(1);
