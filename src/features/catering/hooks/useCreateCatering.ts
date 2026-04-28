import { gql } from "@apollo/client";
import { useMutation } from "@apollo/client/react";
import { MutationCreateCateringArgs, CateringResponse } from "../../../__generated__/catering";

const CREATE_CATERING = gql`
  mutation CreateCatering($input: CreateCateringInput!) {
    createCatering(input: $input) {
      reference_number
      event_date
      event_time
      total_amount
      deposit_amount
    }
  }
`;

export function useCreateCatering() {
  return useMutation<{ createCatering: CateringResponse }, MutationCreateCateringArgs>(
    CREATE_CATERING
  );
}
