"""
AI Cover Letter Models
Handles loading and management of AI mode            # Create T5 text2text generation pipeline
            self.ai_pipeline = pipeline(
                "text2text-generation",  # T5 uses text2text instead of text-generation
                model=self.model,
                tokenizer=self.tokenizer,
                dtype=torch.float32,
                device=-1,  # CPU
                return_full_text=False
            )er letter generation
"""

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import logging
import gc

logger = logging.getLogger(__name__)

# Model configuration - Use specialized cover letter T5 model
MODEL_NAME = "nouamanetazi/cover-letter-t5-base"  # Specialized model for cover letters
MAX_MODEL_LENGTH = 512  
DEVICE = "cpu"

class AIModelManager:
    """Singleton class to manage AI model loading and inference"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIModelManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        if not self.initialized:
            self.tokenizer = None
            self.model = None
            self.ai_pipeline = None
            self.model_loaded = False
            self.initialized = True
    
    def load_model(self):
        """Load specialized cover letter T5 model"""
        if self.model_loaded:
            logger.info("Model already loaded")
            return True
        
        try:
            logger.info(f"🤖 Loading specialized cover letter model: {MODEL_NAME}")
            logger.info(f"🔧 Using device: {DEVICE}")
            logger.info("⏳ Loading cover letter T5 model...")
            
            # Clear any existing memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            
            # Load tokenizer for cover letter model
            self.tokenizer = AutoTokenizer.from_pretrained(
                MODEL_NAME, 
                use_fast=True,
                model_max_length=MAX_MODEL_LENGTH
            )
            
            # Load specialized cover letter model
            logger.info("Loading cover-letter-t5-base model...")
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                MODEL_NAME,
                low_cpu_mem_usage=True
                # Remove dtype parameter - not supported by T5
            )
            logger.info("✅ Cover letter T5 model loaded successfully!")
            
            # Convert to half precision after loading for memory efficiency
            try:
                self.model = self.model.half()
                logger.info("✅ Model converted to float16 for memory efficiency")
            except Exception as e:
                logger.warning(f"Could not convert to float16: {e}, using float32")
            
            # Optimize model for inference
            self.model.eval()
            
            # Use pipeline for cover letter model
            from transformers import pipeline
            self.ai_pipeline = pipeline(
                "text2text-generation",
                model=self.model,
                tokenizer=self.tokenizer
            )
            
            self.model_loaded = True
            logger.info("✅ Cover letter T5 model loaded successfully in Django!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load cover letter model: {e}")
            self.model_loaded = False
            return False
    
    def generate_response(self, prompt: str, max_tokens: int = 400, temperature: float = 0.7) -> str:
        """Generate AI response using t5-small model with pipeline"""
        if not self.model_loaded or self.ai_pipeline is None:
            return "AI model is not loaded. Please wait for initialization or check logs for errors."
        
        try:
            # Use pipeline for t5-small generation
            response = self.ai_pipeline(
                prompt,
                max_new_tokens=min(max_tokens, MAX_MODEL_LENGTH // 2),  # Use max_new_tokens instead of max_length
                min_length=50,
                temperature=temperature,
                do_sample=True,
                top_p=0.8,  # More focused output
                repetition_penalty=1.5,  # Higher penalty to prevent repetition
                early_stopping=True,
                num_return_sequences=1,
                no_repeat_ngram_size=3  # Prevent 3-gram repetition
            )
            
            if isinstance(response, list) and len(response) > 0:
                ai_response = response[0]['generated_text'].strip()
                return ai_response if ai_response else "Unable to generate cover letter. Please try again."
            else:
                return "Unable to generate cover letter. Please try again."
                
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            return f"Error generating cover letter: {str(e)}"
    
    def get_model_status(self):
        """Get current model status"""
        return {
            "model_name": MODEL_NAME,
            "model_loaded": self.model_loaded,
            "device": DEVICE,
            "max_length": MAX_MODEL_LENGTH
        }

# Global instance
ai_manager = AIModelManager()
