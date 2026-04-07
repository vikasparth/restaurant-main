import { MessageCircle } from "lucide-react";
import { RESTAURANT_INFO } from "@/data/menu";

interface WhatsAppButtonProps {
  message: string;
  label?: string;
  className?: string;
  variant?: "floating" | "inline" | "banner";
}

const WhatsAppButton = ({ message, label = "Chat on WhatsApp", className = "", variant = "inline" }: WhatsAppButtonProps) => {
  const url = `https://wa.me/${RESTAURANT_INFO.whatsapp}?text=${encodeURIComponent(message)}`;

  if (variant === "floating") {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className={`fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-whatsapp shadow-lg transition-transform hover:scale-110 ${className}`}
        aria-label="Chat on WhatsApp"
      >
        <MessageCircle className="h-7 w-7 text-whatsapp-foreground" />
      </a>
    );
  }

  if (variant === "banner") {
    return (
      <div className={`rounded-lg border border-border bg-secondary p-4 ${className}`}>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-whatsapp">
            <MessageCircle className="h-5 w-5 text-whatsapp-foreground" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground">{label}</p>
            <p className="text-xs text-muted-foreground">Quick responses for all your questions</p>
          </div>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md bg-whatsapp px-4 py-2 text-sm font-medium text-whatsapp-foreground transition-colors hover:opacity-90"
          >
            Chat Now
          </a>
        </div>
      </div>
    );
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={`inline-flex items-center gap-2 rounded-md bg-whatsapp px-4 py-2.5 text-sm font-medium text-whatsapp-foreground transition-colors hover:opacity-90 ${className}`}
    >
      <MessageCircle className="h-4 w-4" />
      {label}
    </a>
  );
};

export default WhatsAppButton;
