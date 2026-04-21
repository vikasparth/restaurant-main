import { X, Plus, Minus, Trash2, MessageCircle } from "lucide-react";
import { useCart } from "@/context/CartContext";
import { useNavigate } from "react-router-dom";
import { RESTAURANT_INFO } from "@/data/menu";

const CartSidebar = () => {
  const { items, removeItem, updateQuantity, totalPrice, isCartOpen, setIsCartOpen } = useCart();
  const navigate = useNavigate();

  if (!isCartOpen) return null;

  return (
    <>
      <div className="fixed inset-0 z-50 bg-foreground/30" onClick={() => setIsCartOpen(false)} />
      <div className="fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col bg-background shadow-xl animate-slide-in-right">
        <div className="flex items-center justify-between border-b border-border p-4">
          <h2 className="font-serif text-lg font-semibold text-foreground">Your Cart</h2>
          <button
            onClick={() => setIsCartOpen(false)}
            className="rounded-full p-1 hover:bg-secondary"
            aria-label="Close cart"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {items.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">Your cart is empty</p>
          ) : (
            <div className="space-y-4">
              {items.map((ci) => (
                <div key={ci.item.id} className="flex gap-3 rounded-lg border border-border p-3">
                  <img
                    src={ci.item.image_url}
                    alt={ci.item.name}
                    className="h-16 w-16 rounded-md object-cover"
                    loading="lazy"
                  />
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-foreground">{ci.item.name}</h3>
                    <p className="text-sm font-semibold text-primary">
                      ${ci.item.price.toFixed(2)}
                    </p>
                    <div className="mt-1 flex items-center gap-2">
                      <button
                        onClick={() => updateQuantity(ci.item.id, ci.quantity - 1)}
                        className="flex h-6 w-6 items-center justify-center rounded border border-border hover:bg-secondary"
                      >
                        <Minus className="h-3 w-3" />
                      </button>
                      <span className="text-sm font-medium">{ci.quantity}</span>
                      <button
                        onClick={() => updateQuantity(ci.item.id, ci.quantity + 1)}
                        className="flex h-6 w-6 items-center justify-center rounded border border-border hover:bg-secondary"
                      >
                        <Plus className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => removeItem(ci.item.id)}
                        className="ml-auto text-destructive hover:opacity-70"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {items.length > 0 && (
          <div className="border-t border-border p-4 space-y-3">
            <div className="flex justify-between text-lg font-semibold">
              <span>Total</span>
              <span className="text-primary">${totalPrice.toFixed(2)}</span>
            </div>
            <button
              onClick={() => {
                setIsCartOpen(false);
                navigate("/order");
              }}
              className="w-full rounded-md bg-primary py-3 text-sm font-semibold text-primary-foreground transition-colors hover:opacity-90"
            >
              Checkout
            </button>
            <a
              href={`https://wa.me/${RESTAURANT_INFO.whatsapp}?text=${encodeURIComponent("Hi Aap ki Rasoi! I have a question about my order...")}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex w-full items-center justify-center gap-2 text-sm text-muted-foreground hover:text-foreground"
            >
              <MessageCircle className="h-4 w-4" />
              Have questions? Chat on WhatsApp
            </a>
          </div>
        )}
      </div>
    </>
  );
};

export default CartSidebar;
