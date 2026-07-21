import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/auth": "http://127.0.0.1:8000"
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          const normalized = id.replace(/\\/g, "/");
          if (normalized.includes("/node_modules/react") || normalized.includes("/node_modules/react-dom") || normalized.includes("/node_modules/react-router-dom")) return "react";
          if (normalized.includes("/node_modules/lucide-react")) return "icons";
          if (normalized.includes("/src/pages/PatientJourneyWorkspace") || normalized.includes("/src/components/program2")) return "journey-workspace";
          if (normalized.includes("/src/program1")) return "program1";
          if (normalized.includes("/src/pages/Inventory") || normalized.includes("/src/pages/Invoices") || normalized.includes("/src/pages/PurchaseOrders") || normalized.includes("/src/pages/Suppliers")) return "operations-pages";
        }
      }
    }
  }
});
