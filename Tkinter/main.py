"""
Main entry point for the REST Data Loader application (Tkinter GUI).
A basic Tkinter-based GUI for interacting with REST APIs using OpenAPI specifications.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import Dict, Any, Optional
import threading
from pathlib import Path
from datetime import datetime
import sys
import json

# Add parent directory to path to import Essentials
sys.path.insert(0, str(Path(__file__).parent.parent / 'Essentials'))

from openapi_parser import OpenAPIParser
from api_client import APIClient
from gui_components import EndpointFrame, ConfigFrame, ResponseFrame, TaskConfigEditor
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
        file_menu.add_command(label="Manage API Configurations", command=lambda: self.notebook.select(1))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Autonomous Data Loader", command=lambda: self.notebook.select(2))
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        
    def _create_main_layout(self):
        """Create the main application layout with tabbed interface."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: API Testing
        self._create_api_testing_tab()
        
        # Tab 2: Config Management
        self._create_config_management_tab()
        
        # Tab 3: Autonomous Loader
        self._create_autonomous_loader_tab()
    
    def _create_api_testing_tab(self):
        """Create the API Testing tab."""
        api_tab = ttk.Frame(self.notebook)
        self.notebook.add(api_tab, text="API Testing")
        
        # Create paned window for resizable panels
        main_paned = ttk.PanedWindow(api_tab, orient=tk.HORIZONTAL)
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
            text="Refresh Spec",
            command=self._refresh_current_config_spec
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            config_selector_frame,
            text="Switch to Config Tab",
            command=lambda: self.notebook.select(1)
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
        
        # Status bar at bottom of API Testing tab
        status_frame = ttk.Frame(api_tab)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        self.status_label = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_label.pack(fill=tk.X)
    
    def _create_config_management_tab(self):
        """Create the Config Management tab."""
        config_tab = ttk.Frame(self.notebook)
        self.notebook.add(config_tab, text="Config Management")
        
        # Add Configuration Form
        add_frame = ttk.LabelFrame(config_tab, text="Add New Configuration", padding=10)
        add_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Configuration name
        name_frame = ttk.Frame(add_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="Name:", width=12).pack(side=tk.LEFT, padx=5)
        self.new_config_name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.new_config_name_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Base URL
        url_frame = ttk.Frame(add_frame)
        url_frame.pack(fill=tk.X, pady=5)
        ttk.Label(url_frame, text="Base URL:", width=12).pack(side=tk.LEFT, padx=5)
        self.new_config_url_var = tk.StringVar()
        ttk.Entry(url_frame, textvariable=self.new_config_url_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Spec file
        spec_frame = ttk.Frame(add_frame)
        spec_frame.pack(fill=tk.X, pady=5)
        ttk.Label(spec_frame, text="OpenAPI Spec:", width=12).pack(side=tk.LEFT, padx=5)
        self.new_config_spec_var = tk.StringVar()
        ttk.Entry(spec_frame, textvariable=self.new_config_spec_var, width=40, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(
            spec_frame,
            text="Browse",
            command=lambda: self.new_config_spec_var.set(filedialog.askopenfilename(
                title="Select OpenAPI Spec (Optional)",
                filetypes=[("YAML files", "*.yaml *.yml"), ("JSON files", "*.json"), ("All files", "*.*")]
            ))
        ).pack(side=tk.LEFT, padx=5)
        
        # Error message label
        self.config_error_label = ttk.Label(add_frame, text="", foreground="red", wraplength=600)
        self.config_error_label.pack(pady=5)
        
        # Add button
        add_button_frame = ttk.Frame(add_frame)
        add_button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(add_button_frame, text="Add Configuration", command=self._add_config_from_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(add_button_frame, text="Clear Form", command=self._clear_config_form).pack(side=tk.LEFT, padx=5)
        
        # List of configurations
        list_frame = ttk.LabelFrame(config_tab, text="Existing Configurations", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for configs
        columns = ('Name', 'Base URL', 'Spec File')
        self.config_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.config_tree.heading(col, text=col)
            self.config_tree.column(col, width=200)
        
        # Scrollbar for treeview
        tree_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.config_tree.yview)
        self.config_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.config_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate tree
        self._refresh_config_tree()
        
        # Buttons
        button_frame = ttk.Frame(config_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def remove_config():
            selection = self.config_tree.selection()
            if not selection:
                self.config_error_label.config(text="Please select a configuration to remove", foreground="orange")
                return
            
            item = self.config_tree.item(selection[0])
            config_name = item['values'][0]
            
            # Remove without confirmation pop-up
            try:
                self.config_manager.remove_config(config_name)
                self._refresh_config_tree()
                self._refresh_config_selector()
                self.config_error_label.config(text=f"Configuration '{config_name}' removed successfully", foreground="green")
                # Clear message after 3 seconds
                self.root.after(3000, lambda: self.config_error_label.config(text=""))
            except Exception as e:
                self.config_error_label.config(text=f"Error removing configuration: {str(e)}", foreground="red")
        
        def refresh_config_list():
            """Refresh the configuration list display."""
            self._refresh_config_tree()
            self._refresh_config_selector()
            self.config_error_label.config(text="Configurations list refreshed", foreground="green")
            self.root.after(2000, lambda: self.config_error_label.config(text=""))
        
        def refresh_openapi_spec():
            """Refresh the OpenAPI spec for the selected configuration."""
            selection = self.config_tree.selection()
            if not selection:
                self.config_error_label.config(text="Please select a configuration to refresh", foreground="orange")
                return
            
            item = self.config_tree.item(selection[0])
            config_name = item['values'][0]
            
            config = self.config_manager.get_config(config_name)
            if not config:
                self.config_error_label.config(text=f"Configuration '{config_name}' not found", foreground="red")
                return
            
            if not config.openapi_spec_path:
                self.config_error_label.config(
                    text=f"Configuration '{config_name}' has no OpenAPI spec path configured", 
                    foreground="orange"
                )
                return
            
            try:
                # Refresh the OpenAPI spec
                self.config_manager.refresh_config(config_name)
                
                # If this is the current config, reload endpoints
                if self.current_config and self.current_config.name == config_name:
                    self.openapi_spec = config.openapi_spec
                    self.endpoints = config.endpoints
                    self._reload_endpoints()
                
                self.config_error_label.config(
                    text=f"OpenAPI spec refreshed for '{config_name}' ({len(config.endpoints)} endpoint(s))", 
                    foreground="green"
                )
                # Clear message after 3 seconds
                self.root.after(3000, lambda: self.config_error_label.config(text=""))
            except Exception as e:
                self.config_error_label.config(
                    text=f"Error refreshing OpenAPI spec: {str(e)}", 
                    foreground="red"
                )
        
        ttk.Button(button_frame, text="Remove Selected", command=remove_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh OpenAPI Spec", command=refresh_openapi_spec).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh List", command=refresh_config_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Switch to API Testing", command=lambda: self.notebook.select(0)).pack(side=tk.RIGHT, padx=5)
    
    def _add_config_from_form(self):
        """Add configuration from the form fields."""
        name = self.new_config_name_var.get().strip()
        base_url = self.new_config_url_var.get().strip()
        spec_path = self.new_config_spec_var.get().strip()
        
        # Validation
        if not name:
            self.config_error_label.config(text="Please enter a configuration name", foreground="red")
            return
        
        if not base_url:
            self.config_error_label.config(text="Please enter a base URL", foreground="red")
            return
        
        try:
            self.config_manager.add_config(
                name=name,
                base_url=base_url,
                openapi_spec_path=spec_path if spec_path else None
            )
            self._refresh_config_tree()
            self._refresh_config_selector()
            self.config_error_label.config(text=f"Configuration '{name}' added successfully", foreground="green")
            self._clear_config_form()
            # Clear success message after 3 seconds
            self.root.after(3000, lambda: self.config_error_label.config(text=""))
        except ValueError as e:
            self.config_error_label.config(text=f"Error: {str(e)}", foreground="red")
    
    def _clear_config_form(self):
        """Clear the add configuration form."""
        self.new_config_name_var.set("")
        self.new_config_url_var.set("")
        self.new_config_spec_var.set("")
        self.config_error_label.config(text="")
    
    def _create_autonomous_loader_tab(self):
        """Create the Autonomous Loader tab with integrated task editor."""
        loader_tab = ttk.Frame(self.notebook)
        self.notebook.add(loader_tab, text="Autonomous Loader")
        
        # Create notebook for editor and execution
        loader_notebook = ttk.Notebook(loader_tab)
        loader_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: Task Editor
        editor_tab = ttk.Frame(loader_notebook)
        loader_notebook.add(editor_tab, text="Task Editor")
        
        # Create task editor
        def save_config_callback(config_name: str, config_data: Dict[str, Any]):
            """Save task configuration to file."""
            file_path = filedialog.asksaveasfilename(
                title="Save Task Configuration",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"{config_name}.json"
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                return file_path
            return None
        
        self.task_editor = TaskConfigEditor(editor_tab, self.config_manager, save_config_callback)
        self.task_editor.pack(fill=tk.BOTH, expand=True)
        
        # Tab 2: Execution
        execution_tab = ttk.Frame(loader_notebook)
        loader_notebook.add(execution_tab, text="Execute Tasks")
        
        # Instructions
        info_frame = ttk.LabelFrame(execution_tab, text="Instructions", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        info_text = """Execute tasks from the editor or load a task configuration file (JSON).
Tasks will be executed sequentially with the configured delays."""
        ttk.Label(info_frame, text=info_text, wraplength=650).pack()
        
        # Execution options
        options_frame = ttk.LabelFrame(execution_tab, text="Execution Options", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Source selection
        source_frame = ttk.Frame(options_frame)
        source_frame.pack(fill=tk.X, pady=5)
        
        self.task_source_var = tk.StringVar(value="editor")
        ttk.Radiobutton(source_frame, text="Use Editor Config", variable=self.task_source_var, 
                       value="editor").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(source_frame, text="Load from File", variable=self.task_source_var, 
                       value="file").pack(side=tk.LEFT, padx=10)
        
        # File selection (for file source)
        file_frame = ttk.Frame(options_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.task_file_var = tk.StringVar()
        ttk.Label(file_frame, text="Task File:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(file_frame, textvariable=self.task_file_var, width=50, state='readonly').pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(
            file_frame,
            text="Browse",
            command=lambda: self.task_file_var.set(filedialog.askopenfilename(
                title="Select Task Configuration File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            ))
        ).pack(side=tk.LEFT, padx=5)
        
        # Editor config selector (for editor source)
        editor_config_frame = ttk.Frame(options_frame)
        editor_config_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(editor_config_frame, text="Editor Config:").pack(side=tk.LEFT, padx=5)
        self.editor_config_selector_var = tk.StringVar()
        self.editor_config_selector = ttk.Combobox(editor_config_frame, 
                                                   textvariable=self.editor_config_selector_var,
                                                   state="readonly", width=30)
        self.editor_config_selector.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Execution options
        options_inner_frame = ttk.Frame(options_frame)
        options_inner_frame.pack(fill=tk.X, pady=5)
        
        self.stop_on_error_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_inner_frame, text="Stop on Error", 
                       variable=self.stop_on_error_var).pack(side=tk.LEFT, padx=10)
        
        # Progress
        progress_frame = ttk.LabelFrame(execution_tab, text="Progress", padding=10)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.progress_text = tk.Text(progress_frame, height=20, wrap=tk.WORD, font=("Consolas", 9))
        self.progress_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        progress_scrollbar = ttk.Scrollbar(progress_frame, orient="vertical", command=self.progress_text.yview)
        progress_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.progress_text.configure(yscrollcommand=progress_scrollbar.set)
        
        # Buttons
        button_frame = ttk.Frame(execution_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def update_progress(message):
            self.progress_text.insert(tk.END, message + "\n")
            self.progress_text.see(tk.END)
            self.root.update()
        
        def on_task_complete(task, result):
            """Stream individual task results to progress dialog."""
            status_icon = "✓" if result['success'] else "✗"
            status_code = ""
            response_info = ""
            
            if result['success']:
                response = result.get('response', {})
                status_code = response.get('status_code', 'N/A')
                response_info = f"Status: {status_code}"
                
                # Add response body preview if available
                if 'json' in response:
                    json_data = response['json']
                    # Show a preview of the response
                    try:
                        preview = json.dumps(json_data, indent=2, ensure_ascii=False)
                        if len(preview) > 200:
                            preview = preview[:200] + "..."
                        response_info += f"\nResponse: {preview}"
                    except:
                        pass
                elif 'body' in response:
                    body = response['body']
                    if len(body) > 200:
                        body = body[:200] + "..."
                    response_info += f"\nResponse: {body}"
            else:
                error = result.get('error', 'Unknown error')
                response_info = f"Error: {error}"
            
            update_progress(f"\n{status_icon} Task {task.method} {task.path}")
            update_progress(f"  Config: {task.config_name}")
            update_progress(f"  {response_info}")
            update_progress(f"  Executed at: {result.get('executed_at', 'N/A')}")
            update_progress("")
        
        def on_complete(tasks):
            update_progress(f"\n{'='*60}")
            update_progress(f"=== Execution Complete ===")
            update_progress(f"{'='*60}")
            update_progress(f"Total tasks: {len(tasks)}")
            success_count = sum(1 for t in tasks if t.result and not t.error)
            update_progress(f"Successful: {success_count}")
            update_progress(f"Failed: {len(tasks) - success_count}")
            update_progress(f"{'='*60}\n")
        
        def on_error(task, error):
            update_progress(f"✗ ERROR: {task.config_name} - {task.method} {task.path}: {error}")
        
        def execute_tasks():
            self.progress_text.delete(1.0, tk.END)
            update_progress("=== Starting Autonomous Data Loader ===\n")
            
            try:
                # Create loader
                self.autonomous_loader = AutonomousLoader(
                    config_manager=self.config_manager,
                    on_progress=update_progress,
                    on_complete=on_complete,
                    on_error=on_error,
                    on_task_complete=on_task_complete
                )
                
                # Get tasks based on source
                source = self.task_source_var.get()
                tasks = []
                
                if source == "editor":
                    # Get tasks from editor
                    config_name = self.editor_config_selector_var.get()
                    if not config_name:
                        update_progress("ERROR: Please select a configuration from the editor")
                        return
                    
                    config_data = self.task_editor.get_current_config_data()
                    if not config_data:
                        update_progress("ERROR: No tasks in selected configuration")
                        return
                    
                    tasks_data = config_data.get('tasks', [])
                    update_progress(f"Loading {len(tasks_data)} task(s) from editor config: {config_name}")
                    
                    # Convert to RequestTask objects
                    for task_data in tasks_data:
                        try:
                            task = RequestTask.from_dict(task_data)
                            tasks.append(task)
                        except Exception as e:
                            update_progress(f"WARNING: Failed to parse task: {e}")
                            continue
                
                else:  # file source
                    task_file = self.task_file_var.get()
                    if not task_file:
                        update_progress("ERROR: Please select a task configuration file")
                        return
                    
                    update_progress(f"Loading tasks from: {task_file}")
                    tasks = self.autonomous_loader.load_tasks_from_file(task_file)
                
                if not tasks:
                    update_progress("ERROR: No tasks to execute")
                    return
                
                self.autonomous_loader.add_tasks(tasks)
                update_progress(f"Loaded {len(tasks)} task(s)\n")
                
                # Execute in separate thread to avoid blocking UI
                def run_loader():
                    self.autonomous_loader.execute_all(stop_on_error=self.stop_on_error_var.get())
                
                thread = threading.Thread(target=run_loader, daemon=True)
                thread.start()
                
            except Exception as e:
                update_progress(f"ERROR: Failed to execute tasks: {str(e)}")
                import traceback
                update_progress(traceback.format_exc())
        
        def refresh_editor_configs():
            """Refresh editor config selector."""
            if hasattr(self, 'task_editor'):
                config_data = self.task_editor.get_current_config_data()
                # Get all config names from editor
                # We need to access the editor's internal configs
                # For now, just update based on current selection
                current_config = self.task_editor.current_config_name
                if current_config:
                    self.editor_config_selector_var.set(current_config)
                    # Update dropdown values
                    config_names = list(self.task_editor.task_configs.keys())
                    self.editor_config_selector['values'] = config_names
        
        def switch_to_editor():
            """Switch to editor tab and refresh."""
            loader_notebook.select(0)
            refresh_editor_configs()
        
        def export_results():
            """Export results to file."""
            if not hasattr(self, 'autonomous_loader') or not self.autonomous_loader:
                messagebox.showwarning("No Results", "No execution results available to export")
                return
            
            # Ask for export format
            export_format = messagebox.askyesno(
                "Export Format",
                "Export as JSON?\n\nYes = JSON format\nNo = Text format"
            )
            
            file_path = filedialog.asksaveasfilename(
                title="Export Results",
                defaultextension=".json" if export_format else ".txt",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            try:
                if export_format:
                    # Export as JSON
                    self.autonomous_loader.save_results(file_path)
                    messagebox.showinfo("Export Complete", f"Results exported to:\n{file_path}")
                else:
                    # Export as formatted text
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("=" * 80 + "\n")
                        f.write("AUTONOMOUS LOADER EXECUTION RESULTS\n")
                        f.write("=" * 80 + "\n\n")
                        f.write(f"Executed at: {datetime.now().isoformat()}\n")
                        f.write(f"Total tasks: {len(self.autonomous_loader.tasks)}\n\n")
                        
                        for idx, result in enumerate(self.autonomous_loader.results, 1):
                            task = result['task']
                            f.write("-" * 80 + "\n")
                            f.write(f"Task {idx}: {task.method} {task.path}\n")
                            f.write(f"Config: {task.config_name}\n")
                            f.write(f"Executed at: {result.get('executed_at', 'N/A')}\n")
                            
                            if result['success']:
                                response = result.get('response', {})
                                status_code = response.get('status_code', 'N/A')
                                f.write(f"Status: {status_code} ✓\n")
                                
                                # Write response body
                                if 'json' in response:
                                    f.write("\nResponse JSON:\n")
                                    f.write(json.dumps(response['json'], indent=2, ensure_ascii=False))
                                    f.write("\n")
                                elif 'body' in response:
                                    f.write("\nResponse Body:\n")
                                    f.write(response['body'])
                                    f.write("\n")
                            else:
                                f.write(f"Status: ERROR ✗\n")
                                f.write(f"Error: {result.get('error', 'Unknown error')}\n")
                            
                            f.write("\n")
                        
                        f.write("=" * 80 + "\n")
                        f.write("END OF RESULTS\n")
                        f.write("=" * 80 + "\n")
                    
                    messagebox.showinfo("Export Complete", f"Results exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export results:\n{str(e)}")
        
        def export_progress_text():
            """Export current progress text to file."""
            content = self.progress_text.get(1.0, tk.END)
            if not content.strip():
                messagebox.showwarning("No Content", "Progress dialog is empty")
                return
            
            file_path = filedialog.asksaveasfilename(
                title="Export Progress Log",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    messagebox.showinfo("Export Complete", f"Progress log exported to:\n{file_path}")
                except Exception as e:
                    messagebox.showerror("Export Error", f"Failed to export:\n{str(e)}")
        
        ttk.Button(button_frame, text="Execute Tasks", command=execute_tasks).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Progress", command=lambda: self.progress_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Results", command=export_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Log", command=export_progress_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Switch to Editor", command=switch_to_editor).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Switch to API Testing", command=lambda: self.notebook.select(0)).pack(side=tk.RIGHT, padx=5)
        
        # Update editor config selector when task source changes
        def on_source_change(*args):
            source = self.task_source_var.get()
            if source == "editor":
                refresh_editor_configs()
                # Update editor config selector values periodically
                if hasattr(self, 'task_editor'):
                    config_names = list(self.task_editor.task_configs.keys())
                    self.editor_config_selector['values'] = config_names
        
        self.task_source_var.trace('w', on_source_change)
        
        # Periodically refresh editor config selector
        def periodic_refresh():
            if self.task_source_var.get() == "editor" and hasattr(self, 'task_editor'):
                config_names = list(self.task_editor.task_configs.keys())
                self.editor_config_selector['values'] = config_names
                if not self.editor_config_selector_var.get() and config_names:
                    self.editor_config_selector_var.set(config_names[0])
            self.root.after(1000, periodic_refresh)
        
        periodic_refresh()
    
    def _refresh_config_tree(self):
        """Refresh the configuration tree in the Config Management tab."""
        if not hasattr(self, 'config_tree'):
            return
        
        for item in self.config_tree.get_children():
            self.config_tree.delete(item)
        for config in self.config_manager.get_all_configs():
            spec_file = Path(config.openapi_spec_path).name if config.openapi_spec_path else "None"
            self.config_tree.insert('', 'end', values=(config.name, config.base_url, spec_file))
        
    def _refresh_config_selector(self):
        """Refresh the configuration selector dropdown."""
        configs = self.config_manager.get_config_names()
        if hasattr(self, 'config_selector'):
            self.config_selector['values'] = configs
            if self.config_manager.active_config:
                self.config_selector_var.set(self.config_manager.active_config)
                self._on_config_selected()
            elif configs:
                self.config_selector_var.set(configs[0])
                self.config_manager.set_active_config(configs[0])
                self._on_config_selected()
        
        # Also refresh the config tree if it exists
        self._refresh_config_tree()
    
    def _refresh_current_config_spec(self):
        """Refresh the OpenAPI spec for the currently selected configuration."""
        config_name = self.config_selector_var.get()
        if not config_name:
            self._set_status("No configuration selected", "orange")
            return
        
        config = self.config_manager.get_config(config_name)
        if not config:
            self._set_status(f"Configuration '{config_name}' not found", "red")
            return
        
        if not config.openapi_spec_path:
            self._set_status(f"Configuration '{config_name}' has no OpenAPI spec path", "orange")
            return
        
        try:
            # Refresh the OpenAPI spec
            self.config_manager.refresh_config(config_name)
            
            # Update current config reference
            self.current_config = config
            self.openapi_spec = config.openapi_spec
            self.endpoints = config.endpoints
            
            # Reload endpoints in UI
            self._reload_endpoints()
            
            self._set_status(
                f"OpenAPI spec refreshed for '{config_name}' ({len(config.endpoints)} endpoint(s))", 
                "green"
            )
        except Exception as e:
            self._set_status(f"Error refreshing OpenAPI spec: {str(e)}", "red")
    
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
            self._set_status(f"Base URL updated: {self.base_url}", "green")
        else:
            self.api_client = None
            self._set_status("Base URL cleared", "orange")
    
    def _set_status(self, message: str, color: str = "black"):
        """Set status message in the status bar."""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message, foreground=color)
            
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
            # Generate a default name from filename
            file_name = Path(file_path).stem
            config_name = file_name.replace('_', ' ').replace('-', ' ').title()
            
            # Make name unique
            base_name = config_name
            counter = 1
            while config_name in self.config_manager.get_config_names():
                config_name = f"{base_name} {counter}"
                counter += 1
            
            # Try to get base URL from spec
            try:
                parser = OpenAPIParser()
                spec = parser.parse(file_path)
                spec_base_url = parser.get_base_url()
            except:
                spec_base_url = None
            
            # If no base URL in spec, use default
            if not spec_base_url:
                spec_base_url = "http://localhost:8000"
            
            # Switch to Config Management tab and pre-fill the form
            self.notebook.select(1)
            self.new_config_name_var.set(config_name)
            self.new_config_url_var.set(spec_base_url)
            self.new_config_spec_var.set(file_path)
            self.config_error_label.config(
                text=f"Form pre-filled. Review and click 'Add Configuration' to create the config.",
                foreground="blue"
            )
            return
        
        # Load into current config
        try:
            self.current_config.load_openapi_spec(file_path)
            self.openapi_spec = self.current_config.openapi_spec
            self.endpoints = self.current_config.endpoints
        except Exception as e:
            self._set_status(f"Error loading OpenAPI spec: {str(e)}", "red")
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
            self._set_status(f"Loaded {len(self.endpoints)} endpoint(s) from specification", "green")
        else:
            self._set_status("No endpoints found in the OpenAPI specification", "orange")
    
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
                try:
                    parser = OpenAPIParser()
                    spec = parser.parse(file_path)
                    spec_base_url = parser.get_base_url()
                except:
                    spec_base_url = None
                
                # If no base URL in spec, use default
                if not spec_base_url:
                    spec_base_url = "http://localhost:8000"
                
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
        
        # Show results in status bar
        if errors:
            error_msg = f"Loaded {loaded_count} config(s). Errors: {', '.join(errors[:3])}"
            if len(errors) > 3:
                error_msg += f" (+{len(errors) - 3} more)"
            self._set_status(error_msg, "orange")
        else:
            self._set_status(f"Successfully loaded {loaded_count} configuration(s)", "green")
    
            
    def _on_endpoint_request(self, method: str, path: str, params: Dict[str, Any], 
                            headers: Dict[str, Any], body: Optional[str] = None,
                            multipart_data: Optional[Dict[str, Any]] = None,
                            multipart_files: Optional[Dict[str, Any]] = None):
        """Handle endpoint request."""
        if not self.api_client:
            self._set_status("Error: Please configure the base URL first", "red")
            return
            
        try:
            self._set_status(f"Sending {method} request to {path}...", "blue")
            response = self.api_client.make_request(
                method=method,
                path=path,
                params=params,
                headers=headers,
                body=body,
                multipart_data=multipart_data,
                multipart_files=multipart_files
            )
            
            self.response_frame.display_response(response)
            status_code = response.get('status_code', 0)
            if 200 <= status_code < 300:
                self._set_status(f"Request successful: {status_code}", "green")
            else:
                self._set_status(f"Request completed with status: {status_code}", "orange")
            
        except Exception as e:
            self._set_status(f"Request failed: {str(e)}", "red")
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

