import { BACKEND_URL, API_PATHS } from "../config.js";

export const deliveryValidationResolvers = {
  Query: {
    validateZip: async (_, { input }) => {
      const response = await fetch(`${BACKEND_URL}${API_PATHS.deliveryValidate}`, {
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
