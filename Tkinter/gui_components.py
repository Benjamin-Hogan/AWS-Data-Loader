"""
GUI Components for the REST Data Loader application.
Custom Tkinter widgets for configuration, endpoints, and responses.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
from typing import Dict, Any, Optional, Callable
import sys
from pathlib import Path

# Add parent directory to path to import Essentials
sys.path.insert(0, str(Path(__file__).parent.parent / 'Essentials'))


class ConfigFrame(ttk.LabelFrame):
    """Configuration frame for base URL and settings."""
    
    def __init__(self, parent, on_url_change: Callable[[str], None], on_token_change: Callable[[str], None]):
        super().__init__(parent, text="Configuration", padding=10)
        self.on_url_change = on_url_change
        self.on_token_change = on_token_change
        
        # URL input
        ttk.Label(self, text="Base URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar(value="http://localhost:8000")
        url_entry = ttk.Entry(self, textvariable=self.url_var, width=50)
        url_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # URL update button
        ttk.Button(
            self,
            text="Update URL",
            command=self._update_url
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Auth token (optional)
        ttk.Label(self, text="Auth Token:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.token_var = tk.StringVar()
        token_entry = ttk.Entry(self, textvariable=self.token_var, width=50, show="*")
        token_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Button(
            self,
            text="Set Token",
            command=self._set_token
        ).grid(row=1, column=2, padx=5, pady=5)
        
        self.grid_columnconfigure(1, weight=1)
        
    def _update_url(self):
        """Update the base URL."""
        url = self.url_var.get().strip()
        if url:
            self.on_url_change(url)
        else:
            messagebox.showwarning("Invalid URL", "Please enter a valid URL")
            
    def _set_token(self):
        """Set authentication token."""
        token = self.token_var.get().strip()
        if token:
            self.on_token_change(token)
        else:
            messagebox.showwarning("Invalid Token", "Please enter a token")


class EndpointFrame(ttk.LabelFrame):
    """Frame for displaying and interacting with an API endpoint."""
    
    def __init__(
        self,
        parent,
        path: str,
        methods: Dict[str, Any],
        on_request: Callable[[str, str, Dict[str, Any], Dict[str, str], Optional[str]], None]
    ):
        super().__init__(parent, text=f"Endpoint: {path}", padding=10)
        self.path = path
        self.methods = methods
        self.on_request = on_request
        
        # Method selection
        ttk.Label(self, text="Method:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.method_var = tk.StringVar()
        method_combo = ttk.Combobox(
            self,
            textvariable=self.method_var,
            values=list(methods.keys()),
            state="readonly",
            width=10
        )
        method_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        method_combo.current(0)
        method_combo.bind("<<ComboboxSelected>>", self._on_method_change)
        
        # Summary/description
        if methods:
            first_method = list(methods.values())[0]
            summary = first_method.get('summary', '')
            if summary:
                ttk.Label(self, text=f"Summary: {summary}", font=("TkDefaultFont", 9, "italic")).grid(
                    row=0, column=2, sticky=tk.W, padx=10, pady=5
                )
        
        # Parameters frame
        self.params_frame = ttk.Frame(self)
        self.params_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        # Request body frame
        self.body_frame = ttk.Frame(self)
        self.body_frame.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        ttk.Button(
            button_frame,
            text="Load JSON File",
            command=self._load_json_file
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Send Request",
            command=self._send_request
        ).pack(side=tk.LEFT, padx=5)
        
        self.grid_columnconfigure(2, weight=1)
        
        # Initialize with first method
        if methods:
            self._on_method_change()
            
    def _on_method_change(self, event=None):
        """Handle method selection change."""
        method = self.method_var.get()
        if not method or method not in self.methods:
            return
            
        method_info = self.methods[method]
        
        # Clear existing widgets
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        for widget in self.body_frame.winfo_children():
            widget.destroy()
            
        # Create parameter inputs
        parameters = method_info.get('parameters', [])
        self.param_vars = {}
        
        if parameters:
            ttk.Label(self.params_frame, text="Parameters:", font=("TkDefaultFont", 9, "bold")).grid(
                row=0, column=0, columnspan=2, sticky=tk.W, pady=5
            )
            
            for idx, param in enumerate(parameters, start=1):
                param_name = param.get('name', '')
                param_in = param.get('in', 'query')
                param_required = param.get('required', False)
                param_schema = param.get('schema', {})
                param_type = param_schema.get('type', 'string')
                
                label_text = f"{param_name} ({param_in})"
                if param_required:
                    label_text += " *"
                    
                ttk.Label(self.params_frame, text=label_text).grid(
                    row=idx, column=0, sticky=tk.W, padx=5, pady=2
                )
                
                var = tk.StringVar()
                entry = ttk.Entry(self.params_frame, textvariable=var, width=30)
                entry.grid(row=idx, column=1, sticky=tk.W, padx=5, pady=2)
                
                self.param_vars[param_name] = {
                    'var': var,
                    'in': param_in,
                    'type': param_type,
                    'required': param_required
                }
                
        # Create request body input
        request_body = method_info.get('request_body')
        if request_body and method.upper() in ['POST', 'PUT', 'PATCH']:
            ttk.Label(self.body_frame, text="Request Body (JSON):", font=("TkDefaultFont", 9, "bold")).grid(
                row=0, column=0, sticky=tk.W, pady=5
            )
            
            self.body_text = scrolledtext.ScrolledText(
                self.body_frame,
                width=50,
                height=8,
                wrap=tk.WORD
            )
            self.body_text.grid(row=1, column=0, sticky=tk.EW, pady=5)
            
            self.body_frame.grid_columnconfigure(0, weight=1)
        else:
            self.body_text = None
            
    def _load_json_file(self):
        """Load JSON file for request body."""
        if not self.body_text:
            messagebox.showwarning("No Body", "This endpoint does not accept a request body")
            return
            
        file_path = filedialog.askopenfilename(
            title="Select JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Validate JSON
                json.loads(content)
                self.body_text.delete(1.0, tk.END)
                self.body_text.insert(1.0, content)
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"File contains invalid JSON:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
            
    def _send_request(self):
        """Send the API request."""
        method = self.method_var.get()
        if not method:
            messagebox.showwarning("No Method", "Please select a method")
            return
            
        # Collect parameters
        params = {}
        headers = {}
        path = self.path  # Use a copy to avoid modifying the original
        
        for param_name, param_info in self.param_vars.items():
            value = param_info['var'].get().strip()
            if value:
                param_in = param_info['in']
                if param_in == 'query':
                    params[param_name] = value
                elif param_in == 'header':
                    headers[param_name] = value
                elif param_in == 'path':
                    # Replace path parameters in the path
                    path = path.replace(f'{{{param_name}}}', value)
                    
        # Get request body
        body = None
        if self.body_text:
            body_content = self.body_text.get(1.0, tk.END).strip()
            if body_content:
                try:
                    # Validate JSON
                    json.loads(body_content)
                    body = body_content
                except json.JSONDecodeError:
                    messagebox.showerror("Invalid JSON", "Request body contains invalid JSON")
                    return
                    
        # Call the request handler
        self.on_request(method, path, params, headers, body)


class ResponseFrame(ttk.LabelFrame):
    """Frame for displaying API responses."""
    
    def __init__(self, parent):
        super().__init__(parent, text="Response", padding=10)
        
        # Status code label
        self.status_label = ttk.Label(self, text="Status: -", font=("TkDefaultFont", 10, "bold"))
        self.status_label.pack(anchor=tk.W, pady=5)
        
        # Response info
        self.info_text = scrolledtext.ScrolledText(
            self,
            width=60,
            height=4,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.info_text.pack(fill=tk.BOTH, expand=False, pady=5)
        
        # Response body
        ttk.Label(self, text="Response Body:", font=("TkDefaultFont", 9, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        self.body_text = scrolledtext.ScrolledText(
            self,
            width=60,
            height=20,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.body_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Copy button
        ttk.Button(
            self,
            text="Copy Response",
            command=self._copy_response
        ).pack(pady=5)
        
    def display_response(self, response: Dict[str, Any]):
        """Display API response."""
        status_code = response.get('status_code', 0)
        status_text = f"Status: {status_code}"
        
        # Color code status
        if 200 <= status_code < 300:
            status_text += " ✓"
            self.status_label.config(text=status_text, foreground="green")
        elif 400 <= status_code < 500:
            status_text += " ✗"
            self.status_label.config(text=status_text, foreground="orange")
        elif status_code >= 500:
            status_text += " ✗"
            self.status_label.config(text=status_text, foreground="red")
        else:
            self.status_label.config(text=status_text, foreground="blue")
            
        # Display response info
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        info_lines = [
            f"Method: {response.get('method', 'N/A')}",
            f"URL: {response.get('url', 'N/A')}",
            f"Content-Type: {response.get('headers', {}).get('content-type', 'N/A')}"
        ]
        self.info_text.insert(1.0, "\n".join(info_lines))
        self.info_text.config(state=tk.DISABLED)
        
        # Display response body
        self.body_text.delete(1.0, tk.END)
        
        # Try to format JSON
        body = response.get('body', '')
        json_data = response.get('json')
        
        if json_data:
            try:
                formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
                self.body_text.insert(1.0, formatted_json)
            except:
                self.body_text.insert(1.0, body)
        else:
            self.body_text.insert(1.0, body)
            
    def display_error(self, error_message: str):
        """Display error message."""
        self.status_label.config(text="Error ✗", foreground="red")
        
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, "Request failed")
        self.info_text.config(state=tk.DISABLED)
        
        self.body_text.delete(1.0, tk.END)
        self.body_text.insert(1.0, f"Error: {error_message}")
        
    def _copy_response(self):
        """Copy response body to clipboard."""
        content = self.body_text.get(1.0, tk.END)
        if content.strip():
            self.body_text.clipboard_clear()
            self.body_text.clipboard_append(content)
            messagebox.showinfo("Copied", "Response copied to clipboard")

