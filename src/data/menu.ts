import butterChicken from "@/assets/food/butter-chicken.jpg";
import palakPaneer from "@/assets/food/palak-paneer.jpg";
import biryani from "@/assets/food/biryani.jpg";
import samosa from "@/assets/food/samosa.jpg";
import dalMakhani from "@/assets/food/dal-makhani.jpg";
import naan from "@/assets/food/naan.jpg";
import tandooriChicken from "@/assets/food/tandoori-chicken.jpg";
import gulabJamun from "@/assets/food/gulab-jamun.jpg";
import mangoLassi from "@/assets/food/mango-lassi.jpg";
import choleBhature from "@/assets/food/chole-bhature.jpg";
import alooGobi from "@/assets/food/aloo-gobi.jpg";
import masalaDosa from "@/assets/food/masala-dosa.jpg";

export interface MenuItem {
  id: string;
  name: string;
  description: string;
  ingredients: string[];
  price: number;
  image: string;
  category: "appetizers" | "mains" | "breads" | "desserts" | "drinks" | "specials";
  isVegetarian: boolean;
  cateringAvailable: boolean;
  cateringPricePerTray?: number;
}

export const menuItems: MenuItem[] = [
  {
    id: "samosa",
    name: "Samosa",
    description: "Crispy golden pastry stuffed with spiced potatoes and peas, served with mint and tamarind chutney.",
    ingredients: ["Potatoes", "Peas", "Cumin", "Coriander", "Green Chili", "Pastry Dough"],
    price: 6.99,
    image: samosa,
    category: "appetizers",
    isVegetarian: true,
    cateringAvailable: true,
    cateringPricePerTray: 45.99,
  },
  {
    id: "butter-chicken",
    name: "Butter Chicken",
    description: "Tender chicken pieces simmered in a rich, creamy tomato sauce with aromatic spices. Our most beloved dish.",
    ingredients: ["Chicken", "Tomatoes", "Butter", "Cream", "Garam Masala", "Fenugreek"],
    price: 16.99,
    image: butterChicken,
    category: "mains",
    isVegetarian: false,
    cateringAvailable: true,
    cateringPricePerTray: 89.99,
  },
  {
    id: "palak-paneer",
    name: "Palak Paneer",
    description: "Fresh cottage cheese cubes in a velvety spinach gravy, seasoned with garlic and aromatic spices.",
    ingredients: ["Paneer", "Spinach", "Garlic", "Onion", "Cumin", "Cream"],
    price: 14.99,
    image: palakPaneer,
    category: "mains",
    isVegetarian: true,
    cateringAvailable: true,
    cateringPricePerTray: 79.99,
  },
  {
    id: "biryani",
    name: "Chicken Biryani",
    description: "Fragrant basmati rice layered with tender chicken, saffron, and aromatic spices, slow-cooked to perfection.",
    ingredients: ["Basmati Rice", "Chicken", "Saffron", "Cardamom", "Bay Leaf", "Yogurt", "Onion"],
    price: 17.99,
    image: biryani,
    category: "mains",
    isVegetarian: false,
    cateringAvailable: true,
    cateringPricePerTray: 99.99,
  },
  {
    id: "dal-makhani",
    name: "Dal Makhani",
    description: "Creamy black lentils slow-cooked overnight with butter and aromatic spices. A true taste of Punjab.",
    ingredients: ["Black Lentils", "Kidney Beans", "Butter", "Cream", "Tomatoes", "Ginger", "Garlic"],
    price: 13.99,
    image: dalMakhani,
    category: "mains",
    isVegetarian: true,
    cateringAvailable: true,
    cateringPricePerTray: 69.99,
  },
  {
    id: "tandoori-chicken",
    name: "Tandoori Chicken",
    description: "Chicken marinated in yogurt and traditional tandoori spices, roasted in a clay oven until charred and juicy.",
    ingredients: ["Chicken", "Yogurt", "Tandoori Masala", "Lemon", "Ginger", "Garlic"],
    price: 15.99,
    image: tandooriChicken,
    category: "mains",
    isVegetarian: false,
    cateringAvailable: true,
    cateringPricePerTray: 85.99,
  },
  {
    id: "chole-bhature",
    name: "Chole Bhature",
    description: "Spiced chickpea curry served with fluffy deep-fried bread. A classic North Indian comfort meal.",
    ingredients: ["Chickpeas", "Onion", "Tomatoes", "Chole Masala", "Flour", "Yogurt"],
    price: 13.99,
    image: choleBhature,
    category: "mains",
    isVegetarian: true,
    cateringAvailable: true,
    cateringPricePerTray: 74.99,
  },
  {
    id: "aloo-gobi",
    name: "Aloo Gobi",
    description: "Tender potatoes and cauliflower florets cooked with turmeric, cumin, and fresh herbs.",
    ingredients: ["Potatoes", "Cauliflower", "Turmeric", "Cumin", "Tomatoes", "Ginger"],
    price: 12.99,
    image: alooGobi,
    category: "mains",
    isVegetarian: true,
    cateringAvailable: true,
    cateringPricePerTray: 64.99,
  },
  {
    id: "masala-dosa",
    name: "Masala Dosa",
    description: "Crispy fermented rice and lentil crepe filled with spiced potato masala, served with sambar and chutneys.",
    ingredients: ["Rice", "Urad Dal", "Potatoes", "Mustard Seeds", "Curry Leaves", "Turmeric"],
    price: 12.99,
    image: masalaDosa,
    category: "specials",
    isVegetarian: true,
    cateringAvailable: false,
  },
  {
    id: "naan",
    name: "Butter Naan",
    description: "Soft and fluffy leavened bread baked in a tandoor, brushed with melted butter.",
    ingredients: ["Flour", "Yogurt", "Butter", "Yeast"],
    price: 3.99,
    image: naan,
    category: "breads",
    isVegetarian: true,
    cateringAvailable: true,
    cateringPricePerTray: 29.99,
  },
  {
    id: "gulab-jamun",
    name: "Gulab Jamun",
    description: "Golden fried milk dumplings soaked in rose-scented cardamom sugar syrup. A heavenly dessert.",
    ingredients: ["Milk Powder", "Flour", "Cardamom", "Rose Water", "Sugar"],
    price: 7.99,
    image: gulabJamun,
    category: "desserts",
    isVegetarian: true,
    cateringAvailable: true,
    cateringPricePerTray: 49.99,
  },
  {
    id: "mango-lassi",
    name: "Mango Lassi",
    description: "Refreshing yogurt-based drink blended with sweet Alphonso mangoes and a touch of cardamom.",
    ingredients: ["Yogurt", "Mango Pulp", "Sugar", "Cardamom"],
    price: 5.99,
    image: mangoLassi,
    category: "drinks",
    isVegetarian: true,
    cateringAvailable: false,
  },
];

export const categories = [
  { id: "all", label: "All" },
  { id: "appetizers", label: "Appetizers" },
  { id: "mains", label: "Main Course" },
  { id: "breads", label: "Breads" },
  { id: "desserts", label: "Desserts" },
  { id: "drinks", label: "Drinks" },
  { id: "specials", label: "Specials" },
] as const;

export const RESTAURANT_INFO = {
  name: "Aap ki Rasoi",
  phone: "+1234567890",
  whatsapp: "1234567890",
  email: "info@aapkirasoi.com",
  address: "123 Main Street, London, UK",
  facebook: "https://facebook.com/aapkirasoi",
  instagram: "https://instagram.com/aapkirasoi",
  hours: {
    monday: { open: "11:00", close: "22:00" },
    tuesday: { open: "11:00", close: "22:00" },
    wednesday: { open: "11:00", close: "22:00" },
    thursday: { open: "11:00", close: "22:00" },
    friday: { open: "11:00", close: "23:00" },
    saturday: { open: "11:00", close: "23:00" },
    sunday: { open: "12:00", close: "21:00" },
  },
  deliveryRadius: 15,
};
