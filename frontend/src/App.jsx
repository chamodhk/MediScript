import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import LoginPage from "./pages/LoginPage";
import DoctorPortal from "./pages/DoctorPortal";
import PharmacyPortal from "./pages/PharmacyPortal";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/doctor" element={<DoctorPortal />} />
        <Route path="/pharmacy/1" element={<PharmacyPortal pharmacyId={1} />} />
        <Route path="/pharmacy/2" element={<PharmacyPortal pharmacyId={2} />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
