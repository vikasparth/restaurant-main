import { BACKEND_URL, API_PATHS } from "../config.js";

export const menuResolvers = {
  Query: {
    menu: async () => {
      const response = await fetch(`${BACKEND_URL}${API_PATHS.menu}`);
      return response.json();
    },
  },
};
