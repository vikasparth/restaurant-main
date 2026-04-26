import { BACKEND_URL, API_PATHS } from "../config.js";

export const orderResolvers = {
  Mutation: {
    createOrder: async (_, { input }) => {
      // fetch POST /api/orders here
      const response = await fetch(`${BACKEND_URL}${API_PATHS.orders}`, {
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
