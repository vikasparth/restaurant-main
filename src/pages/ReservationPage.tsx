import { useState } from "react";
import { format } from "date-fns";
import { CalendarIcon, Clock } from "lucide-react";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import WhatsAppButton from "@/components/WhatsAppButton";
import { useCreateReservation } from "@/features/reservations/hooks/useCreateReservation";
import { logger } from "@/lib/logger";

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

const ReservationPage = () => {
  const [date, setDate] = useState<Date>();
  const [time, setTime] = useState("");
  const [guests, setGuests] = useState("2");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [notes, setNotes] = useState("");
  const [createReservation, { data, loading }] = useCreateReservation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!date || !time || !name || !phone) {
      toast.error("Please fill in all required fields");
      return;
    }

    try {
      await createReservation({
        variables: {
          input: {
            idempotency_key: crypto.randomUUID(),
            customer_name: name.trim(),
            customer_email: email.trim() || undefined,
            customer_phone: phone.trim(),
            party_size: Number(guests),
            reserved_date: format(date, "yyyy-MM-dd"),
            reserved_time: time,
            notes: notes.trim() || undefined,
          },
        },
      });
      toast.success("Reservation confirmed!");
    } catch (e) {
      logger.error("[reservations] failed to create reservation", e);
      toast.error("Something went wrong. Please try again.");
    }
  };

  if (data?.createReservation) {
    const reservation = data.createReservation;
    return (
      <div className="container max-w-lg py-20 text-center">
        <div className="rounded-xl border border-border bg-card p-8">
          <h1 className="font-serif text-3xl font-bold text-foreground">Reservation Confirmed!</h1>
          <p className="mt-3 text-sm font-mono text-primary tracking-widest">
            {reservation.reference_number}
          </p>
          <p className="mt-4 text-muted-foreground">
            We've reserved a table for{" "}
            <span className="font-semibold text-foreground">{reservation.party_size} guests</span>{" "}
            on <span className="font-semibold text-foreground">{reservation.reserved_date}</span> at{" "}
            <span className="font-semibold text-foreground">{reservation.reserved_time}</span>.
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            A confirmation has been sent to {email || phone}.
          </p>
          <WhatsAppButton
            message={`Hi Aap ki Rasoi! I have a question about my reservation ${reservation.reference_number}`}
            label="Questions? Chat on WhatsApp"
            className="mt-6"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="container max-w-lg py-12">
      <h1 className="text-center font-serif text-4xl font-bold text-foreground">
        Make a Reservation
      </h1>
      <p className="mt-2 text-center text-muted-foreground">
        Book your table and enjoy an authentic Indian dining experience
      </p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-5">
        {/* Date */}
        <div>
          <label className="mb-1.5 block text-sm font-medium text-foreground">Date *</label>
          <Popover>
            <PopoverTrigger asChild>
              <button
                aria-label="Select reservation date"
                className={cn(
                  "flex w-full items-center gap-2 rounded-md border border-input bg-background px-3 py-2.5 text-sm",
                  !date && "text-muted-foreground"
                )}
              >
                <CalendarIcon className="h-4 w-4" aria-hidden="true" />
                {date ? format(date, "PPP") : "Select a date"}
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

        {/* Time */}
        <div>
          <label
            htmlFor="reservation-time"
            className="mb-1.5 block text-sm font-medium text-foreground"
          >
            Time *
          </label>
          <div className="relative">
            <Clock
              className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
            <select
              id="reservation-time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="w-full appearance-none rounded-md border border-input bg-background py-2.5 pl-9 pr-3 text-sm"
            >
              <option value="">Select a time</option>
              {timeSlots.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Guests */}
        <div>
          <label
            htmlFor="reservation-guests"
            className="mb-1.5 block text-sm font-medium text-foreground"
          >
            Number of Guests *
          </label>
          <select
            id="reservation-guests"
            value={guests}
            onChange={(e) => setGuests(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm"
          >
            {[1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20].map((n) => (
              <option key={n} value={n}>
                {n} {n === 1 ? "Guest" : "Guests"}
              </option>
            ))}
          </select>
        </div>

        {/* Name */}
        <div>
          <label
            htmlFor="reservation-name"
            className="mb-1.5 block text-sm font-medium text-foreground"
          >
            Full Name *
          </label>
          <input
            id="reservation-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm"
            placeholder="Your name"
            required
          />
        </div>

        {/* Phone */}
        <div>
          <label
            htmlFor="reservation-phone"
            className="mb-1.5 block text-sm font-medium text-foreground"
          >
            Phone *
          </label>
          <input
            id="reservation-phone"
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm"
            placeholder="Your phone number"
            required
          />
        </div>

        {/* Email */}
        <div>
          <label
            htmlFor="reservation-email"
            className="mb-1.5 block text-sm font-medium text-foreground"
          >
            Email
          </label>
          <input
            id="reservation-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm"
            placeholder="Your email (optional)"
          />
        </div>

        {/* Notes */}
        <div>
          <label
            htmlFor="reservation-notes"
            className="mb-1.5 block text-sm font-medium text-foreground"
          >
            Special Requests
          </label>
          <textarea
            id="reservation-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm resize-none"
            placeholder="e.g. window table, high chair needed (optional)"
          />
        </div>

        <button
          type="submit"
          aria-label="Confirm Reservation"
          disabled={loading}
          className="w-full rounded-md bg-primary py-3 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-colors disabled:opacity-50"
        >
          {loading ? "Confirming…" : "Confirm Reservation"}
        </button>
      </form>

      <WhatsAppButton
        message="Hi Aap ki Rasoi! I have a question about making a reservation..."
        label="Need help with your reservation? Chat with us"
        variant="banner"
        className="mt-8"
      />
    </div>
  );
};

export default ReservationPage;
