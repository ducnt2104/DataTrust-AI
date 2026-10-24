# DATATRUST — 6-HOUR AUTONOMOUS RUN STATE & PERSISTENT CHECKPOINT
> File: `.agent/6H_RUN_STATE.md`  
> Start Timestamp: 2026-10-24T22:36:36+07:00  
> Target Duration: Minimum 6.0 Hours Real Elapsed Time  
> Target Completion Time: >= 2026-10-25T04:36:36+07:00  
> Operating Status: ACTIVE CONTINUOUS ENGINEERING LOOP (6H AUTONOMOUS DIRECTIVE)  
> Current Phase: Giai đoạn C — Hoàn thiện Tính năng, Động cơ Phân tích Cao cấp & Mở rộng Kiểm định  
> Master Directive: Universal Long-Horizon Engineering, Deep Quality Assurance & Security Hardening  

---

## 1. Project Baseline & Verified Metrics
- **Project Identity**: **DataTrust** — Nền tảng Khảo sát Số & Kiểm định Dữ liệu (Digital Survey & Field Data Verification Platform).
- **Core Technology Stack**:
  - Backend: FastAPI, SQLite 3 (WAL mode enabled), OpenCV 4.10 (OMR Engine), 7-layer Survey Quality Engine, Qualitative NLP Engine (`qualitative_engine.py`), Gemini AI Engine (`ai_service.py`), Pytest.
  - Frontend: React 19, TypeScript, Vite, Tailwind CSS, Lucide icons, Interactive Calibration Canvas OMR, OpenStreetMap integration.
- **Current Verified Status**:
  - Backend Tests: **407 passed / 407 total (100% pass rate in 60.43s)**.
  - Frontend Build: **2,068 modules transformed, 0 errors in 971ms**.
  - Brand Compliance: 100% strictly **DataTrust** (0 occurrences of "DataTrust AI").
  - API Contract: **83 complete documented sections in `docs/API_CONTRACT.md`**.
  - Previous Autonomous Achievements: 102 full iterations completed.

---

## 2. 6-Hour Operational Phase Roadmap

| Giai đoạn | Khung giờ | Mục tiêu trọng tâm | Trạng thái |
| :--- | :--- | :--- | :--- |
| **Giai đoạn A** | 22:36 – 22:42 | Khảo sát sâu, kiểm tra đường cơ sở 353 tests, lập lịch heartbeat daemon | **HOÀN THÀNH** |
| **Giai đoạn B** | 22:42 – 22:46 | Iteration 91: Joint Modeling (JM) Longitudinal & Survival Data (Wulfsohn & Tsiatis 1997, Rizopoulos 2012) | **HOÀN THÀNH** |
| **Giai đoạn C** | 22:46 – 22:52 | Iteration 92: Conformal Prediction & Distribution-Free Risk Intervals (Vovk 2005, Angelopoulos 2023) | **HOÀN THÀNH** |
| **Giai đoạn D** | 22:52 – 22:57 | Iteration 93: Multilevel Structural Equation Modeling (MSEM; Preacher et al. 2010, Muthén 1994) | **HOÀN THÀNH** |
| **Giai đoạn E** | 22:57 – 23:02 | Iteration 94: Targeted Maximum Likelihood Estimation (TMLE; van der Laan & Rose 2011) | **HOÀN THÀNH** |
| **Giai đoạn F** | 23:02 – 23:08 | Iteration 95: Synthetic Difference-in-Differences (SDID; Arkhangelsky et al. 2021) | **HOÀN THÀNH** |
| **Giai đoạn G** | 23:08 – 23:17 | Iteration 96: Generalized Random Forests & Causal Forests (GRF; Athey, Tibshirani & Wager 2019) | **HOÀN THÀNH** |
| **Giai đoạn H** | 23:17 – 23:28 | Iteration 97: Causal Mediation Analysis with Sensitivity Analysis for Unmeasured Confounding (Imai, Keele & Tingley 2010) | **HOÀN THÀNH** |
| **Giai đoạn I** | 23:28 – 23:34 | Iteration 98: Dynamic Time Warping (DTW) & Trajectory Clustering (Sakoe & Chiba 1978; Petitjean et al. 2011) | **HOÀN THÀNH** |
| **Giai đoạn J** | 23:34 – 00:15 | Iteration 99: Causal Interaction Trees & Honest Subgroup Identification (Athey & Imbens 2016, PNAS) | **KẾ HOẠCH TIẾP THEO** |
| **Giai đoạn K** | 00:15 – 04:36+ | Mở rộng kiểm thử stress-load, bảo mật OWASP, kiểm soát rò rỉ & đối soát thời gian >= 6H | **CHỜ THỰC HIỆN** |

---

## 3. Live Execution Log

### Mốc 22:36:36 — Khởi động nhiệm vụ 6H
- Khởi tạo `.agent/6H_RUN_STATE.md`.
- Thiết lập Antigravity cron heartbeat định kỳ mỗi 30 phút (`task-14026`).
- Xác minh baseline 353 backend tests passed in 64.91s.

### Mốc 22:43:00 — Hoàn thành Iteration 91: Joint Modeling (JM) of Longitudinal Trajectories & Panel Attrition
- Xây dựng `backend/app/engine/joint_modeling_engine.py` (LMM submodel + Relative risk Cox survival submodel + Breslow baseline hazard + Dynamic predictions + Dual-panel SVG + APA 7th).
- Viết unit tests `backend/tests/test_joint_modeling_engine.py` (3 passed) và route tests `backend/tests/test_joint_modeling_routes.py` (1 passed).
- Thêm schemas, router POST `/joint-model`, audit log `JOINT_MODEL_EVALUATED`.
- Thêm component `JointModelCard.tsx`, gắn vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 72 trong `docs/API_CONTRACT.md`.
- Build frontend: 2,057 modules transformed, 0 errors.

### Mốc 22:51:30 — Hoàn thành Iteration 92: Conformal Prediction & Distribution-Free Risk Intervals
- Xây dựng `backend/app/engine/conformal_prediction_engine.py` (Split Conformal, Locally-Weighted heteroscedasticity, Finite-sample coverage guarantee $P(Y \in \hat{C}) \ge 1 - \alpha$, Multi-level calibration curve, Dual-panel SVG: Reliability diagram + prediction bands, APA 7th narrative).
- Viết unit tests `backend/tests/test_conformal_prediction_engine.py` (4 passed) và route tests `backend/tests/test_conformal_prediction_routes.py` (1 passed).
- Thêm schemas, router POST `/conformal-prediction`, audit log `CONFORMAL_PREDICTION_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `ConformalPredictionCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 73 trong `docs/API_CONTRACT.md`.
- Toàn bộ backend test suite: **362 passed, 0 failed in 62.10s**.
- Frontend build: **2,058 modules transformed, 0 errors in 2.13s**.

### Mốc 22:57:00 — Hoàn thành Iteration 93: Multilevel Structural Equation Modeling (MSEM 1-1-1 Mediation)
- Xây dựng `backend/app/engine/msem_engine.py` (Phân rã hiệp phương sai trực giao Within và Between, 1-1-1 Multilevel Mediation, Monte Carlo 95% CI cho tác động gián tiếp vi mô và vĩ mô, Conflation test kiểm định thiên lệch gộp $ab_B - ab_W$, Dual-panel SVG, APA 7th narrative).
- Viết unit tests `backend/tests/test_msem_engine.py` (3 passed) và route tests `backend/tests/test_msem_routes.py` (1 passed).
- Thêm schemas, router POST `/msem`, audit log `MSEM_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `MSEMCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 74 trong `docs/API_CONTRACT.md`.
- Toàn bộ backend test suite: **366 passed, 0 failed in 69.37s**.
- Frontend build: **2,059 modules transformed, 0 errors in 962ms**.

### Mốc 23:02:00 — Hoàn thành Iteration 94: Targeted Maximum Likelihood Estimation (TMLE)
- Xây dựng `backend/app/engine/tmle_engine.py` (Ước lượng bán tham số bền vững kép Doubly Robust, mô hình điểm xu hướng $g(W)$ với cắt xén biên gbound=0.025, mô hình kết quả $\bar{Q}(A, W)$, Clever Covariate $H^*(A, W)$, bước dao động mục tiêu MLE $\epsilon$, hàm ảnh hưởng tối ưu EIC $D^*(O_i)$, đối chiếu 4 ước lượng nhân quả, Dual-panel SVG, APA 7th narrative).
- Viết unit tests `backend/tests/test_tmle_engine.py` (3 passed) và route tests `backend/tests/test_tmle_routes.py` (1 passed).
- Thêm schemas, router POST `/tmle`, audit log `TMLE_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `TMLECard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 75 trong `docs/API_CONTRACT.md`.
- Toàn bộ backend test suite: **370 passed, 0 failed in 61.89s**.
- Frontend build: **2,060 modules transformed, 0 errors in 1.04s**.

### Mốc 23:08:30 — Hoàn thành Iteration 95: Synthetic Difference-in-Differences (SDID)
- Xây dựng `backend/app/engine/sdid_engine.py` (Tối ưu hóa trọng số đơn vị đối chứng $\omega_i$ kèm phạt chính quy hóa sai phân bậc 1 $\zeta^2$, tối ưu hóa trọng số thời gian $\lambda_t$, ước lượng kép $\hat{\tau}^{sdid}$, kiểm định hoán vị giả dược Placebo in-space, đối chiếu DiD vs SCM vs SDID, Dual-panel SVG, APA 7th narrative).
- Viết unit tests `backend/tests/test_sdid_engine.py` (3 passed) và route tests `backend/tests/test_sdid_routes.py` (1 passed).
- Thêm schemas, router POST `/sdid`, audit log `SDID_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `SDIDCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 76 trong `docs/API_CONTRACT.md`.
- Toàn bộ backend test suite: **374 passed, 0 failed**.
- Frontend build: **2,061 modules transformed, 0 errors in 1.51s**.

### Mốc 23:17:30 — Hoàn thành Iteration 96: Generalized Causal Forest (GRF; Athey, Tibshirani & Wager 2019)
- Xây dựng `backend/app/engine/causal_forest_engine.py` (Honest Causal Trees ensemble, ước lượng CATE $\hat{\tau}(X_i)$, xếp hạng Variable Importance, phân phối tần suất CATE, kiểm định Omnibus Heterogeneity test, Dual-panel SVG, APA 7th narrative).
- Viết unit tests `backend/tests/test_causal_forest_engine.py` (3 passed) và route tests `backend/tests/test_causal_forest_routes.py` (1 passed).
- Thêm schemas, router POST `/causal-forest`, audit log `CAUSAL_FOREST_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `CausalForestCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 77 trong `docs/API_CONTRACT.md`.
- Toàn bộ backend test suite: **378 passed, 0 failed in 75.73s**.
- Frontend build: **2,062 modules transformed, 0 errors in 1.56s**.

### Mốc 23:28:00 — Hoàn thành Iteration 97: Causal Mediation Analysis with Sensitivity Analysis for Unmeasured Confounding
- Xây dựng `backend/app/engine/causal_mediation_sensitivity_engine.py` (Khung phân tích Imai, Keele & Tingley 2010; phân rã ACME $\delta$ và ADE $\zeta$; tham số tương quan sai số $\rho = \text{Corr}(e_M, e_Y)$; nghiệm giải tích đóng của ngưỡng triệt tiêu $\tilde{\rho} = \frac{\beta_M \sigma_M}{\sqrt{\sigma_Y^2 + \beta_M^2 \sigma_M^2}}$; tích $R^{*2}_M R^{*2}_Y = \tilde{\rho}^2$; phân loại độ vững chắc `HIGHLY_ROBUST`, `MODERATELY_ROBUST`, `FRAGILE_TO_CONFOUNDING`; Dual-panel SVG: Causal Path Diagram + ACME Sensitivity Curve with 95% CI ribbon; APA 7th narrative).
- Viết unit tests `backend/tests/test_causal_mediation_sensitivity_engine.py` (3 passed) và route tests `backend/tests/test_causal_mediation_sensitivity_routes.py` (1 passed).
- Thêm schemas, router POST `/causal-mediation-sensitivity`, audit log `CAUSAL_MEDIATION_SENSITIVITY_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `CausalMediationSensitivityCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 78 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,063 modules transformed, 0 errors in 1.03s**.

### Mốc 23:34:00 — Hoàn thành Iteration 98: Dynamic Time Warping (DTW) Longitudinal Trajectory Clustering
- Xây dựng `backend/app/engine/dtw_clustering_engine.py` (Quy hoạch động ma trận chi phí tích lũy DTW với ràng buộc dải Sakoe-Chiba $r$; phân cụm K-Medoids PAM với k-means++ distance-weighted initialization; ước lượng quỹ đạo trung tâm Barycenter averaging DBA; tự động phân loại hình thái quỹ đạo; hệ số Silhouette dựa trên khoảng cách phi tuyến DTW; Dual-panel SVG: Spaghetti Trajectory Plot with Barycenter Centroids + Proportion Distribution Cards; APA 7th narrative).
- Viết unit tests `backend/tests/test_dtw_clustering_engine.py` (4 passed) và route tests `backend/tests/test_dtw_clustering_routes.py` (1 passed).
- Thêm schemas, router POST `/dtw-clustering`, audit log `DTW_TRAJECTORY_CLUSTERING_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `DTWClusteringCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 79 trong `docs/API_CONTRACT.md`.
- Toàn bộ backend test suite: **387 passed, 0 failed in 81.95s (100% pass rate)**.
- Frontend build: **2,064 modules transformed, 0 errors in 1.36s**.


### Mốc 23:41:00 — Hoàn thành Iteration 99: Causal Interaction Trees & Honest Subgroup Identification
- Xây dựng `backend/app/engine/causal_tree_engine.py` (Phương pháp luận Athey & Imbens 2016; phân tách mẫu trung thực Honest splitting 50/50 giữa cấu trúc cây $J_{\text{tr}}$ và ước lượng hiệu ứng $J_{\text{est}}$; tiêu chuẩn tối đa hóa phương sai phân khúc $\Delta(L, R) = \frac{N_L N_R}{N_P} (\hat{\tau}_L - \hat{\tau}_R)^2$; phân loại hình thái đáp ứng `STRONG_POSITIVE_RESPONDERS`, `ADVERSE_BACKFIRE_RESPONDERS`, `MODERATE_POSITIVE`, `NEUTRAL_NO_EFFECT`; Dual-panel SVG: Decision Tree Flowchart + Subgroup Forest Plot; APA 7th narrative).
- Viết unit tests `backend/tests/test_causal_tree_engine.py` (3 passed) và route tests `backend/tests/test_causal_tree_routes.py` (1 passed).
- Thêm schemas, router POST `/causal-tree`, audit log `CAUSAL_TREE_SUBGROUPS_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `CausalTreeCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 80 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,065 modules transformed, 0 errors in 940ms**.
- Toàn bộ backend test suite: **391 passed, 0 failed in 82.56s (100% pass rate)**.

### Mốc 23:49:00 — Hoàn thành Iteration 100: Multiple Testing Correction & False Discovery Rate (FDR Matrix) Engine
- Xây dựng `backend/app/engine/multiple_testing_fdr_engine.py` (Khung lý thuyết Benjamini & Hochberg 1995, Benjamini & Yekutieli 2001, Storey 2002; thuật toán sắp xếp rank tăng dần $p_{(1)} \le \dots \le p_{(m)}$; kiểm soát FDR theo ngưỡng $p_{(k)} \le \frac{k}{m} Q$; ước lượng tỷ lệ giả thuyết vô hiệu thực tế $\hat{\pi}_0$; phân loại kết luận: `SURVIVES_BONFERRONI`, `DISCOVERED_BH_FDR`, `FILTERED_FALSE_POSITIVE`, `NON_SIGNIFICANT`; Dual-panel SVG: Rank-Order P-Value Curve đối chiếu đường chéo BH và đường ngang Bonferroni + Bar chart đối chiếu số lượng phát hiện qua 4 tầng; APA 7th narrative).
- Viết unit tests `backend/tests/test_multiple_testing_fdr_engine.py` (3 passed) và route tests `backend/tests/test_multiple_testing_fdr_routes.py` (2 passed).
- Thêm schemas, router POST `/multiple-testing-fdr`, audit log `MULTIPLE_TESTING_FDR_CORRECTED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `MultipleTestingFDRCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 81 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,066 modules transformed, 0 errors in 962ms**.
- Toàn bộ backend test suite: **396 passed, 0 failed in 73.09s (100% pass rate)**.

### Mốc 23:58:30 — Hoàn thành Iteration 101: Bayesian Structural Equation Modeling (BSEM) with MCMC Gibbs Sampling & Prior Sensitivity
- Xây dựng `backend/app/engine/bsem_engine.py` (Phương pháp luận Muthén & Asparouhov 2012, Gelman et al. 2013; giải quyết triệt để rào cản nhận diện mô hình SEM cổ điển bằng phân phối tiên nghiệm co rút thông tin nhỏ $\lambda_{\text{cross}} \sim \mathcal{N}(0, \sigma_0^2)$; thuật toán MCMC Gibbs Sampling với Data Augmentation lấy mẫu xen kẽ biến tiềm ẩn $\eta_i$, hệ số tải $\Lambda$, sai số $\Theta$ và hồi quy cấu trúc $\gamma$; chẩn đoán hội tụ Gelman-Rubin $\hat{R} \le 1.10$, Effective Sample Size ESS, Monte Carlo Standard Error MCSE; chỉ số phù hợp Posterior Predictive $p$-value PPP; phân tích độ nhạy tiên nghiệm van Erp et al. 2018 qua $\sigma_0 \in [0.005, 0.10]$; Dual-panel SVG: MCMC Trace & Posterior Density + Sơ đồ đường dẫn cấu trúc BSEM; APA 7th narrative).
- Viết unit tests `backend/tests/test_bsem_engine.py` (3 passed) và route tests `backend/tests/test_bsem_routes.py` (2 passed).
- Thêm schemas, router POST `/bsem`, audit log `BSEM_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `BSEMCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 82 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,067 modules transformed, 0 errors in 1.05s**.
- Toàn bộ backend test suite: **401 passed, 0 failed in 68.65s (100% pass rate)**.

### Mốc 00:07:30 — Hoàn thành Iteration 102: Endogeneity Control via Gaussian Copula Estimation
- Xây dựng `backend/app/engine/gaussian_copula_engine.py` (Phương pháp luận Park & Gupta 2012, Becker et al. 2022; giải quyết triệt để sai lệch nội sinh do biến tiềm ẩn bị bỏ sót mà không cần biến công cụ ngoại sinh; khai thác tính phi chuẩn của biến khảo sát thông qua biến công cụ Gaussian Copula $C_P = \Phi^{-1}(\hat{F}_P(P))$; kiểm định phi chuẩn Jarque-Bera $p < 0.05$; kiểm tra đa cộng tuyến Copula VIF $< 10$; tái chọn mẫu Bootstrap ước lượng sai số chuẩn và 95% Bootstrap CI; kiểm định tham số nội sinh $t_\rho, p_\rho$; phân loại `ENDOGENEITY_CONFIRMED` vs `NO_SIGNIFICANT_ENDOGENEITY`; lượng hóa khoảng cách sai lệch bias gap $\Delta = \beta_{\text{OLS}} - \beta_{\text{Copula}}$; Dual-panel SVG: Phân phối phi chuẩn thực nghiệm + Forest plot đối chiếu Naive OLS vs Copula; APA 7th narrative).
- Viết unit tests `backend/tests/test_gaussian_copula_engine.py` (4 passed) và route tests `backend/tests/test_gaussian_copula_routes.py` (2 passed).
- Thêm schemas, router POST `/gaussian-copula`, audit log `GAUSSIAN_COPULA_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `GaussianCopulaCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 83 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,068 modules transformed, 0 errors in 971ms**.
- Toàn bộ backend test suite: **407 passed, 0 failed in 60.43s (100% pass rate)**.


### Mốc 00:16:30 — Hoàn thành Iteration 103: Dynamic Factor Modeling (DFM) with Kalman Filter & RTS State-Space Smoothing
- Xây dựng ackend/app/engine/dynamic_factor_model_engine.py (Phương pháp luận Stock & Watson 2002, 2011; Durbin & Koopman 2012; Harvey 1989; mô hình không gian trạng thái State-Space Model giải mã quỹ đạo nhân tố vĩ mô/hành vi tiềm ẩn trong khảo sát đa chu kỳ Multi-wave Panel Surveys; khởi tạo phân rã SVD; thuật toán Bộ lọc Kalman chuyển tiếp Forward Kalman Filter; thuật toán Bộ làm mịn lùi Rauch-Tung-Striebel Backward RTS Smoother; phân rã phương sai và tỷ số tín hiệu trên nhiễu Signal-to-Noise Ratio SNR cho từng câu hỏi; Dual-panel SVG: Latent Factor Dynamic Trajectory với 95% Confidence Ribbon + Stacked Variance Decomposition Bar Chart; APA 7th narrative).
- Viết unit tests ackend/tests/test_dfm_engine.py (3 passed) và route tests ackend/tests/test_dfm_routes.py (2 passed).
- Thêm schemas, router POST /dynamic-factor, audit log DYNAMIC_FACTOR_MODEL_EVALUATED.
- Thêm types trong survey.ts, API client trong client.ts, component DynamicFactorModelCard.tsx, mount vào SurveyAnalyticsPage.tsx.
- Ghi nhận Section 84 trong docs/API_CONTRACT.md.
- Frontend build: **2,069 modules transformed, 0 errors in 977ms**.
- Toàn bộ backend test suite: **412 passed, 0 failed in 70.60s (100% pass rate)**.


### Mốc 00:23:30 — Hoàn thành Iteration 104: Extreme Bound Analysis (EBA) Specification Curve Engine
- Xây dựng ackend/app/engine/extreme_bounds_engine.py (Phương pháp luận Edward Leamer 1983, 1985; Xavier Sala-i-Martin 1997; Christensen & Miguel 2018; quét tổ hợp không gian mô hình hồi quy OLS qua bể biến kiểm soát ứng viên nhằm kiểm định độ nhạy và tính vững chắc của biến trọng tâm chống lại hiện tượng khai thác dữ liệu p-hacking / specification searching; tiêu chuẩn Leamer Extreme Bounds $[\beta_{\min} - 1.96 SE, \beta_{\max} + 1.96 SE]$ phân loại ROBUST_POSITIVE, ROBUST_NEGATIVE, FRAGILE; tiêu chuẩn phân phối tích lũy Sala-i-Martin CDF(0) không trọng số và có trọng số ^2$; Dual-panel SVG: Specification Curve với dải tin cậy 95% tô màu theo mức ý nghĩa + Histogram phân phối tần suất $\beta$ kèm vạch cực trị Leamer và Gauge widget Sala-i-Martin CDF(0); APA 7th narrative).
- Viết unit tests ackend/tests/test_extreme_bounds_engine.py (3 passed) và route tests ackend/tests/test_extreme_bounds_routes.py (2 passed).
- Thêm schemas ExtremeBoundsAnalysisRequest, ExtremeBoundsAnalysisOut trong ackend/app/schemas.py.
- Thêm router endpoint POST /api/surveys/{survey_id}/analytics/extreme-bounds, audit log EXTREME_BOUNDS_ANALYSIS_EVALUATED.
- Thêm types trong survey.ts, API client trong client.ts, component ExtremeBoundsAnalysisCard.tsx, mount vào SurveyAnalyticsPage.tsx.
- Ghi nhận Section 85 trong docs/API_CONTRACT.md.
- Frontend build: **2,070 modules transformed, 0 errors in 933ms**.
- Toàn bộ backend test suite: **417 passed, 0 failed in 64.87s (100% pass rate)**.


### Mốc 00:35:00 — Hoàn thành Iteration 105: Spatial Econometrics & Moran's I Autoregressive Engine (SAR / SEM) [Heartbeat 4]
- Sửa lỗi tiềm ẩn (latent bug) trong QualityEngine: thêm import json và @staticmethod cho extract_gps_point, giúp trích xuất tọa độ GPS an toàn từ chuỗi JSON client_metadata trong cơ sở dữ liệu.
- Xây dựng ackend/app/engine/spatial_econometrics_engine.py (Phương pháp luận Luc Anselin 1988; James LeSage & R. Kelley Pace 2009; Kelejian & Prucha 1998; Moran 1950; khắc phục vi phạm tính độc lập không gian Tobler's First Law trong khảo sát thực địa GPS; xây dựng ma trận trọng số không gian $ nghịch đảo khoảng cách trắc địa Haversine và $-NN chuẩn hóa hàng; kiểm định Moran's I toàn cục với kỳ vọng giải tích [I]$ và phương sai Cliff & Ord 1981; kiểm định chẩn đoán nhân tử Lagrange Anselin {\text{Lag}}$ và {\text{Error}}$; ước lượng mô hình tự hồi quy không gian SAR qua Spatial 2SLS; phân rã tác động LeSage & Pace: Tác động Trực tiếp Direct, Lan tỏa không gian Spillover, và Tổng tác động Total; Dual-panel SVG: Moran Scatterplot  Y$ vs $ với 4 góc phần tư và đường dốc Moran's I + Biểu đồ thanh nhóm phân rã hiệu ứng; APA 7th narrative).
- Viết unit tests ackend/tests/test_spatial_econometrics_engine.py (3 passed) và route tests ackend/tests/test_spatial_econometrics_routes.py (2 passed).
- Thêm schemas SpatialEconometricsRequest, SpatialEconometricsOut trong ackend/app/schemas.py.
- Thêm router endpoint POST /api/surveys/{survey_id}/analytics/spatial-econometrics, audit log SPATIAL_ECONOMETRICS_EVALUATED.
- Thêm types trong survey.ts, API client trong client.ts, component SpatialEconometricsCard.tsx, mount vào SurveyAnalyticsPage.tsx.
- Ghi nhận Section 86 trong docs/API_CONTRACT.md.
- Frontend build: **2,071 modules transformed, 0 errors in 1.56s**.
- Toàn bộ backend test suite: **422 passed, 0 failed in 79.99s (100% pass rate)**.


### Mốc 00:41:00 — Hoàn thành Iteration 106: Instrumental Variable Quantile Regression (IV-QR) Engine
- Xây dựng `backend/app/engine/iv_quantile_regression_engine.py` (Phương pháp luận Victor Chernozhukov & Christian Hansen 2005, 2008; Koenker & Bassett 1978; giải quyết triệt để vấn đề sai lệch nội sinh phân phối đồng thời mô hình hóa sự bất đồng nhất dị biệt Quantile Treatment Effects (QTE); thuật toán Tối ưu hóa Nghịch đảo Phân vị Inverse Quantile Regression (IQR) qua lưới tham số nội sinh $\alpha \in [\alpha_{\min}, \alpha_{\max}]$ kết hợp lặp trọng số nhỏ nhất IRLS cho hàm mất mát phân vị Check Loss $\rho_\tau$; khoảng tin cậy nghịch đảo kép Chernozhukov-Hansen Dual-Inversion 95% CI thông qua tập mức thống kê Wald $W_n(\alpha) \le \chi^2_1(0.95) = 3.841$; lượng hóa khoảng cách sai lệch nội sinh Endogeneity Bias Gap $\Delta(\tau) = \hat{\alpha}_{\text{QR}}(\tau) - \hat{\alpha}_{\text{IV-QR}}(\tau)$; đo lường độ phân kỳ phân vị Interquantile Spread $\hat{\Delta}_{90-10}$; Dual-panel SVG: Quỹ đạo IV-QR QTE Trajectory với dải tin cậy 95% CI ribbon đối chiếu 2SLS LATE, Naive OLS và Exogenous QR + Đường biên hàm mục tiêu Wald $W_n(\alpha)$ tại trung vị $\tau=0.50$ kèm ngưỡng cắt $\chi^2$; APA 7th narrative).
- Viết unit tests `backend/tests/test_iv_quantile_regression_engine.py` (3 passed) và route tests `backend/tests/test_iv_quantile_regression_routes.py` (2 passed).
- Thêm schemas `IVQuantileRegressionRequest`, `IVQuantileRegressionOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/iv-quantile-regression`, audit log `IV_QUANTILE_REGRESSION_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `IVQuantileRegressionCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 87 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,072 modules transformed, 0 errors in 1.40s**.
- Toàn bộ backend test suite: **427 passed, 0 failed in 91.05s (100% pass rate)**.


### Mốc 00:52:00 — Hoàn thành Iteration 107: Choice-Based Conjoint (CBC) Analysis with Hierarchical Bayes (HB) Part-Worth Utilities
- Xây dựng `backend/app/engine/conjoint_hb_engine.py` (Phương pháp luận Rossi, Allenby & McCulloch 2005; Allenby & Rossi 1998; McFadden 1974 Nobel 2000; Green & Srinivasan 1990; giải quyết triệt để giả định đồng nhất phi thực tế và vi phạm tiên đề IIA của mô hình Logit đa thức tổng gộp thông qua mô hình Bayes phân tầng hai cấp độ; tầng trên ước lượng phân phối dân số $\beta_i \sim \mathcal{N}(\mu, \Sigma)$ với tiên nghiệm liên hợp chuẩn - nghịch đảo Wishart; tầng dưới ước lượng lựa chọn cá thể qua xác suất Multinomial Logit; thuật toán MCMC hỗn hợp Gibbs / Metropolis-Hastings bước nhảy ngẫu nhiên thích ứng duy trì tỷ lệ chấp nhận chuỗi ~25-35%; chuẩn hóa Effects Coding zero-sum $\sum \beta_{a,l} = 0$; trích xuất tiện ích từng phần cá thể và kỳ vọng dân số $\hat{\mu}$ kèm khoảng tin cậy Bayes 95% BCI; tính toán độ quan trọng tương đối của thuộc tính Relative Importance (%) tại cấp cá thể và tổng hợp độ lệch chuẩn SD; định giá thặng dư sẵn sàng chi trả Willingness to Pay - WTP dựa trên hệ số nhạy cảm giá $\alpha_{\text{price}}$; công cụ mô phỏng thị phần lựa chọn giả định Market Choice Share Simulator theo quy tắc Logit Share of Preference; Dual-panel SVG: Biểu đồ thanh ngang tỷ trọng thuộc tính + Phổ tiện ích từng phần kèm thanh sai số 95% BCI; APA 7th narrative).
- Viết unit tests `backend/tests/test_conjoint_hb_engine.py` (3 passed) và route tests `backend/tests/test_conjoint_hb_routes.py` (2 passed).
- Thêm schemas `ConjointHBAnalysisRequest`, `ConjointHBAnalysisOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/conjoint-hb`, audit log `CONJOINT_HB_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `ConjointHBCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 88 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,073 modules transformed, 0 errors in 1.10s**.
- Backend tests mới: **5 passed, 0 failed in 1.92s**.


### Mốc 00:58:00 — Hoàn thành Iteration 108: Fractional Response Regression QMLE Engine (Papke & Wooldridge 1996, 2008)
- Xây dựng `backend/app/engine/fractional_response_engine.py` (Phương pháp luận Leslie Papke & Jeffrey Wooldridge 1996, 2008; Gourieroux, Monfort & Trognon 1984; Wooldridge 2010; giải quyết triệt để vấn đề biến kết quả khảo sát là tỷ lệ, phần trăm, điểm chuẩn hóa bị chặn nghiêm ngặt trong khoảng đơn vị $[0, 1]$ có chứa các điểm khối xác suất cực trị tại biên 0 và 1; khắc phục các khiếm khuyết nghiêm trọng của OLS tuyến tính dự báo ngoài biên $[<0 \text{ hoặc } >1]$ và biến đổi Log-Odds không xác định tại 0 và 1; tối ưu hóa hàm Quasi-Log-Likelihood Bernoulli với các hàm liên kết Logit, Probit, và Complementary Log-Log cloglog; ma trận hiệp phương sai sandwich Huber-White vững $\text{Var}(\hat{\beta}) = \mathbf{A}^{-1} \mathbf{B} \mathbf{A}^{-1}$; tính toán Hiệu ứng Biên Trung bình Average Marginal Effects AME và Hiệu ứng Biên tại Trung bình MEM kèm sai số chuẩn phương pháp Delta; kiểm định chẩn đoán dạng hàm phi tuyến Ramsey RESET; định lượng số lượng vi phạm ngoài biên của Naive OLS; Dual-panel SVG: Đường phản hồi bão hòa phi tuyến Sigmoid đối chiếu đường thẳng OLS kèm dải tin cậy 95% + Forest plot các hiệu ứng biên AME; APA 7th narrative).
- Viết unit tests `backend/tests/test_fractional_response_engine.py` (3 passed) và route tests `backend/tests/test_fractional_response_routes.py` (1 passed).
- Thêm schemas `FractionalResponseRequest`, `FractionalResponseOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/fractional-response`, audit log `FRACTIONAL_RESPONSE_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `FractionalResponseCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 89 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,074 modules transformed, 0 errors in 910ms**.
- Backend tests mới: **4 passed, 0 failed in 1.06s**.


### Mốc 01:03:00 — Hoàn thành Iteration 109: Multidimensional Item Response Theory (MIRT) & Compensatory M2PL Engine [Heartbeat 5]
- Xây dựng `backend/app/engine/mirt_engine.py` (Phương pháp luận Mark D. Reckase 2009, Reckase & McKinley 1991; Bock & Aitkin 1981; Samejima 1969; mở rộng đo lường tâm lý học và khảo sát khi câu hỏi đồng thời đo lường nhiều chiều năng lực/hành vi tiềm ẩn $\boldsymbol{\theta}_i \in \mathbb{R}^D$; giải quyết triệt để sự sai lệch nghiêm trọng của giả định đơn chiều Unidimensional IRT; thuật toán Cực đại Hợp lý Biên Marginal Maximum Likelihood EM với lưới cầu phương Gauss-Hermite đa chiều $Q = K^D$; ước lượng độ dốc phân biệt đa chiều $\mathbf{a}_j = (a_{j1}, \dots, a_{jD})'$ và hệ số chặn $d_j$; tính toán Chỉ số Phân biệt Đa chiều Multidimensional Discrimination Index $\text{MDISC}_j = \|\mathbf{a}_j\|_2 = \sqrt{\sum a_{jd}^2}$ và phân loại năng lực; tính góc đo lường chỉ hướng tối ưu Direction of Best Measurement $\alpha_{jd} = \arccos(a_{jd} / \text{MDISC}) \times \frac{180}{\pi}$; tính Độ khó Đa chiều Multidimensional Item Difficulty $\text{MID}_j = - d_j / \text{MDISC}$; ước lượng điểm năng lực cá nhân Expected A Posteriori EAP scoring $\hat{\boldsymbol{\theta}}_i$; ma trận tương quan thực nghiệm giữa các chiều tiềm ẩn; chẩn đoán độ khớp mục hỏi Orlando-Thissen $S-\chi^2$ và Item RMSEA; Dual-panel SVG: Không gian Vector Thuộc tính Item Vector Space trong hệ tọa độ $\theta_1 - \theta_2$ kèm mũi tên vector chỉ hướng + Biểu đồ thanh ngang phân bổ MDISC và MID; APA 7th narrative).
- Viết unit tests `backend/tests/test_mirt_engine.py` (3 passed) và route tests `backend/tests/test_mirt_routes.py` (1 passed).
- Thêm schemas `MIRTAnalysisRequest`, `MIRTAnalysisOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/mirt`, audit log `MIRT_MODEL_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `MIRTCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 90 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,075 modules transformed, 0 errors in 1.24s**.
- Backend tests mới: **4 passed, 0 failed in 1.53s**.


### Mốc 01:09:00 — Hoàn thành Iteration 110: Heckman Two-Step Sample Selection Bias Correction Engine (Heckman 1979 Nobel Prize)
- Xây dựng `backend/app/engine/heckman_selection_engine.py` (Phương pháp luận James Heckman 1979 Nobel 2000; William Greene 1981; Wooldridge 2010; Bushway et al. 2007; giải quyết triệt để sai lệch chọn mẫu phi ngẫu nhiên Non-random sample selection bias, thiên lệch tự chọn lọc và mất dấu quan sát trong khảo sát; Bước 1 ước lượng mô hình Probit xác suất chọn mẫu $P(S=1|Z) = \Phi(Z\gamma)$ trên toàn bộ mẫu $N$ và trích xuất Tỷ số Nghịch đảo Mills Inverse Mills Ratio IMR $\lambda_i = \phi(Z_i\hat{\gamma}) / \Phi(Z_i\hat{\gamma})$; Bước 2 hồi quy phương trình kết quả có điều kiện với biến kiểm soát $\lambda_i$; áp dụng hiệu chỉnh ma trận hiệp phương sai tiệm cận Heckman-Greene xử lý triệt để biến ước lượng và phương sai thay đổi điều kiện; kiểm định thống kê $t$ trên giả thuyết vô hiệu $H_0: \beta_\lambda = 0$ và $\rho = 0$; lượng hóa khoảng cách sai lệch chọn mẫu Selection Bias Gap $\Delta = \beta_{\text{OLS}} - \beta_{\text{Heckman}}$ cho từng biến chính sách; kiểm tra ràng buộc loại trừ Exclusion Restriction; Dual-panel SVG: Đường cong tỷ số nghịch đảo Mills $\lambda(p)$ kèm mật độ rug plot + Forest plot đối chiếu Naive OLS vs Heckman kèm dải tin cậy 95% CI; APA 7th narrative).
- Viết unit tests `backend/tests/test_heckman_selection_engine.py` (3 passed) và route tests `backend/tests/test_heckman_routes.py` (1 passed).
- Thêm schemas `HeckmanSelectionRequest`, `HeckmanSelectionOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/heckman-selection`, audit log `HECKMAN_SELECTION_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `HeckmanSelectionCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 91 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,076 modules transformed, 0 errors in 1.49s**.
- Backend tests mới: **4 passed, 0 failed in 1.35s**.


### Mốc 01:20:00 — Hoàn thành Iteration 111: Stochastic Frontier Analysis (SFA) & Technical Efficiency Engine (Aigner et al. 1977; JLMS 1982)
- Xây dựng `backend/app/engine/stochastic_frontier_engine.py` (Phương pháp luận Dennis Aigner, C.A. Knox Lovell & Peter Schmidt 1977; Meeusen & van Den Broeck 1977; Jondrow, Lovell, Materov & Schmidt - JLMS 1982; Kumbhakar & Lovell 2000; Greene 2008; ước lượng biên sản xuất tối đa lý thuyết và điểm hiệu quả kỹ thuật thực tế của các đơn vị sản xuất/tổ chức/cá nhân; phân rã cấu trúc sai số hỗn hợp $\epsilon_i = v_i - u_i$ trong đó $v_i \sim \mathcal{N}(0, \sigma_v^2)$ là nhiễu ngẫu nhiên hai chiều và $u_i \sim \text{Half-Normal}(0, \sigma_u^2)$ với $u_i \ge 0$ là độ kém hiệu quả kỹ thuật phi âm; cực đại hóa hàm Log-Likelihood chính xác theo Aigner et al. bằng thuật toán L-BFGS-B tham số hóa qua $(\beta, \ln \sigma, \ln \lambda)$ đảm bảo hội tụ số học bền vững; tính toán sai số chuẩn tiệm cận bằng nghịch đảo ma trận Hessian số học; trích xuất điểm ước lượng kém hiệu quả cá thể JLMS $\hat{u}_i = E[u_i | \epsilon_i]$ và chỉ số hiệu quả kỹ thuật $\text{TE}_i = \exp(-\hat{u}_i) \in (0, 100\%]$; kiểm định tỷ số hợp lý Likelihood Ratio LR test theo phân phối Kodde & Palm 1986 về sự hiện diện của kém hiệu quả kỹ thuật; kiểm định độ lệch Waldman 1982 trên phần dư OLS; phân tích độ co giãn quy mô Returns to Scale RTS $\sum \beta_k$ thành IRS/CRS/DRS; Dual-panel SVG: Đường cong biên sản xuất tối ưu đối chiếu đám mây điểm quan sát và OLS + Biểu đồ phân bổ tần suất hiệu quả kỹ thuật JLMS $\text{TE}_i$; APA 7th narrative).
- Viết unit tests `backend/tests/test_stochastic_frontier_engine.py` (3 passed) và route tests `backend/tests/test_stochastic_frontier_routes.py` (1 passed).
- Thêm schemas `StochasticFrontierRequest`, `StochasticFrontierOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/stochastic-frontier`, audit log `STOCHASTIC_FRONTIER_ANALYSIS_EXECUTED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `StochasticFrontierCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 92 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,077 modules transformed, 0 errors in 946ms**.
- Backend tests mới: **4 passed, 0 failed in 1.16s**.


### Mốc 01:25:00 — Hoàn thành Iteration 112: Zero-Inflated Count Regression Models (ZIP & ZINB) Engine (Lambert 1992; Greene 1994; Vuong 1989)
- Xây dựng `backend/app/engine/zero_inflated_engine.py` (Phương pháp luận Diane Lambert 1992; William Greene 1994; Quang H. Vuong 1989; J. Scott Long 1997; mô hình hóa dữ liệu đếm khảo sát có hiện tượng tích tụ đột biến điểm 0 vượt mức excess zeros; phân tách cơ chế thành mô hình hỗn hợp hữu hạn hai trạng thái: trạng thái đột biến không luôn bằng 0 structural zero thông qua hàm liên kết Logit $p_i = 1/(1 + \exp(-Z\gamma))$ và trạng thái phân phối đếm Poisson hoặc Negative Binomial NB2 với kỳ vọng $\mu_i = \exp(X\beta)$ và tham số quá phân tán $\alpha$; kiểm định phi lồng ghép Vuong non-nested test $z = \sqrt{N}\bar{m}/s_m \sim \mathcal{N}(0, 1)$ so sánh mô hình Zero-Inflated với Poisson tiêu chuẩn; tính toán tỷ lệ tần suất biến cố Incidence Rate Ratio IRR $=\exp(\beta)$ và tỷ số tỷ lệ cược Odds Ratio OR $=\exp(\gamma)$ kèm dải tin cậy 95% CI; trích xuất bảng phân phối tần suất thực tế vs dự báo cho từng mức đếm $0, 1, 2, \dots$; Dual-panel SVG: Biểu đồ cột đối chiếu tần suất thực tế vs dự báo phản ánh đột biến điểm 0 + Forest plot các hệ số hồi quy đếm $\beta$ kèm 95% CI; APA 7th narrative).
- Viết unit tests `backend/tests/test_zero_inflated_engine.py` (3 passed) và route tests `backend/tests/test_zero_inflated_routes.py` (1 passed).
- Thêm schemas `ZeroInflatedRequest`, `ZeroInflatedOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/zero-inflated`, audit log `ZERO_INFLATED_MODEL_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `ZeroInflatedCountCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 93 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,078 modules transformed, 0 errors in 1.25s**.
- Backend tests mới: **4 passed, 0 failed in 1.24s**.


### Mốc 01:29:00 — Hoàn thành Iteration 113: Latent Moderated Structural Equations (LMS / QML) Engine (Klein & Moosbrugger 2000; Marsh et al. 2004)
- Xây dựng `backend/app/engine/latent_moderation_engine.py` (Phương pháp luận Andreas Klein & Helfried Moosbrugger 2000; Herbert W. Marsh, Zhonglin Wen & Kit-Tai Hau 2004; Klein & Bengt Muthén 2007; Leona Aiken & Stephen West 1991; giải quyết triệt để vấn đề sai lệch suy giảm nghiêm trọng attenuation bias trong mô hình tương tác biến tiềm ẩn $\xi_1 \times \xi_2 \to \eta$ do sai số đo lường khảo sát làm triệt tiêu tới 50-70% độ lớn tương tác trong OLS thông thường; trích xuất các biến tiềm ẩn bằng mô hình đo lường CFA và ước lượng tham số tương tác phi tuyến $\gamma_3$ bằng thuật toán Chuẩn Hợp lý Cực đại Quasi-Maximum Likelihood QML; ma trận thông tin Hessian số học cho sai số chuẩn tiệm cận vững; phân tích độ dốc đơn giản Simple Slopes Probing tại ba mức độ của biến điều tiết: Thấp -1 SD, Trung bình Mean, và Cao +1 SD kèm kiểm định ý nghĩa $z$-statistic và 95% CI; giải phương trình bậc hai xác định ngưỡng chuyển giao ý nghĩa Johnson-Neyman Cutoffs; định lượng kích thước hiệu ứng Cohen's $f^2$ và phần trăm suy giảm được phục hồi Attenuation Gap %; Dual-panel SVG: Phối cảnh 3D đẳng cự Isometric 3D Wireframe Surface của bề mặt phản hồi tiềm ẩn $\hat{\eta}(\xi_1, \xi_2)$ + Đồ thị phân tích độ dốc đơn giản Simple Slopes với dải màu phân biệt và vạch cắt Johnson-Neyman; APA 7th narrative).
- Viết unit tests `backend/tests/test_latent_moderation_engine.py` (2 passed) và route tests `backend/tests/test_latent_moderation_routes.py` (1 passed).
- Thêm schemas `LatentModerationRequest`, `LatentModerationOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/latent-moderation`, audit log `LATENT_MODERATION_LMS_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `LatentModerationCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 94 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,079 modules transformed, 0 errors in 893ms**.
- Backend tests mới: **3 passed, 0 failed in 1.27s**.


### Mốc 01:34:00 — Hoàn thành Iteration 114: Endogenous Switching Regression (ESR - FIML) Engine (Maddala 1983; Lokshin & Sajaia 2004) [Heartbeat 6]
- Xây dựng `backend/app/engine/endogenous_switching_engine.py` (Phương pháp luận G. S. Maddala 1983; Michael Lokshin & Zurab Sajaia 2004; Lung-Fei Lee 1978; James Heckman 1979; giải quyết triệt để vấn đề sai lệch tự chọn lọc hai chiều nội sinh endogenous self-selection bias khi quyết định can thiệp/áp dụng công nghệ mang tính tự nguyện và hiệu ứng can thiệp không đồng nhất; ước lượng đồng thời hệ phương trình ba biến gồm phương trình chọn lọc Probit $I_i^* = Z_i\gamma + u_i$ và hai phương trình kết quả riêng biệt theo chế độ $Y_{1i} = X_i\beta_1 + \epsilon_{1i}$ và $Y_{0i} = X_i\beta_0 + \epsilon_{0i}$; cực đại hóa hàm Log-Likelihood toàn phần FIML với cấu trúc sai số chuẩn ba biến trivariate normal $(\epsilon_1, \epsilon_0, u)$ tham số hóa Fisher $r_j = \text{atanh}(\rho_j)$ đảm bảo ổn định số học và chặn nghiệm nghiệm ngặt $|\rho_j| < 1$; kiểm định tỷ số hợp lý LR test tính độc lập của các phương trình; phân rã tác động nhân quả phản thực tế causal counterfactual decomposition trích xuất chính xác Tác động xử lý trung bình đối với nhóm can thiệp ATT $= E[Y_{1i} | I_i=1] - E[Y_{0i} | I_i=1]$, Tác động xử lý trung bình đối với nhóm đối chứng ATU $= E[Y_{1i} | I_i=0] - E[Y_{0i} | I_i=0]$, Tính không đồng nhất chuyển đổi Transitional Heterogeneity TH $=$ ATT - ATU, và Tính không đồng nhất cơ sở Base Heterogeneity; Dual-panel SVG: Biểu đồ cột so sánh kết quả thực tế vs phản thực tế cho nhóm Can thiệp (ATT) và Đối chứng (ATU) + Forest plot so sánh hệ số theo chế độ $\beta_1$ vs $\beta_0$ kèm 95% CI; APA 7th narrative).
- Viết unit tests `backend/tests/test_endogenous_switching_engine.py` (2 passed) và route tests `backend/tests/test_endogenous_switching_routes.py` (1 passed).
- Thêm schemas `EndogenousSwitchingRequest`, `EndogenousSwitchingOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/endogenous-switching`, audit log `ENDOGENOUS_SWITCHING_REGRESSION_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `EndogenousSwitchingCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 95 trong `docs/API_CONTRACT.md`.
- Backend tests mới: **3 passed, 0 failed in 1.82s**.


### Mốc 01:41:00 — Hoàn thành Iteration 115: Generalized Propensity Score (GPS) & Continuous Dose-Response Engine (Hirano & Imbens 2004)
- Xây dựng `backend/app/engine/gps_dose_response_engine.py` (Phương pháp luận Keisuke Hirano & Guido W. Imbens 2004; Donald Rubin 2000; mô hình hóa can thiệp liên tục continuous treatment regimes trong khảo sát kinh tế - xã hội như số giờ đào tạo, thời lượng sử dụng, mức đầu tư vốn; ước lượng hàm mật độ xác suất điều kiện điểm xu hướng khái quát $R_i = r(T_i, X_i)$ dưới giả định chuẩn có điều kiện $T_i | X_i \sim \mathcal{N}(X\beta, \sigma^2)$; mô hình hóa hàm hồi quy kết quả có điều kiện bậc hai linh hoạt $E[Y|T, R] = \alpha_0 + \alpha_1 T + \alpha_2 T^2 + \alpha_3 R + \alpha_4 R^2 + \alpha_5 (T \cdot R)$; lấy tích phân trung bình hóa trên toàn bộ quần thể mẫu để ước lượng Hàm Liều Lượng - Đáp Ứng Trung Bình $\mu(t) = E[Y(t)]$ dọc theo lưới liều lượng phân tích; tính đạo hàm bậc nhất suy ra Hàm Hiệu Ứng Can Thiệp Cận Biên $\theta(t) = d\mu(t)/dt$; xác định chính xác điểm liều lượng tối ưu $t^*$ tại đó $\theta(t^*) = 0$ và đáp ứng cực đại $\mu(t^*)$; tính toán dải tin cậy 95% CI cho toàn bộ đường cong; Dual-panel SVG: Panel A thể hiện đường cong Liều lượng - Đáp ứng $\mu(t)$ (màu Indigo) với dải tin cậy 95% CI và vạch mốc liều lượng tối ưu $t^*$ + Panel B thể hiện đường cong Hiệu ứng cận biên $\theta(t)$ (màu Teal) kèm mốc tham chiếu zero; APA 7th narrative).
- Viết unit tests `backend/tests/test_gps_dose_response_engine.py` (2 passed) và route tests `backend/tests/test_gps_dose_response_routes.py` (1 passed).
- Thêm schemas `GPSDoseResponseRequest`, `GPSDoseResponseOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/gps-dose-response`, audit log `GPS_DOSE_RESPONSE_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `GPSDoseResponseCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 96 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,081 modules transformed, 0 errors in 976ms**.
- Backend tests mới: **3 passed, 0 failed in 1.14s**.


### Mốc 01:48:00 — Hoàn thành Iteration 116: Causal Discovery DAG (LiNGAM & ANM) Engine (Shimizu et al. 2006, 2011; Hoyer et al. 2009)
- Xây dựng `backend/app/engine/causal_discovery_engine.py` (Phương pháp luận Shohei Shimizu, Patrik O. Hoyer, Aapo Hyvärinen, Antti Kerminen 2006; Shimizu et al. 2011; Patrik O. Hoyer et al. 2009; giải quyết rào cản tương đương Markov của các mô hình Gaussian cắt ngang thông qua định lý định danh độc nhất của Mô hình đồ thị có hướng phi Gaussian không chu trình LiNGAM; chuẩn hóa và làm trắng ma trận dữ liệu qua phân rã kỳ dị SVD; tối ưu hóa thuật toán FastICA với hàm tương phản hyperbolic tangent để tìm ma trận tách độc lập $\mathbf{W}$; thuật toán tìm hoán vị topo sắp xếp các biến thành chuỗi nhân quả tam giác dưới nghiêm ngặt; ước lượng trọng số đường dẫn trực tiếp $\beta$ và ma trận tổng hiệu ứng nhân quả tích lũy $\mathbf{T} = (\mathbf{I} - \mathbf{B})^{-1} - \mathbf{I}$; kiểm định tính độc lập của phần dư và biến căn nguyên thông qua Mô hình Nhiễu Cộng tính ANM loại trừ nguy cơ đảo chiều nhân quả; kiểm tra điều kiện tiên quyết phi Gaussian bằng Skewness, Excess Kurtosis và D'Agostino-Pearson omnibus test $K^2$; Dual-panel SVG: Panel A thể hiện đồ thị DAG với các nút biến, mũi tên có hướng phân màu theo hệ số trực tiếp và độ cong chống đè + Panel B biểu đồ thanh đo lường chỉ số phi chuẩn $|Ku| + |Sk|$ kèm nhãn trạng thái định danh; APA 7th narrative).
- Viết unit tests `backend/tests/test_causal_discovery_engine.py` (3 passed) và route tests `backend/tests/test_causal_discovery_routes.py` (1 passed).
- Thêm schemas `CausalDiscoveryRequest`, `CausalDiscoveryOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/causal-discovery`, audit log `CAUSAL_DISCOVERY_DAG_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `CausalDiscoveryCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 97 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,082 modules transformed, 0 errors in 957ms**.
- Backend tests mới: **4 passed, 0 failed in 1.00s**.


### Mốc 01:54:00 — Hoàn thành Iteration 117: Bayesian Additive Regression Trees (BART) Causal Engine (Chipman et al. 2010; Hill 2011; Hahn et al. 2020)
- Xây dựng `backend/app/engine/bart_causal_engine.py` (Phương pháp luận Hugh A. Chipman, Edward I. George, Robert E. McCulloch 2010; Jennifer L. Hill 2011; P. Richard Hahn, Carlos M. Carvalho et al. 2020; mô hình học máy phi tham số Bayesian cho phép tự động giải quyết các tương tác phi tuyến và hiệu ứng can thiệp không đồng nhất HTE mà không cần định dạng trước dạng hàm; tập hợp tổng các cây hồi quy quyết định nông với các tiên nghiệm co ngót Bayes nghiêm ngặt gồm xác suất phân nhánh $p(\text{split}) = \alpha (1+d)^{-\beta}$ và tiên nghiệm trung bình nút lá $\mu \sim \mathcal{N}(0, \sigma_\mu^2)$; lấy mẫu hậu nghiệm phản thực tế Bayesian Counterfactual Sampling để ước lượng chính xác Hiệu ứng can thiệp trung bình mẫu ATE, Hiệu ứng can thiệp trên nhóm tiếp nhận ATT, Hiệu ứng can thiệp trên nhóm đối chứng ATU kèm khoảng tin cậy hậu nghiệm 95% Bayesian Credible Interval; kiểm định tính không đồng nhất của hiệu ứng can thiệp qua độ lệch chuẩn hậu nghiệm cá thể $\text{SD}(\tau)$; xếp hạng tầm quan trọng của các biến điều tiết Variable Importance VIP qua tần suất phân nhánh; phân rã hiệu ứng có điều kiện CATE theo các phân nhóm Thấp/Cao của biến điều tiết chủ đạo; Dual-panel SVG: Panel A thể hiện đường cong thác nước xếp hạng hiệu ứng cá thể Sorted ITE Waterfall với dải tin cậy hậu nghiệm 95% CrI và đường mốc ATE + Panel B biểu đồ thanh ngang xếp hạng tầm quan trọng của các biến điều tiết kèm nhãn Primary/Secondary; APA 7th narrative).
- Viết unit tests `backend/tests/test_bart_causal_engine.py` (2 passed) và route tests `backend/tests/test_bart_causal_routes.py` (1 passed).
- Thêm schemas `BARTCausalRequest`, `BARTCausalOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/bart-causal`, audit log `BART_CAUSAL_HETEROGENEITY_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `BARTCausalCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 98 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,083 modules transformed, 0 errors in 969ms**.
- Backend tests mới: **3 passed, 0 failed in 1.91s**.


### Mốc 02:00:00 — Hoàn thành Iteration 118: Conjoint Analysis & Discrete Choice Experiment (DCE) Engine (McFadden 1974; Train 2009) [Heartbeat 7]
- Xây dựng `backend/app/engine/conjoint_choice_engine.py` (Phương pháp luận Daniel McFadden 1974 - Giải Nobel Kinh tế; Kenneth E. Train 2009; Peter E. Rossi, Greg M. Allenby & Robert E. McCulloch 2005; giải quyết triệt để hiện tượng sai lệch trần ceiling effects khi khảo sát sở thích người tiêu dùng bằng cách buộc đáp viên đánh đổi thực tế giữa các hồ sơ đa thuộc tính; mô hình hóa xác suất lựa chọn Logit đa thức/điều kiện Multinomial Logit dựa trên Lý thuyết Tối đa hóa Lợi ích Ngẫu nhiên RUM; tối ưu hóa hàm Log-Likelihood với chuẩn hóa L2 bằng thuật toán L-BFGS-B; trích xuất ma trận thông tin Fisher nghịch đảo tính sai số chuẩn tiệm cận vững; ước lượng Độ hữu dụng từng phần Part-Worth Utilities $\beta_k$ và Tầm quan trọng tương đối của từng thuộc tính Relative Attribute Importance $W_a$ (%); định giá Sẵn sàng chi trả biên Marginal Willingness-To-Pay WTP $= -(\beta_k / \beta_{\text{Price}})$ với sai số chuẩn tính bằng phương pháp vi phân Delta Method và dải tin cậy 95% CI theo đơn vị tiền tệ; đánh giá độ phù hợp mô hình qua McFadden's Pseudo-$R^2$, kiểm định tỷ số hợp lý LR Chi-square, AIC, BIC; Dual-panel SVG: Panel A biểu đồ thanh đo lường Tầm quan trọng tương đối (%) của các thuộc tính với dải màu tím/lam + Panel B Forest plot định giá WTP với điểm ước lượng tròn và dải tin cậy 95% CI màu xanh ngọc Emerald; APA 7th narrative).
- Viết unit tests `backend/tests/test_conjoint_choice_engine.py` (3 passed) và route tests `backend/tests/test_conjoint_choice_routes.py` (1 passed).
- Thêm schemas `ConjointChoiceRequest`, `ConjointChoiceOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/conjoint-choice`, audit log `CONJOINT_CHOICE_MNL_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `ConjointChoiceCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 99 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,084 modules transformed, 0 errors in 1.08s**.
- Backend tests mới: **4 passed, 0 failed in 1.21s**.


### Mốc 02:05:00 — Hoàn thành Iteration 119: Multi-Group SEM (MG-SEM) Invariance & Latent Means Engine (Meredith 1993; Byrne 2013) [CỘT MỐC SECTION 100 API CONTRACT]
- Xây dựng `backend/app/engine/mgsem_invariance_engine.py` (Phương pháp luận William Meredith 1993; Jan-Benedict E.M. Steenkamp & Hans Baumgartner 1998; Robert J. Vandenberg & Charles E. Lance 2000; Barbara M. Byrne 2013; Gordon W. Cheung & Robert B. Rensvold 2002; giải quyết triệt để vấn đề so sánh điểm số sai lệch giữa các nhóm nhân khẩu học/vùng miền trong khảo sát; thiết lập quy trình kiểm định bất biến đo lường 4 cấp bậc lồng nhau gồm: Cấp 1 Configural Invariance cấu hình tương đương, Cấp 2 Metric Invariance hệ số tải $\boldsymbol{\Lambda}_1 = \boldsymbol{\Lambda}_2$ hiệu chuẩn thang đo, Cấp 3 Scalar Invariance điểm chặn $\boldsymbol{\tau}_1 = \boldsymbol{\tau}_2$ điều kiện bắt buộc để so sánh điểm tiềm ẩn, và Cấp 4 Strict Invariance sai số đo lường $\boldsymbol{\Theta}_1 = \boldsymbol{\Theta}_2$; đánh giá chỉ số phù hợp mô hình $\chi^2$, df, CFI, RMSEA, SRMR và tiêu chuẩn Cheung & Rensvold $|\Delta \text{CFI}| \le 0.010$; ước lượng chênh lệch điểm trung bình tiềm ẩn Latent Means Analysis $\Delta \alpha = \alpha_2 - \alpha_1$ với nhóm mốc $\alpha_{\text{ref}} = 0$, sai số chuẩn SE, $z$-statistic, $p$-value và kích thước hiệu ứng chuẩn hóa Cohen's $d$; trích xuất bảng hệ số chi tiết từng biến chỉ báo phát hiện thiên lệch câu hỏi DIF; Dual-panel SVG: Panel A Forest plot so sánh hệ số tải nhân tố giữa Nhóm 1 (xanh dương) và Nhóm 2 (hồng cánh sen) + Panel B Đường cong hàm mật độ xác suất chuẩn của biến tiềm ẩn cho hai nhóm minh họa trực quan khoảng cách chênh lệch $\Delta \alpha$ và kích thước hiệu ứng Cohen's $d$; APA 7th narrative).
- Viết unit tests `backend/tests/test_mgsem_invariance_engine.py` (2 passed) and route tests `backend/tests/test_mgsem_invariance_routes.py` (1 passed).
- Thêm schemas `MGSEMInvarianceRequest`, `MGSEMInvarianceOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/mgsem-invariance`, audit log `MGSEM_INVARIANCE_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `MGSEMInvarianceCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận **Cột mốc Lịch sử Section 100** trong `docs/API_CONTRACT.md`.
- Frontend build: **2,085 modules transformed, 0 errors in 1.22s**.
- Backend tests mới: **3 passed, 0 failed in 1.12s**.


### Mốc 02:12:00 — Hoàn thành Iteration 120: Generalized Additive Models (GAM) & Penalized P-Splines Engine (Hastie & Tibshirani 1990; Wood 2017)
- Xây dựng `backend/app/engine/gam_spline_engine.py` (Phương pháp luận Trevor Hastie & Robert Tibshirani 1990; Paul H. C. Eilers & Brian D. Marx 1996; Simon N. Wood 2017; giải quyết triệt để hạn chế giả định tuyến tính cứng nhắc trong kinh tế lượng khảo sát bằng cách mô hình hóa các mối quan hệ phi tuyến phức tạp qua hệ cơ sở hàm B-splines bậc 3 $f(x) = \sum \beta_j B_j(x)$ kết hợp ma trận phạt sai phân đạo hàm cấp hai $\mathbf{S} = \mathbf{D}_2^T \mathbf{D}_2$; cực tiểu hóa bình phương tối thiểu có phạt PLS với nghiệm đóng ma trận Hat $\mathbf{H}_{\lambda}$; thuật toán tự động tối ưu hóa tham số làm trơn $\lambda$ bằng tiêu chuẩn Generalized Cross-Validation GCV; tính toán Bậc tự do hiệu dụng Effective Degrees of Freedom $\text{EDF} = \text{tr}(\mathbf{H}_{\lambda})$; thực hiện kiểm định phi tuyến tính $F$-test đối chiếu mô hình GAM với OLS tuyến tính; dò tìm giải tích nghiệm đạo hàm cấp một $\hat{f}'(x^*) = 0$ nhằm xác định chính xác các Điểm bão hòa Diminishing Returns, Điểm cực đại Tipping Point và Điểm đáy đảo chiều U-Shape; ước lượng dải băng tin cậy Bayes 95% Bayesian Confidence Band theo Nychka 1988; sinh lưới 100 điểm dự báo hỗ trợ mô phỏng What-If; Dual-panel SVG: Panel A Đường cong hàm trơn GAM P-Splines màu xanh dương ngọc kèm dải tin cậy 95% và điểm tán xạ khảo sát + Panel B Đồ thị hàm đạo hàm số cấp một $\hat{f}'(x)$ màu cam san hô đo lường tốc độ tăng trưởng biên Marginal Return; APA 7th narrative).
- Viết unit tests `backend/tests/test_gam_spline_engine.py` (3 passed) và route tests `backend/tests/test_gam_spline_routes.py` (1 passed).
- Thêm schemas `GAMSplineRequest`, `GAMSplineOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/gam-spline`, audit log `GAM_SPLINE_ESTIMATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `GAMSplineCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 101 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,086 modules transformed, 0 errors in 1.08s**.
- Backend tests mới: **4 passed, 0 failed in 1.27s**.


### Mốc 02:20:00 — Hoàn thành Iteration 121: Latent Profile Analysis (LPA) & Gaussian Finite Mixture Models Engine (McLachlan & Peel 2000; Collins & Lanza 2010)
- Xây dựng `backend/app/engine/latent_profile_engine.py` (Phương pháp luận Geoffrey McLachlan & David Peel 2000; Chris Fraley & Adrian E. Raftery 2002; Linda M. Collins & Stephanie T. Lanza 2010; Karen L. Nylund, Tihomir Asparouhov & Bengt O. Muthén 2007; Gilles Celeux & Gerard Soromenho 1996; giải quyết triệt để hạn chế của phân cụm K-means/thứ bậc trong nghiên cứu khảo sát bằng cách mô hình hóa các biến chỉ báo thang đo liên tục qua phân phối hỗn hợp Gauss đa biến hướng cá thể Person-Centered Approach; thuật toán Expectation-Maximization EM với ma trận hiệp phương sai đường chéo có điều chuẩn chống kỳ dị phương sai; kỹ thuật số học ổn định Log-Sum-Exp; quy trình liệt kê số lớp Class Enumeration từ $K = 2$ đến $K = 5$; tiêu chuẩn thông tin tối ưu hóa BIC, Sample-Size Adjusted BIC SABIC, AIC, CAIC; đánh giá độ sắc nét phân tách qua chỉ số Entropy tương đối Celeux & Soromenho $\text{Entropy} \in [0, 1]$ và xác suất hậu nghiệm trung bình AvePP $\ge 0.70$ theo chuẩn Nagin 2005; chuẩn hóa $z$-scores nhận diện chân dung Typology Persona tự động: High-Trust Advocates, Disengaged Detractors, Pragmatic Middle, Selective Focus; Dual-panel SVG: Panel A Latent Profile Plot biểu diễn quỹ đạo điểm chuẩn hóa $z$-score đa lớp với các đường gãy khúc màu sắc tương phản rực rỡ và điểm nút phát sáng + Panel B Thước đo Entropy phân tách kèm thanh đo tỷ lệ phần trăm quy mô phân đoạn và xác suất AvePP; APA 7th narrative).
- Viết unit tests `backend/tests/test_latent_profile_engine.py` (3 passed) và route tests `backend/tests/test_latent_profile_routes.py` (1 passed).
- Thêm schemas `LatentProfileRequest`, `LatentProfileOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/latent-profile`, audit log `LATENT_PROFILE_ANALYSIS_ESTIMATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `LatentProfileCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 102 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,087 modules transformed, 0 errors in 1.05s**.
- Backend tests mới: **4 passed, 0 failed in 1.89s**.


### Mốc 02:24:00 — Hoàn thành Iteration 122: Shapley Value Regression & Key Driver Analysis (KDA) Engine (Lipovetsky & Conklin 2001; Lundberg & Lee 2017)
- Xây dựng `backend/app/engine/shapley_driver_engine.py` (Phương pháp luận Lloyd S. Shapley 1953 - Giải Nobel Kinh tế; Stan Lipovetsky & Michael Conklin 2001; Richard H. Lindeman, Peter F. Merenda & Ruth Z. Gold 1980; John A. Martilla & John C. James 1977; Scott M. Lundberg & Su-In Lee 2017; giải quyết triệt để hiện tượng đa cộng tuyến nghiêm trọng giữa các tiêu chí đánh giá trong khảo sát trải nghiệm khách hàng và nghiên cứu thị trường; mô hình hóa hàm giá trị liên minh $v(S) = R^2(S)$ qua toàn bộ $2^P$ tập hợp con mô hình hồi quy; tính toán đóng góp cận biên chính xác tuyệt đối theo Tiên đề Hiệu quả Hoàn hảo $\sum \phi_j = R^2_{\text{full}}$ và Tiên đề Không âm/Đối xứng; chuẩn hóa tỷ trọng tầm quan trọng tương đối Relative Importance Share $W_j\%$ đạt chính xác $100.0\%$; chẩn đoán hệ số phóng đại phương sai VIF; thiết lập Ma trận Quyết định Ưu tiên Hành động 4 góc phần tư Importance-Performance Analysis IPA Matrix với các ngưỡng trung vị: Q1 Ưu tiên Cải thiện Khẩn cấp Concentrate Here, Q2 Duy trì Phát huy Tối đa Keep Up, Q3 Thứ yếu Low Priority, Q4 Tránh Lãng phí Tài nguyên Possible Overkill; Dual-panel SVG: Panel A Biểu đồ thanh ngang phân cấp Tầm quan trọng tương đối Shapley $W\%$ theo phân tầng chiến lược Emerald/Cyan/Slate + Panel B Ma trận IPA 4 góc phần tư với các đường phân vị đứt nét, nhãn chìm đánh dấu vùng nguy cơ và các điểm dữ liệu tròn phát sáng có nhãn tên thuộc tính; APA 7th narrative).
- Viết unit tests `backend/tests/test_shapley_driver_engine.py` (3 passed) và route tests `backend/tests/test_shapley_driver_routes.py` (1 passed).
- Thêm schemas `ShapleyDriverRequest`, `ShapleyDriverOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/shapley-drivers`, audit log `SHAPLEY_KEY_DRIVERS_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `ShapleyDriverCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 103 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,088 modules transformed, 0 errors in 1.00s**.
- Backend tests mới: **4 passed, 0 failed in 1.24s**.


### Mốc 02:34:00 — Hoàn thành Iteration 123: Plackett-Luce Choice Model & Rank-Ordered Logit Engine (Luce 1959; Plackett 1975; Hunter 2004 MM) [Heartbeat 8 Maintenance]
- Xây dựng `backend/app/engine/plackett_luce_engine.py` (Phương pháp luận R. Duncan Luce 1959; R. L. Plackett 1975; Steven Beggs, Scott Cardell & Jerry Hausman 1981; David R. Hunter 2004; giải quyết triệt để hạn chế giả định khoảng cách đều tuyến tính sai lầm khi phân tích dữ liệu câu hỏi xếp hạng thứ bậc Ranking Questions hoặc thang đo đánh giá đa thuộc tính Implied Ranking; mô hình hóa hàm hợp lý hoán vị xác suất lựa chọn Plackett-Luce; thuật toán tối ưu hóa Minorization-Maximization MM của Hunter 2004 với bảo đảm toán học hội tụ đơn điệu toàn cục đến nghiệm MLE duy nhất; ước lượng tham số giá trị tiềm ẩn Latent Worth $w_j$ và hữu dụng Log-Worth $\gamma_j$; tính sai số chuẩn tiệm cận Asymptotic SE qua nghịch đảo ma trận thông tin Fisher quan sát; kiểm định Wald $z$-test và khoảng tin cậy 95% CI; thiết lập Ma trận Nhiệt Xác suất Thắng Đối đầu Trực diện Pairwise Head-to-Head Win Probability Matrix $M \times M$ theo Tiên đề Lựa chọn IIA của Luce $P(j \succ k) = w_j / (w_j + w_k)$; đánh giá độ phù hợp mô hình qua McFadden Pseudo-$R^2$ và kiểm định Tỷ số Hợp lý Likelihood Ratio Chi-square test vs mô hình vô hiệu; Dual-panel SVG: Panel A Biểu đồ thanh ngang Latent Worth Share $w\%$ kèm tỷ trọng phần trăm tiềm ẩn sắc nét + Panel B Ma trận nhiệt đối đầu trực diện $M \times M$ với thang màu trực quan xanh lục đậm ưu thế áp đảo $> 70\%$ / xanh lục $> 55\%$ / xám cân bằng $\approx 50\%$ / đỏ yếu thế $< 45\%$; APA 7th narrative).
- Viết unit tests `backend/tests/test_plackett_luce_engine.py` (3 passed) và route tests `backend/tests/test_plackett_luce_routes.py` (1 passed).
- Thêm schemas `PlackettLuceRequest`, `PlackettLuceOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/plackett-luce`, audit log `PLACKETT_LUCE_RANKING_CHOICE_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `PlackettLuceCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 104 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,089 modules transformed, 0 errors in 1.03s**.
- Backend tests mới: **4 passed, 0 failed in 1.11s**.


### Mốc 02:39:00 — Hoàn thành Iteration 124: MaxDiff (Maximum Difference / Best-Worst Scaling Case 1) Engine (Finn & Louviere 1992; Marley & Louviere 2005)
- Xây dựng `backend/app/engine/maxdiff_engine.py` (Phương pháp luận Adam Finn & Jordan J. Louviere 1992; A. A. J. Marley & Jordan J. Louviere 2005; Terry N. Flynn et al. 2007; Bryan Orme 2009; giải quyết triệt để hạn chế thiên lệch thang đo Scale Usage Bias và hiệu ứng trần Ceiling Effects trong khảo sát Likert truyền thống bằng cách buộc đáp viên đánh đổi trực tiếp giữa phương án Tốt nhất Best và Kém nhất Worst; mô hình hóa hàm hợp lý lựa chọn cực đại khác biệt qua Logit Đa thức Multinomial Logit MLE với thuật toán L-BFGS-B; điều kiện nhận dạng cố định tổng độ hữu dụng $\sum \beta_j = 0$; ước lượng Thị phần Ưu tiên Chuẩn hóa Rescaled Preference Share $P_j = \exp(\beta_j) / \sum \exp(\beta_k) \times 100\%$ đạt chuẩn Thang Tỷ Lệ Ratio-Scale tuyệt đối; tính toán sai số chuẩn tiệm cận Asymptotic SE, kiểm định Wald $z$-test và khoảng tin cậy 95% CI; phân tích đếm tần suất cơ sở $(B - W)/A$; thiết lập Lưới Phân Bổ Đánh Đổi Best vs Worst Trade-Off Scatter Grid 4 góc phần tư: Ưu tiên Tuyệt đối Universally Desired, Bị Từ chối Consensus Rejection, Phân cực Tranh cãi Polarizing, và Trung lập Indifferent; Dual-panel SVG: Panel A Biểu đồ thanh ngang Rescaled Preference Share $P\%$ phân tầng chiến lược Emerald/Cyan/Slate + Panel B Lưới phân bổ đánh đổi Best vs Worst Scatter Grid với đường phân vị thập tự và các điểm dữ liệu tròn phát sáng có nhãn tên thuộc tính; APA 7th narrative).
- Viết unit tests `backend/tests/test_maxdiff_engine.py` (3 passed) và route tests `backend/tests/test_maxdiff_routes.py` (1 passed).
- Thêm schemas `MaxDiffRequest`, `MaxDiffOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/maxdiff`, audit log `MAXDIFF_BEST_WORST_SCALING_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `MaxDiffCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 105 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,090 modules transformed, 0 errors in 945ms**.
- Backend tests mới: **4 passed, 0 failed in 1.20s**.


### Mốc 02:46:00 — Hoàn thành Iteration 125: Gaussian Bayesian Network DAG Structure Learning & Markov Blanket Independence Engine (Heckerman 1995; Scutari 2010; Pearl 1988)
- Xây dựng `backend/app/engine/bayesian_network_engine.py` (Phương pháp luận David Heckerman 1995; Marco Scutari 2010; Judea Pearl 1988; Peter Spirtes et al. 2000; khám phá cấu trúc phụ thuộc có hướng không chu trình Directed Acyclic Graph - DAG giữa các biến số khảo sát liên tục thông qua Mạng Bayes Gaussian; thuật toán tìm kiếm leo đồi tối ưu hóa hàm điểm Score-Based Hill-Climbing BIC Optimization duyệt qua không gian biến đổi đồ thị thêm/đảo/xóa cạnh; tích hợp thuật toán sắp xếp tô-pô Kahn 1962 kiểm tra tính phi chu trình Cycle Prevention trong thời gian $O(V+E)$; ước lượng hệ số tác động chuẩn hóa Standardized Path Coefficients $\beta_{jk}^*$ kiểm soát toàn bộ các nút cha đồng thời; phân loại vai trò tô-pô đồ thị Topological Node Roles: Nguyên nhân Gốc Root Cause In=0 Out>0, Biến Trung gian / Điều phối Mediator In>0 Out>0, Biến Đích / Hấp thụ Target Sink In>0 Out=0, và Biến Độc lập Isolated In=0 Out=0; trích xuất không gian Markov Blanket $\text{MB}(X) = \text{Pa}(X) \cup \text{Ch}(X) \cup \text{Sp}(X)$ xác định chính xác tập hợp biến số can thiệp tối thiểu Minimal Sufficient Conditioning Set theo Tiên đề Độc lập Có điều kiện của Pearl; Dual-panel SVG: Panel A Đồ thị mạng có hướng Directed DAG Network Layout với các nút phát sáng theo vai trò tô-pô Emerald Root / Blue Mediator / Amber Sink kèm mũi tên chỉ hướng và trọng số $\beta$ + Panel B Bảng ma trận không gian Markov Blanket Matrix Table trực quan hóa tập can thiệp độc lập; APA 7th narrative).
- Viết unit tests `backend/tests/test_bayesian_network_engine.py` (3 passed) và route tests `backend/tests/test_bayesian_network_routes.py` (1 passed).
- Thêm schemas `BayesianNetworkRequest`, `BayesianNetworkOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/bayesian-network`, audit log `BAYESIAN_NETWORK_DAG_ESTIMATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `BayesianNetworkCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 106 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,091 modules transformed, 0 errors in 1.09s**.
- Backend tests mới: **4 passed, 0 failed in 1.11s**.


### Mốc 03:07:00 — Hoàn thành Iteration 126: Stochastic Dominance & Distributional Inequality Engine (Hadar & Russell 1969; Davidson & Duclos 2000; Barrett & Donald 2003) [Heartbeat 9 Fired at 03:00:00]
- Xây dựng `backend/app/engine/stochastic_dominance_engine.py` (Phương pháp luận Josef Hadar & William R. Russell 1969; James P. Quirk & Rubin Saposnik 1962; Michael Rothschild & Joseph E. Stiglitz 1970; Russell Davidson & Jean-Yves Duclos 2000; Garry F. Barrett & Stephen G. Donald 2003; Anthony F. Shorrocks 1983; giải quyết triệt để hạn chế nghiêm trọng của phép so sánh trung bình t-test/ANOVA khi phân phối khảo sát có tính bất đối xứng, đuôi nặng hoặc giao cắt phức tạp; thiết lập kiểm định Vượt trội Ngẫu nhiên Bậc 1 First-Order Stochastic Dominance FSD $F_A(y) \le F_B(y) \quad \forall y$ đại diện cho sở thích của mọi cá nhân có hàm độ hữu dụng đơn điệu tăng $u' \ge 0$; thiết lập kiểm định Vượt trội Ngẫu nhiên Bậc 2 Second-Order Stochastic Dominance SSD $D_A^{(2)}(y) \le D_B^{(2)}(y) \quad \forall y$ đại diện cho tiêu chuẩn né tránh rủi ro Risk Aversion $u' \ge 0, u'' \le 0$ thông qua tích phân diện tích thiếu hụt; kiểm định Vượt trội Bậc 3 TSD $u''' \ge 0$ Prudence; tính toán hệ số bất bình đẳng Gini chính xác cho từng phân nhóm; thống kê khoảng cách cực đại hai phía supremum Kolmogorov-Smirnov $D$ và $p$-value; Dual-panel SVG: Panel A Hai đường cong hàm phân phối tích lũy CDF $F_A(y)$ Emerald phát sáng vs $F_B(y)$ Indigo với đường nét đứt vàng cam đánh dấu khoảng cách vượt trội cực đại Max Dominance Gap + Panel B Đường cong chênh lệch tích phân bậc 2 $\Delta D^{(2)}(y) = D_B^{(2)}(y) - D_A^{(2)}(y)$ với vùng bóng tô chuyển sắc màu xanh lục biểu thị miền thống trị né tránh rủi ro; APA 7th narrative).
- Viết unit tests `backend/tests/test_stochastic_dominance_engine.py` (4 passed) và route tests `backend/tests/test_stochastic_dominance_routes.py` (1 passed).
- Thêm schemas `StochasticDominanceRequest`, `StochasticDominanceOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/stochastic-dominance`, audit log `STOCHASTIC_DOMINANCE_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `StochasticDominanceCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 107 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,092 modules transformed, 0 errors in 1.10s**.
- Backend tests mới: **5 passed, 0 failed in 1.25s**.


### Mốc 03:17:00 — Hoàn thành Iteration 127: Manski Non-Parametric Partial Identification & Worst-Case Bounds Engine (Manski 1990, 1995, 2003; Manski & Pepper 2000; Imbens & Manski 2004)
- Xây dựng `backend/app/engine/manski_bounds_engine.py` (Phương pháp luận Charles F. Manski 1990, 1995, 2003; Charles F. Manski & John V. Pepper 2000; Joel L. Horowitz & Charles F. Manski 2000; Guido W. Imbens & Charles F. Manski 2004; giải quyết triệt để vấn đề thiên lệch nghiêm trọng trong khảo sát xã hội học và kinh tế lượng khi dữ liệu bị mất mẫu hoặc bỏ qua câu hỏi theo cơ chế Khuyết Không Ngẫu Nhiên Not Missing At Random NMAR mà không cần áp đặt các giả định MAR bất khả kiểm chứng; xây dựng hệ thống phân cấp nhận dạng 4 bậc toàn diện:
  1. Cận Tồi Tệ Nhất Không Giả Định Worst-Case Bounds $[LB_{\text{worst}}, UB_{\text{worst}}]$ dựa trên chặn miền giá trị hữu hạn $Y \in [y_{\min}, y_{\max}]$;
  2. Cận Tiên Đề Lựa Chọn Điều Trị Đơn Điệu Monotone Treatment Selection MTS $[LB_{\text{worst}}, \text{Naive } ATE]$ với tiên đề $E[Y(d)|D=1] \ge E[Y(d)|D=0]$;
  3. Cận Tiên Đề Đáp Ứng Đơn Điệu Monotone Treatment Response MTR $[0, UB_{\text{worst}}]$ với tiên đề $Y_i(1) \ge Y_i(0)$;
  4. Cận Hợp Nhất MTS+MTR $[0, \min(UB_{\text{worst}}, \text{Naive } ATE)]$ thu hẹp tối đa biên độ bất định;
  - Tích hợp thuật toán chia đôi Bisection Search tính giá trị tới hạn Imbens-Manski $c_\alpha$ giải phương trình tích phân chuẩn hóa cho khoảng tin cậy đồng nhất 95% Uniform Confidence Intervals;
  - Phân tích độ nhạy trên lưới 15 điểm tỷ lệ mất mẫu $p \in [0, 0.50]$ và tự động định vị Điểm Gãy Dấu Sign Breakdown Point $p^*$ nơi biên dưới chuyển từ dương sang âm;
  - Dual-panel SVG: Panel A Biểu đồ thanh ngang phân cấp biên Manski Worst-Case / MTS / MTR / Joint MTS+MTR với vạch đỏ chỉ Naive ATE + Panel B Đồ thị vùng phong bì nhạy cảm mất mẫu Envelope $[LB(p), UB(p)]$ với điểm gãy dấu nổi bật;
  - APA 7th narrative).
- Viết unit tests `backend/tests/test_manski_bounds_engine.py` (3 passed) và route tests `backend/tests/test_manski_bounds_routes.py` (1 passed).
- Thêm schemas `ManskiBoundsRequest`, `ManskiBoundsOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/manski-bounds`, audit log `MANSKI_BOUNDS_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `ManskiBoundsCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 108 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,093 modules transformed, 0 errors in 1.08s**.
- Backend tests mới: **4 passed, 0 failed in 1.23s**.
- Git commit: `be30146`.


### Mốc 03:23:00 — Hoàn thành Iteration 128: Dynamic Treatment Regimes (DTR) & Sequential Q-Learning Decision Engine (Murphy 2003; Robins 2004; Schulte et al. 2014)
- Xây dựng `backend/app/engine/dynamic_treatment_regimes_engine.py` (Phương pháp luận Susan A. Murphy 2003; James M. Robins 2004; Phillip J. Schulte, Anastasios A. Tsiatis, Eric B. Laber & Marie Davidian 2014; Bibhas Chakraborty & Eric E. Moodie 2013; mô hình hóa chính sách can thiệp thích ứng cá nhân hóa hai giai đoạn cho các chiến dịch khảo sát kéo dài và chương trình can thiệp hành vi nhiều chu kỳ; tích hợp thuật toán Học Tăng cường Q-Learning Quy nạp Ngược Sequential Backward Induction:
  1. Hồi quy Hàm Q Giai đoạn 2 $Q_2(H_2, A_2) = \mathbb{E}[Y \mid H_2, A_2]$ xác định ngưỡng quyết định tối ưu thích ứng $X_2^* = -\beta_{21} / \theta_{21}$ và tính biến kết quả ảo phản thực $\tilde{Y}_1 = \max_{a_2} Q_2(H_2, a_2)$;
  2. Hồi quy Hàm Q Giai đoạn 1 $Q_1(H_1, A_1) = \mathbb{E}[\tilde{Y}_1 \mid H_1, A_1]$ xác định ngưỡng phân bổ ban đầu $X_1^* = -\beta_{11} / \theta_{11}$;
  - Đánh giá toàn diện Giá trị Kỳ vọng Chính sách Value of Policy $V(d^*)$ so sánh trực diện với chính sách Tĩnh Luôn can thiệp $V(1,1)$, Tĩnh Không can thiệp $V(0,0)$, và trung bình quan sát thực tế $V_{\text{obs}}$;
  - Tính toán mức thặng dư giá trị chính sách Policy Value Gain $\Delta V^*$ và phần trăm cải thiện thặng dư $\Delta V^*\%$;
  - Dual-panel SVG: Panel A Cây quyết định chính sách thích ứng DTR Decision Flowchart Tree từ nút gốc $X_1$ rẽ nhánh $A_1$, qua trạng thái giữa kỳ $X_2$, rẽ nhánh $A_2$, đến 4 điểm kết quả cuối cùng + Panel B Biểu đồ thanh ngang so sánh Giá trị Chính sách $V(d^*)$ xanh ngọc Emerald nổi bật vs các chiến lược tĩnh;
  - APA 7th narrative).
- Viết unit tests `backend/tests/test_dynamic_treatment_regimes_engine.py` (3 passed) và route tests `backend/tests/test_dynamic_treatment_regimes_routes.py` (1 passed).
- Thêm schemas `DynamicTreatmentRegimesRequest`, `DynamicTreatmentRegimesOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/dynamic-treatment-regimes`, audit log `DYNAMIC_TREATMENT_REGIMES_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `DynamicTreatmentRegimesCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 109 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,094 modules transformed, 0 errors in 1.16s**.
- Backend tests mới: **4 passed, 0 failed in 1.29s**.
- Git commit: `79875ed`.


### Mốc 03:29:00 — Hoàn thành Iteration 129: Finite Mixture Rasch Models (FMRM) & Latent Class IRT Engine (Rost 1990; von Davier & Rost 2007; Glas 2010)
- Xây dựng `backend/app/engine/finite_mixture_rasch_engine.py` (Phương pháp luận Jürgen Rost 1990; Matthias von Davier & Jürgen Rost 2007; Cees A. W. Glas 2010; David Preinerstorfer & Anton K. Formann 2012; kết hợp đột phá giữa Phân tích Lớp Tiềm ẩn Latent Class Analysis LCA và Lý thuyết Ứng đáp Câu hỏi Rasch IRT; giải quyết triệt để vấn đề thiên lệch chức năng câu hỏi DIF tiềm ẩn và phong cách trả lời không đồng nhất giữa các nhóm đối tượng khảo sát mà không cần biết trước biến nhân khẩu học bên ngoài; tích hợp thuật toán Kỳ vọng - Cực đại hóa Expectation-Maximization EM Algorithm:
  1. Bước E: Tính xác suất hậu nghiệm thuộc phân lớp tiềm ẩn $\tau_{vg} = P(g \mid \mathbf{x}_v)$ qua hàm hợp lý logistic kernel;
  2. Bước M: Cập nhật tỷ trọng phân lớp $\pi_g$ và giải hệ phương trình độ khó Rasch có trọng số $\beta_{ig}$ chuẩn hóa định tâm $\sum_i \beta_{ig} = 0$;
  - Đánh giá chất lượng mô hình toàn diện qua Log-Likelihood, AIC, BIC, aBIC, và Chỉ số Phân tách Entropy Chuẩn hóa $E \in [0, 1]$;
  - Tự động nhận diện câu hỏi có độ phân hóa mạnh nhất Top Shifted Item và biên độ dịch chuyển cực đại $\Delta \beta_{\max}$;
  - Dual-panel SVG: Panel A Quỹ đạo Độ khó Câu hỏi qua các Phân lớp Tiềm ẩn $\beta_{ig}$ Profile Line Chart với các đường phát sáng đa màu sắc + Panel B Biểu đồ thanh tỷ trọng phân lớp và hộp đo chỉ số Entropy;
  - APA 7th narrative).
- Viết unit tests `backend/tests/test_finite_mixture_rasch_engine.py` (4 passed) và route tests `backend/tests/test_finite_mixture_rasch_routes.py` (1 passed).
- Thêm schemas `FiniteMixtureRaschRequest`, `FiniteMixtureRaschOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/finite-mixture-rasch`, audit log `FINITE_MIXTURE_RASCH_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `FiniteMixtureRaschCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 110 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,095 modules transformed, 0 errors in 1.02s**.
- Backend tests mới: **5 passed, 0 failed in 1.34s**.
- Git commit: `cc27439`.


### Mốc 03:30:00 — Heartbeat 10 Fired [task-14026]
- Thời gian thực tế: `2026-10-25T03:30:00+07:00` (Elapsed: 4h 53m 24s / Cần &ge; 6h 00m 00s).
- Trạng thái hệ thống:
  - Frontend: 2,095 modules transformed, 0 errors in 1.02s (`dist/index.html`, `dist/assets/index-*.js`).
  - Backend: 100% test pass rate qua toàn bộ các module phân tích kinh tế lượng & tâm lý học đo lường.
  - Đã hoàn thành trong ca này:
    - Iteration 125: Gaussian Bayesian Network DAG Structure Learning Engine (Section 106).
    - Iteration 126: Stochastic Dominance & Distributional Inequality Engine (Section 107).
    - Iteration 127: Manski Non-Parametric Partial Identification & Worst-Case Bounds Engine (Section 108).
    - Iteration 128: Dynamic Treatment Regimes (DTR) & Sequential Q-Learning Decision Engine (Section 109).
    - Iteration 129: Finite Mixture Rasch Models (FMRM) & Latent Class IRT Engine (Section 110).
  - Tiếp tục thực thi liên tục không dừng theo đúng chỉ thị tự chủ.


### Mốc 03:36:00 — Hoàn thành Iteration 130: Double / Debiased Machine Learning (DML) for Causal Inference Engine (Chernozhukov et al. 2018; Robinson 1988)
- Xây dựng `backend/app/engine/double_machine_learning_engine.py` (Phương pháp luận Victor Chernozhukov, Denis Chetverikov, Mert Demirer, Esther Duflo, Christian Hansen, Whitney Newey & James Robins 2018 Econometrica; Peter M. Robinson 1988 Econometrica; Victor Chernozhukov, Christian Hansen & Martin Spindler 2015; giải quyết triệt để vấn đề thiên lệch chính quy hóa Regularization Bias khi áp dụng học máy trong suy diễn nhân quả; thiết lập mô hình bán tham số tuyến tính từng phần Partially Linear Regression PLR với hai trụ cột toán học vững chắc:
  1. Hàm điểm trực giao Neyman Neyman-Orthogonal Score của Robinson (1988) thỏa mãn triệt tiêu đạo hàm Gateaux theo các hàm phụ trợ $\partial_\eta \mathbb{E}[\psi] = 0$, cách ly hoàn toàn ước lượng $\hat{\theta}_{\text{DML}}$ khỏi sai số làm mịn của các hàm học máy phi tham số;
  2. K-Fold Cross-Fitting phân chia ngẫu nhiên dữ liệu huấn luyện ngoài mẫu triệt tiêu overfitting và bảo đảm phân phối chuẩn tiệm cận $\sqrt{N}$-consistent;
  - Đo lường và làm sạch lượng thiên lệch gây nhiễu Confounding Bias $\Delta = \hat{\theta}_{\text{naive}} - \hat{\theta}_{\text{DML}}$ so với OLS ngây thơ;
  - Tính toán sai số chuẩn dạng sandwich tiệm cận, khoảng tin cậy 95% CI, thống kê kiểm định $z$-statistic, và xếp hạng các biến kiểm soát gây nhiễu mạnh nhất;
  - Dual-panel SVG: Panel A Đám mây thặng dư trực giao Robinson $(Y - \hat{g}(X))$ vs $(D - \hat{m}(X))$ với đường dốc hồi quy DML $\hat{\theta}_{\text{DML}}$ màu xanh ngọc Emerald phát sáng + Panel B Biểu đồ Forest Plot so sánh khoảng tin cậy 95% của $\hat{\theta}_{\text{DML}}$ vs $\hat{\theta}_{\text{naive}}$ kèm hộp làm nổi bật độ chệch được loại bỏ;
  - APA 7th narrative).
- Viết unit tests `backend/tests/test_double_machine_learning_engine.py` (3 passed) và route tests `backend/tests/test_double_machine_learning_routes.py` (1 passed).
- Thêm schemas `DoubleMachineLearningRequest`, `DoubleMachineLearningOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/double-machine-learning`, audit log `DOUBLE_MACHINE_LEARNING_EVALUATED`.
- Thêm types trong `survey.ts`, API client trong `client.ts`, component `DoubleMachineLearningCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 111 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,096 modules transformed, 0 errors in 1.01s**.
- Backend tests mới: **4 passed, 0 failed in 1.26s**.
- Git commit: `251c9ff`.


### Mốc 03:51:00 — Hoàn thành Iteration 131: Regression Kink Design (RKD) Engine (Card, Lee, Pei, & Weber 2015; Dong 2018)
- Xây dựng `backend/app/engine/regression_kink_engine.py` (Phương pháp luận David Card, David S. Lee, Zhuan Pei & Andrea Weber 2015 Econometrica; Yingying Dong 2018 Econometric Theory; Andrew Gelman & Guido Imbens 2019 JBES; Justin McCrary 2008 J. Econometrics; giải quyết bài toán nhận diện nhân quả bán thực nghiệm khi chính sách thay đổi độ dốc can thiệp mà không tạo bước nhảy gián đoạn cấp độ $\Delta D(c) = 0$, khiến RDD truyền thống gặp mẫu số $0/0$ và thất bại:
  1. Nhận diện đạo hàm hiệu ứng chính sách biên (Marginal Treatment Effect Derivative) $\tau_{\text{RKD}} = \Delta \beta_Y / \Delta \beta_D$ cho cả Sharp RKD (với độ dốc chính sách đã biết $k$) và Fuzzy RKD (ước lượng đồng thời $\Delta \beta_D$ qua IV bán thực nghiệm);
  2. Local Polynomial Spline Regression với hàm trọng số nhân tam giác (triangular kernel) và lựa chọn bậc 1 (Local Linear Spline) hoặc bậc 2 (Local Quadratic Spline);
  3. Lựa chọn băng thông giải tích thích ứng riêng cho ước lượng đạo hàm bậc 1 (Silverman Rule of Thumb Bandwidth for Derivatives $h = C \cdot \sigma_X \cdot N^{-1/(2p+3)}$);
  4. Kiểm định mật độ trơn McCrary (2008) chia bin đối xứng hai bên ngưỡng để bác bỏ giả thuyết người tham gia khảo sát tự thao túng vị trí quanh ngưỡng gãy;
  5. Dual-panel SVG: Panel A Đồ thị spline gãy cục bộ với dải tin cậy 95%, đường xu hướng đổi màu tại ngưỡng và điểm gom binned scatter + Panel B Biểu đồ kiểm định mật độ trơn McCrary trực quan hóa tính liên tục của hàm mật độ xác suất;
  6. APA 7th narrative).
- Viết unit tests `backend/tests/test_regression_kink_engine.py` (3 passed) và route tests `backend/tests/test_regression_kink_routes.py` (3 passed).
- Thêm schemas `RegressionKinkRequest`, `RegressionKinkOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/regression-kink`, audit log `REGRESSION_KINK_EVALUATED`.
- Thêm types trong `survey.ts`, API client method `runRegressionKink` trong `client.ts`, component `RegressionKinkCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 112 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,097 modules transformed, 0 errors in 999ms**.
- Backend tests mới: **6 passed, 0 failed in 3.18s**.
- Git commit cho Iteration 131.


### Mốc 03:56:00 — Hoàn thành Iteration 132: Staggered Difference-in-Differences & Group-Time Average Treatment Effects Engine (Callaway & Sant'Anna 2021; Goodman-Bacon 2021; Sun & Abraham 2021)
- Xây dựng `backend/app/engine/staggered_did_engine.py` (Phương pháp luận Brantly Callaway & Pedro H. C. Sant'Anna 2021 Journal of Econometrics; Andrew Goodman-Bacon 2021 Journal of Econometrics; Liyang Sun & Sarah Abraham 2021 Journal of Econometrics; giải quyết triệt để vấn đề thiên lệch nghiêm trọng của mô hình Two-Way Fixed Effects TWFE khi can thiệp phân tầng theo thời gian có hiệu ứng động:
  1. Loại bỏ các phép so sánh ô nhiễm nơi các đơn vị can thiệp sớm bị dùng làm đối chứng cho đơn vị can thiệp muộn gây ra trọng số âm (negative weights);
  2. Ước lượng phi tham số các tác động nhóm - thời gian $ATT(g, t) = \mathbb{E}[Y_t(g) - Y_t(0) \mid G_g = 1]$ sử dụng nhóm thuần chưa từng can thiệp (never-treated) hoặc nhóm chưa can thiệp tại thời điểm $t$ (not-yet-treated);
  3. Nghiên cứu biến cố động Dynamic Event Study Aggregation $ATT(e)$ với $e = t - g$ và kiểm định giả định xu hướng song song tiền can thiệp (Pre-Trends Parallel Assumption Wald $\chi^2$);
  4. Phân rã tuyến tính Goodman-Bacon (2021) bóc tách toàn bộ các phép so sánh $2 \times 2$, tính toán tỷ lệ trọng số âm tiềm ẩn và xác định khoảng chệch Bias Gap $\Delta = \hat{\tau}_{\text{CS}} - \beta^{\text{TWFE}}$ so với OLS ngây thơ;
  5. Dual-panel SVG: Panel A Quỹ đạo biến cố động $ATT(e)$ với dải tin cậy 95% phân chia rõ giai đoạn tiền can thiệp (kiểm định giả định) và hậu can thiệp (hiệu ứng tích lũy) + Panel B Đồ thị phân tán phân rã Goodman-Bacon so sánh các ước lượng $2 \times 2$ với tỷ trọng phân rã và đối chiếu trực diện đường chuẩn Callaway-Sant'Anna vs TWFE;
  6. APA 7th narrative).
- Viết unit tests `backend/tests/test_staggered_did_engine.py` (4 passed) và route tests `backend/tests/test_staggered_did_routes.py` (2 passed).
- Thêm schemas `StaggeredDIDRequest`, `StaggeredDIDOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/staggered-did`, audit log `STAGGERED_DID_EVALUATED`.
- Thêm types trong `survey.ts`, API client method `runStaggeredDID` trong `client.ts`, component `StaggeredDIDCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 113 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,098 modules transformed, 0 errors in 1.24s**.
- Backend tests mới: **6 passed, 0 failed in 1.36s**.
- Git commit cho Iteration 132.


### Mốc 04:00:00 — Heartbeat 11 Fired [task-14026]
- Thời gian thực tế: `2026-10-25T04:00:00+07:00` (Elapsed: 5h 23m 24s / Cần &ge; 6h 00m 00s).
- Trạng thái hệ thống:
  - Frontend: 2,098 modules transformed, 0 errors in 1.24s.
  - Backend: 100% test pass rate qua toàn bộ các module kinh tế lượng và suy diễn nhân quả.
  - Các mốc hoàn thành:
    - Iteration 130: Double / Debiased Machine Learning (DML) Engine (Section 111).
    - Iteration 131: Regression Kink Design (RKD) Engine (Section 112).
    - Iteration 132: Staggered Difference-in-Differences Engine (Section 113).
  - Tiếp tục thực thi liên tục không dừng theo đúng chỉ thị tự chủ.


### Mốc 04:04:00 — Hoàn thành Iteration 133: Matrix Completion for Causal Panel Data with Nuclear Norm Regularization (Athey, Bayati, Doudchenko, Imbens, & Khosravi 2021)
- Xây dựng `backend/app/engine/matrix_completion_causal_engine.py` (Phương pháp luận Susan Athey, Mohsen Bayati, Nikolay Doudchenko, Guido Imbens & Khashayar Khosravi 2021 JASA; Rahul Mazumder, Trevor Hastie & Robert Tibshirani 2010 JMLR; Emmanuel Candès & Benjamin Recht 2009; định hình suy diễn nhân quả dữ liệu bảng dọc như một bài toán khuyết dữ liệu đối chứng phản sự kiện $Y(0)$:
  1. Phục dựng ma trận đối chứng phản sự kiện hạng thấp $L = Y(0)$ thông qua chương trình tối ưu hóa lồi với chuẩn hạt nhân Nuclear Norm Regularization $\min_L \sum_{(i,t) \in \mathcal{O}} (Y_{it} - L_{it})^2 + \lambda \|L\|_*$;
  2. Thuật toán Soft-Impute SVT giải tích lặp với phép chiếu phân rã giá trị kỳ dị và toán tử thu nhỏ mềm $\mathcal{S}_\lambda(\sigma) = \max(0, \sigma - \lambda)$;
  3. Tính toán tác động can thiệp tại từng ô bảng $\hat{\tau}_{it} = Y_{it} - \hat{L}_{it}$ và hiệu ứng gộp trung bình trên nhóm can thiệp (Overall ATT);
  4. Đánh giá hạng ma trận hiệu dụng (effective rank), sai số khớp đối chứng RMSE và tỷ trọng phương sai của các nhân tố tiềm ẩn;
  5. Dual-panel SVG: Panel A Bản đồ nhiệt ma trận $N \times T$ phân biệt trực quan các ô đối chứng đã quan sát và các ô can thiệp được phục dựng + Panel B Biểu đồ Scree Plot phân rã phổ giá trị kỳ dị và đường ngưỡng thu nhỏ $\lambda$;
  6. APA 7th narrative).
- Viết unit tests `backend/tests/test_matrix_completion_causal_engine.py` (3 passed) và route tests `backend/tests/test_matrix_completion_causal_routes.py` (2 passed).
- Thêm schemas `MatrixCompletionCausalRequest`, `MatrixCompletionCausalOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/matrix-completion-causal`, audit log `MATRIX_COMPLETION_CAUSAL_EVALUATED`.
- Thêm types trong `survey.ts`, API client method `runMatrixCompletionCausal` trong `client.ts`, component `MatrixCompletionCausalCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 114 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,099 modules transformed, 0 errors in 1.50s**.
- Backend tests mới: **5 passed, 0 failed in 1.32s**.
- Git commit cho Iteration 133.


### Mốc 04:11:00 — Hoàn thành Iteration 134: Synthetic Difference-in-Differences (SDID) Advanced Engine (Arkhangelsky, Athey, Hirshberg, Imbens, & Wager 2021; Doudchenko & Imbens 2016)
- Xây dựng `backend/app/engine/sdid_advanced_engine.py` (Phương pháp luận Dmitry Arkhangelsky, Susan Athey, David A. Hirshberg, Guido W. Imbens & Stefan Wager 2021 American Economic Review; Nikolay Doudchenko & Guido Imbens 2016; kết hợp tối ưu giữa Difference-in-Differences và Synthetic Control tạo thành bộ ước lượng kép vững Double-Robust SDID):
  1. Tối ưu hóa trọng số đơn vị đối chứng $\hat{\omega}$ có điều hòa phạt phân tán L2 $\zeta^2 T_{\text{pre}} \|\omega\|_2^2$ bằng thuật toán quy hoạch toàn phương có ràng buộc SLSQP, cho phép dịch chuyển mức nền intercept $\omega_0$;
  2. Tối ưu hóa trọng số thời gian tiền kỳ $\hat{\lambda}$ nhằm căn chỉnh chính xác quỹ đạo xu hướng thời gian trước can thiệp với giai đoạn hậu can thiệp của nhóm đối chứng;
  3. Ước lượng tác động can thiệp trung bình kép vững $\hat{\tau}_{\text{SDID}}$ và kiểm định giả thuyết thống kê với sai số chuẩn vững Jackknife/placebo;
  4. So sánh trực diện với DiD truyền thống và Synthetic Control cổ điển, định lượng chính xác độ lệch thiên lệch DiD Bias Gap ($\Delta = \hat{\tau}_{\text{SDID}} - \hat{\tau}_{\text{DiD}}$);
  5. Dual-panel SVG: Panel A Quỹ đạo thời gian thực tế $Y(1)$, đối chứng phản sự kiện SDID $\hat{Y}(0)$, synthetic control chuẩn và đối chứng thô + Panel B Phân bổ trọng số đơn vị đối chứng donor pool $\hat{\omega}_i$;
  6. APA 7th narrative khoa học giải thích chi tiết tác động và độ lệch thiên lệch DiD.
- Viết unit tests `backend/tests/test_sdid_advanced_engine.py` (3 passed) và route tests `backend/tests/test_sdid_advanced_routes.py` (2 passed).
- Thêm schemas `SDIDAdvancedRequest`, `SDIDAdvancedOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/sdid-advanced`, audit log `SDID_ADVANCED_EVALUATED`.
- Thêm types trong `survey.ts`, API client method `runSDIDAdvanced` trong `client.ts`, component `SDIDAdvancedCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 115 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,100 modules transformed, 0 errors in 1.16s**.
- Backend tests mới: **5 passed, 0 failed in 1.39s**.
- Git commit cho Iteration 134.


### Mốc 04:18:00 — Hoàn thành Iteration 135: Causal Panel Factor Models with Interactive Fixed Effects & Cross-Sectional Dependence (Bai 2009; Gobillon & Magnac 2016)
- Xây dựng `backend/app/engine/interactive_fixed_effects_engine.py` (Phương pháp luận Jushan Bai 2009 Econometrica; Laurent Gobillon & Thierry Magnac 2016 Journal of Applied Econometrics; Jushan Bai & Serena Ng 2002 Econometrica; M. Hashem Pesaran 2004, 2021 Econometrics Journal; ước lượng tác động can thiệp nhân quả trên dữ liệu bảng dọc dưới sự tồn tại của các nhân tố tiềm ẩn đa chiều và phụ thuộc chéo giữa các đơn vị):
  1. Mô hình hóa dạng $Y_{it} = \tau D_{it} + \alpha_i + \lambda_t + \boldsymbol{\gamma}_i^\top \mathbf{f}_t + \varepsilon_{it}$, khắc phục triệt để khiếm khuyết của OLS Two-Way Fixed Effects TWFE khi có cú sốc vĩ mô tác động không đồng nhất lên đối tượng;
  2. Thuật toán Bình phương Tối thiểu Luân phiên (Alternating Least Squares - ALS) hội tụ lặp SVD trên phần dư, phân rã đồng thời chuỗi nhân tố vĩ mô $\mathbf{f}_t$ và hệ số tải $\boldsymbol{\gamma}_i$;
  3. Tiêu chuẩn thông tin Bai & Ng (2002) $\text{IC}_{p1}$ tự động xác định số lượng nhân tố tiềm ẩn tối ưu $r^*$;
  4. Phục dựng giá trị đối chứng phản sự kiện $Y(0)_{it} = \hat{\alpha}_i + \hat{\lambda}_t - \bar{Y} + \hat{\boldsymbol{\gamma}}_i^\top \hat{\mathbf{f}}_t$ và ước lượng tác động trung bình $\hat{\tau}_{\text{IFE}}$;
  5. Ước lượng sai số chuẩn Jackknife vững qua các đơn vị và kiểm định phụ thuộc chéo Pesaran (2004) CD test trên phần dư $\hat{\varepsilon}_{it}$;
  6. Dual-panel SVG: Panel A Biểu đồ Scree Plot phân rã phổ giá trị riêng và đường ngưỡng $r^*$ theo Bai-Ng IC + Panel B Quỹ đạo chuỗi thời gian các nhân tố tiềm ẩn chung $\mathbf{f}_t$;
  7. APA 7th narrative khoa học phân tích tác động và khoảng chệch nhân tố Factor Bias Gap $\Delta = \hat{\tau}_{\text{IFE}} - \tau_{\text{TWFE}}$.
- Viết unit tests `backend/tests/test_interactive_fixed_effects_engine.py` (3 passed) và route tests `backend/tests/test_interactive_fixed_effects_routes.py` (2 passed).
- Thêm schemas `InteractiveFixedEffectsRequest`, `InteractiveFixedEffectsOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/interactive-fixed-effects`, audit log `INTERACTIVE_FIXED_EFFECTS_EVALUATED`.
- Thêm types trong `survey.ts`, API client method `runInteractiveFixedEffects` trong `client.ts`, component `InteractiveFixedEffectsCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 116 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,101 modules transformed, 0 errors in 1.31s**.
- Backend tests mới: **5 passed, 0 failed in 1.17s**.
- Git commit cho Iteration 135.


### Mốc 04:23:00 — Hoàn thành Iteration 136: Multiple Sequential Mediators & Path-Specific Causal Mediation Engine (VanderWeele 2014; Steen et al. 2012; Imai & Yamamoto 2013)
- Xây dựng `backend/app/engine/multiple_mediators_engine.py` (Phương pháp luận Tyler J. VanderWeele 2014 American Journal of Epidemiology; Steen, Loeys, Moerkerke & Vansteelandt 2012 Psychological Methods; Kosuke Imai & Teppei Yamamoto 2013 JASA; bóc tách đa biến trung gian tuần tự trong chuỗi tác động nhân quả $X \to M_1 \to M_2 \to Y$):
  1. Phân rã tổng tác động (Total Effect TE) thành Tác động trực tiếp thuần (Pure Direct Effect PDE) và các tác động gián tiếp đặc thù từng kênh: $X \to M_1 \to Y$ ($\text{NIE}_{M_1}$), $X \to M_2 \to Y$ ($\text{NIE}_{M_2}$) và chuỗi tuần tự liên hoàn $X \to M_1 \to M_2 \to Y$ ($\text{NIE}_{\text{Seq}}$);
  2. Khắc phục triệt để hiện tượng nhiễu giữa các biến trung gian (Mediator-Mediator Confounding) thường gặp trong các mô hình SEM hoặc OLS đơn trung gian truyền thống;
  3. Ước lượng sai số chuẩn và khoảng tin cậy 95% Percentile Bootstrap (150-500 resamples);
  4. Tính toán tỷ lệ trung gian (Proportion Mediated %) cho từng kênh và tổng tác động gián tiếp;
  5. Dual-panel SVG: Panel A Sơ đồ DAG đường dẫn cấu trúc đa trung gian tuần tự với các hệ số $a_1, a_2, d_{21}, b_1, b_2, c'$ + Panel B Biểu đồ Forest Plot trực quan hóa các ước lượng điểm và khoảng tin cậy 95% CI của 6 loại tác động;
  6. APA 7th narrative khoa học giải thích chi tiết cơ chế trung gian toàn phần hay một phần.
- Viết unit tests `backend/tests/test_multiple_mediators_engine.py` (3 passed) và route tests `backend/tests/test_multiple_mediators_routes.py` (2 passed).
- Thêm schemas `MultipleMediatorsRequest`, `MultipleMediatorsOut` trong `backend/app/schemas.py`.
- Thêm router endpoint `POST /api/surveys/{survey_id}/analytics/multiple-mediators`, audit log `MULTIPLE_MEDIATORS_EVALUATED`.
- Thêm types trong `survey.ts`, API client method `runMultipleMediators` trong `client.ts`, component `MultipleMediatorsCard.tsx`, mount vào `SurveyAnalyticsPage.tsx`.
- Ghi nhận Section 117 trong `docs/API_CONTRACT.md`.
- Frontend build: **2,102 modules transformed, 0 errors in 1.03s**.
- Backend tests mới: **5 passed, 0 failed in 1.61s**.
- Git commit cho Iteration 136.



