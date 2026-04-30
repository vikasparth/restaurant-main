import * as Sentry from "@sentry/react";
import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import { apolloClient } from "./lib/apolloClient.ts";
import { ApolloProvider } from "@apollo/client/react";

import "./index.css";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
  release: import.meta.env.VITE_SENTRY_RELEASE,
  beforeBreadcrumb(breadcrumb, hint) {
    // Tailwind class names make auto-generated selectors unreadable — prefer aria-label or id
    if (breadcrumb.category?.startsWith("ui.")) {
      const target = hint?.event?.target as HTMLElement | undefined;
      const label = target?.getAttribute("aria-label") ?? target?.id;
      if (label) {
        breadcrumb.message = label;
      }
    }
    return breadcrumb;
  },
});

createRoot(document.getElementById("root")!).render(
  <ApolloProvider client={apolloClient}>
    <App />
  </ApolloProvider>
);
