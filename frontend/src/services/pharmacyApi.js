import axios from "axios";

const pharmacyApi = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
  headers: { "Content-Type": "application/json" },
});

pharmacyApi.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const fetchQueue = async (
  pharmacyId,
  statusFilter = "pending,preparing,ready",
) => {
  const response = await pharmacyApi.get(`/pharmacy/${pharmacyId}/queue`, {
    params: { status: statusFilter },
  });
  return response.data;
};

export const fetchPrescriptionImageUrl = async (prescriptionId) => {
  return `/api/pharmacy/prescriptions/${prescriptionId}/image`;
};

export const advanceStatus = async (prescriptionId, newStatus) => {
  const response = await pharmacyApi.patch(
    `/pharmacy/prescriptions/${prescriptionId}/status`,
    { status: newStatus },
  );
  return response.data;
};

export const fetchPharmacyStats = async (pharmacyId) => {
  const response = await pharmacyApi.get(`/pharmacy/${pharmacyId}/stats`);
  return response.data;
};

export default pharmacyApi;
