# PowerShell script za fokusiranje Chrome window-a
param($windowTitle = "Chrome")

Add-Type -TypeDefinition @"
    using System;
    using System.Diagnostics;
    using System.Runtime.InteropServices;
    public class WindowFocuser {
        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);
        
        [DllImport("user32.dll")]
        public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        
        public static void FocusWindow(string processName) {
            Process[] processes = Process.GetProcessesByName(processName);
            foreach (Process process in processes) {
                if (process.MainWindowHandle != IntPtr.Zero) {
                    ShowWindow(process.MainWindowHandle, 9); // SW_RESTORE
                    SetForegroundWindow(process.MainWindowHandle);
                    break;
                }
            }
        }
    }
"@

[WindowFocuser]::FocusWindow("chrome")
Write-Host "Chrome window focused"