// REST Data Loader - Web GUI Frontend
const API_BASE = 'http://localhost:5000/api';

// Global state
let currentConfig = null;
let currentEndpoints = {};
let currentEndpoint = null;
let currentMethod = null;
let currentOpenApiSpec = null;
let savedTasks = []; // Store created tasks

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    // Test API connection first
    const connected = await testAPIConnection();
    if (connected) {
        await initializeApp();
    }
});

async function initializeApp() {
    await loadConfigurations();
    setupEventListeners();
}

// ==================== Configuration Management ====================

async function loadConfigurations() {
    try {
        const response = await fetch(`${API_BASE}/configs`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        const selector = document.getElementById('configSelector');
        selector.innerHTML = '<option value="">No Configuration</option>';
        
        if (data.configs && Array.isArray(data.configs)) {
            data.configs.forEach(config => {
                const option = document.createElement('option');
                option.value = config.name;
                option.textContent = config.name;
                selector.appendChild(option);
            });
            
            if (data.active_config) {
                selector.value = data.active_config;
                await selectConfiguration(data.active_config);
            }
        }
    } catch (error) {
        console.error('Failed to load configurations:', error);
        showError('Failed to load configurations: ' + error.message);
    }
}

async function selectConfiguration(configName) {
    if (!configName) {
        currentConfig = null;
        currentEndpoints = {};
        updateEndpointsList([]);
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/configs/${configName}`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load configuration');
        }
        
        currentConfig = configName;
        document.getElementById('baseUrl').value = data.base_url || '';
        
        if (data.has_openapi_spec) {
            await loadEndpoints(configName);
        } else {
            currentEndpoints = {};
            updateEndpointsList([]);
        }
    } catch (error) {
        console.error('Failed to select configuration:', error);
        showError(error.message || 'Failed to load configuration');
    }
}

async function loadEndpoints(configName) {
    try {
        const response = await fetch(`${API_BASE}/configs/${configName}/endpoints`);
        const data = await response.json();
        
        if (data.success && data.endpoints) {
            currentEndpoints = data.endpoints;
            currentOpenApiSpec = data.openapi_spec || null;
            updateEndpointsList(Object.keys(data.endpoints));
        }
    } catch (error) {
        console.error('Failed to load endpoints:', error);
    }
}

// ==================== UI Updates ====================

function updateEndpointsList(endpointPaths) {
    const list = document.getElementById('endpointsList');
    
    if (endpointPaths.length === 0) {
        list.innerHTML = '<div class="empty-state">No endpoints loaded. Load an OpenAPI specification to get started.</div>';
        return;
    }
    
    list.innerHTML = endpointPaths.map(path => {
        const methods = currentEndpoints[path] || {};
        const methodList = Object.keys(methods).join(', ').toUpperCase();
        
        return `
            <div class="endpoint-item" data-path="${path}">
                <div class="endpoint-item-path">${path}</div>
                <div class="endpoint-item-methods">${methodList}</div>
            </div>
        `;
    }).join('');
    
    // Add click handlers
    list.querySelectorAll('.endpoint-item').forEach(item => {
        item.addEventListener('click', () => {
            const path = item.dataset.path;
            selectEndpoint(path);
            
            // Update active state
            list.querySelectorAll('.endpoint-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

function selectEndpoint(path) {
    currentEndpoint = path;
    const methods = currentEndpoints[path] || {};
    const methodNames = Object.keys(methods);
    
    if (methodNames.length === 0) return;
    
    // Show endpoint details panel
    const detailsPanel = document.getElementById('endpointDetails');
    detailsPanel.style.display = 'block';
    
    // Update path
    document.getElementById('endpointPath').textContent = path;
    
    // Update method selector
    const methodSelect = document.getElementById('methodSelect');
    methodSelect.innerHTML = methodNames.map(m => `<option value="${m}">${m.toUpperCase()}</option>`).join('');
    methodSelect.value = methodNames[0];
    
    currentMethod = methodNames[0];
    updateMethodDetails(methodNames[0], methods[methodNames[0]]);
    
    // Add change handler
    methodSelect.onchange = (e) => {
        currentMethod = e.target.value;
        updateMethodDetails(currentMethod, methods[currentMethod]);
    };
}

function updateMethodDetails(method, methodInfo) {
    // Update requirements section
    updateRequirementsSection(methodInfo);
    
    // Update parameters section
    updateParametersSection(methodInfo);
    
    // Update request body section
    updateRequestBodySection(method, methodInfo);
}

function updateRequirementsSection(methodInfo) {
    const section = document.getElementById('requirementsSection');
    const params = methodInfo.parameters || [];
    const requestBody = methodInfo.request_body;
    
    const requiredParams = params.filter(p => p.required);
    const optionalParams = params.filter(p => !p.required);
    
    let html = '<h3>📋 Configuration Requirements</h3>';
    
    if (methodInfo.description) {
        html += `<p>${methodInfo.description}</p>`;
    }
    
    if (requiredParams.length > 0) {
        html += `<p class="required-params">Required Parameters (${requiredParams.length}): ${requiredParams.map(p => `${p.name} (${p.in})`).join(', ')}</p>`;
    }
    
    if (optionalParams.length > 0) {
        html += `<p class="optional-params">Optional Parameters (${optionalParams.length}): ${optionalParams.map(p => `${p.name} (${p.in})`).join(', ')}</p>`;
    }
    
    if (requestBody) {
        const required = requestBody.required ? 'Required' : 'Optional';
        html += `<p class="${requestBody.required ? 'required-params' : 'optional-params'}">Request Body: ${required}</p>`;
    }
    
    if (params.length === 0 && !requestBody) {
        html += '<p class="optional-params">No additional configuration required</p>';
    }
    
    section.innerHTML = html;
}

function updateParametersSection(methodInfo) {
    const section = document.getElementById('parametersSection');
    const params = methodInfo.parameters || [];
    
    if (params.length === 0) {
        section.innerHTML = '';
        return;
    }
    
    let html = '<h3>Parameters</h3>';
    
    params.forEach(param => {
        const schema = param.schema || {};
        const type = schema.type || 'string';
        const example = schema.example || param.example || schema.default || '';
        const description = param.description || '';
        
        html += `
            <div class="parameter-item">
                <div class="parameter-label">
                    <span class="param-name">
                        ${param.name}
                        ${param.required ? '<span class="param-required">*</span>' : ''}
                    </span>
                    <div class="param-info">${type} (${param.in})${example ? ` - Example: ${example}` : ''}</div>
                    ${description ? `<div class="param-info" style="font-size: 10px; margin-top: 2px;">${description}</div>` : ''}
                </div>
                <div class="parameter-input">
                    <input type="text" 
                           class="input param-input" 
                           data-param="${param.name}" 
                           data-in="${param.in}"
                           placeholder="Enter ${param.name}${example ? ` (e.g., ${example})` : ''}">
                </div>
            </div>
        `;
    });
    
    section.innerHTML = html;
}

function resolveSchemaRef(schema) {
    /**
     * Resolve $ref references in a schema using the OpenAPI spec.
     */
    if (!schema || typeof schema !== 'object') {
        return schema;
    }
    
    // If this schema has a $ref, resolve it
    if (schema.$ref && currentOpenApiSpec) {
        const refPath = schema.$ref.substring(1).split('/').filter(p => p); // Remove leading '#' and empty parts
        let resolved = currentOpenApiSpec;
        
        for (const part of refPath) {
            if (resolved && typeof resolved === 'object' && part in resolved) {
                resolved = resolved[part];
            } else {
                console.warn('Could not resolve $ref:', schema.$ref, 'at path part:', part);
                return schema; // Can't resolve, return original
            }
        }
        
        if (resolved && typeof resolved === 'object') {
            // Create a deep copy to avoid modifying the original
            const resolvedCopy = JSON.parse(JSON.stringify(resolved));
            // Recursively resolve any nested $ref in the resolved schema
            const result = resolveSchemaRef(resolvedCopy);
            // Merge any additional properties from the original schema (except $ref)
            for (const key in schema) {
                if (key !== '$ref' && !(key in result)) {
                    result[key] = schema[key];
                }
            }
            return result;
        } else {
            console.warn('Resolved $ref is not an object:', schema.$ref);
            return schema;
        }
    }
    
    // If no $ref, recursively resolve nested schemas
    const result = {};
    for (const key in schema) {
        if (key === '$ref') {
            // Skip $ref here, it's handled above
            continue;
        } else if (Array.isArray(schema[key])) {
            result[key] = schema[key].map(item => 
                typeof item === 'object' && item !== null ? resolveSchemaRef(item) : item
            );
        } else if (typeof schema[key] === 'object' && schema[key] !== null) {
            result[key] = resolveSchemaRef(schema[key]);
        } else {
            result[key] = schema[key];
        }
    }
    
    return result;
}

function updateRequestBodySection(method, methodInfo) {
    const section = document.getElementById('requestBodySection');
    const requestBody = methodInfo.request_body;
    
    if (!requestBody || !['POST', 'PUT', 'PATCH'].includes(method.toUpperCase())) {
        section.innerHTML = '';
        window.currentBodySchema = null;
        return;
    }
    
    const required = requestBody.required;
    const bodyContent = requestBody.content || {};
    let jsonSchema = bodyContent['application/json']?.schema || bodyContent['application/json'] || {};
    
    console.log('=== Update Request Body Section ===');
    console.log('Method:', method);
    console.log('Request body:', requestBody);
    console.log('Body content:', bodyContent);
    console.log('Original schema before resolution:', jsonSchema);
    console.log('Has $ref:', jsonSchema && jsonSchema.$ref);
    
    // Resolve $ref references if present
    if (jsonSchema) {
        if (jsonSchema.$ref) {
            console.log('Resolving $ref:', jsonSchema.$ref);
            jsonSchema = resolveSchemaRef(jsonSchema);
            console.log('Resolved schema:', jsonSchema);
        } else if (Object.keys(jsonSchema).length > 0) {
            // Even if no $ref, recursively resolve any nested $ref
            jsonSchema = resolveSchemaRef(jsonSchema);
        }
    }
    
    let html = '<h3>Request Body (JSON)</h3>';
    
    if (required) {
        html += '<p class="required-params">* Required</p>';
    }
    
    if (jsonSchema && jsonSchema.type) {
        html += `<p style="font-size: 11px; color: var(--text-muted);">Schema: ${jsonSchema.type}`;
        if (jsonSchema.required) {
            html += ` | Required fields: ${jsonSchema.required.join(', ')}`;
        }
        html += '</p>';
    } else if (jsonSchema && jsonSchema.properties) {
        html += `<p style="font-size: 11px; color: var(--text-muted);">Schema: object`;
        if (jsonSchema.required) {
            html += ` | Required fields: ${jsonSchema.required.join(', ')}`;
        }
        html += '</p>';
    } else if (jsonSchema && jsonSchema.$ref) {
        html += `<p style="font-size: 11px; color: var(--text-muted);">Schema: reference (${jsonSchema.$ref})</p>`;
    }
    
    html += `
        <textarea id="requestBody" class="request-body-textarea" placeholder='Enter JSON body...'></textarea>
    `;
    
    section.innerHTML = html;
    
    // Store resolved schema for example generation
    window.currentBodySchema = jsonSchema;
    console.log('Stored schema for example generation:', window.currentBodySchema);
    console.log('Schema has type:', window.currentBodySchema && window.currentBodySchema.type);
    console.log('Schema has properties:', window.currentBodySchema && window.currentBodySchema.properties);
    console.log('=== End Update ===');
}

// ==================== API Requests ====================

async function sendRequest() {
    if (!currentConfig || !currentEndpoint || !currentMethod) {
        showError('Please select a configuration and endpoint');
        return;
    }
    
    const method = currentMethod.toUpperCase();
    let path = currentEndpoint;
    
    // Collect parameters
    const params = {};
    const headers = {};
    
    document.querySelectorAll('.param-input').forEach(input => {
        const value = input.value.trim();
        if (value) {
            const paramName = input.dataset.param;
            const paramIn = input.dataset.in;
            
            if (paramIn === 'query') {
                params[paramName] = value;
            } else if (paramIn === 'header') {
                headers[paramName] = value;
            } else if (paramIn === 'path') {
                path = path.replace(`{${paramName}}`, value);
            }
        }
    });
    
    // Get request body
    const bodyTextarea = document.getElementById('requestBody');
    const body = bodyTextarea ? bodyTextarea.value.trim() : null;
    
    try {
        const response = await fetch(`${API_BASE}/configs/${currentConfig}/request`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                method,
                path,
                params,
                headers,
                body
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResponse(data.response);
        } else {
            displayError(data.error || 'Request failed');
        }
    } catch (error) {
        console.error('Request failed:', error);
        displayError(error.message);
    }
}

function displayResponse(response) {
    const statusEl = document.getElementById('responseStatus');
    const infoEl = document.getElementById('responseInfo');
    const bodyEl = document.getElementById('responseBody');
    
    const statusCode = response.status_code || 0;
    statusEl.textContent = `Status: ${statusCode}`;
    
    // Color code status
    statusEl.className = 'response-status';
    if (statusCode >= 200 && statusCode < 300) {
        statusEl.classList.add('success');
        statusEl.textContent += ' ✓';
    } else if (statusCode >= 400 && statusCode < 500) {
        statusEl.classList.add('warning');
        statusEl.textContent += ' ✗';
    } else if (statusCode >= 500) {
        statusEl.classList.add('error');
        statusEl.textContent += ' ✗';
    }
    
    // Display info
    infoEl.textContent = `Method: ${response.method || 'N/A'} | URL: ${response.url || 'N/A'}`;
    
    // Display body
    if (response.json) {
        bodyEl.textContent = JSON.stringify(response.json, null, 2);
    } else {
        bodyEl.textContent = response.body || '';
    }
}

function displayError(error) {
    const statusEl = document.getElementById('responseStatus');
    const bodyEl = document.getElementById('responseBody');
    
    statusEl.textContent = 'Error ✗';
    statusEl.className = 'response-status error';
    bodyEl.textContent = `Error: ${error}`;
}

// ==================== Event Listeners ====================

function setupEventListeners() {
    // Configuration selector
    document.getElementById('configSelector').addEventListener('change', (e) => {
        selectConfiguration(e.target.value);
    });
    
    // Update URL button
    document.getElementById('updateUrlBtn').addEventListener('click', async () => {
        if (!currentConfig) {
            showError('Please select a configuration first');
            return;
        }
        
        const baseUrl = document.getElementById('baseUrl').value.trim();
        if (!baseUrl) {
            showError('Please enter a base URL');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/configs/${currentConfig}/url`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ base_url: baseUrl })
            });
            
            const data = await response.json();
            if (data.success) {
                showSuccess('Base URL updated');
            } else {
                showError(data.error || 'Failed to update URL');
            }
        } catch (error) {
            showError('Failed to update URL');
        }
    });
    
    // Set token button
    document.getElementById('setTokenBtn').addEventListener('click', async () => {
        if (!currentConfig) {
            showError('Please select a configuration first');
            return;
        }
        
        const token = document.getElementById('authToken').value.trim();
        
        try {
            const response = await fetch(`${API_BASE}/configs/${currentConfig}/auth`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ auth_token: token })
            });
            
            const data = await response.json();
            if (data.success) {
                showSuccess('Auth token updated');
            } else {
                showError(data.error || 'Failed to update token');
            }
        } catch (error) {
            showError('Failed to update token');
        }
    });
    
    // Send request button
    document.getElementById('sendRequestBtn').addEventListener('click', sendRequest);
    
    // Create task button
    document.getElementById('createTaskBtn').addEventListener('click', createTaskFromCurrentRequest);
    
    // Task manager button (we'll add this to the top bar or make it accessible)
    // For now, we'll open it from the create task action
    
    // Task manager modal buttons
    document.getElementById('saveTasksBtn').addEventListener('click', saveTasksToFile);
    document.getElementById('executeSavedTasksBtn').addEventListener('click', executeSavedTasks);
    document.getElementById('clearTasksBtn').addEventListener('click', clearAllTasks);
    
    // Load JSON button
    document.getElementById('loadJsonBtn').addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    try {
                        const json = JSON.parse(event.target.result);
                        const textarea = document.getElementById('requestBody');
                        if (textarea) {
                            textarea.value = JSON.stringify(json, null, 2);
                        }
                    } catch (error) {
                        showError('Invalid JSON file');
                    }
                };
                reader.readAsText(file);
            }
        };
        input.click();
    });
    
    // Generate example button
    document.getElementById('generateExampleBtn').addEventListener('click', () => {
        let schema = window.currentBodySchema;
        
        // Debug: Log what we have
        console.log('=== Generate Example Debug ===');
        console.log('Current schema:', schema);
        console.log('Schema type:', typeof schema);
        console.log('Has $ref:', schema && schema.$ref);
        console.log('Has type:', schema && schema.type);
        console.log('Has properties:', schema && schema.properties);
        console.log('OpenAPI spec available:', !!currentOpenApiSpec);
        
        // Try to resolve $ref if it still exists
        if (schema && schema.$ref) {
            console.log('Resolving $ref:', schema.$ref);
            schema = resolveSchemaRef(schema);
            console.log('After resolution:', schema);
            window.currentBodySchema = schema; // Update stored schema
        }
        
        // If schema is still empty or invalid, try to get it from the current endpoint
        if (!schema || (!schema.type && !schema.properties && !schema.$ref)) {
            console.log('Schema is invalid, trying to get from current endpoint');
            if (currentEndpoint && currentMethod && currentEndpoints[currentEndpoint]) {
                const methodInfo = currentEndpoints[currentEndpoint][currentMethod.toLowerCase()];
                if (methodInfo && methodInfo.request_body) {
                    const bodyContent = methodInfo.request_body.content || {};
                    schema = bodyContent['application/json']?.schema || {};
                    console.log('Retrieved schema from endpoint:', schema);
                    if (schema && schema.$ref) {
                        schema = resolveSchemaRef(schema);
                        console.log('Resolved schema from endpoint:', schema);
                    }
                    window.currentBodySchema = schema;
                }
            }
        }
        
        if (!schema || (!schema.type && !schema.properties && !schema.$ref)) {
            console.error('Invalid schema after all attempts:', schema);
            showError('No schema available to generate example from. Please select an endpoint with a request body.');
            return;
        }
        
        console.log('Final schema for generation:', schema);
        const example = generateExampleFromSchema(schema);
        console.log('Generated example:', example);
        
        const textarea = document.getElementById('requestBody');
        if (textarea) {
            if (example) {
                textarea.value = JSON.stringify(example, null, 2);
                showSuccess('Example generated');
            } else {
                const schemaStr = JSON.stringify(schema, null, 2);
                console.error('Failed to generate example.');
                console.error('Schema details:', schemaStr);
                console.error('Schema keys:', Object.keys(schema || {}));
                showError('Could not generate example from schema. The schema may be incomplete or invalid. Check browser console (F12) for details.');
            }
        }
        console.log('=== End Debug ===');
    });
    
    // Copy response button
    document.getElementById('copyResponseBtn').addEventListener('click', () => {
        const bodyEl = document.getElementById('responseBody');
        navigator.clipboard.writeText(bodyEl.textContent);
        showSuccess('Response copied to clipboard');
    });
    
    // Manage configs button
    document.getElementById('manageConfigsBtn').addEventListener('click', () => {
        openModal('manageConfigsModal');
        loadConfigsList();
    });
    
    // Load OpenAPI button
    document.getElementById('loadOpenApiBtn').addEventListener('click', () => {
        if (!currentConfig) {
            showError('Please select a configuration first');
            return;
        }
        openModal('loadOpenApiModal');
    });
    
    // Autonomous loader button
    document.getElementById('autonomousLoaderBtn').addEventListener('click', () => {
        if (!currentConfig) {
            showError('Please select a configuration first');
            return;
        }
        openModal('autonomousLoaderModal');
    });
    
    // Task manager button
    document.getElementById('taskManagerBtn').addEventListener('click', () => {
        updateTasksList();
        openModal('taskManagerModal');
    });
    
    // Task manager modal close
    document.getElementById('taskManagerModal').querySelector('.modal-close').addEventListener('click', (e) => {
        closeModal(e.target.closest('.modal'));
    });
    
    // Modal close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            closeModal(e.target.closest('.modal'));
        });
    });
    
    // Add config button
    document.getElementById('addConfigBtn').addEventListener('click', () => {
        closeModal(document.getElementById('manageConfigsModal'));
        openModal('addConfigModal');
    });
    
    // File input handlers
    document.getElementById('newConfigSpecFile').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            document.getElementById('newConfigSpec').value = file.name;
            window.newConfigSpecFile = file;
        }
    });
    
    document.getElementById('openApiFile').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            document.getElementById('openApiPath').value = file.name;
            window.openApiFile = file;
        }
    });
    
    document.getElementById('taskFile').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            document.getElementById('taskFilePath').value = file.name;
            window.taskFile = file;
        }
    });
    
    // Save config button
    document.getElementById('saveConfigBtn').addEventListener('click', async () => {
        const name = document.getElementById('newConfigName').value.trim();
        const baseUrl = document.getElementById('newConfigUrl').value.trim();
        const specFile = window.newConfigSpecFile;
        const token = document.getElementById('newConfigToken').value.trim();
        
        if (!name || !baseUrl) {
            showError('Name and Base URL are required');
            return;
        }
        
        try {
            let specPath = null;
            if (specFile) {
                // Upload file and get path
                const formData = new FormData();
                formData.append('file', specFile);
                formData.append('name', name);
                
                const uploadResponse = await fetch(`${API_BASE}/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                const uploadData = await uploadResponse.json();
                if (uploadData.success) {
                    specPath = uploadData.file_path;
                } else {
                    showError(uploadData.error || 'Failed to upload file');
                    return;
                }
            }
            
            const response = await fetch(`${API_BASE}/configs`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    base_url: baseUrl,
                    openapi_spec_path: specPath,
                    auth_token: token || null
                })
            });
            
            const data = await response.json();
            if (data.success) {
                showSuccess('Configuration added');
                closeModal(document.getElementById('addConfigModal'));
                // Reset form
                document.getElementById('newConfigName').value = '';
                document.getElementById('newConfigUrl').value = '';
                document.getElementById('newConfigSpec').value = '';
                document.getElementById('newConfigSpecFile').value = '';
                document.getElementById('newConfigToken').value = '';
                window.newConfigSpecFile = null;
                await loadConfigurations();
            } else {
                showError(data.error || 'Failed to add configuration');
            }
        } catch (error) {
            showError('Failed to add configuration: ' + error.message);
        }
    });
    
    // Load OpenAPI file button
    document.getElementById('loadOpenApiFileBtn').addEventListener('click', async () => {
        if (!currentConfig) return;
        
        const file = window.openApiFile;
        if (!file) {
            showError('Please select a file');
            return;
        }
        
        try {
            // Upload file and get path
            const formData = new FormData();
            formData.append('file', file);
            formData.append('config_name', currentConfig);
            
            const uploadResponse = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData
            });
            
            const uploadData = await uploadResponse.json();
            if (!uploadData.success) {
                showError(uploadData.error || 'Failed to upload file');
                return;
            }
            
            const response = await fetch(`${API_BASE}/configs/${currentConfig}/openapi`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_path: uploadData.file_path })
            });
            
            const data = await response.json();
            if (data.success) {
                showSuccess('OpenAPI spec loaded');
                closeModal(document.getElementById('loadOpenApiModal'));
                // Reset form
                document.getElementById('openApiPath').value = '';
                document.getElementById('openApiFile').value = '';
                window.openApiFile = null;
                await loadEndpoints(currentConfig);
            } else {
                showError(data.error || 'Failed to load OpenAPI spec');
            }
        } catch (error) {
            showError('Failed to load OpenAPI spec: ' + error.message);
        }
    });
    
    // Execute tasks button
    document.getElementById('executeTasksBtn').addEventListener('click', async () => {
        if (!currentConfig) return;
        
        const file = window.taskFile;
        if (!file) {
            showError('Please select a task file');
            return;
        }
        
        try {
            // Read file content
            const reader = new FileReader();
            reader.onload = async (event) => {
                try {
                    const tasksData = JSON.parse(event.target.result);
                    
                    const execResponse = await fetch(`${API_BASE}/configs/${currentConfig}/tasks`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ tasks: tasksData.tasks || [] })
                    });
                    
                    const execData = await execResponse.json();
                    if (execData.success) {
                        displayTaskResults(execData);
                    } else {
                        showError(execData.error || 'Failed to execute tasks');
                    }
                } catch (error) {
                    showError('Invalid JSON file: ' + error.message);
                }
            };
            reader.onerror = () => {
                showError('Failed to read file');
            };
            reader.readAsText(file);
        } catch (error) {
            showError('Failed to execute tasks: ' + error.message);
        }
    });
    
    // Endpoint search
    document.getElementById('endpointSearch').addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const items = document.querySelectorAll('.endpoint-item');
        
        items.forEach(item => {
            const path = item.dataset.path.toLowerCase();
            if (path.includes(searchTerm)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    });
}

// ==================== Helper Functions ====================

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalElement) {
    modalElement.classList.remove('active');
}

async function loadConfigsList() {
    try {
        const response = await fetch(`${API_BASE}/configs`);
        const data = await response.json();
        
        const list = document.getElementById('configsList');
        list.innerHTML = data.configs.map(config => `
            <div class="config-item">
                <div>
                    <div class="config-item-name">${config.name}</div>
                    <div style="font-size: 12px; color: var(--text-muted);">${config.base_url}</div>
                </div>
                <div class="config-item-actions">
                    <button class="btn btn-danger" onclick="deleteConfig('${config.name}')">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load configs list:', error);
    }
}

async function deleteConfig(name) {
    if (!confirm(`Delete configuration "${name}"?`)) return;
    
    try {
        const response = await fetch(`${API_BASE}/configs/${name}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        if (data.success) {
            showSuccess('Configuration deleted');
            await loadConfigurations();
            loadConfigsList();
        } else {
            showError(data.error || 'Failed to delete configuration');
        }
    } catch (error) {
        showError('Failed to delete configuration');
    }
}

function generateExampleFromSchema(schema) {
    if (!schema || typeof schema !== 'object') return null;
    
    // Handle schemas without explicit type (might be a reference or have $ref)
    if (!schema.type && schema.$ref) {
        // Try to resolve it one more time
        const resolved = resolveSchemaRef(schema);
        if (resolved && resolved !== schema) {
            return generateExampleFromSchema(resolved);
        }
        // For $ref that can't be resolved, return a placeholder
        return { "example": "value" };
    }
    
    // If no type specified, try to infer from properties or other indicators
    if (!schema.type) {
        if (schema.properties) {
            // Has properties, treat as object
            schema = {...schema, type: 'object'};
        } else if (schema.items) {
            // Has items, treat as array
            schema = {...schema, type: 'array'};
        } else if (Object.keys(schema).length === 0) {
            // Empty object
            return null;
        } else {
            // Unknown schema structure
            return null;
        }
    }
    
    if (schema.type === 'object') {
        const example = {};
        const properties = schema.properties || {};
        const required = schema.required || [];
        
        // If there are no properties but additionalProperties is true, generate a simple example
        if (Object.keys(properties).length === 0) {
            if (schema.additionalProperties === true || schema.additionalProperties === undefined) {
                // Generate a simple example object with placeholder fields
                return {
                    "key": "value",
                    "data": "example"
                };
            } else {
                // No properties and additionalProperties is false or an object
                return null;
            }
        }
        
        // First, add all required properties (these are mandatory)
        for (const key of required) {
            if (properties[key]) {
                const value = generateExampleFromSchema(properties[key]);
                if (value !== null && value !== undefined) {
                    example[key] = value;
                } else {
                    // Even if generation fails, add a placeholder for required fields
                    const propSchema = properties[key];
                    if (propSchema && propSchema.type === 'string') {
                        example[key] = propSchema.example || propSchema.default || 'string';
                    } else if (propSchema && propSchema.type === 'integer') {
                        example[key] = propSchema.example || propSchema.default || 0;
                    } else if (propSchema && propSchema.type === 'number') {
                        example[key] = propSchema.example || propSchema.default || 0.0;
                    } else if (propSchema && propSchema.type === 'boolean') {
                        example[key] = propSchema.example || propSchema.default || false;
                    } else {
                        example[key] = 'value';
                    }
                }
            }
        }
        
        // Then add optional properties (up to 3 to keep it focused on required fields)
        let optionalCount = 0;
        for (const [key, propSchema] of Object.entries(properties)) {
            if (!required.includes(key) && optionalCount < 3) {
                const value = generateExampleFromSchema(propSchema);
                if (value !== null && value !== undefined) {
                    example[key] = value;
                    optionalCount++;
                }
            }
        }
        
        // If we still have an empty object but there are properties, include at least the first required one
        if (Object.keys(example).length === 0 && Object.keys(properties).length > 0) {
            // Prefer required properties first
            const firstRequired = required.length > 0 ? required[0] : null;
            const keyToAdd = firstRequired || Object.keys(properties)[0];
            const value = generateExampleFromSchema(properties[keyToAdd]);
            if (value !== null && value !== undefined) {
                example[keyToAdd] = value;
            } else {
                // Even if the value is null, include the key with a default
                example[keyToAdd] = "example";
            }
        }
        
        // If we still have nothing, return null instead of empty object
        if (Object.keys(example).length === 0) {
            return null;
        }
        
        return example;
    } else if (schema.type === 'array') {
        const itemExample = generateExampleFromSchema(schema.items || {});
        return itemExample ? [itemExample] : [];
    } else if (schema.type === 'string') {
        if (schema.example) return schema.example;
        if (schema.format === 'email') return 'user@example.com';
        if (schema.format === 'date-time') return '2024-01-01T00:00:00Z';
        if (schema.format === 'date') return '2024-01-01';
        if (schema.format === 'uri') return 'https://example.com';
        if (schema.format === 'uuid') return '123e4567-e89b-12d3-a456-426614174000';
        if (schema.enum && schema.enum.length > 0) return schema.enum[0];
        return 'string';
    } else if (schema.type === 'integer') {
        if (schema.example !== undefined) return schema.example;
        if (schema.default !== undefined) return schema.default;
        if (schema.minimum !== undefined) return schema.minimum;
        return 0;
    } else if (schema.type === 'number') {
        if (schema.example !== undefined) return schema.example;
        if (schema.default !== undefined) return schema.default;
        if (schema.minimum !== undefined) return schema.minimum;
        return 0.0;
    } else if (schema.type === 'boolean') {
        if (schema.example !== undefined) return schema.example;
        if (schema.default !== undefined) return schema.default;
        return false;
    }
    
    return null;
}

function displayTaskResults(data) {
    const resultsEl = document.getElementById('taskResults');
    resultsEl.innerHTML = `
        <h3>Task Results</h3>
        <p>Total: ${data.total} | Successful: ${data.successful}</p>
        <div style="max-height: 300px; overflow-y: auto; margin-top: 10px;">
            ${data.results.map((result, idx) => `
                <div style="padding: 10px; margin-bottom: 8px; background: var(--bg-tertiary); border-radius: 6px;">
                    <div style="font-weight: 600;">Task ${idx + 1}: ${result.task.method} ${result.task.path}</div>
                    <div style="color: ${result.success ? 'var(--accent-success)' : 'var(--accent-error)'};">
                        ${result.success ? '✓ Success' : '✗ Failed: ' + (result.error || 'Unknown error')}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function showSuccess(message) {
    // Simple notification (could be enhanced with a toast library)
    alert(message);
}

function showError(message) {
    console.error('Error:', message);
    alert('Error: ' + message);
}

// ==================== Task Management ====================

function createTaskFromCurrentRequest() {
    if (!currentConfig || !currentEndpoint || !currentMethod) {
        showError('Please select a configuration and endpoint first');
        return;
    }
    
    const method = currentMethod.toUpperCase();
    let path = currentEndpoint;
    
    // Collect parameters
    const params = {};
    const headers = {};
    
    document.querySelectorAll('.param-input').forEach(input => {
        const value = input.value.trim();
        if (value) {
            const paramName = input.dataset.param;
            const paramIn = input.dataset.in;
            
            if (paramIn === 'query') {
                params[paramName] = value;
            } else if (paramIn === 'header') {
                headers[paramName] = value;
            } else if (paramIn === 'path') {
                // Replace path parameter in the path
                path = path.replace(`{${paramName}}`, value);
            }
        }
    });
    
    // Get request body
    const bodyTextarea = document.getElementById('requestBody');
    const body = bodyTextarea ? bodyTextarea.value.trim() : null;
    
    // Create task object
    const task = {
        config_name: currentConfig,
        method: method,
        path: path,
        params: Object.keys(params).length > 0 ? params : undefined,
        headers: Object.keys(headers).length > 0 ? headers : undefined,
        body: body || undefined,
        delay_before: 0,
        delay_after: 0
    };
    
    // Remove undefined fields
    Object.keys(task).forEach(key => {
        if (task[key] === undefined) {
            delete task[key];
        }
    });
    
    // Add to saved tasks
    savedTasks.push(task);
    
    showSuccess(`Task created: ${method} ${path}`);
    
    // Optionally open task manager to show the new task
    updateTasksList();
    openModal('taskManagerModal');
}

function updateTasksList() {
    const tasksList = document.getElementById('tasksList');
    const taskCount = document.getElementById('taskCount');
    
    // Update task count
    if (taskCount) {
        taskCount.textContent = savedTasks.length;
    }
    
    if (savedTasks.length === 0) {
        tasksList.innerHTML = '<div class="empty-state">No tasks created yet. Use "Create Task" button to add tasks from API requests.</div>';
        return;
    }
    
    tasksList.innerHTML = savedTasks.map((task, index) => {
        const paramsStr = task.params ? JSON.stringify(task.params) : 'None';
        const headersStr = task.headers ? JSON.stringify(task.headers) : 'None';
        const bodyPreview = task.body ? (task.body.length > 100 ? task.body.substring(0, 100) + '...' : task.body) : 'None';
        
        return `
            <div class="task-item">
                <div class="task-item-header">
                    <div class="task-item-method">${task.method}</div>
                    <div class="task-item-path">${task.path}</div>
                    <button class="btn btn-danger btn-small" onclick="removeTask(${index})">Remove</button>
                </div>
                <div class="task-item-details">
                    <div><strong>Config:</strong> ${task.config_name}</div>
                    <div><strong>Params:</strong> ${paramsStr}</div>
                    <div><strong>Headers:</strong> ${headersStr}</div>
                    <div><strong>Body:</strong> ${bodyPreview}</div>
                    ${task.delay_before > 0 ? `<div><strong>Delay Before:</strong> ${task.delay_before}s</div>` : ''}
                    ${task.delay_after > 0 ? `<div><strong>Delay After:</strong> ${task.delay_after}s</div>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

function removeTask(index) {
    if (confirm(`Remove task ${index + 1}?`)) {
        savedTasks.splice(index, 1);
        updateTasksList();
        showSuccess('Task removed');
    }
}

function clearAllTasks() {
    if (savedTasks.length === 0) {
        showError('No tasks to clear');
        return;
    }
    
    if (confirm(`Clear all ${savedTasks.length} task(s)?`)) {
        savedTasks = [];
        updateTasksList();
        showSuccess('All tasks cleared');
    }
}

function saveTasksToFile() {
    if (savedTasks.length === 0) {
        showError('No tasks to save');
        return;
    }
    
    const tasksData = {
        tasks: savedTasks
    };
    
    const blob = new Blob([JSON.stringify(tasksData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tasks_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showSuccess(`Saved ${savedTasks.length} task(s) to file`);
}

async function executeSavedTasks() {
    if (savedTasks.length === 0) {
        showError('No tasks to execute');
        return;
    }
    
    if (!currentConfig) {
        showError('Please select a configuration first');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/configs/${currentConfig}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tasks: savedTasks })
        });
        
        const data = await response.json();
        if (data.success) {
            closeModal(document.getElementById('taskManagerModal'));
            openModal('autonomousLoaderModal');
            displayTaskResults(data);
            showSuccess(`Executed ${data.total} task(s), ${data.successful} successful`);
        } else {
            showError(data.error || 'Failed to execute tasks');
        }
    } catch (error) {
        showError('Failed to execute tasks: ' + error.message);
    }
}

// Test API connection on load
async function testAPIConnection() {
    try {
        const response = await fetch(`${API_BASE}/configs`);
        if (!response.ok) {
            console.error('API connection failed:', response.status, response.statusText);
            showError(`Cannot connect to server. Make sure the Flask server is running on port 5000. Status: ${response.status}`);
            return false;
        }
        return true;
    } catch (error) {
        console.error('API connection error:', error);
        showError(`Cannot connect to server: ${error.message}. Make sure the Flask server is running on port 5000.`);
        return false;
    }
}

