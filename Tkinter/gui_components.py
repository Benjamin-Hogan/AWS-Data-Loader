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


class TaskEditorFrame(ttk.Frame):
    """Frame for editing individual task properties."""
    
    def __init__(self, parent, task_data: Dict[str, Any], config_names: list, on_update: Callable[[Dict[str, Any]], None]):
        super().__init__(parent)
        self.task_data = task_data.copy()
        self.on_update = on_update
        self.config_names = config_names
        
        # Main container
        main_frame = ttk.LabelFrame(self, text="Task Editor", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Config name
        ttk.Label(main_frame, text="API Config:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.config_var = tk.StringVar(value=task_data.get('config_name', ''))
        config_combo = ttk.Combobox(main_frame, textvariable=self.config_var, values=config_names, width=30)
        config_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        config_combo.bind("<<ComboboxSelected>>", lambda e: self._update_task())
        
        # Method
        ttk.Label(main_frame, text="Method:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.method_var = tk.StringVar(value=task_data.get('method', 'GET'))
        method_combo = ttk.Combobox(main_frame, textvariable=self.method_var, 
                                   values=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], 
                                   state="readonly", width=30)
        method_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        method_combo.bind("<<ComboboxSelected>>", lambda e: self._update_task())
        
        # Path
        ttk.Label(main_frame, text="Path:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.path_var = tk.StringVar(value=task_data.get('path', ''))
        path_entry = ttk.Entry(main_frame, textvariable=self.path_var, width=30)
        path_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        path_entry.bind('<KeyRelease>', lambda e: self._update_task())
        
        # Parameters
        ttk.Label(main_frame, text="Params (JSON):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.params_text = scrolledtext.ScrolledText(main_frame, width=40, height=4, wrap=tk.WORD)
        self.params_text.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        params_data = task_data.get('params', {})
        if params_data:
            self.params_text.insert(1.0, json.dumps(params_data, indent=2))
        self.params_text.bind('<KeyRelease>', lambda e: self._update_task())
        
        # Headers
        ttk.Label(main_frame, text="Headers (JSON):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.headers_text = scrolledtext.ScrolledText(main_frame, width=40, height=4, wrap=tk.WORD)
        self.headers_text.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
        headers_data = task_data.get('headers', {})
        if headers_data:
            self.headers_text.insert(1.0, json.dumps(headers_data, indent=2))
        self.headers_text.bind('<KeyRelease>', lambda e: self._update_task())
        
        # Body
        body_label_frame = ttk.Frame(main_frame)
        body_label_frame.grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Label(body_label_frame, text="Body (JSON):").pack(side=tk.LEFT)
        
        body_input_frame = ttk.Frame(main_frame)
        body_input_frame.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=5)
        body_input_frame.grid_columnconfigure(0, weight=1)
        
        self.body_text = scrolledtext.ScrolledText(body_input_frame, width=40, height=6, wrap=tk.WORD)
        self.body_text.grid(row=0, column=0, sticky=tk.EW)
        
        body_button_frame = ttk.Frame(body_input_frame)
        body_button_frame.grid(row=0, column=1, sticky=tk.N, padx=(5, 0))
        ttk.Button(body_button_frame, text="Load File", command=self._load_body_file).pack(pady=2)
        ttk.Button(body_button_frame, text="Clear", command=self._clear_body).pack(pady=2)
        
        body_data = task_data.get('body')
        if body_data:
            # If it's a string, try to parse and format it
            try:
                if isinstance(body_data, str):
                    parsed = json.loads(body_data)
                    self.body_text.insert(1.0, json.dumps(parsed, indent=2))
                else:
                    self.body_text.insert(1.0, json.dumps(body_data, indent=2))
            except:
                self.body_text.insert(1.0, str(body_data))
        self.body_text.bind('<KeyRelease>', lambda e: self._update_task())
        
        # Delays
        delay_frame = ttk.Frame(main_frame)
        delay_frame.grid(row=6, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        ttk.Label(delay_frame, text="Delay Before:").pack(side=tk.LEFT, padx=5)
        self.delay_before_var = tk.StringVar(value=str(task_data.get('delay_before', 0.0)))
        ttk.Entry(delay_frame, textvariable=self.delay_before_var, width=10).pack(side=tk.LEFT, padx=5)
        self.delay_before_var.trace('w', lambda *args: self._update_task())
        
        ttk.Label(delay_frame, text="Delay After:").pack(side=tk.LEFT, padx=5)
        self.delay_after_var = tk.StringVar(value=str(task_data.get('delay_after', 0.0)))
        ttk.Entry(delay_frame, textvariable=self.delay_after_var, width=10).pack(side=tk.LEFT, padx=5)
        self.delay_after_var.trace('w', lambda *args: self._update_task())
        
        main_frame.grid_columnconfigure(1, weight=1)
        
    def _update_task(self):
        """Update task data from form fields."""
        try:
            # Parse params
            params = {}
            params_text = self.params_text.get(1.0, tk.END).strip()
            if params_text:
                params = json.loads(params_text)
            
            # Parse headers
            headers = {}
            headers_text = self.headers_text.get(1.0, tk.END).strip()
            if headers_text:
                headers = json.loads(headers_text)
            
            # Parse body
            body = None
            body_text = self.body_text.get(1.0, tk.END).strip()
            if body_text:
                try:
                    # Try to parse as JSON
                    parsed = json.loads(body_text)
                    body = json.dumps(parsed, ensure_ascii=False)
                except:
                    # If not valid JSON, use as-is
                    body = body_text
            
            # Parse delays
            delay_before = float(self.delay_before_var.get() or 0.0)
            delay_after = float(self.delay_after_var.get() or 0.0)
            
            self.task_data = {
                'config_name': self.config_var.get(),
                'method': self.method_var.get(),
                'path': self.path_var.get(),
                'params': params if params else None,
                'headers': headers if headers else None,
                'body': body,
                'delay_before': delay_before,
                'delay_after': delay_after
            }
            
            self.on_update(self.task_data)
        except json.JSONDecodeError:
            # Invalid JSON, but don't update yet
            pass
        except ValueError:
            # Invalid delay value, but don't update yet
            pass
    
    def _load_body_file(self):
        """Load JSON file for request body."""
        file_path = filedialog.askopenfilename(
            title="Select JSON File for Request Body",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Validate JSON
                parsed = json.loads(content)
                # Format and insert
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                self.body_text.delete(1.0, tk.END)
                self.body_text.insert(1.0, formatted)
                self._update_task()
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"File contains invalid JSON:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
    
    def _clear_body(self):
        """Clear the body text field."""
        self.body_text.delete(1.0, tk.END)
        self._update_task()
    
    def get_task_data(self) -> Dict[str, Any]:
        """Get current task data."""
        self._update_task()
        return self.task_data


class TaskConfigEditor(ttk.Frame):
    """Editor for creating and managing task configurations."""
    
    def __init__(self, parent, config_manager, on_save: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.on_save = on_save
        self.current_config_name = None
        self.task_configs: Dict[str, Dict[str, Any]] = {}
        self.current_tasks: list = []
        self.selected_task_index = None
        
        self._create_ui()
        
    def _create_ui(self):
        """Create the UI components."""
        # Top frame: Config selector and management
        top_frame = ttk.LabelFrame(self, text="Task Configuration", padding=10)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Config selector
        ttk.Label(top_frame, text="Config:").pack(side=tk.LEFT, padx=5)
        self.config_selector_var = tk.StringVar()
        self.config_selector = ttk.Combobox(top_frame, textvariable=self.config_selector_var, 
                                          state="readonly", width=25)
        self.config_selector.pack(side=tk.LEFT, padx=5)
        self.config_selector.bind("<<ComboboxSelected>>", self._on_config_selected)
        
        # Buttons
        ttk.Button(top_frame, text="New Config", command=self._new_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Save Config", command=self._save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Load Config", command=self._load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Delete Config", command=self._delete_config).pack(side=tk.LEFT, padx=5)
        
        # Main paned window
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel: Task list
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        task_list_frame = ttk.LabelFrame(left_frame, text="Tasks", padding=5)
        task_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Task list with scrollbar
        list_container = ttk.Frame(task_list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.task_listbox = tk.Listbox(list_container, height=15)
        self.task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.task_listbox.bind('<<ListboxSelect>>', self._on_task_selected)
        
        list_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.task_listbox.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_listbox.configure(yscrollcommand=list_scrollbar.set)
        
        # Task list buttons
        task_buttons_frame = ttk.Frame(task_list_frame)
        task_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(task_buttons_frame, text="Add Task", command=self._add_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(task_buttons_frame, text="Remove Task", command=self._remove_task).pack(side=tk.LEFT, padx=2)
        ttk.Button(task_buttons_frame, text="Move Up", command=self._move_task_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(task_buttons_frame, text="Move Down", command=self._move_task_down).pack(side=tk.LEFT, padx=2)
        
        # Right panel: Task editor
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        self.editor_container = ttk.Frame(right_frame)
        self.editor_container.pack(fill=tk.BOTH, expand=True)
        
        # Status label
        self.status_label = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Initialize
        self._refresh_config_selector()
        
    def _refresh_config_selector(self):
        """Refresh the config selector dropdown."""
        config_names = list(self.task_configs.keys())
        self.config_selector['values'] = config_names
        if self.current_config_name and self.current_config_name in config_names:
            self.config_selector_var.set(self.current_config_name)
        elif config_names:
            self.config_selector_var.set(config_names[0])
            self._on_config_selected()
    
    def _on_config_selected(self, event=None):
        """Handle config selection change."""
        config_name = self.config_selector_var.get()
        if not config_name or config_name not in self.task_configs:
            return
        
        self.current_config_name = config_name
        config_data = self.task_configs[config_name]
        self.current_tasks = config_data.get('tasks', []).copy()
        self._refresh_task_list()
        self._clear_editor()
        self._set_status(f"Loaded config: {config_name}")
    
    def _new_config(self):
        """Create a new task configuration."""
        name = tk.simpledialog.askstring("New Config", "Enter configuration name:")
        if not name:
            return
        
        if name in self.task_configs:
            if not messagebox.askyesno("Config Exists", f"Config '{name}' already exists. Overwrite?"):
                return
        
        self.task_configs[name] = {'tasks': []}
        self.current_config_name = name
        self.current_tasks = []
        self._refresh_config_selector()
        self.config_selector_var.set(name)
        self._on_config_selected()
        self._set_status(f"Created new config: {name}")
    
    def _save_config(self):
        """Save current task configuration."""
        if not self.current_config_name:
            messagebox.showwarning("No Config", "Please select or create a configuration first")
            return
        
        # Update current task if editor is open
        if self.selected_task_index is not None and hasattr(self, 'task_editor'):
            try:
                task_data = self.task_editor.get_task_data()
                if 0 <= self.selected_task_index < len(self.current_tasks):
                    self.current_tasks[self.selected_task_index] = task_data
            except:
                pass
        
        # Save to internal storage
        self.task_configs[self.current_config_name] = {'tasks': self.current_tasks.copy()}
        
        # Save to file if callback provided
        if self.on_save:
            try:
                self.on_save(self.current_config_name, self.task_configs[self.current_config_name])
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save config: {str(e)}")
                return
        
        self._set_status(f"Saved config: {self.current_config_name}")
    
    def _load_config(self):
        """Load task configuration from file."""
        file_path = filedialog.askopenfilename(
            title="Load Task Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract config name from filename
            config_name = Path(file_path).stem
            if config_name in self.task_configs:
                if not messagebox.askyesno("Config Exists", f"Config '{config_name}' already exists. Overwrite?"):
                    return
            
            self.task_configs[config_name] = data
            self.current_config_name = config_name
            self.current_tasks = data.get('tasks', []).copy()
            self._refresh_config_selector()
            self.config_selector_var.set(config_name)
            self._on_config_selected()
            self._set_status(f"Loaded config from: {file_path}")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load config: {str(e)}")
    
    def _delete_config(self):
        """Delete current task configuration."""
        if not self.current_config_name:
            return
        
        if not messagebox.askyesno("Delete Config", f"Delete configuration '{self.current_config_name}'?"):
            return
        
        del self.task_configs[self.current_config_name]
        if self.current_config_name == self.current_config_name:
            self.current_config_name = None
            self.current_tasks = []
            self._clear_editor()
            self._refresh_task_list()
        
        self._refresh_config_selector()
        self._set_status(f"Deleted config: {self.current_config_name}")
    
    def _refresh_task_list(self):
        """Refresh the task list display."""
        self.task_listbox.delete(0, tk.END)
        for idx, task in enumerate(self.current_tasks):
            method = task.get('method', 'GET')
            path = task.get('path', '/')
            config_name = task.get('config_name', 'N/A')
            self.task_listbox.insert(tk.END, f"{idx + 1}. {method} {path} ({config_name})")
    
    def _on_task_selected(self, event=None):
        """Handle task selection."""
        selection = self.task_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if 0 <= idx < len(self.current_tasks):
            # Save current task if editor is open
            if self.selected_task_index is not None and hasattr(self, 'task_editor'):
                try:
                    task_data = self.task_editor.get_task_data()
                    if 0 <= self.selected_task_index < len(self.current_tasks):
                        self.current_tasks[self.selected_task_index] = task_data
                except:
                    pass
            
            self.selected_task_index = idx
            task_data = self.current_tasks[idx]
            self._show_task_editor(task_data)
    
    def _show_task_editor(self, task_data: Dict[str, Any]):
        """Show task editor for the selected task."""
        # Clear existing editor
        for widget in self.editor_container.winfo_children():
            widget.destroy()
        
        # Get config names
        config_names = self.config_manager.get_config_names()
        
        # Create editor
        self.task_editor = TaskEditorFrame(
            self.editor_container,
            task_data,
            config_names,
            lambda data: self._on_task_update(data)
        )
        self.task_editor.pack(fill=tk.BOTH, expand=True)
    
    def _on_task_update(self, task_data: Dict[str, Any]):
        """Handle task data update from editor."""
        if self.selected_task_index is not None and 0 <= self.selected_task_index < len(self.current_tasks):
            self.current_tasks[self.selected_task_index] = task_data
            self._refresh_task_list()
            # Reselect the task
            self.task_listbox.selection_clear(0, tk.END)
            self.task_listbox.selection_set(self.selected_task_index)
    
    def _clear_editor(self):
        """Clear the task editor."""
        for widget in self.editor_container.winfo_children():
            widget.destroy()
        self.selected_task_index = None
    
    def _add_task(self):
        """Add a new task."""
        if not self.current_config_name:
            messagebox.showwarning("No Config", "Please select or create a configuration first")
            return
        
        # Get default config name
        default_config = self.config_manager.active_config or (self.config_manager.get_config_names()[0] if self.config_manager.get_config_names() else '')
        
        new_task = {
            'config_name': default_config,
            'method': 'GET',
            'path': '/api/endpoint',
            'params': {},
            'headers': {},
            'delay_before': 0.0,
            'delay_after': 0.0
        }
        
        self.current_tasks.append(new_task)
        self._refresh_task_list()
        # Select the new task
        self.task_listbox.selection_clear(0, tk.END)
        self.task_listbox.selection_set(len(self.current_tasks) - 1)
        self._on_task_selected()
        self._set_status("Added new task")
    
    def _remove_task(self):
        """Remove selected task."""
        selection = self.task_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if 0 <= idx < len(self.current_tasks):
            self.current_tasks.pop(idx)
            self._refresh_task_list()
            self._clear_editor()
            self._set_status("Removed task")
    
    def _move_task_up(self):
        """Move selected task up."""
        selection = self.task_listbox.curselection()
        if not selection or selection[0] == 0:
            return
        
        idx = selection[0]
        if idx > 0:
            self.current_tasks[idx], self.current_tasks[idx - 1] = self.current_tasks[idx - 1], self.current_tasks[idx]
            self._refresh_task_list()
            self.task_listbox.selection_set(idx - 1)
            self._on_task_selected()
    
    def _move_task_down(self):
        """Move selected task down."""
        selection = self.task_listbox.curselection()
        if not selection or selection[0] >= len(self.current_tasks) - 1:
            return
        
        idx = selection[0]
        if idx < len(self.current_tasks) - 1:
            self.current_tasks[idx], self.current_tasks[idx + 1] = self.current_tasks[idx + 1], self.current_tasks[idx]
            self._refresh_task_list()
            self.task_listbox.selection_set(idx + 1)
            self._on_task_selected()
    
    def _set_status(self, message: str):
        """Set status message."""
        self.status_label.config(text=message)
    
    def get_current_config_data(self) -> Optional[Dict[str, Any]]:
        """Get current configuration data."""
        if not self.current_config_name:
            return None
        
        # Update current task if editor is open
        if self.selected_task_index is not None and hasattr(self, 'task_editor'):
            try:
                task_data = self.task_editor.get_task_data()
                if 0 <= self.selected_task_index < len(self.current_tasks):
                    self.current_tasks[self.selected_task_index] = task_data
            except:
                pass
        
        return {
            'tasks': self.current_tasks.copy()
        }
    
    def load_config_data(self, config_name: str, config_data: Dict[str, Any]):
        """Load configuration data."""
        self.task_configs[config_name] = config_data
        self.current_config_name = config_name
        self.current_tasks = config_data.get('tasks', []).copy()
        self._refresh_config_selector()
        self.config_selector_var.set(config_name)
        self._on_config_selected()