import { gql } from "@apollo/client";
import { useMutation } from "@apollo/client/react";
import { MutationCreateOrderArgs, OrderResponse } from "../../../__generated__/orders";

const CREATE_ORDER = gql`
  mutation CreateOrder($input: CreateOrderInput!) {
    createOrder(input: $input) {
      order_type
      reference_number
      status
      scheduled_date
      scheduled_time
      subtotal
      delivery_fee
      total
    }
  }
`;

export function useCreateOrder() {
  return useMutation<{ createOrder: OrderResponse }, MutationCreateOrderArgs>(CREATE_ORDER);
}
