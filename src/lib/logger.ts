import * as Sentry from "@sentry/react";

export const logger = {
  error(message: string, error?: unknown) {
    if (import.meta.env.PROD) {
      Sentry.captureException(error ?? new Error(message));
    } else {
      console.error(message, error);
    }
  },
  warn(message: string) {
    if (import.meta.env.PROD) {
      Sentry.captureMessage(message, "warning");
    } else {
      console.warn(message);
    }
  },
};
