import {
  Survey,
  SurveyListItem,
  ResponseListItem,
  ResponseDetail,
  SurveyAnalytics,
  Question
} from '../types/survey';

const BASE_URL = '/api';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = 'Lỗi kết nối máy chủ.';
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        if (typeof errJson.detail === 'string') {
          errorDetail = errJson.detail;
        } else if (errJson.detail.validation_errors) {
          errorDetail = errJson.detail.validation_errors.join('; ');
        } else {
          errorDetail = JSON.stringify(errJson.detail);
        }
      }
    } catch {
      errorDetail = `Lỗi HTTP ${res.status}: ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // --- Surveys Management ---
  async getSurveys(status?: string): Promise<SurveyListItem[]> {
    const url = status ? `${BASE_URL}/surveys?status=${encodeURIComponent(status)}` : `${BASE_URL}/surveys`;
    const res = await fetch(url);
    return handleResponse<SurveyListItem[]>(res);
  },

  async createSurvey(data: { title: string; description?: string; instructions?: string }): Promise<Survey> {
    const res = await fetch(`${BASE_URL}/surveys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return handleResponse<Survey>(res);
  },

  async getSurvey(id: string): Promise<Survey> {
    const res = await fetch(`${BASE_URL}/surveys/${id}`);
    return handleResponse<Survey>(res);
  },

  async updateSurvey(id: string, data: Partial<Survey>): Promise<Survey> {
    const res = await fetch(`${BASE_URL}/surveys/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return handleResponse<Survey>(res);
  },

  async publishSurvey(id: string): Promise<{ id: string; status: string; public_slug: string; public_url: string }> {
    const res = await fetch(`${BASE_URL}/surveys/${id}/publish`, {
      method: 'POST'
    });
    return handleResponse(res);
  },

  async closeSurvey(id: string): Promise<Survey> {
    const res = await fetch(`${BASE_URL}/surveys/${id}/close`, {
      method: 'POST'
    });
    return handleResponse<Survey>(res);
  },

  async reopenSurvey(id: string): Promise<Survey> {
    const res = await fetch(`${BASE_URL}/surveys/${id}/reopen`, {
      method: 'POST'
    });
    return handleResponse<Survey>(res);
  },

  async duplicateSurvey(id: string): Promise<Survey> {
    const res = await fetch(`${BASE_URL}/surveys/${id}/duplicate`, {
      method: 'POST'
    });
    return handleResponse<Survey>(res);
  },

  async deleteSurvey(id: string): Promise<void> {
    const res = await fetch(`${BASE_URL}/surveys/${id}`, {
      method: 'DELETE'
    });
    if (!res.ok) {
      throw new Error('Không thể xóa khảo sát.');
    }
  },

  // --- Public Survey ---
  async getPublicSurvey(slugOrId: string): Promise<Survey> {
    const res = await fetch(`${BASE_URL}/public/surveys/${encodeURIComponent(slugOrId)}`);
    return handleResponse<Survey>(res);
  },

  async submitPublicSurvey(slugOrId: string, payload: {
    started_at: string;
    submitted_at: string;
    client_metadata?: Record<string, any>;
    answers: Record<string, any>;
  }): Promise<{ response_id: string; message: string; risk_score?: number; risk_level?: string }> {
    const res = await fetch(`${BASE_URL}/public/surveys/${encodeURIComponent(slugOrId)}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  // --- Responses & Review ---
  async getResponses(surveyId: string, riskLevel?: string, reviewStatus?: string): Promise<ResponseListItem[]> {
    const params = new URLSearchParams();
    if (riskLevel) params.append('risk_level', riskLevel);
    if (reviewStatus) params.append('review_status', reviewStatus);
    const url = `${BASE_URL}/surveys/${surveyId}/responses?${params.toString()}`;
    const res = await fetch(url);
    return handleResponse<ResponseListItem[]>(res);
  },

  async getResponseDetail(surveyId: string, responseId: string): Promise<ResponseDetail> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/responses/${responseId}`);
    return handleResponse<ResponseDetail>(res);
  },

  async updateReviewDecision(surveyId: string, responseId: string, reviewStatus: string, reviewNotes?: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/responses/${responseId}/review`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ review_status: reviewStatus, review_notes: reviewNotes || '' })
    });
    return handleResponse(res);
  },

  async compareResponses(surveyId: string, resp1: string, resp2: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/responses/compare/side-by-side?resp1=${encodeURIComponent(resp1)}&resp2=${encodeURIComponent(resp2)}`);
    return handleResponse(res);
  },

  // --- Analytics ---
  async getSurveyAnalytics(surveyId: string): Promise<SurveyAnalytics> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics`);
    return handleResponse<SurveyAnalytics>(res);
  },

  // --- AI Assistant ---
  async generateSurveyDraft(topic: string, audience?: string, minutes: number = 5): Promise<any> {
    const res = await fetch(`${BASE_URL}/ai/generate-survey`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, audience: audience || '', expected_time_minutes: minutes })
    });
    return handleResponse(res);
  },

  async auditQuestions(questions: Question[]): Promise<any> {
    const res = await fetch(`${BASE_URL}/ai/audit-questions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ questions })
    });
    return handleResponse(res);
  },

  async getAiStatus(): Promise<any> {
    const res = await fetch(`${BASE_URL}/ai/status`);
    return handleResponse(res);
  },

  // --- Paper Survey & OMR Scanning ---
  async getPaperTemplate(surveyId: string): Promise<{ template_id: string; survey_id: string; version: number; layout: any }> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/paper/template`);
    return handleResponse(res);
  },

  async scanPaperImage(surveyId: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/paper/scan`, {
      method: 'POST',
      body: formData
    });
    return handleResponse(res);
  },

  async ingestPaperResponse(surveyId: string, payload: {
    form_id: string;
    enumerator_id?: string;
    answers: Record<string, any>;
    omr_confidence?: number;
    scan_image_url?: string;
    manual_corrections?: any[];
  }): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/paper/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  // --- Enumerator Analytics ---
  async getEnumeratorAnalytics(surveyId: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/enumerators`);
    return handleResponse(res);
  },

  // --- Quality Audit Report & Compliance ---
  async getQualityAuditReport(surveyId: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/audit-report`);
    return handleResponse(res);
  },

  async anonymizeSurveyResponses(surveyId: string, payload: {
    anonymize_client_metadata?: boolean;
    mask_text_answers?: boolean;
    operator_notes?: string;
  }): Promise<{ message: string; anonymized_responses_count: number; audit_log_id: string }> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/privacy/anonymize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  // --- Statistical & Academic Tools (Benford & Codebook) ---
  async getBenfordAnalysis(surveyId: string, questionId?: string): Promise<any> {
    const query = questionId ? `?question_id=${encodeURIComponent(questionId)}` : '';
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/analytics/benford${query}`);
    return handleResponse(res);
  },

  async getSurveyCodebook(surveyId: string, format: 'json' | 'spss' = 'json'): Promise<any> {
    const res = await fetch(`${BASE_URL}/surveys/${surveyId}/codebook?format=${format}`);
    if (format === 'spss') {
      return res.text();
    }
    return handleResponse(res);
  }
};
