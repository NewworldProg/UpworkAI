import os
import sys
from typing import Optional


class CoverGenerator:
    """Generate cover letters using template-based approach.
    
    This is a simplified version focused on template generation only.
    All AI backends have been removed to allow testing of custom models.
    """

    def _template(self, project_description: str, skills: str, job_title: str = None, company_name: str = None) -> str:
        """Generate a comprehensive template-based cover letter"""
        title_text = f"the {job_title} position" if job_title else "this opportunity"
        company_text = f" at {company_name}" if company_name else ""
        
        # Extract key points from project description
        desc_preview = project_description[:200] if project_description else "the project requirements"
        if len(project_description) > 200:
            desc_preview += "..."
        
        # Parse skills into a list for better formatting
        skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        
        return f"""Dear Hiring Manager,

I am writing to express my enthusiastic interest in {title_text}{company_text}. With my extensive experience and proven track record in delivering high-quality solutions, I am confident that I would be an excellent addition to your project team.

PROJECT UNDERSTANDING:
After carefully reviewing your project description: "{desc_preview}", I have a clear understanding of your requirements and objectives. Your project aligns perfectly with my expertise and professional interests, and I am excited about the opportunity to contribute to its success.

MY EXPERTISE & QUALIFICATIONS:
I bring comprehensive experience in the following areas:
{chr(10).join([f'• {skill.strip()} - Extensive hands-on experience with practical implementation' for skill in skills_list])}

WHAT I CAN DELIVER:
• High-quality, professional work that meets or exceeds your expectations
• Clear and consistent communication throughout the project lifecycle
• Adherence to deadlines and project milestones
• Collaborative approach with detailed progress updates
• Clean, well-documented, and maintainable solutions
• Post-delivery support and optimization recommendations

MY APPROACH:
I believe in understanding the complete scope before starting any work. I will begin by conducting a thorough analysis of your requirements, followed by a detailed project plan with clear milestones. My development process emphasizes quality assurance, regular testing, and iterative feedback to ensure the final deliverable perfectly matches your vision.

VALUE PROPOSITION:
What sets me apart is my commitment to not just completing the task, but ensuring it adds real value to your business. I focus on creating solutions that are scalable, efficient, and aligned with your long-term goals.

I would welcome the opportunity to discuss your project in more detail and demonstrate how my skills and experience can contribute to its success. I am available for a call at your convenience to answer any questions and provide additional information about my approach.

Thank you for considering my proposal. I look forward to the possibility of working together and contributing to your project's success.

Best regards,
[Your Name]

P.S. I am committed to delivering exceptional results and building long-term professional relationships. Your project's success is my priority."""

    def generate(
        self,
        project_description: str,
        skills: str,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
        only_backend: Optional[str] = None,
        return_provider: bool = False,
    ):
        """Generate a cover letter using your custom model ONLY.
        
        Returns None until you integrate your model - NO FALLBACK.
        """
        # TODO: Replace with your actual model implementation
        # For now, using simple template to test the flow
        result = self._template(project_description, skills, job_title=job_title, company_name=company_name)
        provider = 'zephyr_template'

        if return_provider:
            return (result, provider)
        return result

    async def generate_async(self, project_description: str, skills: str, job_title: Optional[str] = None) -> str:
        """Async version that just calls the sync version since no AI is involved"""
        return self.generate(project_description, skills, job_title)
