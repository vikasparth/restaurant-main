import { useState, useEffect } from "react";
import { Plus, Minus } from "lucide-react";
import { format, addHours, isBefore } from "date-fns";
import { CalendarIcon, Clock } from "lucide-react";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import WhatsAppButton from "@/components/WhatsAppButton";
import { fetchMenu } from "@/services/menuService";
import { createCateringOrder } from "@/services/cateringService";
import type { MenuItem } from "@/types/menu";
import type { CateringCreateResponse } from "@/types/catering";

interface CateringCartItem {
  itemId: string;
  trays: number;
}

const timeSlots = [
  "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00", "14:30",
  "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"
];

const CateringPage = () => {
  const [cateringItems, setCateringItems] = useState<MenuItem[]>([]);
  const [cart, setCart] = useState<CateringCartItem[]>([]);
  const [date, setDate] = useState<Date>();
  const [time, setTime] = useState("");
  const [address, setAddress] = useState("");
  const [zipCode, setZipCode] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [specialInstructions, setSpecialInstructions] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [cateringResult, setCateringResult] = useState<CateringCreateResponse | null>(null);

  useEffect(() => {
    fetchMenu().then((data) => {
      const allItems = data.categories.flatMap((c) => c.items);
      setCateringItems(allItems.filter((i) => i.catering_available));
    });
  }, []);

  const addTray = (id: string) => {
    setCart((prev) => {
      const existing = prev.find((c) => c.itemId === id);
      if (existing) return prev.map((c) => c.itemId === id ? { ...c, trays: c.trays + 1 } : c);
      return [...prev, { itemId: id, trays: 1 }];
    });
  };

  const removeTray = (id: string) => {
    setCart((prev) => {
      const existing = prev.find((c) => c.itemId === id);
      if (!existing) return prev;
      if (existing.trays <= 1) return prev.filter((c) => c.itemId !== id);
      return prev.map((c) => c.itemId === id ? { ...c, trays: c.trays - 1 } : c);
    });
  };

  const getTrays = (id: string) => cart.find((c) => c.itemId === id)?.trays || 0;

  const totalPrice = cart.reduce((sum, ci) => {
    const item = cateringItems.find((i) => i.id === ci.itemId);
    return sum + (item?.catering_price_per_tray || 0) * ci.trays;
  }, 0);

  const handleOrder = async () => {
    if (cart.length === 0) { toast.error("Please add items to your catering order"); return; }
    if (!date || !time) { toast.error("Please select date and time"); return; }
    if (!address.trim()) { toast.error("Please enter delivery address"); return; }
    if (!name.trim() || !email.trim() || !phone.trim()) { toast.error("Please fill in your contact details"); return; }
    if (!zipCode.trim()) { toast.error("Please enter your zip code"); return; }
    const minDate = addHours(new Date(), 48);
    if (isBefore(date, minDate)) { toast.error("Catering orders must be placed at least 48 hours in advance"); return; }

    setSubmitting(true);
    try {
      const result = await createCateringOrder({
        idempotency_key: crypto.randomUUID(),
        customer_name: name.trim(),
        customer_email: email.trim(),
        customer_phone: phone.trim(),
        event_date: format(date, "yyyy-MM-dd"),
        event_time: time,
        delivery_address: address.trim(),
        zip_code: zipCode.trim(),
        items: cart.map((ci) => ({ item_id: ci.itemId, trays: ci.trays })),
        special_instructions: specialInstructions.trim() || undefined,
      });
      setCateringResult(result);
      toast.success("Catering order placed!");
    } catch (err) {
      const code = err instanceof Error ? err.message : "CATERING_FAILED";
      if (code === "LESS_THAN_48_HOURS") {
        toast.error("Catering orders must be placed at least 48 hours in advance.");
      } else if (code === "BELOW_MIN_CATERING_ORDER") {
        toast.error("Minimum catering order is $100. Please add more items.");
      } else if (code === "INVALID_MENU_ITEM") {
        toast.error("One or more items are no longer available. Please refresh and try again.");
      } else if (code === "ITEM_NOT_CATERING_AVAILABLE") {
        toast.error("One or more items are not available for catering. Please refresh and try again.");
      } else if (code === "ZIP_NOT_COVERED") {
        toast.error("Sorry, we don't deliver to that zip code.");
      } else {
        toast.error("Something went wrong. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (cateringResult) {
    return (
      <div className="container max-w-lg py-20 text-center">
        <div className="rounded-xl border border-border bg-card p-8">
          <h1 className="font-serif text-3xl font-bold text-foreground">Catering Order Confirmed!</h1>
          <p className="mt-3 text-sm font-mono text-primary tracking-widest">{cateringResult.reference_number}</p>
          <p className="mt-4 text-muted-foreground">
            Your catering will be delivered on{" "}
            <span className="font-semibold text-foreground">{cateringResult.event_date}</span> at{" "}
            <span className="font-semibold text-foreground">{cateringResult.event_time}</span>.
          </p>
          <div className="mt-4 rounded-lg bg-secondary p-4 text-sm text-foreground space-y-1">
            <p>Order total: <span className="font-semibold">${cateringResult.total_amount.toFixed(2)}</span></p>
            <p>Deposit required: <span className="font-semibold text-primary">${cateringResult.deposit_amount.toFixed(2)}</span></p>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">Our team will contact you within 24 hours to arrange the deposit payment.</p>
          <WhatsAppButton message={`Hi Aap ki Rasoi! I have a question about my catering order ${cateringResult.reference_number}`} label="Questions? Chat on WhatsApp" className="mt-6" />
        </div>
      </div>
    );
  }

  return (
    <div className="container py-12">
      <h1 className="text-center font-serif text-4xl font-bold text-foreground">Catering</h1>
      <p className="mx-auto mt-2 max-w-lg text-center text-muted-foreground">
        Perfect for events, parties, and celebrations. All orders must be placed at least 48 hours in advance.
      </p>

      <WhatsAppButton
        message="Hi Aap ki Rasoi! I'm interested in catering and have some questions..."
        label="Questions about catering? Chat with us on WhatsApp for custom inquiries"
        variant="banner"
        className="mt-6"
      />

      {/* Menu */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cateringItems.map((item) => {
          const trays = getTrays(item.id);
          return (
            <div key={item.id} className="rounded-xl border border-border bg-card p-4">
              <img src={item.image_url} alt={item.name} className="h-40 w-full rounded-lg object-cover" loading="lazy" width={512} height={512} />
              <h3 className="mt-3 font-serif text-base font-semibold text-foreground">{item.name}</h3>
              <p className="text-sm text-primary font-bold">${item.catering_price_per_tray?.toFixed(2)} / tray</p>
              <div className="mt-3 flex items-center gap-3">
                <button onClick={() => removeTray(item.id)} className="flex h-8 w-8 items-center justify-center rounded border border-border hover:bg-secondary" disabled={trays === 0}>
                  <Minus className="h-4 w-4" />
                </button>
                <span className="w-6 text-center font-medium">{trays}</span>
                <button onClick={() => addTray(item.id)} className="flex h-8 w-8 items-center justify-center rounded border border-border hover:bg-secondary">
                  <Plus className="h-4 w-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Checkout */}
      {cart.length > 0 && (
        <div className="mx-auto mt-10 max-w-lg space-y-5">
          <h2 className="font-serif text-2xl font-bold text-foreground">Catering Order Details</h2>

          <div className="rounded-xl border border-border bg-secondary p-5 space-y-2">
            {cart.map((ci) => {
              const item = cateringItems.find((i) => i.id === ci.itemId)!;
              return (
                <div key={ci.itemId} className="flex justify-between text-sm">
                  <span>{item.name} × {ci.trays} trays</span>
                  <span className="font-medium">${((item.catering_price_per_tray || 0) * ci.trays).toFixed(2)}</span>
                </div>
              );
            })}
            <div className="flex justify-between border-t border-border pt-2 text-lg font-semibold">
              <span>Total</span>
              <span className="text-primary">${totalPrice.toFixed(2)}</span>
            </div>
          </div>

          {/* Contact details */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">Full Name *</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm" placeholder="Your name" />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">Phone *</label>
              <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm" placeholder="Your phone number" />
            </div>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground">Email *</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm" placeholder="Your email" />
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="sm:col-span-2">
              <label className="mb-1.5 block text-sm font-medium text-foreground">Delivery Address *</label>
              <input type="text" value={address} onChange={(e) => setAddress(e.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm" placeholder="Full delivery address" />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">Zip Code *</label>
              <input type="text" value={zipCode} onChange={(e) => setZipCode(e.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm" placeholder="e.g. 98004" />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">Date *</label>
              <Popover>
                <PopoverTrigger asChild>
                  <button className={cn("flex w-full items-center gap-2 rounded-md border border-input bg-background px-3 py-2.5 text-sm", !date && "text-muted-foreground")}>
                    <CalendarIcon className="h-4 w-4" />
                    {date ? format(date, "PPP") : "Select date"}
                  </button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar mode="single" selected={date} onSelect={setDate} disabled={(d) => d < addHours(new Date(), 48)} initialFocus className="p-3 pointer-events-auto" />
                </PopoverContent>
              </Popover>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">Time *</label>
              <div className="relative">
                <Clock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <select value={time} onChange={(e) => setTime(e.target.value)} className="w-full appearance-none rounded-md border border-input bg-background py-2.5 pl-9 pr-3 text-sm">
                  <option value="">Select time</option>
                  {timeSlots.map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
            </div>
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-foreground">Special Instructions</label>
            <textarea value={specialInstructions} onChange={(e) => setSpecialInstructions(e.target.value)} rows={3} className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm resize-none" placeholder="e.g. vegetarian guests only, no nuts (optional)" />
          </div>

          <p className="text-xs text-muted-foreground">⚠️ All catering orders must be placed at least 48 hours in advance.</p>

          <button onClick={handleOrder} disabled={submitting} className="w-full rounded-md bg-primary py-3 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-colors disabled:opacity-50">
            {submitting ? "Placing Order…" : "Place Catering Order"}
          </button>
        </div>
      )}
    </div>
  );
};

export default CateringPage;
