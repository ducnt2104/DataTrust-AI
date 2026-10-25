import pytest
from app.engine.topic_model_engine import TopicModelingEngine


def test_vietnamese_text_preprocessing():
    """Kiểm tra tiền xử lý văn bản, ghép từ ghép tiếng Việt và loại trừ stopwords."""
    text = "Dịch vụ khách hàng và chất lượng hỗ trợ thực sự rất tốt, giao diện dễ sử dụng!"
    tokens = TopicModelingEngine.preprocess_text(text)

    # Từ ghép phải được nhận diện
    assert "dịch_vụ" in tokens or "khách_hàng" in tokens
    assert "chất_lượng" in tokens or "giao_diện" in tokens
    assert "dễ_sử_dụng" in tokens

    # Stopwords như 'và', 'thực sự', 'rất' phải bị loại bỏ
    assert "và" not in tokens
    assert "rất" not in tokens
    assert "thực_sự" not in tokens


def test_lda_topic_model_fitting():
    """Kiểm tra khớp mô hình chủ đề LDA với Collapsed Gibbs Sampling và đánh giá UMass Coherence."""
    # Tạo 12 phản hồi định tính thuộc 2 chủ đề rõ rệt: Kỹ thuật/Giao diện và Dịch vụ/Hỗ trợ
    sample_docs = [
        {"id": "doc1", "text": "Giao diện hệ thống rất đẹp, tốc độ tải trang nhanh và mượt mà.", "covariate": 5.0},
        {"id": "doc2", "text": "Hệ thống có giao diện trực quan, tốc độ xử lý rất nhanh và ổn định.", "covariate": 5.0},
        {"id": "doc3", "text": "Tốc độ tải chậm, giao diện cần cải tiến thêm nhiều tính năng mới.", "covariate": 3.0},
        {"id": "doc4", "text": "Giao diện thân thiện người dùng, tính năng tìm kiếm nhanh chóng.", "covariate": 4.5},
        {"id": "doc5", "text": "Dịch vụ khách hàng nhiệt tình, nhân viên hỗ trợ giải đáp rất chu đáo.", "covariate": 5.0},
        {"id": "doc6", "text": "Nhân viên hỗ trợ khách hàng chuyên nghiệp, dịch vụ chăm sóc tốt.", "covariate": 4.5},
        {"id": "doc7", "text": "Dịch vụ hỗ trợ chậm trễ, nhân viên chưa giải quyết thỏa đáng phản hồi.", "covariate": 2.0},
        {"id": "doc8", "text": "Chất lượng dịch vụ và chăm sóc khách hàng cần nâng cấp đào tạo nhân viên.", "covariate": 2.5},
        {"id": "doc9", "text": "Bảo mật hệ thống rất an toàn, dữ liệu khảo sát tin cậy.", "covariate": 4.0},
        {"id": "doc10", "text": "Nền tảng bảo mật thông tin tốt, quy trình khảo sát an toàn bảo mật.", "covariate": 4.0},
        {"id": "doc11", "text": "Hệ thống bảo mật dữ liệu khách hàng an toàn và tin cậy tuyệt đối.", "covariate": 5.0},
        {"id": "doc12", "text": "Dịch vụ khách hàng tốt, giao diện mượt mà và bảo mật an toàn.", "covariate": 4.5}
    ]

    res = TopicModelingEngine.fit_lda_topic_model(
        documents=sample_docs,
        num_topics=2,
        num_iterations=40,
        random_seed=42
    )

    assert res["status"] == "SUCCESS"
    assert res["sample_size"] == 12
    assert res["num_topics"] == 2
    assert res["vocabulary_size"] >= 10
    assert len(res["topics"]) == 2

    # Mỗi chủ đề phải có danh sách từ khóa với xác suất hợp lệ
    for topic in res["topics"]:
        assert "label" in topic
        assert len(topic["top_words"]) > 0
        assert topic["prevalence_percent"] > 0
        for w in topic["top_words"]:
            assert w["probability"] > 0.0
            assert "word" in w

    # Kiểm tra tác động của biến đồng biến (Covariate Effects)
    assert "covariate_effects" in res
    assert len(res["covariate_effects"]) == 2

    # Kiểm tra phân bổ tài liệu mẫu
    assert len(res["document_sample_assignments"]) == 12
    for doc_assign in res["document_sample_assignments"]:
        assert doc_assign["dominant_topic_id"] in [1, 2]
        assert doc_assign["dominant_probability"] >= 0.5

    # Kiểm tra đoạn văn thuyết minh học thuật chuẩn APA 7th Edition
    assert "apa_narrative" in res
    assert "Latent Dirichlet Allocation" in res["apa_narrative"]
    assert "UMass" in res["apa_narrative"]


def test_lda_topic_model_insufficient_samples():
    """Kiểm tra xử lý biên khi không đủ phản hồi hoặc từ vựng."""
    # Quá ít văn bản
    res_few = TopicModelingEngine.fit_lda_topic_model(
        documents=[{"id": "1", "text": "Một văn bản ngắn."}],
        num_topics=3
    )
    assert res_few["status"] == "INSUFFICIENT_DATA"

    # Toàn stopwords
    res_stopwords = TopicModelingEngine.fit_lda_topic_model(
        documents=[
            {"id": "1", "text": "Và là của cho với"},
            {"id": "2", "text": "Những các có không khi"},
            {"id": "3", "text": "Rất này thì đã sẽ đang"}
        ],
        num_topics=2
    )
    assert res_stopwords["status"] == "INSUFFICIENT_VOCABULARY"
