import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router";
import {
  RotateCcw,
  RotateCw,
  Trash2,
  PenTool,
  Eraser,
  Pill,
  Stethoscope,
  Printer,
  FileDown,
  CheckCircle2,
  User,
  ArrowLeft,
  Activity,
  Circle,
  Mic,
  Square,
} from "lucide-react";
import api from "../services/api";
import { useAudioRecorder } from "../hooks/useAudioRecorder";

const clinicalPhrases = [
  "Get plenty of rest",
  "Report any unusual symptoms",
  "Avoid alcohol",
  "Seek medical attention if worsens",
];

// Normalize patient object regardless of which field names the API uses
const normalizePatient = (raw) => {
  if (!raw) return null;
  return {
    full_name:
      raw.full_name ||
      raw.name ||
      raw.patient_name ||
      raw.fullName ||
      "",
    age:
      raw.age ||
      raw.patient_age ||
      raw.patientAge ||
      "",
    sex:
      raw.sex ||
      raw.gender ||
      raw.patient_gender ||
      "",
    id:
      raw.id ||
      raw.patient_id ||
      raw.patientId ||
      "",
    allergies:
      raw.allergies ||
      raw.allergy_list ||
      raw.allergyList ||
      [],
  };
};

export default function MediScriptPrescriptionCanvas() {
  const navigate = useNavigate();
  const [tool, setTool] = useState("pen");
  const [brushColor, setBrushColor] = useState("#111827");
  const [brushSize, setBrushSize] = useState(6);
  const [palmRejection, setPalmRejection] = useState(true);
  const [canvasMode, setCanvasMode] = useState("standard");
  const [addedMeds, setAddedMeds] = useState([]);
  const [savedImage, setSavedImage] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [savedPrescriptionId, setSavedPrescriptionId] = useState(null);
  const [doctorInfo, setDoctorInfo] = useState({
    full_name: "Dr. [Name]",
    role: "[Specialty]",
  });
  const [patientInfo, setPatientInfo] = useState(null);
  const [consultationId, setConsultationId] = useState(null);
  const [pharmacyId] = useState(1);
  const [recordingTime, setRecordingTime] = useState(0);
  const [transcriptStatus, setTranscriptStatus] = useState(null);
  const [isLoadingTranscript, setIsLoadingTranscript] = useState(false);

  // ── Audio Recording Hook ──────────────────────────────────────────────────
  const { isRecording, audioBlob, startRecording: recordStart, stopRecording: recordStop, setAudioBlob } = useAudioRecorder();

  const canvasRef = useRef(null);
  const isDrawingRef = useRef(false);
  const lastPointRef = useRef({ x: 0, y: 0 });
  const undoStackRef = useRef([]);
  const redoStackRef = useRef([]);
  const palmRejectionRef = useRef(palmRejection);
  const recordingIntervalRef = useRef(null);

  const colors = useMemo(() => ["#111827", "#1d4ed8", "#e11d48"], []);
  const sizes = useMemo(() => [4, 6, 10], []);

  // Keep palm rejection ref in sync
  useEffect(() => {
    palmRejectionRef.current = palmRejection;
  }, [palmRejection]);

  // ── Fetch doctor info ──────────────────────────────────────────────────────
  useEffect(() => {
    const fetchDoctorInfo = async () => {
      try {
        const response = await api.get("/auth/me");
        setDoctorInfo({
          full_name: response.data.full_name || "Dr. [Name]",
          role: response.data.role || "[Specialty]",
        });
      } catch (error) {
        console.error("Failed to fetch doctor info:", error);
      }
    };
    fetchDoctorInfo();
  }, []);

  // ── Load consultation ID ───────────────────────────────────────────────────
  useEffect(() => {
    try {
      const savedConsultationId = localStorage.getItem("currentConsultationId");
      if (savedConsultationId) {
        setConsultationId(parseInt(savedConsultationId, 10));
      }
    } catch (error) {
      console.error("Failed to load consultation ID:", error);
    }
  }, []);

  // ── Load patient info (fixed) ──────────────────────────────────────────────
  // Strategy:
  //   1. Try localStorage key "currentPatient" (normalize field names)
  //   2. Fallback: fetch from API using consultationId
  useEffect(() => {
    const loadPatient = async () => {
      // Step 1 — localStorage
      try {
        const raw = localStorage.getItem("currentPatient");
        if (raw) {
          const parsed = JSON.parse(raw);
          const normalized = normalizePatient(parsed);
          if (normalized && normalized.full_name) {
            setPatientInfo(normalized);
            return; // done — no need for API call
          }
        }
      } catch (error) {
        console.error("Failed to parse currentPatient from localStorage:", error);
      }

      // Step 2 — API fallback using consultationId
      const rawConsultationId = localStorage.getItem("currentConsultationId");
      if (!rawConsultationId) return;

      try {
        // Try a few common endpoint patterns; adjust to match your backend
        const res = await api.get(
          `/consultations/${rawConsultationId}/patient`
        );
        const normalized = normalizePatient(res.data);
        if (normalized) {
          setPatientInfo(normalized);
          // Cache for next time
          localStorage.setItem("currentPatient", JSON.stringify(res.data));
        }
      } catch {
        // Try alternative endpoint shape
        try {
          const res2 = await api.get(
            `/consultations/${rawConsultationId}`
          );
          const patient =
            res2.data?.patient || res2.data?.patientInfo || res2.data;
          const normalized = normalizePatient(patient);
          if (normalized) setPatientInfo(normalized);
        } catch (err2) {
          console.error("All patient fetch attempts failed:", err2);
        }
      }
    };

    loadPatient();
  }, []); // runs once on mount — consultationId from localStorage directly

  // ── Canvas setup & resize ──────────────────────────────────────────────────
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resizeCanvas = () => {
      const parent = canvas.parentElement;
      const rect = parent.getBoundingClientRect();
      const oldImage =
        canvas.width > 0 && canvas.height > 0
          ? canvas.toDataURL("image/png")
          : null;

      canvas.width = Math.max(900, Math.floor(rect.width - 8));
      canvas.height = 640;

      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      if (oldImage && oldImage !== "data:,") {
        const img = new Image();
        img.onload = () =>
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        img.src = oldImage;
      }
    };

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);
    saveCanvasState();
    // Don't load latest prescription here - defer until consultationId is available
    // loadLatestPrescription();

    return () => window.removeEventListener("resize", resizeCanvas);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Load latest prescription when consultationId is available ────────────────
  useEffect(() => {
    if (consultationId) {
      loadLatestPrescription();
    }
  }, [consultationId]);

  // ── Drawing helpers ────────────────────────────────────────────────────────
  const getCoordinates = (event) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    if (event.touches && event.touches.length > 0) {
      return {
        x: (event.touches[0].clientX - rect.left) * scaleX,
        y: (event.touches[0].clientY - rect.top) * scaleY,
      };
    }

    return {
      x: (event.clientX - rect.left) * scaleX,
      y: (event.clientY - rect.top) * scaleY,
    };
  };

  const saveCanvasState = () => {
    const canvas = canvasRef.current;
    if (!canvas || canvas.width === 0 || canvas.height === 0) return;
    const imageData = canvas.toDataURL("image/png");
    undoStackRef.current.push(imageData);
    if (undoStackRef.current.length > 20) undoStackRef.current.shift();
  };

  const restoreCanvasState = (imageData) => {
    const canvas = canvasRef.current;
    if (!canvas || !imageData) return;
    const ctx = canvas.getContext("2d");
    const img = new Image();
    img.onload = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    };
    img.src = imageData;
  };

  // ── Palm rejection ─────────────────────────────────────────────────────────
  const isPalmTouch = (event) => {
    if (!palmRejectionRef.current) return false;
    if (event.touches && event.touches.length > 1) return true;
    if (event.touches && event.touches.length === 1) {
      const touch = event.touches[0];
      if (touch.radiusX && touch.radiusY) {
        if (touch.radiusX > 30 || touch.radiusY > 30) return true;
      }
    }
    return false;
  };

  const startDrawing = (event) => {
    event.preventDefault();
    if (isPalmTouch(event)) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const { x, y } = getCoordinates(event);

    isDrawingRef.current = true;
    lastPointRef.current = { x, y };

    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (event) => {
    if (!isDrawingRef.current) return;
    event.preventDefault();
    if (isPalmTouch(event)) {
      stopDrawing();
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const { x, y } = getCoordinates(event);

    ctx.lineWidth = brushSize;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = tool === "eraser" ? "#ffffff" : brushColor;

    ctx.beginPath();
    ctx.moveTo(lastPointRef.current.x, lastPointRef.current.y);
    ctx.lineTo(x, y);
    ctx.stroke();

    lastPointRef.current = { x, y };
  };

  const stopDrawing = () => {
    if (!isDrawingRef.current) return;
    isDrawingRef.current = false;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    ctx.beginPath();

    saveCanvasState();
    redoStackRef.current = [];
  };

  // ── Recording Handlers (using useAudioRecorder hook) ────────────────────────
  const sendAudioToBackend = async (audioData) => {
    if (!audioData || !consultationId) {
      console.warn("⚠️ Cannot send audio - Missing audioData or consultationId", {
        hasAudioData: !!audioData,
        consultationId
      });
      return;
    }

    setIsLoadingTranscript(true);
    const audioSize = (audioData.size / 1024 / 1024).toFixed(2);

    console.log("🎤 AUDIO UPLOAD STARTED", {
      consultationId,
      audioFormat: audioData.type,
      audioSize: `${audioSize} MB`,
      timestamp: new Date().toLocaleTimeString()
    });

    try {
      const formData = new FormData();
      formData.append("audio", audioData, "recording.webm");

      const response = await api.post(
        `/transcription/transcribe/${consultationId}`,
        formData
      );

      console.log("✅ BACKEND RESPONSE RECEIVED", {
        status: response.status,
        hasTranscript: !!response.data.raw_transcript,
        transcriptLength: response.data.raw_transcript?.length || 0,
        hasStructured: !!response.data.structured,
        timestamp: new Date().toLocaleTimeString()
      });

      if (response.data.raw_transcript) {
        setTranscriptStatus(response.data);
        alert("✅ Transcription successful! Check console for details.");
      }
    } catch (error) {
      console.error("❌ TRANSCRIPTION ERROR", {
        errorMessage: error.message,
        statusCode: error.response?.status,
        detail: error.response?.data?.detail,
        timestamp: new Date().toLocaleTimeString()
      });
      alert(`Transcription failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsLoadingTranscript(false);
      setAudioBlob(null);
    }
  };

  const startRecording = async () => {
    setRecordingTime(0);
    recordingIntervalRef.current = setInterval(() => setRecordingTime(t => t + 1), 1000);
    await recordStart();
  };

  const stopRecording = async () => {
    clearInterval(recordingIntervalRef.current);
    await recordStop();
  };

  // ── Send audio to backend when recording completes ──────────────────────────
  useEffect(() => {
    if (audioBlob && !isRecording && consultationId && !isLoadingTranscript) {
      sendAudioToBackend(audioBlob);
    }
  }, [audioBlob, isRecording, consultationId, isLoadingTranscript]);

  // ── Old Recording Handlers (COMMENTED OUT - use useAudioRecorder hook instead) ──────────────────
  /* 
  // const startRecording = async () => {
  //   try {
  //     const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  //     const mediaRecorder = new MediaRecorder(stream);
  //     mediaRecorderRef.current = mediaRecorder;
  //     audioChunksRef.current = [];
  //     
  //     mediaRecorder.ondataavailable = (event) => {
  //       audioChunksRef.current.push(event.data);
  //     };
  //     
  //     mediaRecorder.onstop = () => {
  //       const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
  //       const audioUrl = URL.createObjectURL(audioBlob);
  //       console.log('Recording saved:', audioUrl);
  //     };
  //     
  //     mediaRecorder.start();
  //     setIsRecording(true);
  //     setRecordingTime(0);
  //     
  //     recordingIntervalRef.current = setInterval(() => {
  //       setRecordingTime((prev) => prev + 1);
  //     }, 1000);
  //   } catch (error) {
  //     console.error('Error accessing microphone:', error);
  //     alert('Unable to access microphone. Please check permissions.');
  //   }
  // };

  // const stopRecording = () => {
  //   if (mediaRecorderRef.current && isRecording) {
  //     mediaRecorderRef.current.stop();
  //     mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
  //     setIsRecording(false);
  //     if (recordingIntervalRef.current) {
  //       clearInterval(recordingIntervalRef.current);
  //     }
  //   }
  // };
  */

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // ── Actions ────────────────────────────────────────────────────────────────
  const handleUndo = () => {
    if (undoStackRef.current.length <= 1) return;
    const currentState = undoStackRef.current.pop();
    redoStackRef.current.push(currentState);
    restoreCanvasState(
      undoStackRef.current[undoStackRef.current.length - 1]
    );
  };

  const handleRedo = () => {
    if (redoStackRef.current.length === 0) return;
    const redoState = redoStackRef.current.pop();
    undoStackRef.current.push(redoState);
    restoreCanvasState(redoState);
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    saveCanvasState();
    redoStackRef.current = [];
    setSavedImage("");
  };

  const loadLatestPrescription = async () => {
    // Use state variable instead of localStorage
    if (!consultationId) return;
    
    try {
      const response = await api.get(`/prescriptions/session/${consultationId}`);
      
      if (Array.isArray(response.data) && response.data.length > 0) {
        const latest = response.data[0];
        setSavedPrescriptionId(latest.id ?? null);
        if (latest.image_data_b64) {
          setSavedImage(latest.image_data_b64);
          restoreCanvasState(latest.image_data_b64);
        }
      }
    } catch (error) {
      console.error("Load prescriptions error:", error.message);
    }
  };

  const handleValidateHandwriting = async () => {
    const imageData = canvasRef.current.toDataURL("image/png");
    setIsValidating(true);
    try {
      const response = await api.post("/prescriptions/validate", {
        image_data: imageData,
      });
      
      console.log("✅ Validation result:", response.data);
      alert("✅ Handwriting validated successfully! Check console for details.");
    } catch (error) {
      console.error("❌ Validation error:", {
        errorMessage: error.message,
        statusCode: error.response?.status,
        detail: error.response?.data?.detail,
      });
      
      const errorDetail = error.response?.data?.detail || error.message || "Unknown error";
      alert(`Failed to validate handwriting: ${errorDetail}`);
    } finally {
      setIsValidating(false);
    }
  };

  const handleSavePrescription = async () => {
    // Use state variable instead of localStorage for reliability
    if (!consultationId) {
      alert(
        "Consultation ID not found. Please return to dashboard and reload patient."
      );
      return;
    }
    
    const imageData = canvasRef.current.toDataURL("image/png");
    setIsSaving(true);
    
    try {
      const response = await api.post("/prescriptions/prescription", {
        consultation_id: consultationId,
        pharmacy_id: pharmacyId,
        image_data: imageData,
        image_mime_type: "image/png",
      });
      
      if (response.data) {
        setSavedPrescriptionId(response.data.id ?? null);
        setSavedImage(response.data.image_data_b64 || imageData);
        alert("✅ Prescription saved successfully!");
        navigate("/doctor");
      }
    } catch (error) {
      console.error("❌ Save prescription error:", {
        errorMessage: error.message,
        statusCode: error.response?.status,
        detail: error.response?.data?.detail,
        timestamp: new Date().toLocaleTimeString()
      });
      
      const errorDetail = error.response?.data?.detail || error.message || "Unknown error";
      alert(`Failed to save prescription: ${errorDetail}`);
    } finally {
      setIsSaving(false);
    }
  };

  const isFocus = canvasMode === "focus";

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#f4f6f8] text-slate-900">

      {/* Standard header */}
      {!isFocus && (
        <header className="border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-3 font-semibold text-blue-600">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm">
                  <Activity className="h-5 w-5" />
                </div>
                <span className="text-2xl">MediScript Pro</span>
              </div>

              <nav className="hidden items-center gap-3 md:flex">
                <button className="rounded-xl px-4 py-2 text-slate-600 hover:bg-slate-100" onClick={() => navigate("/doctor")}>
                  Dashboard
                </button>
                <button className="rounded-xl bg-blue-50 px-4 py-2 font-medium text-blue-600">
                  Prescription Canvas
                </button>
              </nav>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
                <div className="text-right leading-tight">
                  <p className="font-semibold">{doctorInfo.full_name}</p>
                  <p className="text-xs uppercase tracking-wide text-slate-500">
                    {doctorInfo.role}
                  </p>
                </div>
                <div className="relative">
                  <div className="flex h-11 w-11 items-center justify-center rounded-full bg-slate-200">
                    <User className="h-5 w-5 text-slate-600" />
                  </div>
                  <span className="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white bg-emerald-500" />
                </div>
              </div>
            </div>
          </div>
        </header>
      )}

      {/* Focus mode minimal bar */}
      {isFocus && (
        <div className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3 shadow-sm">
          <div className="flex items-center gap-3 font-semibold text-blue-600">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
              <Activity className="h-4 w-4" />
            </div>
            <span className="text-lg">MediScript — Focus Mode</span>
          </div>
          <button
            onClick={() => setCanvasMode("standard")}
            className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
          >
            Exit Focus
          </button>
        </div>
      )}

      <main
        className={`grid min-h-[calc(100vh-88px)] gap-6 p-6 ${
          isFocus
            ? "grid-cols-1"
            : "grid-cols-1 xl:grid-cols-[290px_minmax(0,1fr)]"
        }`}
      >
        {/* ── Sidebar ── */}
        {!isFocus && (
          <aside className="space-y-5">

            {/* Patient Info card */}
            <div className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
              <div className="mb-4 flex items-start justify-between">
                <h3 className="text-2xl font-bold">Patient Info</h3>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                  Active Session
                </span>
              </div>

              {/* Loading state */}
              {!patientInfo && (
                <p className="text-sm text-slate-400 italic">
                  Loading patient data…
                </p>
              )}

              {patientInfo && (
                <div className="space-y-4 text-sm">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                      Full Name
                    </p>
                    <p className="mt-1 text-lg font-semibold">
                      {patientInfo.full_name || "—"}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3 border-t border-slate-200 pt-4">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        Age
                      </p>
                      <p className="mt-1 font-semibold">
                        {patientInfo.age && patientInfo.sex
                          ? `${patientInfo.age}Y / ${patientInfo.sex}`
                          : patientInfo.age
                          ? `${patientInfo.age}Y`
                          : patientInfo.sex
                          ? patientInfo.sex
                          : "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        ID
                      </p>
                      <p className="mt-1 font-semibold">
                        {patientInfo.id ? `#${patientInfo.id}` : "—"}
                      </p>
                    </div>
                  </div>

                  <div className="border-t border-slate-200 pt-4">
                    <p className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <Circle className="h-3 w-3 fill-rose-500 text-rose-500" />
                      Critical Allergies
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {patientInfo.allergies &&
                      patientInfo.allergies.length > 0 ? (
                        patientInfo.allergies.map((allergy, idx) => (
                          <span
                            key={idx}
                            className="rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-700"
                          >
                            {allergy}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-500">
                          No allergies recorded
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Last prescription */}
            <div className="rounded-3xl bg-[#f7fbff] p-5 shadow-sm ring-1 ring-slate-200">
              <div className="mb-4 flex items-center gap-2 font-semibold">
                <Stethoscope className="h-4 w-4 text-blue-600" />
                Last Prescription
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4">
                <p className="font-semibold text-slate-500">
                  No previous prescriptions
                </p>
              </div>
            </div>

            {/* Clinical phrases */}
            <div className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
              <h4 className="mb-4 text-lg font-semibold">Clinical Phrases</h4>
              <div className="space-y-3">
                {clinicalPhrases.map((phrase) => (
                  <button
                    key={phrase}
                    className="w-full rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-left text-sm font-medium text-slate-700 transition hover:border-blue-300 hover:bg-blue-50"
                  >
                    {phrase}
                  </button>
                ))}
              </div>
            </div>
          </aside>
        )}

        {/* ── Canvas Section ── */}
        <section className="space-y-5">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div>
              {!isFocus && (
                <button className="mb-2 flex items-center gap-2 text-sm font-medium text-blue-600">
                  <ArrowLeft className="h-4 w-4" />
                  Return to Session Note
                </button>
              )}
              <h1 className="text-5xl font-bold tracking-tight text-slate-900">
                Prescription Canvas
              </h1>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => setPalmRejection((v) => !v)}
                className={`rounded-xl px-4 py-3 text-sm font-semibold shadow-sm transition ${
                  palmRejection
                    ? "bg-blue-600 text-white"
                    : "bg-white text-slate-700 ring-1 ring-slate-200"
                }`}
                title={
                  palmRejection
                    ? "Palm Rejection is ON — multi-touch blocked"
                    : "Palm Rejection is OFF"
                }
              >
                {palmRejection
                  ? "🤚 Palm Rejection: ON"
                  : "🤚 Palm Rejection: OFF"}
              </button>

              <button
                onClick={() =>
                  setCanvasMode((prev) =>
                    prev === "standard" ? "focus" : "standard"
                  )
                }
                className={`rounded-xl px-4 py-3 text-sm font-semibold shadow-sm transition ${
                  isFocus
                    ? "bg-slate-800 text-white"
                    : "bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-slate-50"
                }`}
                title={
                  isFocus
                    ? "Exit Focus Mode"
                    : "Enter Focus Mode — hides sidebar and header"
                }
              >
                {isFocus ? "⛶ Exit Focus" : "⛶ Focus Mode"}
              </button>
            </div>
          </div>

          {/* Toolbar */}
          <div className="rounded-[28px] bg-white p-4 shadow-sm ring-1 ring-slate-200">
            <div className="flex flex-col gap-4 2xl:flex-row 2xl:items-center 2xl:justify-between">
              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={() => setTool("pen")}
                  className={`flex min-w-[88px] flex-col items-center rounded-2xl px-4 py-3 text-xs font-semibold ${
                    tool === "pen"
                      ? "bg-blue-50 text-blue-600"
                      : "bg-slate-50 text-slate-500"
                  }`}
                >
                  <PenTool className="mb-1 h-4 w-4" />
                  PEN
                </button>

                <button
                  onClick={() => setTool("eraser")}
                  className={`flex min-w-[88px] flex-col items-center rounded-2xl px-4 py-3 text-xs font-semibold ${
                    tool === "eraser"
                      ? "bg-blue-50 text-blue-600"
                      : "bg-slate-50 text-slate-500"
                  }`}
                >
                  <Eraser className="mb-1 h-4 w-4" />
                  ERASER
                </button>

                <div className="mx-2 hidden h-12 w-px bg-slate-200 md:block" />

                <div className="flex items-center gap-3">
                  {colors.map((color) => (
                    <button
                      key={color}
                      onClick={() => setBrushColor(color)}
                      className="rounded-full"
                      aria-label={`Select ${color}`}
                    >
                      <span
                        className={`block h-10 w-10 rounded-full border-4 ${
                          brushColor === color
                            ? "border-slate-800/90"
                            : "border-transparent"
                        }`}
                        style={{ backgroundColor: color }}
                      />
                    </button>
                  ))}
                </div>

                <div className="mx-2 hidden h-12 w-px bg-slate-200 md:block" />

                <div className="flex items-center gap-3">
                  {sizes.map((size) => (
                    <button
                      key={size}
                      onClick={() => setBrushSize(size)}
                      className={`flex h-11 w-11 items-center justify-center rounded-2xl ${
                        brushSize === size
                          ? "bg-slate-100 ring-2 ring-blue-200"
                          : "bg-slate-50"
                      }`}
                    >
                      <span
                        className="rounded-full bg-slate-900"
                        style={{ width: size, height: size }}
                      />
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={handleUndo}
                  className="rounded-2xl bg-slate-50 p-3 text-slate-600 ring-1 ring-slate-200 transition hover:bg-slate-100"
                >
                  <RotateCcw className="h-5 w-5" />
                </button>

                <button
                  onClick={handleRedo}
                  className="rounded-2xl bg-slate-50 p-3 text-slate-600 ring-1 ring-slate-200 transition hover:bg-slate-100"
                >
                  <RotateCw className="h-5 w-5" />
                </button>

                <button
                  onClick={clearCanvas}
                  className="flex items-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold text-rose-500 hover:bg-rose-50"
                >
                  <Trash2 className="h-4 w-4" />
                  Clear Canvas
                </button>

                <button
                  onClick={handleValidateHandwriting}
                  disabled={isValidating}
                  className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:opacity-50"
                >
                  {isValidating ? "Validating..." : "Validate Handwriting"}
                </button>
              </div>
            </div>
          </div>

          {/* Palm rejection indicator */}
          {palmRejection && (
            <div className="flex items-center gap-2 rounded-xl bg-blue-50 px-4 py-2 text-xs font-medium text-blue-700 ring-1 ring-blue-200">
              <span className="inline-block h-2 w-2 rounded-full bg-blue-500" />
              Palm rejection active — simultaneous multi-touch contacts will be
              ignored
            </div>
          )}

          {/* Canvas card */}
          <div className="rounded-[32px] bg-white shadow-xl ring-1 ring-slate-200">
            <div className="grid grid-cols-1 gap-6 p-4 lg:grid-cols-[minmax(0,1fr)_220px]">
              <div className="relative min-h-[760px] rounded-[28px] border border-slate-200 bg-white p-4">
                <div className="mb-4 inline-flex rounded-full bg-blue-50 px-4 py-2 text-xs font-semibold text-blue-600">
                  PRESCRIPTION_SERIAL: #PS-2023-99812-TX
                </div>

                <div className="relative rounded-[24px] bg-white">
                  <canvas
                    ref={canvasRef}
                    className="block w-full rounded-[24px] border border-slate-200 bg-white cursor-crosshair touch-none"
                    onMouseDown={startDrawing}
                    onMouseMove={draw}
                    onMouseUp={stopDrawing}
                    onMouseLeave={stopDrawing}
                    onTouchStart={startDrawing}
                    onTouchMove={draw}
                    onTouchEnd={stopDrawing}
                  />
                </div>

                <div className="mt-4 flex flex-wrap gap-3">
                  {addedMeds.map((med, index) => (
                    <div
                      key={`${med.name}-${index}`}
                      className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4 text-sm font-medium shadow-sm"
                    >
                      <span className="mr-2 font-bold text-slate-400">Rx</span>
                      {med.name}{" "}
                      <span className="text-slate-500">{med.dose}</span>
                    </div>
                  ))}
                </div>

                <button className="absolute bottom-5 left-5 rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-4 font-semibold text-slate-700 transition hover:border-blue-300 hover:bg-blue-50">
                  + Add Signature Stamp
                </button>
              </div>

              {/* Recording sidebar */}
              <div className="space-y-4">
                <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                  <p className="mb-4 text-xs font-semibold uppercase tracking-[0.18em] text-blue-400">
                    Voice Recording & Transcription
                  </p>
                  
                  {isRecording && (
                    <div className="mb-4 rounded-xl bg-red-50 px-3 py-2 text-center">
                      <p className="text-sm font-semibold text-red-600">
                        {formatTime(recordingTime)}
                      </p>
                      <p className="mt-1 flex items-center justify-center gap-2 text-xs text-red-600">
                        <span className="animate-pulse inline-block h-2 w-2 rounded-full bg-red-600" />
                        Recording...
                      </p>
                    </div>
                  )}

                  {isLoadingTranscript && (
                    <div className="mb-4 rounded-xl bg-blue-50 px-3 py-2 text-center">
                      <p className="text-sm font-semibold text-blue-600">
                        Processing...
                      </p>
                      <p className="mt-1 flex items-center justify-center gap-2 text-xs text-blue-600">
                        <span className="animate-pulse inline-block h-2 w-2 rounded-full bg-blue-600" />
                        Sending to transcription
                      </p>
                    </div>
                  )}

                  {transcriptStatus && !isLoadingTranscript && (
                    <div className="mb-4 rounded-xl bg-green-50 px-3 py-2 text-center">
                      <p className="text-xs font-semibold text-green-700">
                        ✅ Transcription Complete
                      </p>
                      <p className="mt-2 max-h-20 overflow-y-auto text-xs text-green-700 bg-white rounded px-2 py-1">
                        {transcriptStatus.raw_transcript?.substring(0, 100)}...
                      </p>
                    </div>
                  )}
                  
                  {!isRecording && !isLoadingTranscript ? (
                    <button
                      onClick={startRecording}
                      className="flex w-full items-center justify-center gap-2 rounded-2xl bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700"
                    >
                      <Mic className="h-4 w-4" />
                      Start Recording
                    </button>
                  ) : isRecording ? (
                    <button
                      onClick={stopRecording}
                      className="flex w-full items-center justify-center gap-2 rounded-2xl bg-red-600 px-4 py-3 font-semibold text-white transition hover:bg-red-700"
                    >
                      <Square className="h-4 w-4" />
                      Stop Recording
                    </button>
                  ) : (
                    <button
                      disabled
                      className="flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-300 px-4 py-3 font-semibold text-white cursor-not-allowed"
                    >
                      <Mic className="h-4 w-4" />
                      Processing...
                    </button>
                  )}
                </div>
              </div>


            </div>

            {/* Footer actions */}
            <div className="flex flex-col gap-4 border-t border-slate-200 px-5 py-5 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex flex-wrap items-center gap-6 text-sm text-slate-600">
                <span>Session: #RH-Henderson-Active</span>
                {savedPrescriptionId && (
                  <span>Prescription ID: #{savedPrescriptionId}</span>
                )}

                <button className="flex items-center gap-2 font-medium hover:text-slate-900">
                  <Printer className="h-4 w-4" />
                  Print Script
                </button>

                <button className="flex items-center gap-2 font-medium hover:text-slate-900">
                  <FileDown className="h-4 w-4" />
                  Export PDF
                </button>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={clearCanvas}
                  className="rounded-2xl border border-slate-300 bg-white px-6 py-3 font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  Discard Changes
                </button>

                <button
                  onClick={() => navigate("/writingpad")}
                  className="rounded-2xl border border-slate-300 bg-white px-6 py-3 font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  Writing Pad
                </button>

                <button
                  onClick={handleSavePrescription}
                  disabled={isSaving}
                  className="flex items-center gap-2 rounded-2xl bg-blue-600 px-6 py-3 font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:opacity-50"
                >
                  <CheckCircle2 className="h-5 w-5" />
                  {isSaving
                    ? "Saving..."
                    : "Save & Attach to Patient Record"}
                </button>
              </div>
            </div>
          </div>

          {/* Saved canvas preview */}
          {savedImage && (
            <div className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
              <h3 className="mb-4 text-lg font-semibold">
                Saved Canvas Preview
              </h3>
              <img
                src={savedImage}
                alt="Saved prescription canvas"
                className="max-h-[320px] rounded-2xl border border-slate-200"
              />
            </div>
          )}
        </section>
      </main>
    </div>
  );
}