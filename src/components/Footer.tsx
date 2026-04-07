import { Link } from "react-router-dom";
import { Phone, Mail, MapPin, Clock } from "lucide-react";
import { RESTAURANT_INFO } from "@/data/menu";
import logo from "@/assets/logo.png";

const Footer = () => (
  <footer className="border-t border-border bg-secondary">
    <div className="container py-12">
      <div className="grid gap-8 md:grid-cols-4">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <img src={logo} alt="Aap ki Rasoi" className="h-8 w-8 object-contain" />
            <span className="font-serif text-lg font-bold text-foreground">Aap ki Rasoi</span>
          </div>
          <p className="text-sm text-muted-foreground">Authentic Indian home cooking, bringing the warmth of home to your table.</p>
        </div>
        <div>
          <h3 className="mb-3 font-serif text-sm font-semibold text-foreground">Quick Links</h3>
          <nav className="flex flex-col gap-2">
            {[
              { to: "/menu", label: "Food Menu" },
              { to: "/our-story", label: "Our Story" },
              { to: "/reservation", label: "Reservations" },
              { to: "/order", label: "Order Online" },
              { to: "/catering", label: "Catering" },
              { to: "/contact", label: "Contact Us" },
            ].map((l) => (
              <Link key={l.to} to={l.to} className="text-sm text-muted-foreground hover:text-primary transition-colors">{l.label}</Link>
            ))}
          </nav>
        </div>
        <div>
          <h3 className="mb-3 font-serif text-sm font-semibold text-foreground">Contact</h3>
          <div className="space-y-2 text-sm text-muted-foreground">
            <div className="flex items-center gap-2"><Phone className="h-4 w-4" /><a href={`tel:${RESTAURANT_INFO.phone}`}>{RESTAURANT_INFO.phone}</a></div>
            <div className="flex items-center gap-2"><Mail className="h-4 w-4" /><a href={`mailto:${RESTAURANT_INFO.email}`}>{RESTAURANT_INFO.email}</a></div>
            <div className="flex items-start gap-2"><MapPin className="h-4 w-4 mt-0.5" /><span>{RESTAURANT_INFO.address}</span></div>
          </div>
        </div>
        <div>
          <h3 className="mb-3 font-serif text-sm font-semibold text-foreground">Hours</h3>
          <div className="space-y-1 text-sm text-muted-foreground">
            <div className="flex items-center gap-2"><Clock className="h-4 w-4" /><span>Mon-Thu: 11am - 10pm</span></div>
            <div className="pl-6"><span>Fri-Sat: 11am - 11pm</span></div>
            <div className="pl-6"><span>Sun: 12pm - 9pm</span></div>
          </div>
        </div>
      </div>
      <div className="mt-8 border-t border-border pt-6 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} Aap ki Rasoi. All rights reserved.
      </div>
    </div>
  </footer>
);

export default Footer;
