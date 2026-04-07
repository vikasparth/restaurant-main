import spicesBg from "@/assets/spices-bg.jpg";

const OurStory = () => (
  <div>
    <section className="relative min-h-[60vh] overflow-hidden">
      <img src={spicesBg} alt="Indian spices" className="absolute inset-0 h-full w-full object-cover" width={1920} height={1080} />
      <div className="absolute inset-0 bg-foreground/60" />
      <div className="container relative flex min-h-[60vh] flex-col justify-center py-20">
        <h1 className="font-serif text-5xl font-bold text-background md:text-6xl animate-fade-in">Our Story</h1>
        <p className="mt-4 max-w-2xl text-lg text-background/90 animate-fade-in" style={{ animationDelay: "0.2s" }}>
          A journey of flavors, traditions, and love — from our kitchen to your heart.
        </p>
      </div>
    </section>

    <section className="container max-w-3xl py-20 space-y-8">
      <div>
        <h2 className="font-serif text-3xl font-bold text-foreground">The Heart of Indian Home Cooking</h2>
        <p className="mt-4 text-muted-foreground leading-relaxed">
          Aap ki Rasoi — meaning "Your Kitchen" — was born from a simple belief: that the most memorable meals 
          are the ones cooked with love, at home. Our founder grew up watching their grandmother transform humble 
          ingredients into extraordinary dishes, using recipes whispered from generation to generation.
        </p>
        <p className="mt-4 text-muted-foreground leading-relaxed">
          Every dish we serve carries the essence of that home kitchen — the warmth of a mother's hands, 
          the patience of slow-cooked flavors, and the joy of gathering around a shared table.
        </p>
      </div>

      <div>
        <h2 className="font-serif text-3xl font-bold text-foreground">The Magic of Indian Spices</h2>
        <p className="mt-4 text-muted-foreground leading-relaxed">
          Indian cooking is an art form built on spices — each one a healer, each blend a story. At Aap ki Rasoi, 
          we source our spices directly, grinding them fresh to unlock their full potential.
        </p>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {[
            { name: "Turmeric (Haldi)", benefit: "Known as 'golden spice,' it's a powerful anti-inflammatory and antioxidant used in Ayurvedic medicine for centuries." },
            { name: "Cumin (Jeera)", benefit: "Aids digestion and boosts immunity. Its earthy warmth is the foundation of countless Indian dishes." },
            { name: "Black Cardamom (Badi Elaichi)", benefit: "A smoky, complex spice that supports respiratory health and adds depth to curries and biryanis." },
            { name: "Ginger (Adrak)", benefit: "A natural remedy for nausea and inflammation, ginger brings a bright, warming heat to every dish." },
            { name: "Clove (Laung)", benefit: "Rich in antioxidants with antibacterial properties, cloves bring an intense, sweet warmth to our masalas." },
            { name: "Coriander (Dhaniya)", benefit: "Both the seeds and fresh leaves are used — seeds for earthy depth, leaves for bright, herbaceous freshness." },
          ].map((spice) => (
            <div key={spice.name} className="rounded-lg border border-border bg-secondary p-4">
              <h3 className="font-serif text-sm font-semibold text-foreground">{spice.name}</h3>
              <p className="mt-1 text-xs text-muted-foreground">{spice.benefit}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="font-serif text-3xl font-bold text-foreground">Our Promise</h2>
        <p className="mt-4 text-muted-foreground leading-relaxed">
          Every meal at Aap ki Rasoi is prepared with the same care and authenticity as a home-cooked meal in India. 
          We use no artificial colors, no preservatives — just pure, honest food made with love. 
          Because when you eat at Aap ki Rasoi, you're not just a customer — you're family.
        </p>
      </div>
    </section>
  </div>
);

export default OurStory;
