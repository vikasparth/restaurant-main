import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { CartProvider } from "@/context/CartContext";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import CartSidebar from "@/components/CartSidebar";
import WhatsAppButton from "@/components/WhatsAppButton";
import Index from "./pages/Index";
import MenuPage from "./pages/MenuPage";
import OurStory from "./pages/OurStory";
import ReservationPage from "./pages/ReservationPage";
import OrderPage from "./pages/OrderPage";
import CateringPage from "./pages/CateringPage";
import ContactPage from "./pages/ContactPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <CartProvider>
        <Sonner />
        <BrowserRouter>
          <Navbar />
          <main className="min-h-screen">
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/menu" element={<MenuPage />} />
              <Route path="/our-story" element={<OurStory />} />
              <Route path="/reservation" element={<ReservationPage />} />
              <Route path="/order" element={<OrderPage />} />
              <Route path="/catering" element={<CateringPage />} />
              <Route path="/contact" element={<ContactPage />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
          <Footer />
          <CartSidebar />
          <WhatsAppButton message="Hi Aap ki Rasoi! How can I help you today?" variant="floating" />
        </BrowserRouter>
      </CartProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
