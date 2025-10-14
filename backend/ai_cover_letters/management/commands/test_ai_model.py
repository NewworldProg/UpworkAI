"""
Django Management Command: Test AI Model
Usage: python manage.py test_ai_model
"""

from django.core.management.base import BaseCommand
from ai_cover_letters.models import ai_manager


class Command(BaseCommand):
    help = 'Test T5 Cover Genie AI model functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quick',
            action='store_true',
            help='Run quick test with single example',
        )
        parser.add_argument(
            '--job-title',
            type=str,
            help='Custom job title for testing',
        )
        parser.add_argument(
            '--company',
            type=str, 
            help='Custom company name for testing',
        )
        parser.add_argument(
            '--skills',
            type=str,
            help='Custom skills list for testing',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🤖 Testing T5 Cover Genie AI Model')
        )
        self.stdout.write('=' * 50)

        # Check model status
        status = ai_manager.get_model_status()
        self.stdout.write(f"📊 Model Status: {status}")

        # Load model if needed
        if not ai_manager.model_loaded:
            self.stdout.write("📥 Loading AI model...")
            success = ai_manager.load_model()
            if not success:
                self.stdout.write(
                    self.style.ERROR("❌ Failed to load AI model")
                )
                return
            self.stdout.write(
                self.style.SUCCESS("✅ Model loaded successfully!")
            )

        # Prepare test cases
        if options['quick']:
            test_cases = [{
                'job_title': options.get('job_title', 'Software Developer'),
                'company_name': options.get('company', 'TechCorp'),
                'skills': options.get('skills', 'Python, Django, React')
            }]
        else:
            test_cases = [
                {
                    'job_title': 'Senior Python Developer',
                    'company_name': 'TechStartup',
                    'skills': 'Python, Django, FastAPI, Docker, AWS'
                },
                {
                    'job_title': 'Frontend Developer',
                    'company_name': 'InnovateLab', 
                    'skills': 'React, TypeScript, Next.js, TailwindCSS'
                },
                {
                    'job_title': 'Full Stack Engineer',
                    'company_name': 'GrowthCorp',
                    'skills': 'Node.js, React, PostgreSQL, GraphQL, Kubernetes'
                }
            ]

        # Run tests
        for i, test_case in enumerate(test_cases, 1):
            self.stdout.write(f"\n🧪 Test {i}: {test_case['job_title']} at {test_case['company_name']}")
            
            # Create prompt
            prompt = f"Generate a professional cover letter for the position of {test_case['job_title']} at {test_case['company_name']}. Required skills: {test_case['skills']}"
            
            # Generate cover letter
            try:
                response = ai_manager.generate_response(
                    prompt, 
                    max_tokens=400, 
                    temperature=0.8
                )
                
                self.stdout.write(f"📄 Generated Cover Letter ({len(response)} characters):")
                self.stdout.write("-" * 80)
                self.stdout.write(response)
                self.stdout.write("-" * 80)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Generation failed: {e}")
                )

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(
            self.style.SUCCESS("🎉 AI Model test completed!")
        )