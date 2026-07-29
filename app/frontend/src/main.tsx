import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Customers from "./pages/Customers";
import CustomerDetail from "./pages/CustomerDetail";
import Dashboard from "./pages/Dashboard";
import Reports from "./pages/Reports";
import AppShell from "./components/AppShell";
import GenieWidget from "./components/GenieWidget";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<Navigate to="/customers" replace />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/customers/:id" element={<CustomerDetail />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/reports" element={<Reports />} />
          </Route>
        </Routes>
        <GenieWidget />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
