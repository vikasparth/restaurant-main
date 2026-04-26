# GraphQL Naming Chain

How names flow from schema → resolver → generated types → hook → component.
Two examples: one query, one mutation.

---

## Query Example — `validateZip`

### 1. Schema (`delivery.graphql`)
```graphql
input ValidateZipInput {
  zip_code: String!         # field name the backend expects
}

type DeliveryValidateResponse {
  is_covered: Boolean!
  city: String
}

type Query {
  validateZip(input: ValidateZipInput!): DeliveryValidateResponse!
  ^^^^^^^^^^^
  This name must match the resolver key and the gql field name
}
```

### 2. Resolver (`resolvers/delivery.ts`)
```ts
export const deliveryValidationResolvers = {
  Query: {
    validateZip: async (_, { input }) => {   // must match schema field name
      ...
    },
  },
};
```

### 3. Codegen output (`src/__generated__/delivery.ts`)
```ts
// Generated from ValidateZipInput in schema
export type ValidateZipInput = {
  zip_code: Scalars['String']['input'];
};

// Generated from DeliveryValidateResponse in schema
export type DeliveryValidateResponse = {
  is_covered: Scalars['Boolean']['output'];
  city?: Maybe<Scalars['String']['output']>;
};

// Generated from Query.validateZip arguments
// Pattern: Query + <FieldName> + Args
export type QueryValidateZipArgs = {
  input: ValidateZipInput;
};
```

### 4. Hook (`useValidateZip.ts`)
```ts
const VALIDATE_ZIP = gql`
  query ValidateZip($input: ValidateZipInput!) {
  #     ^^^^^^^^^^^  — operation name, for Apollo cache/debugging only (arbitrary)
  #                   ^^^^^^^^^^^^^^^^  — must match input type name in schema
    validateZip(input: $input) {
    ^^^^^^^^^^^  — must match schema Query field name
      is_covered
      city        — fields from DeliveryValidateResponse you want returned
    }
  }
`;

export function useValidateZip() {
  return useLazyQuery<
    { validateZip: DeliveryValidateResponse },
    //  ^^^^^^^^^^^  — must match the gql field name above
    QueryValidateZipArgs   // from __generated__/delivery.ts
  >(VALIDATE_ZIP);
}
```

### 5. Component (`OrderPage.tsx`)
```ts
const [validateZip] = useValidateZip();
//     ^^^^^^^^^^^    ^^^^^^^^^^^^^^
//     arbitrary      must match exported function name in hook file

const { data: zipData } = await validateZip({
  variables: { input: { zip_code: zip } },
  //                    ^^^^^^^^  — must match ValidateZipInput field name in schema
});

zipData?.validateZip.is_covered
//       ^^^^^^^^^^^  — must match gql field name in hook
```

---

## Mutation Example — `createReservation`

### 1. Schema (`reservations.graphql`)
```graphql
input CreateReservationInput {
  customer_name: String!
  ...
}

type ReservationResponse {
  reference_number: String!
  ...
}

type Mutation {
  createReservation(input: CreateReservationInput!): ReservationResponse!
  ^^^^^^^^^^^^^^^^^
  This name must match the resolver key and the gql field name
}
```

### 2. Resolver (`resolvers/reservations.ts`)
```ts
export const reservationResolvers = {
  Mutation: {
    createReservation: async (_, { input }) => {   // must match schema field name
      ...
    },
  },
};
```

### 3. Codegen output (`src/__generated__/reservations.ts`)
```ts
export type CreateReservationInput = { ... };
export type ReservationResponse = { ... };

// Pattern: Mutation + <FieldName> + Args
export type MutationCreateReservationArgs = {
  input: CreateReservationInput;
};
```

### 4. Hook (`useCreateReservation.ts`)
```ts
const CREATE_RESERVATION = gql`
  mutation CreateReservation($input: CreateReservationInput!) {
  #         ^^^^^^^^^^^^^^^^^  — operation name, arbitrary (debugging only)
  #                             ^^^^^^^^^^^^^^^^^^^^^^^^  — must match input type in schema
    createReservation(input: $input) {
    ^^^^^^^^^^^^^^^^^  — must match schema Mutation field name
      reference_number
      party_size        — only fields you need on the confirmation screen
      reserved_date
      reserved_time
    }
  }
`;

export function useCreateReservation() {
  return useMutation<
    { createReservation: ReservationResponse },
    //  ^^^^^^^^^^^^^^^^^  — must match gql field name above
    MutationCreateReservationArgs   // from __generated__/reservations.ts
  >(CREATE_RESERVATION);
}
```

### 5. Component (`ReservationPage.tsx`)
```ts
const [createReservation, { data, loading }] = useCreateReservation();
//     ^^^^^^^^^^^^^^^^^                        ^^^^^^^^^^^^^^^^^^^^
//     arbitrary                                must match exported hook function name

await createReservation({
  variables: { input: { customer_name: name, ... } },
});

data?.createReservation.reference_number
//    ^^^^^^^^^^^^^^^^^  — must match gql field name in hook
```

---

## What Must Match vs What Is Arbitrary

| Name | Must match | Arbitrary |
|---|---|---|
| Schema field (`validateZip`, `createReservation`) | Resolver key + `gql` field name | — |
| Input type name (`ValidateZipInput`) | Codegen type + `gql` variable type | — |
| Operation name (`ValidateZip`, `CreateReservation`) | — | Yes — Apollo cache/debugging only |
| Argument variable (`$input`) | The argument name used in the field call | — |
| Exported hook name (`useValidateZip`) | Component import statement | — |
| Destructured variable in component (`validateZip`) | — | Yes — local name only |
| `data?.createReservation` key | `gql` field name in hook | — |

---

## The Short Rule

**Three things that must match:**
1. Schema field name = resolver key = `gql` field name
2. Input type name in schema = `$variable` type in `gql` string = codegen type
3. Exported hook function name = import in component

**Two things that are arbitrary:**
1. Operation name (the word after `query` or `mutation`)
2. Destructured variable name in the component
