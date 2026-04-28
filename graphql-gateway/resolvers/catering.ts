import { BACKEND_URL, API_PATHS } from "../config.js";

export const cateringResolvers = {
  Mutation: {
    createCatering: async (_: unknown, { input }: { input: unknown }) => {
      const response = await fetch(`${BACKEND_URL}${API_PATHS.catering}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(input),
      });
      return response.json();
    },
  },
};
