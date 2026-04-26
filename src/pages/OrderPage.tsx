import { useState } from "react";
import { format } from "date-fns";
import { CalendarIcon, Clock, Truck, Store } from "lucide-react";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { useCart } from "@/context/CartContext";
import { toast } from "sonner";
import WhatsAppButton from "@/components/WhatsAppButton";
import { useValidateZip } from "@/features/delivery/hooks/useValidateZip";
import { useCreateOrder } from "@/features/orders/hooks/useCreateOrder";

const timeSlots = [
  "11:00",
  "11:30",
  "12:00",
  "12:30",
  "13:00",
  "13:30",
  "14:00",
  "14:30",
  "17:00",
  "17:30",
  "18:00",
  "18:30",
  "19:00",
  "19:30",
  "20:00",
  "20:30",
  "21:00",
];

const OrderPage = () => {
  const { items, totalPrice, removeItem, updateQuantity, clearCart } = useCart();
  const [mode, setMode] = useState<"pickup" | "delivery">("pickup");
  const [date, setDate] = useState<Date>();
  const [time, setTime] = useState("");
  const [address, setAddress] = useState("");
  const [zip, setZip] = useState("");
  const [zipStatus, setZipStatus] = useState<"idle" | "checking" | "covered" | "not_covered">(
    "idle"
  );
  const [zipCity, setZipCity] = useState<string | null>(null);
  const [customerName, setCustomerName] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [createOrder, { data, loading }] = useCreateOrder();
  const [validateZip] = useValidateZip();

  const deliveryFee = mode === "delivery" ? 4.99 : 0;
  const grandTotal = totalPrice + deliveryFee;

  const handleZipBlur = async () => {
    if (!zip.trim()) return;
    setZipStatus("checking");
    try {
      const { data: zipData } = await validateZip({
        variables: { input: { zip_code: zip.trim() } },
      });
      if (zipData?.validateZip.is_covered) {
        setZipStatus("covered");
        setZipCity(zipData.validateZip.city ?? null);
      } else {
        setZipStatus("not_covered");
        setZipCity(null);
      }
    } catch {
      setZipStatus("idle");
      toast.error("Could not validate zip code. Please try again.");
    }
  };

  const handleOrder = async () => {
    if (!customerName.trim() || !customerEmail.trim() || !customerPhone.trim()) {
      toast.error("Please fill in your contact details");
      return;
    }
    if (!date || !time) {
      toast.error("Please select date and time");
      return;
    }
    if (mode === "delivery" && zipStatus !== "covered") {
      toast.error("Please enter a valid delivery zip code");
      return;
    }
    if (mode === "delivery" && !address.trim()) {
      toast.error("Please enter a delivery address");
      return;
    }
    if (items.length === 0) {
      toast.error("Your cart is empty");
      return;
    }

    try {
      await createOrder({
        variables: {
          input: {
            idempotency_key: crypto.randomUUID(),
            customer_name: customerName.trim(),
            customer_email: customerEmail.trim(),
            customer_phone: customerPhone.trim(),
            order_type: mode,
            scheduled_date: format(date, "yyyy-MM-dd"),
            scheduled_time: time,
            items: items.map((ci) => ({ menu_item_id: ci.item.id, quantity: ci.quantity })),
            ...(mode === "delivery" && {
              delivery_address: address.trim(),
              delivery_zip: zip.trim(),
            }),
          },
        },
      });
      clearCart();
      toast.success("Order placed successfully!");
    } catch {
      toast.error("Something went wrong. Please try again.");
    }
  };

  if (data?.createOrder) {
    const order = data.createOrder;
    return (
      <div className="container max-w-lg py-20 text-center">
        <div className="rounded-xl border border-border bg-card p-8">
          <h1 className="font-serif text-3xl font-bold text-foreground">Order Confirmed!</h1>
          <p className="mt-3 text-sm font-mono text-primary tracking-widest">
            {order.reference_number}
          </p>
          <p className="mt-4 text-muted-foreground">
            Your {order.order_type} order has been placed for {order.scheduled_date} at{" "}
            {order.scheduled_time}.
          </p>
          <div className="mt-4 space-y-1 text-sm text-muted-foreground">
            <div className="flex justify-between">
              <span>Subtotal</span>
              <span>${order.subtotal.toFixed(2)}</span>
            </div>
            {order.delivery_fee > 0 && (
              <div className="flex justify-between">
                <span>Delivery fee</span>
                <span>${order.delivery_fee.toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between font-semibold text-foreground border-t border-border pt-1">
              <span>Status</span>
              <span>{order.status}</span>
            </div>
            <div className="flex justify-between font-semibold text-foreground border-t border-border pt-1">
              <span>Total</span>
              <span>${order.total.toFixed(2)}</span>
            </div>
          </div>
          <WhatsAppButton
            message={`Hi Aap ki Rasoi! I have a question about my order ${order.reference_number}`}
            label="Track or need help? Chat on WhatsApp"
            className="mt-6"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="container max-w-2xl py-12">
      <h1 className="text-center font-serif text-4xl font-bold text-foreground">Order Online</h1>

      {/* Mode Toggle */}
      <div className="mt-8 flex rounded-lg border border-border bg-secondary p-1">
        <button
          onClick={() => setMode("pickup")}
          className={cn(
            "flex flex-1 items-center justify-center gap-2 rounded-md py-2.5 text-sm font-medium transition-colors",
            mode === "pickup" ? "bg-background shadow-sm text-foreground" : "text-muted-foreground"
          )}
        >
          <Store className="h-4 w-4" /> Pickup
        </button>
        <button
          onClick={() => setMode("delivery")}
          className={cn(
            "flex flex-1 items-center justify-center gap-2 rounded-md py-2.5 text-sm font-medium transition-colors",
            mode === "delivery"
              ? "bg-background shadow-sm text-foreground"
              : "text-muted-foreground"
          )}
        >
          <Truck className="h-4 w-4" /> Delivery
        </button>
      </div>

      {/* Cart Items */}
      <div className="mt-6 space-y-3">
        <h2 className="font-serif text-lg font-semibold text-foreground">Your Items</h2>
        {items.length === 0 ? (
          <p className="rounded-lg border border-border bg-secondary p-6 text-center text-sm text-muted-foreground">
            Your cart is empty.{" "}
            <a href="/menu" className="text-primary hover:underline">
              Browse our menu
            </a>{" "}
            to add items.
          </p>
        ) : (
          items.map((ci) => (
            <div
              key={ci.item.id}
              className="flex items-center gap-3 rounded-lg border border-border p-3"
            >
              <img
                src={ci.item.image_url}
                alt={ci.item.name}
                className="h-12 w-12 rounded-md object-cover"
                loading="lazy"
              />
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">{ci.item.name}</p>
                <p className="text-sm text-primary">${(ci.item.price * ci.quantity).toFixed(2)}</p>
              </div>
              <select
                value={ci.quantity}
                onChange={(e) => updateQuantity(ci.item.id, Number(e.target.value))}
                className="rounded border border-input bg-background px-2 py-1 text-sm"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
              <button
                onClick={() => removeItem(ci.item.id)}
                className="text-xs text-destructive hover:underline"
              >
                Remove
              </button>
            </div>
          ))
        )}
      </div>

      {/* Contact Details */}
      <div className="mt-6 space-y-4">
        <h2 className="font-serif text-lg font-semibold text-foreground">Your Details</h2>
        <div>
          <label className="mb-1.5 block text-sm font-medium text-foreground">Name *</label>
          <input
            type="text"
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm"
            placeholder="Full name"
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground">Email *</label>
            <input
              type="email"
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground">Phone *</label>
            <input
              type="tel"
              value={customerPhone}
              onChange={(e) => setCustomerPhone(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm"
              placeholder="10-digit number"
            />
          </div>
        </div>
      </div>

      {/* Schedule */}
      <div className="mt-6 space-y-4">
        <h2 className="font-serif text-lg font-semibold text-foreground">
          {mode === "pickup" ? "Pickup" : "Delivery"} Details
        </h2>

        {mode === "delivery" && (
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">Zip Code *</label>
              <input
                type="text"
                value={zip}
                onChange={(e) => {
                  setZip(e.target.value);
                  setZipStatus("idle");
                }}
                onBlur={handleZipBlur}
                className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm"
                placeholder="Enter your zip code"
              />
              {zipStatus === "checking" && (
                <p className="mt-1 text-xs text-muted-foreground">Checking coverage…</p>
              )}
              {zipStatus === "covered" && (
                <p className="mt-1 text-xs text-green-600">We deliver to {zipCity}!</p>
              )}
              {zipStatus === "not_covered" && (
                <p className="mt-1 text-xs text-destructive">
                  Sorry, we don't deliver to this zip code.
                </p>
              )}
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">
                Delivery Address *
              </label>
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm"
                placeholder="Enter your full street address"
              />
            </div>
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground">Date *</label>
            <Popover>
              <PopoverTrigger asChild>
                <button
                  className={cn(
                    "flex w-full items-center gap-2 rounded-md border border-input bg-background px-3 py-2.5 text-sm",
                    !date && "text-muted-foreground"
                  )}
                >
                  <CalendarIcon className="h-4 w-4" />
                  {date ? format(date, "PPP") : "Select date"}
                </button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={setDate}
                  disabled={(d) => d < new Date()}
                  initialFocus
                  className="p-3 pointer-events-auto"
                />
              </PopoverContent>
            </Popover>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground">Time *</label>
            <div className="relative">
              <Clock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <select
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="w-full appearance-none rounded-md border border-input bg-background py-2.5 pl-9 pr-3 text-sm"
              >
                <option value="">Select time</option>
                {timeSlots.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Summary */}
      {items.length > 0 && (
        <div className="mt-8 rounded-xl border border-border bg-secondary p-5 space-y-2">
          <h2 className="font-serif text-lg font-semibold text-foreground">Order Summary</h2>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Subtotal</span>
            <span>${totalPrice.toFixed(2)}</span>
          </div>
          {mode === "delivery" && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Delivery Fee</span>
              <span>${deliveryFee.toFixed(2)}</span>
            </div>
          )}
          <div className="flex justify-between border-t border-border pt-2 text-lg font-semibold">
            <span>Total</span>
            <span className="text-primary">${grandTotal.toFixed(2)}</span>
          </div>
          <button
            onClick={handleOrder}
            disabled={loading}
            className="mt-3 w-full rounded-md bg-primary py-3 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-colors disabled:opacity-50"
          >
            {loading ? "Placing Order…" : "Place Order"}
          </button>
        </div>
      )}

      <WhatsAppButton
        message={`Hi Aap ki Rasoi! I have a question about my ${mode} order...`}
        label={`Questions about your ${mode} order? Chat with us`}
        variant="banner"
        className="mt-6"
      />
    </div>
  );
};

export default OrderPage;
