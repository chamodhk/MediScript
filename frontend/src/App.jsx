import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import LoginPage from "./pages/LoginPage";
import PharmacyPortal from "./pages/PharmacyPortal";
import MediScriptDashboard from "./pages/MediScriptDashboard";
import WritingPad from "./pages/WritingPad";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/doctor" element={<MediScriptDashboard/>} />
        <Route path="/pharmacy/1" element={<PharmacyPortal pharmacyId={1} />} />
        <Route path="/pharmacy/2" element={<PharmacyPortal pharmacyId={2} />} />
        <Route path="/writing-pad" element={<WritingPad />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
