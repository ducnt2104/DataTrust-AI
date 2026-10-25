import io
import json
import zipfile
import hashlib
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def academic_survey():
    """Tạo một khảo sát học thuật hoàn chỉnh với nhiều loại câu hỏi và phản hồi mẫu"""
    survey_payload = {
        "title": "Khảo sát Nghiên cứu Thực địa DataTrust 2026",
        "description": "Nghiên cứu khoa học mẫu phục vụ kiểm định xuất hồ sơ học thuật",
        "instructions": "Vui lòng trả lời trung thực các câu hỏi bên dưới."
    }
    res = client.post("/api/surveys", json=survey_payload)
    assert res.status_code == 201, res.text
    survey = res.json()
    survey_id = survey["id"]

    questions_payload = [
        {
            "order_index": 0,
            "question_type": "single_choice",
            "title": "Giới tính của bạn?",
            "is_required": True,
            "options": [
                {"id": "opt_m", "label": "Nam"},
                {"id": "opt_f", "label": "Nữ"}
            ]
        },
        {
            "order_index": 1,
            "question_type": "likert",
            "title": "Mức độ hài lòng với chất lượng dịch vụ?",
            "is_required": True,
            "options": [
                {"id": "likert_1", "label": "Rất không hài lòng"},
                {"id": "likert_2", "label": "Không hài lòng"},
                {"id": "likert_3", "label": "Bình thường"},
                {"id": "likert_4", "label": "Hài lòng"},
                {"id": "likert_5", "label": "Rất hài lòng"}
            ]
        },
        {
            "order_index": 2,
            "question_type": "number",
            "title": "Độ tuổi của bạn?",
            "is_required": True,
            "options": []
        },
        {
            "order_index": 3,
            "question_type": "long_text",
            "title": "Ý kiến đóng góp cải tiến của bạn?",
            "is_required": False,
            "options": []
        }
    ]

    put_res = client.put(f"/api/surveys/{survey_id}", json={"questions": questions_payload})
    assert put_res.status_code == 200, put_res.text
    updated_survey = put_res.json()

    client.post(f"/api/surveys/{survey_id}/publish")

    # Thêm 3 phản hồi mẫu
    q_ids = [q["id"] for q in updated_survey["questions"]]
    sample_responses = [
        {
            "started_at": "2026-10-23T10:00:00.000Z",
            "submitted_at": "2026-10-23T10:01:05.000Z",
            "answers": {
                q_ids[0]: "Nam",
                q_ids[1]: "Hài lòng",
                q_ids[2]: "25",
                q_ids[3]: "Giao diện hệ thống rất nhanh và mượt mà."
            },
            "source": "online_form",
            "enumerator_id": "DTV_HN_01"
        },
        {
            "started_at": "2026-10-23T10:05:00.000Z",
            "submitted_at": "2026-10-23T10:06:18.000Z",
            "answers": {
                q_ids[0]: "Nữ",
                q_ids[1]: "Rất hài lòng",
                q_ids[2]: "32",
                q_ids[3]: "Hài lòng với tốc độ giải quyết thắc mắc."
            },
            "source": "online_form",
            "enumerator_id": "DTV_HN_02"
        },
        {
            "started_at": "2026-10-23T10:10:00.000Z",
            "submitted_at": "2026-10-23T10:10:55.000Z",
            "answers": {
                q_ids[0]: "Nam",
                q_ids[1]: "Bình thường",
                q_ids[2]: "40",
                q_ids[3]: "Cần bổ sung thêm bản đồ thực địa ngoại tuyến."
            },
            "source": "online_form",
            "enumerator_id": "DTV_HN_01"
        }
    ]

    for s_resp in sample_responses:
        sub_res = client.post(f"/api/public/surveys/{updated_survey['public_slug']}/submit", json=s_resp)
        assert sub_res.status_code == 201, sub_res.text

    return updated_survey

def test_export_academic_dossier_zip_structure(academic_survey):
    """Kiểm tra việc xuất gói hồ sơ học thuật đầy đủ 8 thành phần trong tệp .ZIP"""
    survey_id = academic_survey["id"]

    res = client.get(f"/api/surveys/{survey_id}/export/academic-dossier?scope=verified_clean")
    assert res.status_code == 200
    assert "application/zip" in res.headers["content-type"]
    assert "datatrust_academic_dossier" in res.headers.get("content-disposition", "")

    # Mở và xác thực nội dung bên trong file zip
    zip_bytes = io.BytesIO(res.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        namelist = zf.namelist()
        expected_files = [
            "README_RESEARCH_DOSSIER.md",
            "RESEARCH_MANUSCRIPT.md",
            "dataset_clean.csv",
            "dataset_labeled.csv",
            "spss_syntax.sps",
            "stata_syntax.do",
            "sas_syntax.sas",
            "run_analysis.R",
            "analyze_data.py",
            "CODEBOOK.md",
            "INTEGRITY_CERTIFICATE_SHA256.json"
        ]
        for f in expected_files:
            assert f in namelist, f"Thiếu tệp {f} trong gói hồ sơ học thuật ZIP!"

        # 1. Đọc và kiểm tra chứng chỉ băm mật mã học
        cert_raw = zf.read("INTEGRITY_CERTIFICATE_SHA256.json").decode("utf-8")
        cert_data = json.loads(cert_raw)
        assert cert_data["survey_id"] == survey_id
        assert cert_data["total_records_certified"] >= 3
        assert cert_data["audit_ledger_status"]["chain_valid"] is True

        # 2. Kiểm chứng đối soát mã băm SHA-256 thực tế với chứng chỉ
        clean_csv_bytes = zf.read("dataset_clean.csv")
        actual_clean_sha256 = hashlib.sha256(clean_csv_bytes).hexdigest()
        assert actual_clean_sha256 == cert_data["dataset_cryptographic_fingerprints"]["dataset_clean_csv_sha256"]

        labeled_csv_bytes = zf.read("dataset_labeled.csv")
        actual_labeled_sha256 = hashlib.sha256(labeled_csv_bytes).hexdigest()
        assert actual_labeled_sha256 == cert_data["dataset_cryptographic_fingerprints"]["dataset_labeled_csv_sha256"]

        # 3. Kiểm tra dataset_clean.csv có các cột VAR001, VAR002...
        clean_text = clean_csv_bytes.decode("utf-8")
        assert "VAR001" in clean_text
        assert "VAR002" in clean_text
        assert "VAR003" in clean_text
        assert "VAR004" in clean_text

        # 4. Kiểm tra spss_syntax.sps
        spss_text = zf.read("spss_syntax.sps").decode("utf-8")
        assert "VARIABLE LABELS" in spss_text
        assert "VALUE LABELS" in spss_text
        assert "MISSING VALUES ALL (999)." in spss_text

        # 5. Kiểm tra run_analysis.R
        r_text = zf.read("run_analysis.R").decode("utf-8")
        assert "cronbach_alpha" in r_text
        assert "read.csv" in r_text

        # 6. Kiểm tra analyze_data.py
        py_text = zf.read("analyze_data.py").decode("utf-8")
        assert "import pandas as pd" in py_text
        assert "descriptive_statistics.csv" in py_text

        # 6b. Kiểm tra sas_syntax.sas
        sas_text = zf.read("sas_syntax.sas").decode("utf-8")
        assert "PROC IMPORT" in sas_text
        assert "PROC FORMAT" in sas_text
        assert "PROC MEANS" in sas_text

        # 7. Kiểm tra verify_dossier.py thực thi kiểm chứng tự động
        assert "verify_dossier.py" in namelist
        verify_py_text = zf.read("verify_dossier.py").decode("utf-8")
        assert "DATATRUST ACADEMIC DOSSIER" in verify_py_text

def test_verify_dossier_cli_execution(academic_survey, tmp_path):
    """Kiểm tra kịch bản kiểm chứng toàn vẹn dòng lệnh verify_dossier.py trên tệp giải nén thực tế"""
    import subprocess
    import sys
    survey_id = academic_survey["id"]

    res = client.get(f"/api/surveys/{survey_id}/export/academic-dossier?scope=verified_clean")
    assert res.status_code == 200

    zip_bytes = io.BytesIO(res.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        zf.extractall(tmp_path)

    # Chạy verify_dossier.py trên thư mục hợp lệ
    run_res = subprocess.run(
        [sys.executable, "verify_dossier.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True
    )
    assert run_res.returncode == 0
    assert "100% DOSSIER INTEGRITY VERIFIED" in run_res.stdout
    assert "[ PASS ]" in run_res.stdout

    # Giả lập can thiệp gian lận dữ liệu (Tampering) trên dataset_clean.csv
    tampered_file = tmp_path / "dataset_clean.csv"
    with open(tampered_file, "a", encoding="utf-8") as f:
        f.write("\n9999,fabricated_data,fraud_entry,2026-10-24,10.0,0.0,low,verified_valid,5,5,5,5\n")

    # Chạy lại verify_dossier.py -> phải phát hiện gian lận và trả về mã lỗi 1
    run_tampered = subprocess.run(
        [sys.executable, "verify_dossier.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True
    )
    assert run_tampered.returncode == 1
    assert "INTEGRITY CHECK FAILED" in run_tampered.stdout
    assert "[ FAIL ]" in run_tampered.stdout


def test_maintenance_wal_checkpoint():
    """Kiểm tra API bảo trì dồn trang SQLite WAL và thu nhỏ dung lượng"""
    res = client.post("/api/system/maintenance/wal-checkpoint")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "checkpoint_mode" in data
    assert data["checkpoint_mode"] == "TRUNCATE"
    assert "db_size_bytes" in data
    assert "wal_size_bytes" in data

def test_database_backup_endpoint():
    """Kiểm tra API tạo bản sao lưu nguyên tử (Atomic Online Backup) của cơ sở dữ liệu"""
    res = client.post("/api/system/maintenance/backup")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "backup_file" in data
    assert "backup_size_bytes" in data
    assert data["backup_size_bytes"] > 0
    import os
    assert os.path.exists(data["backup_file"])
    # Dọn dẹp tệp sao lưu sau test
    try:
        os.remove(data["backup_file"])
    except Exception:
        pass

def test_database_vacuum_endpoint():
    """Kiểm tra API thực hiện VACUUM chống phân mảnh và dọn dẹp trang trống của CSDL"""
    res = client.post("/api/system/maintenance/vacuum")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "initial_size_bytes" in data
    assert "final_size_bytes" in data
    assert "freed_bytes" in data
    assert data["final_size_bytes"] > 0

def test_export_research_manuscript_endpoints(academic_survey):
    """
    Kiểm tra API xuất Bản thảo Nghiên cứu Khoa học (Academic Manuscript)
    hỗ trợ 3 định dạng xuất bản: Markdown (.md), HTML (.html), và LaTeX (.tex).
    """
    survey_id = academic_survey["id"]

    # 1. Định dạng Markdown
    res_md = client.get(f"/api/surveys/{survey_id}/export/manuscript?format=markdown&scope=verified_clean")
    assert res_md.status_code == 200
    assert "text/markdown" in res_md.headers["content-type"]
    assert "datatrust_manuscript" in res_md.headers.get("content-disposition", "")
    md_text = res_md.text
    assert "BẢN THẢO NGHIÊN CỨU KHOA HỌC THỰC NGHIỆM" in md_text
    assert "Data Trust Index" in md_text
    assert "Cronbach" in md_text
    assert "Don Dillman" in md_text

    # 2. Định dạng HTML in ấn
    res_html = client.get(f"/api/surveys/{survey_id}/export/manuscript?format=html&scope=verified_clean")
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
    html_text = res_html.text
    assert "<!DOCTYPE html>" in html_text
    assert "window.print()" in html_text
    assert "DataTrust Verified Academic Manuscript" in html_text

    # 3. Định dạng LaTeX / Overleaf
    res_tex = client.get(f"/api/surveys/{survey_id}/export/manuscript?format=latex&scope=verified_clean")
    assert res_tex.status_code == 200
    assert "datatrust_manuscript" in res_tex.headers.get("content-disposition", "")
    tex_text = res_tex.text
    assert "\\documentclass" in tex_text
    assert "\\maketitle" in tex_text
    assert "\\begin{abstract}" in tex_text
    assert "\\end{document}" in tex_text

def test_codebook_sas_syntax_endpoint(academic_survey):
    """Kiểm tra API xuất từ điển dữ liệu định dạng cú pháp SAS (.sas)"""
    survey_id = academic_survey["id"]

    # 1. Kiểm tra JSON codebook chứa trường sas_syntax
    res_json = client.get(f"/api/surveys/{survey_id}/codebook?format=json")
    assert res_json.status_code == 200
    cb_data = res_json.json()
    assert "sas_syntax" in cb_data
    assert "PROC IMPORT" in cb_data["sas_syntax"]
    assert "PROC FORMAT" in cb_data["sas_syntax"]

    # 2. Kiểm tra tải tệp .sas trực tiếp
    res_sas = client.get(f"/api/surveys/{survey_id}/codebook?format=sas")
    assert res_sas.status_code == 200
    assert "text/plain" in res_sas.headers["content-type"]
    assert ".sas" in res_sas.headers.get("content-disposition", "")
    assert "FILENAME csvfile" in res_sas.text
    assert "PROC MEANS" in res_sas.text



