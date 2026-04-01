import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Search,
  Bell,
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
} from "lucide-react";

const quickInsertData = [
  { name: "Amoxicillin", dose: "500mg" },
  { name: "Lisinopril", dose: "20mg" },
  { name: "Metformin", dose: "500mg" },
  { name: "Ibuprofen", dose: "400mg" },
];

const clinicalPhrases = [
  "Take with meals",
  "Finish full course",
  "Avoid alcohol",
  "Monitor BP daily",
];

export default function MediScriptPrescriptionCanvas() {
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

  const canvasRef = useRef(null);
  const isDrawingRef = useRef(false);
  const lastPointRef = useRef({ x: 0, y: 0 });
  const undoStackRef = useRef([]);
  const redoStackRef = useRef([]);

  const CONSULTATION_ID = 1;
  const PHARMACY_ID = 1;
  const API_BASE = "http://127.0.0.1:8000";

  const colors = useMemo(() => ["#111827", "#1d4ed8", "#e11d48"], []);
  const sizes = useMemo(() => [4, 6, 10], []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resizeCanvas = () => {
      const parent = canvas.parentElement;
      const rect = parent.getBoundingClientRect();
      const oldImage = canvas.width > 0 && canvas.height > 0 ? canvas.toDataURL("image/png") : null;

      canvas.width = Math.max(900, Math.floor(rect.width - 8));
      canvas.height = 640;

      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      if (oldImage && oldImage !== "data:,") {
        const img = new Image();
        img.onload = () => {
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        };
        img.src = oldImage;
      }
    };

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);
    saveCanvasState();
    loadLatestPrescription();

    return () => {
      window.removeEventListener("resize", resizeCanvas);
    };
  }, []);

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

    if (undoStackRef.current.length > 20) {
      undoStackRef.current.shift();
    }
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

  const startDrawing = (event) => {
    event.preventDefault();

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

  const handleQuickInsert = (item) => {
    setAddedMeds((prev) => [...prev, item]);
  };

  const handleUndo = () => {
    if (undoStackRef.current.length <= 1) return;

    const currentState = undoStackRef.current.pop();
    redoStackRef.current.push(currentState);

    const previousState = undoStackRef.current[undoStackRef.current.length - 1];
    restoreCanvasState(previousState);
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
    try {
      const res = await fetch(`${API_BASE}/api/prescriptions/session/${CONSULTATION_ID}`);
      if (!res.ok) {
        throw new Error("Failed to load previous prescriptions");
      }

      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        const latest = data[0];
        setSavedPrescriptionId(latest.id ?? null);

        if (latest.image_data_b64) {
          setSavedImage(latest.image_data_b64);
          restoreCanvasState(latest.image_data_b64);
        }
      }
    } catch (error) {
      console.error("Load prescriptions error:", error);
    }
  };

  const handleValidateHandwriting = async () => {
    const imageData = canvasRef.current.toDataURL("image/png");
    setIsValidating(true);

    try {
      const res = await fetch(`${API_BASE}/api/prescriptions/validate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          image_data: imageData,
        }),
      });

      if (!res.ok) {
        throw new Error("Validation failed");
      }

      const data = await res.json();
      console.log("Validation result:", data);
      alert("Handwriting validated. Check console for result.");
    } catch (error) {
      console.error("Validation error:", error);
      alert(`Failed to validate handwriting: ${error.message}`);
    } finally {
      setIsValidating(false);
    }
  };

  const handleSavePrescription = async () => {
    const imageData = canvasRef.current.toDataURL("image/png");
    setIsSaving(true);

    try {
      const res = await fetch(`${API_BASE}/api/prescriptions/prescription`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          consultation_id: CONSULTATION_ID,
          pharmacy_id: PHARMACY_ID,
          image_data: imageData,
          image_mime_type: "image/png",
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Save failed");
      }

      const data = await res.json();
      setSavedPrescriptionId(data.id ?? null);

      if (data.image_data_b64) {
        setSavedImage(data.image_data_b64);
      } else {
        setSavedImage(imageData);
      }

      alert("Prescription saved successfully");
    } catch (error) {
      console.error("Save error:", error);
      alert(`Failed to save prescription: ${error.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f4f6f8] text-slate-900">
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
              <button className="rounded-xl px-4 py-2 text-slate-600 hover:bg-slate-100">
                Dashboard
              </button>
              <button className="rounded-xl bg-blue-50 px-4 py-2 font-medium text-blue-600">
                Prescription Canvas
              </button>
            </nav>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 lg:flex">
              <Search className="h-4 w-4 text-slate-400" />
              <input
                className="w-64 bg-transparent text-sm outline-none"
                placeholder="Search patients, records..."
              />
            </div>

            <button className="rounded-full p-2 hover:bg-slate-100">
              <Bell className="h-5 w-5 text-slate-500" />
            </button>

            <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
              <div className="text-right leading-tight">
                <p className="font-semibold">Dr. Sarah Miller</p>
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  Senior Cardiologist
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

      <main className="grid min-h-[calc(100vh-88px)] grid-cols-1 gap-6 p-6 xl:grid-cols-[290px_minmax(0,1fr)]">
        <aside className="space-y-5">
          <div className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <div className="mb-4 flex items-start justify-between">
              <h3 className="text-2xl font-bold">Patient Info</h3>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                Active Session
              </span>
            </div>

            <div className="space-y-4 text-sm">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Full Name
                </p>
                <p className="mt-1 text-lg font-semibold">Robert J. Henderson</p>
              </div>

              <div className="grid grid-cols-2 gap-3 border-t border-slate-200 pt-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Age / Sex
                  </p>
                  <p className="mt-1 font-semibold">54Y / Male</p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    ID
                  </p>
                  <p className="mt-1 font-semibold">#RH-9920</p>
                </div>
              </div>

              <div className="border-t border-slate-200 pt-4">
                <p className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <Circle className="h-3 w-3 fill-rose-500 text-rose-500" />
                  Critical Allergies
                </p>
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-700">
                    Penicillin
                  </span>
                  <span className="rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-700">
                    Sulfa Drugs
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-3xl bg-[#f7fbff] p-5 shadow-sm ring-1 ring-slate-200">
            <div className="mb-4 flex items-center gap-2 font-semibold">
              <Stethoscope className="h-4 w-4 text-blue-600" />
              Last Prescription
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4">
              <p className="font-semibold text-blue-600">Atorvastatin 20mg</p>
              <p className="mt-2 text-sm text-slate-500">Issued: Oct 12, 2023</p>
              <p className="text-sm text-slate-600">1 Tab Daily @ Bedtime</p>
            </div>
          </div>

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

        <section className="space-y-5">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <button className="mb-2 flex items-center gap-2 text-sm font-medium text-blue-600">
                <ArrowLeft className="h-4 w-4" />
                Return to Session Note
              </button>
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
              >
                Palm Rejection
              </button>

              <button
                onClick={() =>
                  setCanvasMode((prev) =>
                    prev === "standard" ? "focus" : "standard"
                  )
                }
                className="rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 shadow-sm"
              >
                {canvasMode === "standard" ? "Standard" : "Focus"}
              </button>
            </div>
          </div>

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
                      {med.name} <span className="text-slate-500">{med.dose}</span>
                    </div>
                  ))}
                </div>

                <button className="absolute bottom-5 left-5 rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-4 font-semibold text-slate-700 transition hover:border-blue-300 hover:bg-blue-50">
                  + Add Signature Stamp
                </button>
              </div>

              <div className="space-y-4">
                <p className="pt-4 text-right text-xs font-semibold uppercase tracking-[0.18em] text-blue-400">
                  Prescribe Quick-Insert
                </p>

                {quickInsertData.map((item) => (
                  <button
                    key={item.name}
                    onClick={() => handleQuickInsert(item)}
                    className="flex w-full items-center gap-4 rounded-2xl border border-slate-200 bg-white px-4 py-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:bg-blue-50"
                  >
                    <div className="flex h-11 w-11 items-center justify-center rounded-full bg-slate-100">
                      <Pill className="h-5 w-5 text-slate-500" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900">{item.name}</p>
                      <p className="text-sm text-slate-500">{item.dose}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-col gap-4 border-t border-slate-200 px-5 py-5 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex flex-wrap items-center gap-6 text-sm text-slate-600">
                <span>Session: #RH-Henderson-Active</span>
                {savedPrescriptionId && <span>Prescription ID: #{savedPrescriptionId}</span>}

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
                  onClick={handleSavePrescription}
                  disabled={isSaving}
                  className="flex items-center gap-2 rounded-2xl bg-blue-600 px-6 py-3 font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:opacity-50"
                >
                  <CheckCircle2 className="h-5 w-5" />
                  {isSaving ? "Saving..." : "Save & Attach to Patient Record"}
                </button>
              </div>
            </div>
          </div>

          {savedImage && (
            <div className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
              <h3 className="mb-4 text-lg font-semibold">Saved Canvas Preview</h3>
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
