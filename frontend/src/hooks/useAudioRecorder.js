import { useState } from "react";

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);

  // TODO: implement MediaRecorder logic
  const startRecording = () => setIsRecording(true);
  const stopRecording = () => setIsRecording(false);

  return { isRecording, startRecording, stopRecording };
}
