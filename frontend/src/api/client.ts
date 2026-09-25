const BASE_URL = '/api';

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('access_token');
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    ...getAuthHeaders(),
    ...(options.headers || {}),
  } as Record<string, string>;

  // Don't set Content-Type if sending FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `HTTP Error ${response.status}`;
    let errorCode = undefined;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.message || errorDetail;
      errorCode = errorJson.code || errorJson.error_code;
    } catch {
      // Ignore json parse error
    }
    const err = new Error(typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail)) as Error & { code?: string; status?: number };
    err.code = errorCode;
    err.status = response.status;
    throw err;
  }

  if (response.status === 24) return {} as T;
  return response.json();
}

export const api = {
  // Auth
  login: (credentials: any) => request<any>('/auth/login', { method: 'POST', body: JSON.stringify(credentials) }),
  register: (data: any) => request<any>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  refreshToken: (refreshToken: string) => request<any>('/auth/refresh', { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) }),
  getMe: () => request<any>('/auth/me'),

  // Complaints
  listComplaints: (params: Record<string, string> = {}) => {
    const query = new URLSearchParams(params).toString();
    return request<any[]>(`/complaints${query ? `?${query}` : ''}`);
  },
  createComplaint: (data: any) => request<any>('/complaints', { method: 'POST', body: JSON.stringify(data) }),
  getComplaint: (id: string | number) => request<any>(`/complaints/${id}`),
  updateComplaint: (id: string | number, data: any) => request<any>(`/complaints/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  // Knowledge Base (Public / Standard)
  searchKB: (query?: string, category?: string) => {
    const params: Record<string, string> = {};
    if (query) params.query = query;
    if (category) params.category = category;
    const q = new URLSearchParams(params).toString();
    return request<any[]>(`/knowledge_base${q ? `?${q}` : ''}`);
  },
  deleteKB: (id: number) => request<any>(`/knowledge_base/${id}`, { method: 'DELETE' }),

  // Admin Knowledge Base Upload & Policy Lifecycle Module
  uploadKBDocument: (formData: FormData) => request<any>('/admin/knowledge-base/upload', { method: 'POST', body: formData }),
  listAdminKBDocuments: () => request<any[]>('/admin/knowledge-base'),
  getDocumentStatus: (docId: string) => request<any>(`/admin/knowledge-base/${docId}/status`),
  getDocumentChunks: (docId: string) => request<any>(`/admin/knowledge-base/${docId}/chunks`),
  getDocumentHistory: (docId: string) => request<any>(`/admin/knowledge-base/${docId}/history`),
  activateDocument: (docId: string, reason: string) => request<any>(`/admin/knowledge-base/${docId}/activate`, {
    method: 'POST',
    body: JSON.stringify({ reason })
  }),

  // Rule Matrix Public & Admin
  getRuleMatrix: () => request<any[]>('/rule_matrix'),
  listAdminRuleMatrix: (params: Record<string, any> = {}) => {
    const cleanParams: Record<string, string> = {};
    Object.keys(params).forEach(k => {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        cleanParams[k] = String(params[k]);
      }
    });
    const q = new URLSearchParams(cleanParams).toString();
    return request<any>(`/admin/rule-matrix${q ? `?${q}` : ''}`);
  },
  createAdminRule: (data: any) => request<any>('/admin/rule-matrix', { method: 'POST', body: JSON.stringify(data) }),
  updateAdminRule: (ruleId: string, data: any) => request<any>(`/admin/rule-matrix/${encodeURIComponent(ruleId)}`, { method: 'PUT', body: JSON.stringify(data) }),
  deactivateAdminRule: (ruleId: string) => request<any>(`/admin/rule-matrix/${encodeURIComponent(ruleId)}`, { method: 'DELETE' }),
  getRuleAuditLog: (ruleId: string) => request<any>(`/admin/rule-matrix/${encodeURIComponent(ruleId)}/audit-log`),
  updateRuleMatrix: (category: string, data: any) => request<any>(`/rule_matrix/${encodeURIComponent(category)}`, { method: 'PATCH', body: JSON.stringify(data) }),
  createRuleMatrix: (data: any) => request<any>('/rule_matrix', { method: 'POST', body: JSON.stringify(data) }),

  // Pipelines
  processGenAI: (complaintId: number) => request<any>('/genai_pipeline/process', { method: 'POST', body: JSON.stringify({ complaint_id: complaintId }) }),
  analyzeComplaint: (complaintId: string | number) => request<any>(`/complaints/${complaintId}/analyze`, { method: 'POST' }),
  getComplaintAnalysis: (complaintId: string | number) => request<any>(`/complaints/${complaintId}/analysis`),
  validateComplaint: (complaintId: string | number) => request<any>(`/complaints/${complaintId}/validate`, { method: 'POST' }),
  getComplaintVerification: (complaintId: string | number) => request<any>(`/complaints/${complaintId}/verification`),
  runValidation: (complaintId: number) => request<any>('/validation/run', { method: 'POST', body: JSON.stringify({ complaint_id: complaintId }) }),
  runComparison: (complaintId: number) => request<any>('/comparison/check', { method: 'POST', body: JSON.stringify({ complaint_id: complaintId }) }),

  // Dashboards
  getDashboard: (role: string) => request<any>(`/dashboards/${role.toLowerCase()}`),

  // Reports
  getReportsSummary: () => request<any>('/reports/summary')
};
