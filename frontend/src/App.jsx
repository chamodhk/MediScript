import { BrowserRouter, Routes, Route, Navigate } from "react-router";

import LoginPage from "./pages/LoginPage";
import PharmacyPortal from "./pages/PharmacyPortal";
import MediScriptDashboard from "./pages/MediScriptDashboard";
import WritingPad from "./pages/WritingPad";
import AdminPortal from "./pages/AdminPortal";
import MediScriptPrescriptionCanvas from "./pages/MediscriptionCanvas";
import QueuePanel from "./components/pharmacy/QueuePanel";
import DetailPanel from "./components/pharmacy/DetailPanel";
import PharmacyHeader from "./components/pharmacy/PharmacyHeader";
import PrescriptionCard from "./components/pharmacy/PrescriptionCard";
import StatusBadge from "./components/pharmacy/StatusBadge";

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("accessToken");
  if (!token) {
    return <Navigate to="/" replace />;
  }
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminPortal />
            </ProtectedRoute>
          }
        />
        <Route
          path="/doctor"
          element={
            <ProtectedRoute>
              <MediScriptDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/writingpad"
          element={
            <ProtectedRoute>

              <MediScriptPrescriptionCanvas />
            </ProtectedRoute>
          }
        />
        <Route
          path="/pharmacy/1"
          element={
            <ProtectedRoute>
              <PharmacyPortal pharmacyId={1} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/pharmacy/2"
          element={
            <ProtectedRoute>
              <PharmacyPortal pharmacyId={2} />
            </ProtectedRoute>
          }
        />
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
