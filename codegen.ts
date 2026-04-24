import type { CodegenConfig } from "@graphql-codegen/cli";

const config: CodegenConfig = {
  generates: {
    "./src/__generated__/menu.ts": {
      schema: "./graphql-gateway/schemas/menu.graphql",
      plugins: ["typescript", "typescript-operations"],
    },
  },
};

export default config;
