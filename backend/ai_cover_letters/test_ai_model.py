"""
AI Model Test Script
Standalone testing of T5 Cover Genie model
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SECRET', 'test-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    django.setup()
except Exception as e:
    print(f"Django setup error: {e}")

def test_ai_model_standalone():
    """Test AI model without Django dependencies"""
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
    import torch
    
    print("🤖 Testing T5 Cover Genie model standalone...")
    
    MODEL_NAME = "Hariharavarshan/Cover_genie"
    
    try:
        print("📥 Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        
        print("📥 Loading model...")
        model = AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,
            device_map="cpu"
        )
        
        print("🔧 Creating pipeline...")
        ai_pipeline = pipeline(
            "text2text-generation",
            model=model,
            tokenizer=tokenizer,
            device=-1  # CPU
        )
        
        print("✅ Model loaded successfully!")
        
        # Test cases
        test_cases = [
            {
                'name': 'Python Developer',
                'prompt': 'Generate cover letter for: Python Developer at TechCorp. Skills: Python, Django, FastAPI, PostgreSQL'
            },
            {
                'name': 'Frontend Developer', 
                'prompt': 'Generate cover letter for: Frontend Developer at StartupInc. Skills: React, JavaScript, TypeScript, CSS'
            },
            {
                'name': 'Data Scientist',
                'prompt': 'Generate cover letter for: Data Scientist at DataCorp. Skills: Python, Machine Learning, TensorFlow, SQL'
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}: {test_case['name']}")
            print(f"📝 Prompt: {test_case['prompt']}")
            
            result = ai_pipeline(
                test_case['prompt'],
                max_length=400,
                min_length=150,
                temperature=0.8,
                do_sample=True,
                repetition_penalty=1.2,
                no_repeat_ngram_size=3
            )
            
            response = result[0]['generated_text'].strip()
            print(f"📄 Generated cover letter ({len(response)} chars):")
            print("-" * 80)
            print(response)
            print("-" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Standalone test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_model_django():
    """Test AI model using Django ai_cover_letters app"""
    try:
        from ai_cover_letters.models import ai_manager
        
        print("🤖 Testing T5 Cover Genie model via Django...")
        
        # Test Django AI manager
        print("📊 Model status:", ai_manager.get_model_status())
        
        # Load model if not loaded
        if not ai_manager.model_loaded:
            print("📥 Loading model via Django manager...")
            success = ai_manager.load_model()
            if not success:
                print("❌ Failed to load model via Django")
                return False
        
        print("✅ Model loaded via Django!")
        
        # Test cases via Django
        test_cases = [
            {
                'job_title': 'Senior Python Developer',
                'company_name': 'TechStartup',
                'skills': 'Python, Django, FastAPI, Docker, AWS, PostgreSQL'
            },
            {
                'job_title': 'Full Stack Developer', 
                'company_name': 'InnovateLab',
                'skills': 'React, Node.js, TypeScript, MongoDB, GraphQL'
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Django Test {i}: {test_case['job_title']}")
            
            # Create prompt using Django format
            prompt = f"Generate a professional cover letter for the position of {test_case['job_title']} at {test_case['company_name']}. Required skills: {test_case['skills']}"
            
            print(f"📝 Testing prompt: {prompt[:100]}...")
            
            response = ai_manager.generate_response(prompt, max_tokens=400, temperature=0.8)
            
            print(f"📄 Django generated cover letter ({len(response)} chars):")
            print("-" * 80)
            print(response)
            print("-" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Django test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 AI Cover Letter Model Test Suite")
    print("=" * 50)
    
    # Test 1: Standalone
    print("\n1️⃣ STANDALONE TEST:")
    standalone_success = test_ai_model_standalone()
    
    print("\n" + "="*50)
    
    # Test 2: Django integration
    print("\n2️⃣ DJANGO INTEGRATION TEST:")
    django_success = test_ai_model_django()
    
    print("\n" + "="*50)
    print("\n📋 TEST SUMMARY:")
    print(f"   Standalone: {'✅ PASS' if standalone_success else '❌ FAIL'}")
    print(f"   Django:     {'✅ PASS' if django_success else '❌ FAIL'}")
    
    if standalone_success and django_success:
        print("\n🎉 All tests passed! AI model is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check error messages above.")

if __name__ == "__main__":
    main()