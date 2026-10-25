/**
 * DataTrust — Academic Research Chart Vector & High-DPI Graphics Generator
 * Generates publication-ready SVG vector charts and 300-DPI PNGs for research papers,
 * theses, conference slides, and scientific posters (IEEE/ACM/ISEF/KHKT standard).
 */

export interface ChartExportOptions {
  theme?: 'modern' | 'monochrome';
  includeMetadata?: boolean;
  surveyTitle?: string;
  sourceNote?: string;
  width?: number;
  height?: number;
}

const DEFAULT_SOURCE_NOTE = 'Nguồn: DataTrust Verification Engine • Tiêu chuẩn Khảo sát Thực địa Don Dillman & AAPOR';

function escapeXml(unsafe: string): string {
  return (unsafe || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

/**
 * 1. Biểu đồ Phân Bố Mức Độ Rủi Ro Dữ Liệu (Donut / Bar Chart)
 */
export function generateRiskDistributionSvg(
  riskDist: { low?: number; medium?: number; high?: number },
  totalResponses: number,
  options: ChartExportOptions = {}
): string {
  const width = options.width || 800;
  const height = options.height || 480;
  const isMono = options.theme === 'monochrome';
  const title = options.surveyTitle || 'Phân Bố Mức Độ Rủi Ro & Độ Tin Cậy Dữ Liệu';

  const low = riskDist.low || 0;
  const med = riskDist.medium || 0;
  const high = riskDist.high || 0;
  const total = totalResponses || (low + med + high) || 1;

  const lowPct = Math.round((low / total) * 100);
  const medPct = Math.round((med / total) * 100);
  const highPct = Math.round((high / total) * 100);

  // Bảng màu
  const colors = isMono
    ? {
        low: '#525252',
        med: '#737373',
        high: '#171717',
        bg: '#ffffff',
        text: '#171717',
        subtext: '#525252',
        border: '#d4d4d4',
        cardBg: '#fafafa'
      }
    : {
        low: '#059669', // Emerald
        med: '#d97706', // Amber
        high: '#e11d48', // Rose
        bg: '#ffffff',
        text: '#0f172a',
        subtext: '#64748b',
        border: '#e2e8f0',
        cardBg: '#f8fafc'
      };

  const trustIndex = Math.round(((low + med * 0.5) / total) * 100);

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
  <defs>
    <style>
      .title { font-size: 20px; font-weight: 800; fill: ${colors.text}; }
      .subtitle { font-size: 13px; font-weight: 500; fill: ${colors.subtext}; }
      .label { font-size: 13px; font-weight: 600; fill: ${colors.text}; }
      .val-bold { font-size: 16px; font-weight: 800; }
      .footnote { font-size: 11px; fill: ${colors.subtext}; font-style: italic; }
      .metric-title { font-size: 11px; font-weight: 600; text-transform: uppercase; fill: ${colors.subtext}; letter-spacing: 0.5px; }
      .metric-num { font-size: 28px; font-weight: 800; fill: ${colors.text}; }
    </style>
  </defs>

  <!-- Background -->
  <rect width="${width}" height="${height}" fill="${colors.bg}" />
  <rect x="12" y="12" width="${width - 24}" height="${height - 24}" rx="12" fill="none" stroke="${colors.border}" stroke-width="1" />

  <!-- Header -->
  <text x="36" y="48" class="title">${escapeXml(title)}</text>
  <text x="36" y="70" class="subtitle">Tổng mẫu khảo sát N = ${total} • Kiểm định tự động 7 tầng (DataTrust 7-Layer Quality Engine)</text>

  <!-- Summary Metric Cards -->
  <g transform="translate(36, 92)">
    <!-- Card 1: Tổng phản hồi -->
    <rect x="0" y="0" width="160" height="70" rx="8" fill="${colors.cardBg}" stroke="${colors.border}" stroke-width="1" />
    <text x="16" y="24" class="metric-title">Tổng mẫu (N)</text>
    <text x="16" y="54" class="metric-num">${total}</text>

    <!-- Card 2: Chỉ số Data Trust Index -->
    <rect x="175" y="0" width="180" height="70" rx="8" fill="${colors.cardBg}" stroke="${colors.border}" stroke-width="1" />
    <text x="191" y="24" class="metric-title">Data Trust Index</text>
    <text x="191" y="54" class="metric-num" fill="${colors.low}">${trustIndex}%</text>

    <!-- Card 3: Tỷ lệ sạch (Low Risk) -->
    <rect x="370" y="0" width="165" height="70" rx="8" fill="${colors.cardBg}" stroke="${colors.border}" stroke-width="1" />
    <text x="386" y="24" class="metric-title">Mẫu An Toàn</text>
    <text x="386" y="54" class="metric-num" fill="${colors.low}">${lowPct}%</text>

    <!-- Card 4: Rủi ro cao (Flagged) -->
    <rect x="550" y="0" width="175" height="70" rx="8" fill="${colors.cardBg}" stroke="${colors.border}" stroke-width="1" />
    <text x="566" y="24" class="metric-title">Rủi ro / Bất thường</text>
    <text x="566" y="54" class="metric-num" fill="${colors.high}">${highPct}%</text>
  </g>

  <!-- Horizontal Comparison Distribution Bar -->
  <g transform="translate(36, 195)">
    <text x="0" y="0" class="label">Biểu đồ cơ cấu phân vị rủi ro (%)</text>
    
    <!-- Multi-segment progress bar (Width = 728) -->
    <rect x="0" y="16" width="728" height="34" rx="8" fill="${colors.cardBg}" stroke="${colors.border}" stroke-width="1" />
    
    <!-- Segment: Low -->
    <rect x="2" y="18" width="${Math.max(4, (724 * lowPct) / 100)}" height="30" rx="6" fill="${colors.low}" />
    <!-- Segment: Medium -->
    <rect x="${2 + (724 * lowPct) / 100}" y="18" width="${Math.max(0, (724 * medPct) / 100)}" height="30" fill="${colors.med}" />
    <!-- Segment: High -->
    <rect x="${2 + (724 * (lowPct + medPct)) / 100}" y="18" width="${Math.max(0, (724 * highPct) / 100)}" height="30" rx="6" fill="${colors.high}" />

    <!-- Details below bar -->
    <!-- Low -->
    <g transform="translate(0, 75)">
      <circle cx="8" cy="8" r="8" fill="${colors.low}" />
      <text x="26" y="12" class="label">Rủi ro thấp (Low Risk - An toàn): <tspan class="val-bold" fill="${colors.low}">${low}</tspan> (${lowPct}%)</text>
      <text x="26" y="32" class="subtitle">Đạt tiêu chuẩn khoa học, thời gian làm bài hợp lý, không trùng lặp</text>
    </g>

    <!-- Medium -->
    <g transform="translate(0, 130)">
      <circle cx="8" cy="8" r="8" fill="${colors.med}" />
      <text x="26" y="12" class="label">Rủi ro trung bình (Medium Risk - Cần xem xét): <tspan class="val-bold" fill="${colors.med}">${med}</tspan> (${medPct}%)</text>
      <text x="26" y="32" class="subtitle">Có dấu hiệu lặp phương án nhẹ hoặc tốc độ hoàn thành nhanh</text>
    </g>

    <!-- High -->
    <g transform="translate(0, 185)">
      <circle cx="8" cy="8" r="8" fill="${colors.high}" />
      <text x="26" y="12" class="label">Rủi ro cao (High Risk - Gian lận / Bất thường): <tspan class="val-bold" fill="${colors.high}">${high}</tspan> (${highPct}%)</text>
      <text x="26" y="32" class="subtitle">Vi phạm quy tắc straightlining, thời gian làm bài siêu tốc hoặc trùng lặp 100%</text>
    </g>
  </g>

  <!-- Footnote -->
  <line x1="36" y1="${height - 40}" x2="${width - 36}" y2="${height - 40}" stroke="${colors.border}" stroke-width="1" />
  <text x="36" y="${height - 20}" class="footnote">${escapeXml(options.sourceNote || DEFAULT_SOURCE_NOTE)}</text>
  <text x="${width - 36}" y="${height - 20}" text-anchor="end" class="footnote">Xuất bởi DataTrust • ${new Date().toLocaleDateString('vi-VN')}</text>
</svg>`;
}

/**
 * 2. Biểu đồ Phễu Hoàn Thành & Tỷ Lệ Rơi Rụng (Don Dillman Drop-off Funnel)
 */
export function generateFunnelChartSvg(
  funnelSteps: Array<{
    step: number;
    question_title: string;
    total_answers: number;
    completion_rate_pct: number;
    drop_off_pct?: number;
  }>,
  overallCompletionRate: number = 100,
  options: ChartExportOptions = {}
): string {
  const steps = funnelSteps || [];
  const barHeight = 28;
  const gap = 20;
  const height = Math.max(480, 150 + steps.length * (barHeight + gap) + 60);
  const width = options.width || 840;
  const isMono = options.theme === 'monochrome';
  const title = options.surveyTitle || 'Phễu Hoàn Thành & Điểm Nghẽn Rơi Rụng (Drop-off Funnel)';

  const colors = isMono
    ? {
        bar: '#404040',
        barWarn: '#737373',
        bg: '#ffffff',
        text: '#171717',
        subtext: '#525252',
        border: '#d4d4d4',
        cardBg: '#fafafa'
      }
    : {
        bar: '#4f46e5', // Indigo
        barWarn: '#f59e0b', // Amber warning
        bg: '#ffffff',
        text: '#0f172a',
        subtext: '#64748b',
        border: '#e2e8f0',
        cardBg: '#f8fafc'
      };

  let barsSvg = '';
  const maxBarWidth = 460;

  steps.forEach((s, idx) => {
    const y = 140 + idx * (barHeight + gap);
    const w = Math.max(10, (maxBarWidth * (s.completion_rate_pct || 0)) / 100);
    const isWarning = (s.drop_off_pct || 0) >= 15;
    const barColor = isWarning ? colors.barWarn : colors.bar;

    barsSvg += `
    <g transform="translate(36, ${y})">
      <!-- Question Label -->
      <text x="0" y="16" font-size="12" font-weight="700" fill="${colors.text}">
        Câu #${s.step}:
      </text>
      <text x="56" y="16" font-size="12" font-weight="500" fill="${colors.subtext}">
        ${escapeXml(s.question_title.length > 30 ? s.question_title.substring(0, 30) + '...' : s.question_title)}
      </text>

      <!-- Bar Background Track -->
      <rect x="250" y="2" width="${maxBarWidth}" height="${barHeight}" rx="6" fill="${colors.cardBg}" stroke="${colors.border}" stroke-width="1" />
      <!-- Animated / Fill Bar -->
      <rect x="250" y="2" width="${w}" height="${barHeight}" rx="6" fill="${barColor}" />

      <!-- Completion % text -->
      <text x="${250 + w + 12}" y="20" font-size="12" font-weight="800" fill="${barColor}">
        ${s.completion_rate_pct}%
      </text>

      <!-- Drop-off Badge if significant -->
      ${
        isWarning
          ? `<rect x="735" y="4" width="70" height="22" rx="4" fill="${isMono ? '#e5e5e5' : '#fff1f2'}" stroke="${isMono ? '#737373' : '#fecdd3'}" />
             <text x="770" y="19" font-size="10" font-weight="700" fill="${isMono ? '#171717' : '#e11d48'}" text-anchor="middle">-${s.drop_off_pct}%</text>`
          : `<text x="770" y="19" font-size="11" font-weight="500" fill="${colors.subtext}" text-anchor="middle">${s.total_answers} trả lời</text>`
      }
    </g>`;
  });

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
  <!-- Background -->
  <rect width="${width}" height="${height}" fill="${colors.bg}" />
  <rect x="12" y="12" width="${width - 24}" height="${height - 24}" rx="12" fill="none" stroke="${colors.border}" stroke-width="1" />

  <!-- Header -->
  <text x="36" y="48" font-size="20" font-weight="800" fill="${colors.text}">${escapeXml(title)}</text>
  <text x="36" y="70" font-size="13" font-weight="500" fill="${colors.subtext}">
    Phương pháp luận Don Dillman: Phân tích độ mệt mỏi nhận thức và điểm rơi rụng qua từng bước khảo sát
  </text>

  <!-- Metric Pill -->
  <g transform="translate(${width - 240}, 34)">
    <rect x="0" y="0" width="204" height="40" rx="8" fill="${colors.cardBg}" stroke="${colors.border}" stroke-width="1" />
    <text x="14" y="25" font-size="11" font-weight="600" fill="${colors.subtext}">Hoàn thành toàn bài:</text>
    <text x="145" y="26" font-size="15" font-weight="800" fill="${colors.bar}">${overallCompletionRate}%</text>
  </g>

  <!-- Section Divider -->
  <line x1="36" y1="95" x2="${width - 36}" y2="95" stroke="${colors.border}" stroke-width="1" />

  <!-- Funnel Bars -->
  ${barsSvg}

  <!-- Footnote -->
  <line x1="36" y1="${height - 40}" x2="${width - 36}" y2="${height - 40}" stroke="${colors.border}" stroke-width="1" />
  <text x="36" y="${height - 20}" font-size="11" fill="${colors.subtext}" font-style="italic">${escapeXml(options.sourceNote || DEFAULT_SOURCE_NOTE)}</text>
  <text x="${width - 36}" y="${height - 20}" text-anchor="end" font-size="11" fill="${colors.subtext}">Xuất bởi DataTrust • ${new Date().toLocaleDateString('vi-VN')}</text>
</svg>`;
}

/**
 * 3. Biểu đồ Phân Bố Tần Số Cho Từng Câu Hỏi Khảo Sát
 */
export function generateQuestionDistributionSvg(
  questionTitle: string,
  questionType: string,
  optionDistribution: Record<string, number>,
  totalAnswers: number,
  options: ChartExportOptions = {}
): string {
  const entries = Object.entries(optionDistribution || {});
  const barHeight = 26;
  const gap = 18;
  const height = Math.max(420, 150 + entries.length * (barHeight + gap) + 60);
  const width = options.width || 800;
  const isMono = options.theme === 'monochrome';
  const title = options.surveyTitle ? `${options.surveyTitle} — ${questionTitle}` : questionTitle;

  const colors = isMono
    ? {
        bar: '#404040',
        bg: '#ffffff',
        text: '#171717',
        subtext: '#525252',
        border: '#d4d4d4',
        cardBg: '#fafafa'
      }
    : {
        bar: '#4f46e5',
        bg: '#ffffff',
        text: '#0f172a',
        subtext: '#64748b',
        border: '#e2e8f0',
        cardBg: '#f8fafc'
      };

  const maxTrackWidth = 440;
  let barsSvg = '';

  entries.forEach(([label, count], idx) => {
    const y = 135 + idx * (barHeight + gap);
    const pct = totalAnswers > 0 ? Math.round((count / totalAnswers) * 100) : 0;
    const barW = Math.max(6, (maxTrackWidth * pct) / 100);

    barsSvg += `
    <g transform="translate(36, ${y})">
      <!-- Option Label -->
      <text x="0" y="17" font-size="12" font-weight="600" fill="${colors.text}">
        ${escapeXml(label.length > 32 ? label.substring(0, 32) + '...' : label)}
      </text>

      <!-- Track -->
      <rect x="230" y="2" width="${maxTrackWidth}" height="${barHeight}" rx="6" fill="${colors.cardBg}" stroke="${colors.border}" stroke-width="1" />
      <!-- Bar -->
      <rect x="230" y="2" width="${barW}" height="${barHeight}" rx="6" fill="${colors.bar}" />

      <!-- Count & Pct -->
      <text x="${230 + barW + 12}" y="19" font-size="12" font-weight="700" fill="${colors.bar}">
        ${count} (${pct}%)
      </text>
    </g>`;
  });

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">
  <!-- Background -->
  <rect width="${width}" height="${height}" fill="${colors.bg}" />
  <rect x="12" y="12" width="${width - 24}" height="${height - 24}" rx="12" fill="none" stroke="${colors.border}" stroke-width="1" />

  <!-- Header -->
  <text x="36" y="44" font-size="12" font-weight="700" text-transform="uppercase" fill="${colors.subtext}">
    PHÂN BỐ TẦN SỐ • LOẠI CÂU HỎI: ${escapeXml(questionType.toUpperCase())}
  </text>
  <text x="36" y="70" font-size="18" font-weight="800" fill="${colors.text}">
    ${escapeXml(questionTitle)}
  </text>
  <text x="36" y="92" font-size="13" font-weight="500" fill="${colors.subtext}">
    Tổng câu trả lời hợp lệ N = ${totalAnswers} lượt
  </text>

  <!-- Divider -->
  <line x1="36" y1="108" x2="${width - 36}" y2="108" stroke="${colors.border}" stroke-width="1" />

  <!-- Bars -->
  ${barsSvg}

  <!-- Footnote -->
  <line x1="36" y1="${height - 40}" x2="${width - 36}" y2="${height - 40}" stroke="${colors.border}" stroke-width="1" />
  <text x="36" y="${height - 20}" font-size="11" fill="${colors.subtext}" font-style="italic">${escapeXml(options.sourceNote || DEFAULT_SOURCE_NOTE)}</text>
  <text x="${width - 36}" y="${height - 20}" text-anchor="end" font-size="11" fill="${colors.subtext}">Xuất bởi DataTrust • ${new Date().toLocaleDateString('vi-VN')}</text>
</svg>`;
}

/**
 * 4. Chuyển đổi SVG thành PNG Độ Phân Giải Cao (300 DPI) bằng HTML5 Canvas
 */
export async function rasterizeSvgToPng(
  svgString: string,
  width: number = 800,
  height: number = 500,
  scale: number = 3 // 3x scale = 2400x1500 (300 DPI publication print quality)
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    try {
      const canvas = document.createElement('canvas');
      canvas.width = width * scale;
      canvas.height = height * scale;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        reject(new Error('Canvas 2D context not available'));
        return;
      }

      // Đảm bảo nền trắng sạch
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.scale(scale, scale);

      const img = new Image();
      const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(svgBlob);

      img.onload = () => {
        ctx.drawImage(img, 0, 0, width, height);
        URL.revokeObjectURL(url);
        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob);
            } else {
              reject(new Error('Canvas toBlob failed'));
            }
          },
          'image/png',
          1.0
        );
      };

      img.onerror = (err) => {
        URL.revokeObjectURL(url);
        reject(err);
      };

      img.src = url;
    } catch (err) {
      reject(err);
    }
  });
}

/**
 * 5. Tải file Blob hoặc Text về thiết bị
 */
export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function downloadSvgFile(svgString: string, filename: string) {
  const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
  downloadBlob(blob, filename.endsWith('.svg') ? filename : `${filename}.svg`);
}

/**
 * 6. Sinh Đoạn Mã LaTeX (Pgfplots) tương thích Overleaf / LaTeX Papers
 */
export function generateLatexPgfplotsSnippet(
  chartType: 'risk' | 'question',
  data: any,
  title: string
): string {
  if (chartType === 'risk') {
    return `% === DataTrust Academic LaTeX PGFPlots Snippet ===
% Yêu cầu gói: \\usepackage{pgfplots} \\pgfplotsset{compat=1.18}
\\begin{figure}[htbp]
\\centering
\\begin{tikzpicture}
\\begin{axis}[
    ybar,
    bar width=20pt,
    width=0.85\\textwidth,
    height=6cm,
    title={${title || 'Phân Bố Rủi Ro Dữ Liệu Thực Địa'}},
    ylabel={Tỷ lệ phần trăm (\\%)},
    symbolic x coords={Rủi ro thấp, Rủi ro vừa, Rủi ro cao},
    xtick=data,
    nodes near coords,
    nodes near coords align={vertical},
    ymin=0, ymax=100,
    grid=major,
    legend style={at={(0.5,-0.15)}, anchor=north,legend columns=-1}
]
\\addplot[fill=black!60] coordinates {
    (Rủi ro thấp, ${data.low_pct || 80})
    (Rủi ro vừa, ${data.med_pct || 15})
    (Rủi ro cao, ${data.high_pct || 5})
};
\\end{axis}
\\end{tikzpicture}
\\caption{Kiểm định phân bố chất lượng và rủi ro mẫu theo chuẩn Don Dillman (N = ${data.total || 100}). Nguồn: DataTrust.}
\\label{fig:datatrust_risk_distribution}
\\end{figure}`;
  }

  return `% === DataTrust Academic Question Distribution Snippet ===
\\begin{figure}[htbp]
\\centering
\\begin{tikzpicture}
\\begin{axis}[
    xbar,
    bar width=14pt,
    width=0.85\\textwidth,
    height=7cm,
    title={${title}},
    xlabel={Số lượng câu trả lời},
    symbolic y coords={${Object.keys(data).map(k => `{${k}}`).join(', ')}},
    ytick=data,
    nodes near coords,
    nodes near coords align={horizontal},
    grid=major
]
\\addplot[fill=black!70] coordinates {
    ${Object.entries(data).map(([k, v]) => `(${v},{${k}})`).join('\n    ')}
};
\\end{axis}
\\end{tikzpicture}
\\caption{Phân bố tần suất phương án câu hỏi. Nguồn: DataTrust.}
\\end{figure}`;
}
