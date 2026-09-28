import { Route, Routes } from "react-router";
import { HomeRedirect, PublicOnly, RequireAuth, RequireRole } from "./components/guards";
import Layout from "./components/Layout";
import { STAFF_ROLES } from "./labels";
import DeliveriesPage from "./pages/DeliveriesPage";
import LoginPage from "./pages/LoginPage";
import NotFoundPage from "./pages/NotFoundPage";
import OrderDetailPage from "./pages/OrderDetailPage";
import OrderFormPage from "./pages/OrderFormPage";
import OrdersPage from "./pages/OrdersPage";
import RegisterPage from "./pages/RegisterPage";
import UserFormPage from "./pages/UserFormPage";
import UsersPage from "./pages/UsersPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicOnly><LoginPage /></PublicOnly>} />
      <Route path="/cadastro" element={<PublicOnly><RegisterPage /></PublicOnly>} />
      <Route element={<RequireAuth><Layout /></RequireAuth>}>
        <Route index element={<HomeRedirect />} />
        <Route path="pedidos" element={<RequireRole roles={STAFF_ROLES}><OrdersPage /></RequireRole>} />
        <Route path="pedidos/novo" element={<RequireRole roles={STAFF_ROLES}><OrderFormPage /></RequireRole>} />
        <Route path="pedidos/:id" element={<OrderDetailPage />} />
        <Route path="pedidos/:id/editar" element={<RequireRole roles={STAFF_ROLES}><OrderFormPage /></RequireRole>} />
        <Route path="entregas" element={<RequireRole roles={["COURIER"]}><DeliveriesPage /></RequireRole>} />
        <Route path="usuarios" element={<RequireRole roles={["ADMIN"]}><UsersPage /></RequireRole>} />
        <Route path="usuarios/novo" element={<RequireRole roles={["ADMIN"]}><UserFormPage /></RequireRole>} />
        <Route path="usuarios/:id/editar" element={<RequireRole roles={["ADMIN"]}><UserFormPage /></RequireRole>} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
