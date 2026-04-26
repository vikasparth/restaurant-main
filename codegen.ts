import type { CodegenConfig } from "@graphql-codegen/cli";

const config: CodegenConfig = {
  generates: {
    "./src/__generated__/menu.ts": {
      schema: "./graphql-gateway/schemas/menu.graphql",
      plugins: ["typescript", "typescript-operations"],
    },
    "./src/__generated__/orders.ts": {
      schema: "./graphql-gateway/schemas/orders.graphql",
      plugins: ["typescript", "typescript-operations"],
    },
    "./src/__generated__/reservations.ts": {
      schema: "./graphql-gateway/schemas/reservations.graphql",
      plugins: ["typescript", "typescript-operations"],
    },
    "./src/__generated__/delivery.ts": {
      schema: "./graphql-gateway/schemas/delivery.graphql",
      plugins: ["typescript", "typescript-operations"],
    },
  },
};

export default config;
