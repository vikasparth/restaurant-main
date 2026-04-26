import { gql } from "@apollo/client";
import { useMutation } from "@apollo/client/react";
import {
  MutationCreateReservationArgs,
  ReservationResponse,
} from "../../../__generated__/reservations";

const CREATE_RESERVATION = gql`
  mutation CreateReservation($input: ValidateZipInput!) {
    createReservation(input: $input) {
      reference_number
      party_size
      reserved_date
      reserved_time
    }
  }
`;

export function useCreateReservation() {
  return useMutation<{ createReservation: ReservationResponse }, MutationCreateReservationArgs>(
    CREATE_RESERVATION
  );
}
