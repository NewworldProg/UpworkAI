"""
Find Hugging Face model cache location
"""
import os
from pathlib import Path

def find_model_cache():
    """Find where HF models are cached"""
    
    # Common cache locations
    cache_paths = [
        Path.home() / ".cache" / "huggingface" / "hub",
        Path("C:/Users") / os.getenv('USERNAME', 'Administrator') / ".cache" / "huggingface" / "hub",
        Path("~/.cache/huggingface/hub").expanduser()
    ]
    
    model_name = "models--Hariharavarshan--Cover_genie"
    
    for cache_path in cache_paths:
        model_path = cache_path / model_name
        if model_path.exists():
            print(f"✅ Found model at: {model_path}")
            
            # List contents
            for item in model_path.iterdir():
                if item.is_dir():
                    print(f"📁 {item.name}")
                else:
                    size_mb = item.stat().st_size / (1024*1024)
                    print(f"📄 {item.name} ({size_mb:.1f}MB)")
            
            return str(model_path)
    
    print("❌ Model not found in cache")
    return None

if __name__ == "__main__":
    find_model_cache()