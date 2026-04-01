import os
import gc
from faster_whisper import WhisperModel


class WhisperService:
    def __init__(self, model_size="small"):
        self.model_size = model_size
        self.model = None

    def load_model(self):
        if self.model is None:
            # Use CPU by default to avoid hard CUDA requirements in local dev.
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")

    def unload_model(self):
        if self.model is not None:
            del self.model
            self.model = None
            gc.collect()
            print("Model unloaded and memory cleared.")

    def transcribe(self, audio_path): 
        try:
            self.load_model()
            segments, _ = self.model.transcribe(audio_path)
            raw_text = " ".join(segment.text for segment in segments).strip()

            self.unload_model()  # Unload the model after transcription to free up GPU memory

            if os.path.exists(audio_path):
                os.remove(audio_path)
                print(f"Deleted audio file: {audio_path}")  
            return raw_text
        except Exception as e:    
            if self.model is not None:
                self.unload_model()  # Ensure model is unloaded in case of an error
            print(f"Error during transcription: {e}")

            if os.path.exists(audio_path):
                os.remove(audio_path)
            raise Exception(f"Transcription failed: {e}")
        
            
