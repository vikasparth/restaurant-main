import { Link } from "react-router-dom";
import { Star, ArrowRight } from "lucide-react";
import heroFood from "@/assets/hero-food.jpg";
import { menuItems, RESTAURANT_INFO } from "@/data/menu";
import { useCart } from "@/context/CartContext";

const reviews = [
  { name: "Priya S.", rating: 5, text: "The best butter chicken I've ever had outside of India! Tastes just like my grandmother's cooking." },
  { name: "James M.", rating: 5, text: "Authentic flavors, generous portions. The biryani is absolutely divine. Will definitely come back!" },
  { name: "Anita K.", rating: 5, text: "Finally found a place that makes real dal makhani. The naan is perfectly fluffy too!" },
  { name: "David L.", rating: 4, text: "Wonderful experience. The staff is incredibly warm and the food is consistently excellent." },
  { name: "Meera R.", rating: 5, text: "The catering for our Diwali party was phenomenal. Every dish was a hit with our guests!" },
];

const offers = [
  { id: "butter-chicken", title: "Butter Chicken Special", desc: "Our signature dish at a special price this week", discount: "15% OFF" },
  { id: "biryani", title: "Biryani Feast", desc: "Order biryani and get free naan bread", discount: "FREE NAAN" },
  { id: "gulab-jamun", title: "Sweet Treats", desc: "Complimentary gulab jamun with orders over $30", discount: "FREE DESSERT" },
];

const Index = () => {
  const { addItem } = useCart();
  const mealOfDay = menuItems.find((i) => i.id === "biryani")!;

  return (
    <div>
      {/* Hero */}
      <section className="relative h-[70vh] min-h-[500px] overflow-hidden">
        <img src={heroFood} alt="Indian food spread" className="absolute inset-0 h-full w-full object-cover" width={1920} height={1080} />
        <div className="absolute inset-0 bg-foreground/50" />
        <div className="container relative flex h-full flex-col items-center justify-center text-center">
          <h1 className="font-serif text-5xl font-bold text-background md:text-7xl animate-fade-in">Aap ki Rasoi</h1>
          <p className="mt-4 max-w-lg text-lg text-background/90 animate-fade-in" style={{ animationDelay: "0.2s" }}>
            Home-like food, away from home
          </p>
          <div className="mt-8 flex gap-4 animate-fade-in" style={{ animationDelay: "0.4s" }}>
            <Link to="/menu" className="rounded-md bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-colors">
              View Menu
            </Link>
            <Link to="/order" className="rounded-md border border-background/30 bg-background/10 px-6 py-3 text-sm font-semibold text-background backdrop-blur hover:bg-background/20 transition-colors">
              Order Online
            </Link>
          </div>
        </div>
      </section>

      {/* Welcome */}
      <section className="container py-20 text-center">
        <h2 className="font-serif text-3xl font-bold text-foreground md:text-4xl">Welcome to Our Kitchen</h2>
        <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
          At Aap ki Rasoi, we believe every meal should feel like home. Our recipes have been passed down through generations, 
          using the finest spices and freshest ingredients to bring you the authentic taste of Indian home cooking. 
          Whether you're craving a comforting dal or a festive biryani, every dish is made with love — just like maa ke haath ka khana.
        </p>
      </section>

      {/* Meal of the Day */}
      <section className="bg-secondary py-16">
        <div className="container">
          <h2 className="text-center font-serif text-3xl font-bold text-foreground">Meal of the Day</h2>
          <div className="mx-auto mt-8 flex max-w-3xl flex-col items-center gap-8 md:flex-row">
            <img src={mealOfDay.image} alt={mealOfDay.name} className="h-64 w-64 rounded-xl object-cover shadow-lg" loading="lazy" width={512} height={512} />
            <div>
              <h3 className="font-serif text-2xl font-bold text-foreground">{mealOfDay.name}</h3>
              <p className="mt-2 text-muted-foreground">{mealOfDay.description}</p>
              <p className="mt-3 text-2xl font-bold text-primary">${mealOfDay.price.toFixed(2)}</p>
              <button
                onClick={() => addItem(mealOfDay)}
                className="mt-4 rounded-md bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-colors"
              >
                Add to Cart
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Latest Offers */}
      <section className="container py-20">
        <h2 className="text-center font-serif text-3xl font-bold text-foreground">Latest Offers</h2>
        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {offers.map((offer) => {
            const item = menuItems.find((i) => i.id === offer.id)!;
            return (
              <div key={offer.id} className="group overflow-hidden rounded-xl border border-border bg-card transition-shadow hover:shadow-lg">
                <div className="relative">
                  <img src={item.image} alt={offer.title} className="h-48 w-full object-cover transition-transform group-hover:scale-105" loading="lazy" width={512} height={512} />
                  <span className="absolute right-3 top-3 rounded-full bg-primary px-3 py-1 text-xs font-bold text-primary-foreground">{offer.discount}</span>
                </div>
                <div className="p-5">
                  <h3 className="font-serif text-lg font-semibold text-foreground">{offer.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{offer.desc}</p>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-lg font-bold text-primary">${item.price.toFixed(2)}</span>
                    <button
                      onClick={() => addItem(item)}
                      className="rounded-md bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground hover:opacity-90 transition-colors"
                    >
                      Add to Cart
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Reviews */}
      <section className="bg-secondary py-20">
        <div className="container">
          <h2 className="text-center font-serif text-3xl font-bold text-foreground">What Our Customers Say</h2>
          <div className="mt-8 grid gap-6 md:grid-cols-3 lg:grid-cols-5">
            {reviews.map((r, i) => (
              <div key={i} className="rounded-xl border border-border bg-background p-5">
                <div className="flex gap-0.5">
                  {Array.from({ length: r.rating }).map((_, j) => (
                    <Star key={j} className="h-4 w-4 fill-primary text-primary" />
                  ))}
                </div>
                <p className="mt-3 text-sm text-muted-foreground">"{r.text}"</p>
                <p className="mt-3 text-sm font-semibold text-foreground">{r.name}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Info & Map */}
      <section className="container py-20">
        <div className="grid gap-8 md:grid-cols-2">
          <div>
            <h2 className="font-serif text-3xl font-bold text-foreground">Visit Us</h2>
            <div className="mt-6 space-y-4 text-muted-foreground">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Address</h3>
                <p>{RESTAURANT_INFO.address}</p>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">Hours of Operation</h3>
                <p>Monday - Thursday: 11:00 AM – 10:00 PM</p>
                <p>Friday - Saturday: 11:00 AM – 11:00 PM</p>
                <p>Sunday: 12:00 PM – 9:00 PM</p>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">Contact</h3>
                <p>Phone: <a href={`tel:${RESTAURANT_INFO.phone}`} className="hover:text-primary">{RESTAURANT_INFO.phone}</a></p>
                <p>Email: <a href={`mailto:${RESTAURANT_INFO.email}`} className="hover:text-primary">{RESTAURANT_INFO.email}</a></p>
              </div>
            </div>
            <Link to="/reservation" className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-primary hover:opacity-80">
              Make a Reservation <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="overflow-hidden rounded-xl">
            <iframe
              src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2483.5430576923!2d-0.1277!3d51.5074!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zNTHCsDMwJzI2LjYiTiAwwrAwNyc0MC.0iVw!5e0!3m2!1sen!2suk!4v1234567890"
              width="100%"
              height="350"
              style={{ border: 0 }}
              allowFullScreen
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
              title="Restaurant Location"
            />
          </div>
        </div>
      </section>
    </div>
  );
};

export default Index;
