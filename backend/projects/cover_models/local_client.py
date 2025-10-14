import os
import sys
import subprocess
from typing import Optional


class LocalClient:
    def __init__(self, script_path: Optional[str] = None, python_executable: Optional[str] = None):
        self.script_path = script_path
        self.python_executable = python_executable or sys.executable

    def generate(self, project_description: str, skills: str, job_title: Optional[str] = None, timeout: int = 120) -> Optional[str]:
        jt = (f"Project title: {job_title}. " if job_title else "")
        user_text = f"{jt}Project description: {project_description} Skills: {skills}"
        prompt = f"<start_of_turn>user {user_text} <end_of_turn>\n<start_of_turn>model"

        if not self.script_path or not os.path.exists(self.script_path):
            return None

        cmd = [
            self.python_executable,
            self.script_path,
            '--prompt', prompt,
            '--max_new_tokens', '512',
            '--temperature', '0.7',
            '--top_p', '0.9',
            '--top_k', '50',
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if proc.returncode != 0:
                if proc.stderr:
                    print(f"[local_client] stderr:\n{proc.stderr}", file=sys.stderr)
                return None
            out = proc.stdout
            marker = '--- Generated cover letter ---\n'
            if marker in out:
                part = out.split(marker, 1)[1]
                endm = '\n--- End ---'
                if endm in part:
                    part = part.split(endm, 1)[0]
                return part.strip()
            return out.strip()
        except Exception:
            return None
