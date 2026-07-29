import { NavLink, Outlet } from "react-router-dom";

const linkStyle = ({ isActive }: { isActive: boolean }) => ({
  display: "block",
  padding: "8px 16px",
  textDecoration: "none",
  color: isActive ? "#fff" : "#cbd5e1",
  background: isActive ? "#2563eb" : "transparent",
  borderRadius: 6,
});

export default function AppShell() {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <nav style={{ width: 200, background: "#1e293b", padding: 12, flexShrink: 0 }}>
        <div style={{ color: "#fff", fontWeight: 600, padding: "8px 16px" }}>Customer 360</div>
        <NavLink to="/customers" style={linkStyle}>Customers</NavLink>
        <NavLink to="/dashboard" style={linkStyle}>Dashboard</NavLink>
        <NavLink to="/reports" style={linkStyle}>Reports</NavLink>
      </nav>
      <main style={{ flex: 1, padding: 24 }}>
        <Outlet />
      </main>
    </div>
  );
}
