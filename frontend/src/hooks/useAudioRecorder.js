import { useState, useRef, useCallback } from "react";

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const startRecording = useCallback(async () => {
    try {
      console.log("🎙️ RECORDING STARTED - Requesting microphone access...");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      console.log("✅ Microphone access granted", {
        audioTracks: stream.getAudioTracks().length,
        deviceName: stream.getAudioTracks()[0]?.label || "Unknown device"
      });

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
        const duration = Math.round(mediaRecorder.stream?.getTracks()[0]?.enabled ? 0 : 0);
        
        console.log("🛑 RECORDING STOPPED", {
          audioFormat: blob.type,
          audioSize: `${(blob.size / 1024).toFixed(2)} KB`,
          chunks: audioChunksRef.current.length,
          timestamp: new Date().toLocaleTimeString()
        });

        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      console.log("▶️ MediaRecorder started");
    } catch (err) {
      console.error("❌ MICROPHONE ERROR", {
        errorName: err.name,
        errorMessage: err.message,
        timestamp: new Date().toLocaleTimeString()
      });
      alert("Microphone access denied. Please enable microphone permissions.");
    }
  }, []);

  const stopRecording = useCallback(async () => {
    if (mediaRecorderRef.current && isRecording) {
      console.log("⏹️ STOPPING RECORDING...");
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, [isRecording]);

  return { isRecording, audioBlob, startRecording, stopRecording, setAudioBlob };
}
