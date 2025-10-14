"""
Chrome DevTools Protocol controller for opening URLs in debug Chrome instance
"""
import requests
import json
import logging
import websocket
import threading
import time

logger = logging.getLogger(__name__)

class ChromeController:
    def __init__(self, chrome_host='localhost', chrome_port=9222):
        self.chrome_host = chrome_host
        self.chrome_port = chrome_port
        self.base_url = f'http://{chrome_host}:{chrome_port}'
    
    def get_tabs(self):
        """Get list of all open tabs in Chrome"""
        try:
            response = requests.get(f'{self.base_url}/json', timeout=5)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get Chrome tabs: {e}")
            return []
    
    def find_upwork_tab(self):
        """Find existing Upwork tab"""
        tabs = self.get_tabs()
        for tab in tabs:
            if 'upwork.com' in tab.get('url', ''):
                return tab
        return None
    
    def create_new_tab(self, url):
        """Create new tab with specific URL using simpler method"""
        try:
            # Use Chrome's simple new tab creation
            response = requests.put(f'{self.base_url}/json/new?{url}', timeout=5)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            logger.error(f"Failed to create new tab: {e}")
            return None
    
    def navigate_existing_tab(self, tab_id, url):
        """Navigate existing tab to URL using Runtime.evaluate"""
        try:
            tabs = self.get_tabs()
            tab = next((t for t in tabs if t['id'] == tab_id), None)
            
            if not tab:
                logger.error(f"Tab {tab_id} not found")
                return False
            
            ws_url = tab.get('webSocketDebuggerUrl')
            if not ws_url:
                logger.error(f"No WebSocket URL for tab {tab_id}")
                return False
            
            # Use simple JavaScript navigation
            command = {
                "id": 1,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": f"window.location.href = '{url}'; true;"
                }
            }
            
            # Send command via WebSocket (simplified)
            result = self._send_websocket_command(ws_url, command)
            return result
            
        except Exception as e:
            logger.error(f"Failed to navigate tab: {e}")
            return False
    
    def _send_websocket_command(self, ws_url, command):
        """Send command via WebSocket to Chrome tab"""
        try:
            result = {'success': False}
            
            def on_message(ws, message):
                data = json.loads(message)
                if data.get('id') == 1:  # Our command response
                    result['success'] = True
                    result['data'] = data
                    ws.close()
            
            def on_error(ws, error):
                logger.error(f"WebSocket error: {error}")
                result['error'] = str(error)
                ws.close()
            
            def on_open(ws):
                ws.send(json.dumps(command))
            
            ws = websocket.WebSocketApp(ws_url,
                                      on_message=on_message,
                                      on_error=on_error,
                                      on_open=on_open)
            
            # Run WebSocket in thread with timeout
            ws_thread = threading.Thread(target=ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            ws_thread.join(timeout=3)  # 3 second timeout
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"WebSocket communication failed: {e}")
            return False
    
    def open_upwork_message(self, conversation_id):
        """Open specific Upwork message conversation"""
        try:
            url = f"https://www.upwork.com/messages/{conversation_id}"
            logger.info(f"Opening Upwork message: {url}")
            
            # First try to find existing Upwork tab
            upwork_tab = self.find_upwork_tab()
            
            if upwork_tab:
                # Navigate existing tab
                tab_id = upwork_tab['id']
                logger.info(f"Navigating existing Upwork tab {tab_id} to {url}")
                success = self.navigate_existing_tab(tab_id, url)
                
                if success:
                    return {
                        'success': True,
                        'action': 'navigated_existing_tab',
                        'tab_id': tab_id,
                        'url': url
                    }
                else:
                    # If navigation failed, try creating new tab
                    logger.warning("Navigation failed, creating new tab")
                    new_tab = self.create_new_tab(url)
                    return {
                        'success': bool(new_tab),
                        'action': 'created_new_tab_after_nav_fail',
                        'tab_id': new_tab.get('id') if new_tab else None,
                        'url': url
                    }
            else:
                # Create new tab
                logger.info(f"Creating new tab for {url}")
                new_tab = self.create_new_tab(url)
                return {
                    'success': bool(new_tab),
                    'action': 'created_new_tab',
                    'tab_id': new_tab.get('id') if new_tab else None,
                    'url': url
                }
                
        except Exception as e:
            logger.error(f"Failed to open Upwork message: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

# Global controller instance
chrome_controller = ChromeController()