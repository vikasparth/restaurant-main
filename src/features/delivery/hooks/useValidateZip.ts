import { useLazyQuery } from "@apollo/client/react";
import { gql } from "@apollo/client";
import { QueryValidateZipArgs, DeliveryValidateResponse } from "../../../__generated__/delivery";

const VALIDATE_ZIP = gql`
  query ValidateZip($input: ValidateZipInput!) {
    validateZip(input: $input) {
      is_covered
      city
    }
  }
`;

export function useValidateZip() {
  return useLazyQuery<{ validateZip: DeliveryValidateResponse }, QueryValidateZipArgs>(
    VALIDATE_ZIP
  );
}
