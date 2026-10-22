import React from 'react';
import { Question } from '../types/survey';

interface Props {
  question: Question;
  index: number;
  value: any;
  onChange?: (val: any) => void;
  disabled?: boolean;
  error?: string;
}

export const QuestionRenderer: React.FC<Props> = ({
  question,
  index,
  value,
  onChange,
  disabled = false,
  error
}) => {
  const handleChange = (newVal: any) => {
    if (!disabled && onChange) {
      onChange(newVal);
    }
  };

  const qType = question.question_type;
  const options = question.options || [];

  return (
    <div className={`p-6 rounded-2xl bg-white border transition-all duration-200 ${
      error ? 'border-rose-400 ring-2 ring-rose-100' : 'border-slate-200/80 shadow-xs hover:border-slate-300'
    }`}>
      {/* Title & Description */}
      <div className="mb-4">
        <div className="flex items-start gap-2">
          <span className="font-semibold text-indigo-600 text-sm mt-0.5">{index + 1}.</span>
          <div className="flex-1">
            <h3 className="text-base font-semibold text-slate-900 leading-snug">
              {question.title}
              {question.is_required && <span className="text-rose-500 ml-1 font-bold">*</span>}
            </h3>
            {question.description && (
              <p className="text-sm text-slate-500 mt-1">{question.description}</p>
            )}
          </div>
        </div>
      </div>

      {/* Input controls based on question_type */}
      <div className="mt-2 space-y-2">
        {/* Short Text */}
        {qType === 'short_text' && (
          <input
            type="text"
            disabled={disabled}
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder="Nhập câu trả lời của bạn..."
            className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-slate-900 placeholder:text-slate-400 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 transition-all text-sm disabled:bg-slate-50 disabled:text-slate-500"
          />
        )}

        {/* Long Text */}
        {qType === 'long_text' && (
          <textarea
            rows={3}
            disabled={disabled}
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder="Nhập chi tiết ý kiến hoặc nhận xét của bạn..."
            className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-slate-900 placeholder:text-slate-400 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 transition-all text-sm disabled:bg-slate-50 disabled:text-slate-500 resize-y"
          />
        )}

        {/* Single Choice (Radio) */}
        {qType === 'single_choice' && (
          <div className="space-y-2">
            {options.map((opt) => {
              const isSelected = value === opt.id || value === opt.label;
              return (
                <label
                  key={opt.id}
                  className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all text-sm ${
                    isSelected
                      ? 'border-indigo-600 bg-indigo-50/50 text-indigo-950 font-medium'
                      : 'border-slate-200 hover:bg-slate-50/80 text-slate-700'
                  } ${disabled ? 'cursor-default pointer-events-none' : ''}`}
                >
                  <input
                    type="radio"
                    name={`q_${question.id}`}
                    disabled={disabled}
                    checked={isSelected}
                    onChange={() => handleChange(opt.id)}
                    className="w-4 h-4 text-indigo-600 border-slate-300 focus:ring-indigo-500"
                  />
                  <span>{opt.label}</span>
                </label>
              );
            })}
          </div>
        )}

        {/* Multiple Choice (Checkboxes) */}
        {qType === 'multiple_choice' && (
          <div className="space-y-2">
            {options.map((opt) => {
              const currentList: string[] = Array.isArray(value) ? value : [];
              const isSelected = currentList.includes(opt.id) || currentList.includes(opt.label);
              return (
                <label
                  key={opt.id}
                  className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all text-sm ${
                    isSelected
                      ? 'border-indigo-600 bg-indigo-50/50 text-indigo-950 font-medium'
                      : 'border-slate-200 hover:bg-slate-50/80 text-slate-700'
                  } ${disabled ? 'cursor-default pointer-events-none' : ''}`}
                >
                  <input
                    type="checkbox"
                    disabled={disabled}
                    checked={isSelected}
                    onChange={(e) => {
                      if (e.target.checked) {
                        handleChange([...currentList, opt.id]);
                      } else {
                        handleChange(currentList.filter((x) => x !== opt.id && x !== opt.label));
                      }
                    }}
                    className="w-4 h-4 text-indigo-600 rounded-sm border-slate-300 focus:ring-indigo-500"
                  />
                  <span>{opt.label}</span>
                </label>
              );
            })}
          </div>
        )}

        {/* Dropdown */}
        {qType === 'dropdown' && (
          <select
            disabled={disabled}
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-300 text-slate-900 bg-white focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 transition-all text-sm disabled:bg-slate-50 disabled:text-slate-500"
          >
            <option value="">-- Chọn phương án --</option>
            {options.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.label}
              </option>
            ))}
          </select>
        )}

        {/* Linear Scale (1 - 5 or 1 - 10) */}
        {qType === 'linear_scale' && (
          <div className="pt-2">
            <div className="flex items-center justify-between text-xs text-slate-500 mb-2 font-medium">
              <span>{options[0]?.label || '1 (Thấp / Không)'}</span>
              <span>{options[1]?.label || '10 (Cao / Rất sẵn lòng)'}</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => {
                const isSelected = String(value) === String(num);
                return (
                  <button
                    key={num}
                    type="button"
                    disabled={disabled}
                    onClick={() => handleChange(num)}
                    className={`flex-1 min-w-[38px] py-2.5 rounded-xl text-sm font-semibold border transition-all ${
                      isSelected
                        ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300'
                    } ${disabled ? 'pointer-events-none' : ''}`}
                  >
                    {num}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Likert Scale (5-point) */}
        {qType === 'likert' && (
          <div className="space-y-2 pt-1">
            {(options.length > 0 ? options : [
              { id: '1', label: '1 - Hoàn toàn không đồng ý' },
              { id: '2', label: '2 - Không đồng ý' },
              { id: '3', label: '3 - Trung lập / Bình thường' },
              { id: '4', label: '4 - Đồng ý' },
              { id: '5', label: '5 - Hoàn toàn đồng ý' }
            ]).map((opt) => {
              const isSelected = String(value) === String(opt.id) || String(value) === String(opt.label);
              return (
                <label
                  key={opt.id}
                  className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all text-sm ${
                    isSelected
                      ? 'border-indigo-600 bg-indigo-50/50 text-indigo-950 font-medium'
                      : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  } ${disabled ? 'cursor-default pointer-events-none' : ''}`}
                >
                  <input
                    type="radio"
                    name={`q_${question.id}`}
                    disabled={disabled}
                    checked={isSelected}
                    onChange={() => handleChange(opt.id)}
                    className="w-4 h-4 text-indigo-600 border-slate-300 focus:ring-indigo-500"
                  />
                  <span>{opt.label}</span>
                </label>
              );
            })}
          </div>
        )}

        {/* Number */}
        {qType === 'number' && (
          <input
            type="number"
            disabled={disabled}
            value={value !== undefined && value !== null ? value : ''}
            onChange={(e) => handleChange(e.target.value === '' ? '' : Number(e.target.value))}
            placeholder="Nhập số..."
            className="w-full max-w-xs px-4 py-2.5 rounded-xl border border-slate-300 text-slate-900 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 transition-all text-sm disabled:bg-slate-50"
          />
        )}

        {/* Date */}
        {qType === 'date' && (
          <input
            type="date"
            disabled={disabled}
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            className="w-full max-w-xs px-4 py-2.5 rounded-xl border border-slate-300 text-slate-900 focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 transition-all text-sm disabled:bg-slate-50"
          />
        )}

        {/* Boolean (Yes / No) */}
        {qType === 'boolean' && (
          <div className="flex gap-3 max-w-xs">
            {['Có / Đúng', 'Không / Sai'].map((label, idx) => {
              const boolVal = idx === 0 ? 'yes' : 'no';
              const isSelected = value === boolVal || value === (idx === 0);
              return (
                <button
                  key={boolVal}
                  type="button"
                  disabled={disabled}
                  onClick={() => handleChange(boolVal)}
                  className={`flex-1 py-2.5 rounded-xl text-sm font-medium border transition-all ${
                    isSelected
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                  } ${disabled ? 'pointer-events-none' : ''}`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Validation Error */}
      {error && (
        <p className="mt-2 text-xs font-medium text-rose-600 flex items-center gap-1">
          <span>⚠️ {error}</span>
        </p>
      )}
    </div>
  );
};
