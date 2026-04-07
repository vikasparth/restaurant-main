import { Phone, Mail, MapPin, MessageCircle } from "lucide-react";
import { RESTAURANT_INFO } from "@/data/menu";
import { useState } from "react";
import { toast } from "sonner";
import WhatsAppButton from "@/components/WhatsAppButton";

const ContactPage = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !message) { toast.error("Please fill in all fields"); return; }
    toast.success("Message sent! We'll get back to you soon.");
    setName(""); setEmail(""); setMessage("");
  };

  return (
    <div className="container py-12">
      <h1 className="text-center font-serif text-4xl font-bold text-foreground">Contact Us</h1>
      <p className="mt-2 text-center text-muted-foreground">We'd love to hear from you</p>

      <div className="mx-auto mt-10 grid max-w-4xl gap-10 md:grid-cols-2">
        {/* Contact Info */}
        <div className="space-y-6">
          <div>
            <h2 className="font-serif text-xl font-semibold text-foreground">Get in Touch</h2>
            <div className="mt-4 space-y-4">
              <a href={`tel:${RESTAURANT_INFO.phone}`} className="flex items-center gap-3 text-muted-foreground hover:text-primary transition-colors">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary"><Phone className="h-5 w-5" /></div>
                <span>{RESTAURANT_INFO.phone}</span>
              </a>
              <a href={`mailto:${RESTAURANT_INFO.email}`} className="flex items-center gap-3 text-muted-foreground hover:text-primary transition-colors">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary"><Mail className="h-5 w-5" /></div>
                <span>{RESTAURANT_INFO.email}</span>
              </a>
              <div className="flex items-center gap-3 text-muted-foreground">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary"><MapPin className="h-5 w-5" /></div>
                <span>{RESTAURANT_INFO.address}</span>
              </div>
            </div>
          </div>

          {/* Social Media */}
          <div>
            <h2 className="font-serif text-xl font-semibold text-foreground">Follow Us on Social Media</h2>
            <div className="mt-4 flex gap-4">
              <a href={RESTAURANT_INFO.facebook} target="_blank" rel="noopener noreferrer" className="flex h-12 w-12 items-center justify-center rounded-full transition-transform hover:scale-110" style={{ backgroundColor: "hsl(220, 46%, 48%)" }} aria-label="Facebook">
                <svg className="h-6 w-6 fill-current" style={{ color: "white" }} viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" /></svg>
              </a>
              <a href={RESTAURANT_INFO.instagram} target="_blank" rel="noopener noreferrer" className="flex h-12 w-12 items-center justify-center rounded-full transition-transform hover:scale-110" style={{ background: "linear-gradient(45deg, #f09433, #e6683c, #dc2743, #cc2366, #bc1888)" }} aria-label="Instagram">
                <svg className="h-6 w-6 fill-current" style={{ color: "white" }} viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" /></svg>
              </a>
            </div>
          </div>

          {/* WhatsApp */}
          <div>
            <h2 className="font-serif text-xl font-semibold text-foreground">Chat with Us on WhatsApp</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              For quick responses to order inquiries, reservations, catering questions, and general support.
            </p>
            <WhatsAppButton
              message="Hi Aap ki Rasoi! How can I get help?"
              label="Chat on WhatsApp"
              className="mt-3"
            />
          </div>
        </div>

        {/* Contact Form & Map */}
        <div className="space-y-6">
          <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-border bg-card p-6">
            <h2 className="font-serif text-xl font-semibold text-foreground">Send Us a Message</h2>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">Name</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm" placeholder="Your name" required />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm" placeholder="Your email" required />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-foreground">Message</label>
              <textarea value={message} onChange={(e) => setMessage(e.target.value)} rows={4} className="w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm" placeholder="Your message" required />
            </div>
            <button type="submit" className="w-full rounded-md bg-primary py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-colors">
              Send Message
            </button>
          </form>

          <div className="overflow-hidden rounded-xl">
            <iframe
              src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2483.5430576923!2d-0.1277!3d51.5074!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zNTHCsDMwJzI2LjYiTiAwwrAwNyc0MC4wIlc!5e0!3m2!1sen!2suk!4v1234567890"
              width="100%"
              height="250"
              style={{ border: 0 }}
              allowFullScreen
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
              title="Restaurant Location"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactPage;
