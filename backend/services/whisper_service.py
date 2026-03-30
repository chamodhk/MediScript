import whisper
import os
import gc
import torch
class WhisperService:
    def __init__(self, model_size="small"):
        self.model_size = model_size
        self.model = None

    def load_model(self):
        if self.model is None:
            self.model = whisper.load_model(self.model_size)

    def unload_model(self):
        if self.model is not None:
            del self.model
            self.model = None
            gc.collect()
            torch.cuda.empty_cache()
            print("Model unloaded and GPU memory cleared.")

    def transcribe(self, audio_path): 
        try:
            self.load_model()
            result = self.model.transcribe(audio_path,language =None,task="transcribe")#auto-detect language, force transcription task

            raw_text = result["text"].strip()
            '''print(f"Transcription result: {raw_text}")'''

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
        
            
