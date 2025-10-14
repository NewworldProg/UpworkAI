"""
Chrome Control for opening URLs in debug Chrome instance
Simple subprocess approach - no need for complex WebSocket communication
"""
import subprocess
import logging
import os
import platform

logger = logging.getLogger(__name__)

class ChromeController:
    def __init__(self):
        self.chrome_paths = self._get_chrome_paths()
    
    def _get_chrome_paths(self):
        """Get possible Chrome executable paths for different OS"""
        if platform.system() == "Windows":
            return [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
                "chrome.exe"  # If in PATH
            ]
        elif platform.system() == "Darwin":  # macOS
            return [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "google-chrome"
            ]
        else:  # Linux
            return [
                "google-chrome",
                "google-chrome-stable",
                "chromium-browser"
            ]
    
    def _find_chrome_executable(self):
        """Find working Chrome executable"""
        for chrome_path in self.chrome_paths:
            try:
                # Test if Chrome exists
                result = subprocess.run(
                    [chrome_path, "--version"], 
                    capture_output=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"Found Chrome at: {chrome_path}")
                    return chrome_path
            except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                continue
        
        logger.error("Chrome executable not found")
        return None
    
    def open_upwork_message(self, conversation_id):
        """Open specific Upwork message in Chrome debugger instance"""
        try:
            url = f"https://www.upwork.com/messages/{conversation_id}"
            chrome_exe = self._find_chrome_executable()
            
            if not chrome_exe:
                return {
                    'success': False,
                    'error': 'Chrome executable not found',
                    'url': url
                }
            
            # Use subprocess to open URL in existing Chrome with debugging port
            # --remote-debugging-port=9222 should already be running
            cmd = [
                chrome_exe,
                "--remote-debugging-port=9222",  # Connect to existing debug instance
                "--new-tab",  # Open in new tab
                url
            ]
            
            logger.info(f"Opening URL in Chrome: {url}")
            logger.info(f"Command: {' '.join(cmd)}")
            
            # Run command without waiting (non-blocking)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'action': 'opened_in_chrome_debugger',
                    'url': url,
                    'chrome_path': chrome_exe
                }
            else:
                logger.error(f"Chrome command failed: {result.stderr}")
                return {
                    'success': False,
                    'error': f'Chrome command failed: {result.stderr}',
                    'url': url
                }
                
        except subprocess.TimeoutExpired:
            logger.error("Chrome command timed out")
            return {
                'success': False,
                'error': 'Chrome command timed out',
                'url': url
            }
        except Exception as e:
            logger.error(f"Error opening Chrome: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

# Global controller instance
chrome_controller = ChromeController()