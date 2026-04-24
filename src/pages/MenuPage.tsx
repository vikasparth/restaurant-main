import { useState } from "react";
import { Plus } from "lucide-react";
import { useMenu } from "@/features/menu/hooks/useMenu";
import type { MenuItem } from "@/features/menu/types";
import { useCart } from "@/context/CartContext";
import FoodItemModal from "@/components/FoodItemModal";

const MenuPage = () => {
  const { data: menuData, loading, error } = useMenu();
  const [activeCategory, setActiveCategory] = useState("all");
  const [selectedItem, setSelectedItem] = useState<MenuItem | null>(null);
  const { addItem } = useCart();

  const allItems = menuData?.categories.flatMap((c) => c.items) ?? [];
  const filtered =
    activeCategory === "all" ? allItems : allItems.filter((i) => i.category === activeCategory);
  const categoryNames = menuData?.categories.map((c) => c.name) ?? [];

  if (loading)
    return <div className="container py-12 text-center text-muted-foreground">Loading menu…</div>;
  if (error)
    return (
      <div className="container py-12 text-center text-destructive">
        Failed to load menu. Please try again later.
      </div>
    );

  return (
    <div className="container py-12">
      <h1 className="text-center font-serif text-4xl font-bold text-foreground">
        Aap ki Rasoi Mein
      </h1>
      <p className="mx-auto mt-2 max-w-lg text-center text-muted-foreground">
        Explore our authentic Indian dishes, crafted with love and traditional spices
      </p>

      {/* Categories */}
      <div className="mt-8 flex flex-wrap justify-center gap-2">
        {["all", ...categoryNames].map((name) => (
          <button
            key={name}
            onClick={() => setActiveCategory(name)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
              activeCategory === name
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground hover:bg-primary/10"
            }`}
          >
            {name === "all" ? "All" : name.charAt(0).toUpperCase() + name.slice(1)}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className="mt-10 grid gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {filtered.map((item) => (
          <div
            key={item.id}
            className="group cursor-pointer overflow-hidden rounded-xl border border-border bg-card transition-shadow hover:shadow-lg"
            onClick={() => setSelectedItem(item)}
          >
            <div className="relative overflow-hidden">
              <img
                src={item.image_url}
                alt={item.name}
                className="h-48 w-full object-cover transition-transform group-hover:scale-105"
                loading="lazy"
                width={512}
                height={512}
              />
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  addItem(item);
                }}
                className="absolute bottom-3 right-3 flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-md transition-transform hover:scale-110"
                aria-label={`Add ${item.name} to cart`}
              >
                <Plus className="h-5 w-5" />
              </button>
            </div>
            <div className="p-4">
              <h3 className="font-serif text-base font-semibold text-foreground">{item.name}</h3>
              <p className="mt-1 text-lg font-bold text-primary">${item.price.toFixed(2)}</p>
            </div>
          </div>
        ))}
      </div>

      {selectedItem && <FoodItemModal item={selectedItem} onClose={() => setSelectedItem(null)} />}
    </div>
  );
};

export default MenuPage;
