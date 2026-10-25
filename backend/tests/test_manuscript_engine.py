import pytest
from app.main import app
from fastapi.testclient import TestClient
from app.engine.manuscript_engine import AcademicManuscriptEngine

client = TestClient(app)

def test_manuscript_generation_full_cycle():
    # 1. Tạo khảo sát kiểm thử
    create_res = client.post("/api/surveys", json={
        "title": "Nghiên Cứu Tác Động Công Nghệ Số Đến Trải Nghiệm Khách Hàng",
        "description": "Bản thảo khoa học kiểm chứng dữ liệu thực nghiệm",
        "instructions": "Vui lòng trả lời trung thực"
    })
    assert create_res.status_code == 201
    survey_id = create_res.json()["id"]
    slug = create_res.json()["public_slug"]

    # 2. Tạo 3 câu hỏi thang đo và 1 câu hỏi mở
    client.put(f"/api/surveys/{survey_id}", json={
        "title": "Nghiên Cứu Tác Động Công Nghệ Số Đến Trải Nghiệm Khách Hàng",
        "questions": [
            {
                "order_index": 1,
                "question_type": "rating",
                "title": "Độ thuận tiện của giao diện",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "order_index": 2,
                "question_type": "rating",
                "title": "Tốc độ xử lý giao dịch",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "order_index": 3,
                "question_type": "rating",
                "title": "Mức độ hài lòng chung",
                "is_required": True,
                "options": ["1", "2", "3", "4", "5"],
                "logic_rules": []
            },
            {
                "order_index": 4,
                "question_type": "short_text",
                "title": "Ý kiến đóng góp cải tiến",
                "is_required": False,
                "options": [],
                "logic_rules": []
            }
        ]
    })
    client.post(f"/api/surveys/{survey_id}/publish")

    public_q = client.get(f"/api/public/surveys/{slug}").json()["questions"]
    q1_id = public_q[0]["id"]
    q2_id = public_q[1]["id"]
    q3_id = public_q[2]["id"]
    q4_id = public_q[3]["id"]

    # 3. Gửi 10 phản hồi thực tế
    for i in range(10):
        client.post(f"/api/public/surveys/{slug}/submit", json={
            "started_at": f"2026-10-24T02:{i:02d}:00Z",
            "submitted_at": f"2026-10-24T02:{i:02d}:40Z",
            "answers": {
                q1_id: str((i % 5) + 1),
                q2_id: str(((i + 1) % 5) + 1),
                q3_id: str(((i + 2) % 5) + 1),
                q4_id: f"Hệ thống vận hành rất nhanh và tiện lợi #{i}"
            }
        })

    # 4. Kiểm tra compile_manuscript_data
    data = AcademicManuscriptEngine.compile_manuscript_data(survey_id, scope="all")
    assert data["total_responses"] == 10
    assert data["trust_index"] > 0
    assert len(data["questions"]) == 4

    # 5. Kiểm tra sinh Markdown
    md = AcademicManuscriptEngine.generate_markdown(survey_id, scope="all")
    assert "# BẢN THẢO NGHIÊN CỨU KHOA HỌC THỰC NGHIỆM" in md
    assert "CRONBACH'S ALPHA" in md
    assert "SHA-256" in md
    assert "REFERENCES" in md

    # 6. Kiểm tra sinh HTML
    html = AcademicManuscriptEngine.generate_html(survey_id, scope="all")
    assert "<!DOCTYPE html>" in html
    assert "DataTrust Verified Academic Manuscript" in html
    assert "@media print" in html

    # 7. Kiểm tra sinh LaTeX
    tex = AcademicManuscriptEngine.generate_latex(survey_id, scope="all")
    assert "\\documentclass" in tex
    assert "\\begin{abstract}" in tex
    assert "\\begin{document}" in tex

    # 8. Kiểm tra API endpoints xuất file
    res_html = client.get(f"/api/surveys/{survey_id}/export/manuscript?format=html&scope=all")
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]

    res_tex = client.get(f"/api/surveys/{survey_id}/export/manuscript?format=latex&scope=all")
    assert res_tex.status_code == 200
    assert "datatrust_manuscript_" in res_tex.headers["content-disposition"]

    res_md = client.get(f"/api/surveys/{survey_id}/export/manuscript?format=markdown&scope=all")
    assert res_md.status_code == 200
    assert "datatrust_manuscript_" in res_md.headers["content-disposition"]
