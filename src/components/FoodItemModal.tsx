import { X, Plus, Minus } from "lucide-react";
import { useState } from "react";
import type { MenuItem } from "@/types/menu";
import { useCart } from "@/context/CartContext";

interface FoodItemModalProps {
  item: MenuItem;
  onClose: () => void;
}

const FoodItemModal = ({ item, onClose }: FoodItemModalProps) => {
  const [qty, setQty] = useState(1);
  const { addItem } = useCart();

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/40 p-4" onClick={onClose}>
        <div
          className="relative w-full max-w-lg overflow-hidden rounded-xl bg-background shadow-xl animate-fade-in"
          onClick={(e) => e.stopPropagation()}
        >
          <button onClick={onClose} className="absolute right-3 top-3 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-background/80 hover:bg-secondary" aria-label="Close">
            <X className="h-4 w-4" />
          </button>
          <img src={item.image_url} alt={item.name} className="h-64 w-full object-cover" />
          <div className="p-6">
            <div className="flex items-start justify-between">
              <h2 className="font-serif text-2xl font-bold text-foreground">{item.name}</h2>
              <span className="text-xl font-bold text-primary">${item.price.toFixed(2)}</span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">{item.description}</p>
            <div className="mt-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Allergens</h4>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {item.allergens.map((allergen) => (
                  <span key={allergen} className="rounded-full bg-secondary px-2.5 py-0.5 text-xs text-secondary-foreground">{allergen}</span>
                ))}
              </div>
            </div>
            <div className="mt-6 flex items-center gap-4">
              <div className="flex items-center gap-3 rounded-md border border-border px-2">
                <button onClick={() => setQty(Math.max(1, qty - 1))} className="p-1 hover:text-primary"><Minus className="h-4 w-4" /></button>
                <span className="w-6 text-center font-medium">{qty}</span>
                <button onClick={() => setQty(qty + 1)} className="p-1 hover:text-primary"><Plus className="h-4 w-4" /></button>
              </div>
              <button
                onClick={() => { addItem(item, qty); onClose(); }}
                className="flex-1 rounded-md bg-primary py-2.5 text-sm font-semibold text-primary-foreground hover:opacity-90 transition-colors"
              >
                Add to Cart — ${(item.price * qty).toFixed(2)}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default FoodItemModal;
