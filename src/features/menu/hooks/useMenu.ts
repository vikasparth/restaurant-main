import { useQuery } from "@apollo/client/react";
import { gql } from "@apollo/client";
import type { MenuResponse } from "@/__generated__/menu";

const MENU_QUERY = gql`
  query GetMenu {
    menu {
      categories {
        name
        items {
          id
          name
          description
          price
          category
          image_url
          is_vegetarian
          is_available
          catering_available
          catering_price_per_tray
          allergens
          display_order
        }
      }
    }
  }
`;

export function useMenu() {
  const { data, loading, error } = useQuery<{ menu: MenuResponse }>(MENU_QUERY);
  return { data: data?.menu ?? null, loading, error };
}
