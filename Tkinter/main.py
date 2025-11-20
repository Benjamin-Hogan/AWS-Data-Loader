"""
Main entry point for the REST Data Loader application (Tkinter GUI).
A basic Tkinter-based GUI for interacting with REST APIs using OpenAPI specifications.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import Dict, Any, Optional
import threading
from pathlib import Path
import sys

# Add parent directory to path to import Essentials
sys.path.insert(0, str(Path(__file__).parent.parent / 'Essentials'))

from openapi_parser import OpenAPIParser
from api_client import APIClient
from gui_components import EndpointFrame, ConfigFrame, ResponseFrame
from api_config_manager import APIConfigManager, APIConfig
from autonomous_loader import AutonomousLoader, RequestTask


class RESTDataLoaderApp:
    """Main application class for the REST Data Loader."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("REST Data Loader - Tkinter")
        self.root.geometry("1400x900")
        
        # Application state
        self.base_url: Optional[str] = None
        self.openapi_spec: Optional[Dict[str, Any]] = None
        self.endpoints: Dict[str, Any] = {}
        self.api_client: Optional[APIClient] = None
        self.endpoint_frames: list = []  # Store references to endpoint frames for filtering
        
        # Multi-API configuration
        self.config_manager = APIConfigManager()
        self.current_config: Optional[APIConfig] = None
        self.autonomous_loader: Optional[AutonomousLoader] = None
        
        # Create UI components
        self._create_menu()
        self._create_main_layout()
        
        # Load saved configurations
        self._refresh_config_selector()
        
    def _create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load OpenAPI Spec", command=self._load_openapi_spec)
        file_menu.add_command(label="Load Multiple OpenAPI Specs", command=self._load_multiple_openapi_specs)
        file_menu.add_separator()
        file_menu.add_command(label="Manage API Configurations", command=self._manage_configs)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Autonomous Data Loader", command=self._open_autonomous_loader)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        
    def _create_main_layout(self):
        """Create the main application layout."""
        # Create paned window for resizable panels
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel: Configuration and Endpoints
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # API Configuration selector
        config_selector_frame = ttk.LabelFrame(left_frame, text="API Configuration", padding=5)
        config_selector_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(config_selector_frame, text="Active Config:").pack(side=tk.LEFT, padx=5)
        self.config_selector_var = tk.StringVar()
        self.config_selector = ttk.Combobox(
            config_selector_frame,
            textvariable=self.config_selector_var,
            state="readonly",
            width=25
        )
        self.config_selector.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.config_selector.bind("<<ComboboxSelected>>", self._on_config_selected)
        
        ttk.Button(
            config_selector_frame,
            text="Manage",
            command=self._manage_configs
        ).pack(side=tk.LEFT, padx=5)
        
        # Configuration frame
        self.config_frame = ConfigFrame(left_frame, self._on_url_change, self._on_token_change)
        self.config_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 5))
        
        # Search frame for endpoints
        search_frame = ttk.LabelFrame(left_frame, text="Search Endpoints", padding=5)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._filter_endpoints())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Clear search button
        ttk.Button(
            search_frame,
            text="Clear",
            command=lambda: self.search_var.set("")
        ).pack(side=tk.RIGHT)
        
        # Endpoints frame with scrollbar
        endpoints_container = ttk.Frame(left_frame)
        endpoints_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollable frame for endpoints
        canvas = tk.Canvas(endpoints_container)
        scrollbar = ttk.Scrollbar(endpoints_container, orient="vertical", command=canvas.yview)
        self.endpoints_scrollable = ttk.Frame(canvas)
        
        self.endpoints_scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.endpoints_scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right panel: Response viewer
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        self.response_frame = ResponseFrame(right_frame)
        self.response_frame.pack(fill=tk.BOTH, expand=True)
        
        # Store canvas reference for scrolling
        self.endpoints_canvas = canvas
        
    def _refresh_config_selector(self):
        """Refresh the configuration selector dropdown."""
        configs = self.config_manager.get_config_names()
        self.config_selector['values'] = configs
        if self.config_manager.active_config:
            self.config_selector_var.set(self.config_manager.active_config)
            self._on_config_selected()
        elif configs:
            self.config_selector_var.set(configs[0])
            self.config_manager.set_active_config(configs[0])
            self._on_config_selected()
    
    def _on_config_selected(self, event=None):
        """Handle configuration selection change."""
        config_name = self.config_selector_var.get()
        if not config_name:
            return
        
        config = self.config_manager.get_config(config_name)
        if not config:
            return
        
        self.config_manager.set_active_config(config_name)
        self.current_config = config
        self.base_url = config.base_url
        self.api_client = config.api_client
        self.openapi_spec = config.openapi_spec
        self.endpoints = config.endpoints
        
        # Update UI
        self.config_frame.url_var.set(config.base_url)
        if config.auth_token:
            self.config_frame.token_var.set(config.auth_token)
        
        # Reload endpoints
        self._reload_endpoints()
    
    def _reload_endpoints(self):
        """Reload endpoints for the current configuration."""
        # Clear existing endpoints
        for widget in self.endpoints_scrollable.winfo_children():
            widget.destroy()
        self.endpoint_frames.clear()
        
        # Create endpoint frames
        if self.endpoints:
            for path, methods in self.endpoints.items():
                endpoint_frame = EndpointFrame(
                    self.endpoints_scrollable,
                    path,
                    methods,
                    self._on_endpoint_request
                )
                endpoint_frame.pack(fill=tk.X, padx=5, pady=2)
                # Store reference with metadata for filtering
                self.endpoint_frames.append({
                    'frame': endpoint_frame,
                    'path': path,
                    'methods': list(methods.keys()),
                    'summaries': [m.get('summary', '') for m in methods.values()],
                    'descriptions': [m.get('description', '') for m in methods.values()],
                    'tags': [tag for m in methods.values() for tag in m.get('tags', [])],
                    'operation_ids': [m.get('operation_id', '') for m in methods.values()]
                })
        
        # Update canvas scroll region
        self.endpoints_scrollable.update_idletasks()
        self.endpoints_canvas.configure(scrollregion=self.endpoints_canvas.bbox("all"))
    
    def _on_url_change(self, url: str):
        """Handle URL configuration change."""
        self.base_url = url.rstrip('/')
        if self.base_url:
            if self.current_config:
                self.current_config.base_url = self.base_url
                self.current_config._init_client()
                self.api_client = self.current_config.api_client
            else:
                self.api_client = APIClient(self.base_url)
            # Re-apply token if it was set
            if hasattr(self.config_frame, 'token_var') and self.config_frame.token_var.get():
                self._on_token_change(self.config_frame.token_var.get())
            messagebox.showinfo("URL Updated", f"Base URL set to: {self.base_url}")
        else:
            self.api_client = None
            
    def _on_token_change(self, token: str):
        """Handle authentication token change."""
        if self.api_client and token:
            self.api_client.set_auth_token(token)
            if self.current_config:
                self.current_config.set_auth_token(token)
            
    def _load_openapi_spec(self):
        """Load OpenAPI specification from file."""
        file_path = filedialog.askopenfilename(
            title="Select OpenAPI Specification",
            filetypes=[
                ("YAML files", "*.yaml *.yml"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        # Check if we should create a new config or use existing
        if not self.current_config:
            # Ask for config name
            config_name = simpledialog.askstring(
                "Configuration Name",
                "Enter a name for this API configuration:",
                initialvalue="API Config"
            )
            if not config_name:
                return
            
            # Get base URL
            base_url = simpledialog.askstring(
                "Base URL",
                "Enter the base URL for this API:",
                initialvalue="http://localhost:8000"
            )
            if not base_url:
                return
            
            try:
                config = self.config_manager.add_config(
                    name=config_name,
                    base_url=base_url,
                    openapi_spec_path=file_path
                )
                self.current_config = config
                self._refresh_config_selector()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                return
        else:
            # Load into current config
            try:
                self.current_config.load_openapi_spec(file_path)
                self.openapi_spec = self.current_config.openapi_spec
                self.endpoints = self.current_config.endpoints
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load OpenAPI spec:\n{str(e)}")
                return
        
        # Try to get base URL from spec and update if not already set
        if self.current_config.parser:
            spec_base_url = self.current_config.parser.get_base_url()
            if spec_base_url and not self.base_url:
                self.config_frame.url_var.set(spec_base_url)
                self._on_url_change(spec_base_url)
        
        # Reload endpoints
        self._reload_endpoints()
        
        if self.endpoints:
            messagebox.showinfo(
                "OpenAPI Loaded",
                f"Loaded {len(self.endpoints)} endpoint(s) from specification"
            )
        else:
            messagebox.showwarning("No Endpoints", "No endpoints found in the OpenAPI specification")
    
    def _load_multiple_openapi_specs(self):
        """Load multiple OpenAPI specifications at once."""
        file_paths = filedialog.askopenfilenames(
            title="Select OpenAPI Specifications",
            filetypes=[
                ("YAML files", "*.yaml *.yml"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if not file_paths:
            return
        
        loaded_count = 0
        errors = []
        
        for file_path in file_paths:
            try:
                # Extract name from filename
                file_name = Path(file_path).stem
                config_name = file_name.replace('_', ' ').replace('-', ' ').title()
                
                # Make name unique
                base_name = config_name
                counter = 1
                while config_name in self.config_manager.get_config_names():
                    config_name = f"{base_name} {counter}"
                    counter += 1
                
                # Try to get base URL from spec
                parser = OpenAPIParser()
                spec = parser.parse(file_path)
                spec_base_url = parser.get_base_url()
                
                if not spec_base_url:
                    spec_base_url = simpledialog.askstring(
                        "Base URL",
                        f"Enter base URL for '{config_name}':",
                        initialvalue="http://localhost:8000"
                    )
                    if not spec_base_url:
                        continue
                
                # Create config
                config = self.config_manager.add_config(
                    name=config_name,
                    base_url=spec_base_url,
                    openapi_spec_path=file_path
                )
                loaded_count += 1
                
            except Exception as e:
                errors.append(f"{Path(file_path).name}: {str(e)}")
        
        # Refresh UI
        self._refresh_config_selector()
        
        # Show results
        message = f"Loaded {loaded_count} configuration(s)"
        if errors:
            message += f"\n\nErrors:\n" + "\n".join(errors)
        messagebox.showinfo("Batch Load Complete", message)
    
    def _manage_configs(self):
        """Open configuration management dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manage API Configurations")
        dialog.geometry("600x500")
        
        # List of configurations
        list_frame = ttk.LabelFrame(dialog, text="Configurations", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview for configs
        columns = ('Name', 'Base URL', 'Spec File')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Populate tree
        def refresh_tree():
            for item in tree.get_children():
                tree.delete(item)
            for config in self.config_manager.get_all_configs():
                spec_file = Path(config.openapi_spec_path).name if config.openapi_spec_path else "None"
                tree.insert('', 'end', values=(config.name, config.base_url, spec_file))
        
        refresh_tree()
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def add_config():
            name = simpledialog.askstring("New Configuration", "Enter configuration name:")
            if not name:
                return
            
            base_url = simpledialog.askstring("Base URL", "Enter base URL:")
            if not base_url:
                return
            
            spec_path = filedialog.askopenfilename(
                title="Select OpenAPI Spec (Optional)",
                filetypes=[("YAML files", "*.yaml *.yml"), ("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            try:
                self.config_manager.add_config(
                    name=name,
                    base_url=base_url,
                    openapi_spec_path=spec_path if spec_path else None
                )
                refresh_tree()
                self._refresh_config_selector()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        def remove_config():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a configuration to remove")
                return
            
            item = tree.item(selection[0])
            config_name = item['values'][0]
            
            if messagebox.askyesno("Confirm", f"Remove configuration '{config_name}'?"):
                self.config_manager.remove_config(config_name)
                refresh_tree()
                self._refresh_config_selector()
        
        ttk.Button(button_frame, text="Add", command=add_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove", command=remove_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _open_autonomous_loader(self):
        """Open autonomous data loader dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Autonomous Data Loader")
        dialog.geometry("700x600")
        
        # Instructions
        info_frame = ttk.LabelFrame(dialog, text="Instructions", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        info_text = """Load a task configuration file (JSON) to automatically execute API requests.
The file should contain a 'tasks' array with request definitions."""
        ttk.Label(info_frame, text=info_text, wraplength=650).pack()
        
        # File selection
        file_frame = ttk.Frame(dialog)
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.task_file_var = tk.StringVar()
        ttk.Label(file_frame, text="Task File:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(file_frame, textvariable=self.task_file_var, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(
            file_frame,
            text="Browse",
            command=lambda: self.task_file_var.set(filedialog.askopenfilename(
                title="Select Task Configuration File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            ))
        ).pack(side=tk.LEFT, padx=5)
        
        # Progress
        progress_frame = ttk.LabelFrame(dialog, text="Progress", padding=10)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.progress_text = tk.Text(progress_frame, height=15, wrap=tk.WORD)
        self.progress_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(progress_frame, orient="vertical", command=self.progress_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.progress_text.configure(yscrollcommand=scrollbar.set)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def update_progress(message):
            self.progress_text.insert(tk.END, message + "\n")
            self.progress_text.see(tk.END)
            dialog.update()
        
        def on_complete(tasks):
            update_progress(f"\n=== Execution Complete ===")
            update_progress(f"Total tasks: {len(tasks)}")
            success_count = sum(1 for t in tasks if t.result and not t.error)
            update_progress(f"Successful: {success_count}")
            update_progress(f"Failed: {len(tasks) - success_count}")
            
            # Ask to save results
            if messagebox.askyesno("Save Results", "Save execution results to file?"):
                file_path = filedialog.asksaveasfilename(
                    title="Save Results",
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
                )
                if file_path and self.autonomous_loader:
                    self.autonomous_loader.save_results(file_path)
                    update_progress(f"Results saved to: {file_path}")
        
        def on_error(task, error):
            update_progress(f"ERROR: {task.config_name} - {task.method} {task.path}: {error}")
        
        def execute_tasks():
            task_file = self.task_file_var.get()
            if not task_file:
                messagebox.showerror("Error", "Please select a task configuration file")
                return
            
            self.progress_text.delete(1.0, tk.END)
            update_progress("=== Starting Autonomous Data Loader ===\n")
            
            try:
                # Create loader
                self.autonomous_loader = AutonomousLoader(
                    config_manager=self.config_manager,
                    on_progress=update_progress,
                    on_complete=on_complete,
                    on_error=on_error
                )
                
                # Load tasks
                update_progress(f"Loading tasks from: {task_file}")
                tasks = self.autonomous_loader.load_tasks_from_file(task_file)
                self.autonomous_loader.add_tasks(tasks)
                update_progress(f"Loaded {len(tasks)} task(s)\n")
                
                # Execute in separate thread to avoid blocking UI
                def run_loader():
                    self.autonomous_loader.execute_all()
                
                thread = threading.Thread(target=run_loader, daemon=True)
                thread.start()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to execute tasks:\n{str(e)}")
                update_progress(f"ERROR: {str(e)}")
        
        ttk.Button(button_frame, text="Execute Tasks", command=execute_tasks).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
            
    def _on_endpoint_request(self, method: str, path: str, params: Dict[str, Any], 
                            headers: Dict[str, Any], body: Optional[str] = None):
        """Handle endpoint request."""
        if not self.api_client:
            messagebox.showerror("Error", "Please configure the base URL first")
            return
            
        try:
            response = self.api_client.make_request(
                method=method,
                path=path,
                params=params,
                headers=headers,
                body=body
            )
            
            self.response_frame.display_response(response)
            
        except Exception as e:
            messagebox.showerror("Request Failed", f"Error making request:\n{str(e)}")
            self.response_frame.display_error(str(e))
            
    def _filter_endpoints(self):
        """Filter endpoints based on search term."""
        search_term = self.search_var.get().lower().strip()
        
        for endpoint_data in self.endpoint_frames:
            frame = endpoint_data['frame']
            
            if not search_term:
                # Show all endpoints if search is empty
                frame.pack(fill=tk.X, padx=5, pady=2)
            else:
                # Check if search term matches any field
                matches = (
                    search_term in endpoint_data['path'].lower() or
                    any(search_term in method.lower() for method in endpoint_data['methods']) or
                    any(search_term in summary.lower() for summary in endpoint_data['summaries'] if summary) or
                    any(search_term in desc.lower() for desc in endpoint_data['descriptions'] if desc) or
                    any(search_term in tag.lower() for tag in endpoint_data['tags'] if tag) or
                    any(search_term in op_id.lower() for op_id in endpoint_data['operation_ids'] if op_id)
                )
                
                if matches:
                    frame.pack(fill=tk.X, padx=5, pady=2)
                else:
                    frame.pack_forget()
        
        # Update canvas scroll region
        self.endpoints_scrollable.update_idletasks()
        self.endpoints_canvas.configure(scrollregion=self.endpoints_canvas.bbox("all"))
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """REST Data Loader - Tkinter v1.0

A basic Tkinter-based GUI for REST API testing and data loading.

Features:
- Multiple API configurations
- OpenAPI specification support
- Dynamic endpoint generation
- Autonomous data loading
- Request/Response viewer

Built with Tkinter and Python."""
        messagebox.showinfo("About", about_text)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = RESTDataLoaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

