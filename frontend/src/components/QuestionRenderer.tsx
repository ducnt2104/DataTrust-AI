import React from 'react';
import { ChevronUp, ChevronDown, Move } from 'lucide-react';
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
  const optionList: { id: string; label: string }[] = Array.isArray(question.options) ? question.options : [];

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
            {optionList.map((opt) => {
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
            {optionList.map((opt) => {
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
            {optionList.map((opt) => (
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
            ]).map((opt: any) => {
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

        {/* Matrix (Grid of Rows x Columns) */}
        {qType === 'matrix' && (() => {
          const matrixRows: { id: string; label: string }[] = Array.isArray(options?.rows)
            ? options.rows
            : [
                { id: 'r1', label: 'Tiêu chí 1' },
                { id: 'r2', label: 'Tiêu chí 2' },
                { id: 'r3', label: 'Tiêu chí 3' }
              ];
          const matrixCols: { id: string; label: string }[] = Array.isArray(options?.columns)
            ? options.columns
            : [
                { id: 'c1', label: 'Kém' },
                { id: 'c2', label: 'Bình thường' },
                { id: 'c3', label: 'Tốt' }
              ];
          const currentMatrixVal: Record<string, string> = (value && typeof value === 'object') ? value : {};

          return (
            <div className="overflow-x-auto pt-2">
              <table className="w-full text-left text-sm border-collapse border border-slate-200 rounded-xl overflow-hidden">
                <thead className="bg-slate-50 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4 border border-slate-200">Tiêu chí / Khía cạnh</th>
                    {matrixCols.map((col) => (
                      <th key={col.id} className="py-3 px-4 border border-slate-200 text-center">
                        {col.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {matrixRows.map((row) => (
                    <tr key={row.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3.5 px-4 font-medium text-slate-800 border border-slate-200">
                        {row.label}
                      </td>
                      {matrixCols.map((col) => {
                        const isChecked = currentMatrixVal[row.id] === col.id;
                        return (
                          <td
                            key={col.id}
                            onClick={() => {
                              if (!disabled) {
                                handleChange({ ...currentMatrixVal, [row.id]: col.id });
                              }
                            }}
                            className={`py-3.5 px-4 text-center border border-slate-200 cursor-pointer transition-colors ${
                              isChecked ? 'bg-indigo-50/50' : 'hover:bg-slate-100/50'
                            }`}
                          >
                            <input
                              type="radio"
                              name={`matrix_${question.id}_${row.id}`}
                              disabled={disabled}
                              checked={isChecked}
                              onChange={() => {
                                handleChange({ ...currentMatrixVal, [row.id]: col.id });
                              }}
                              className="w-4 h-4 text-indigo-600 border-slate-300 focus:ring-indigo-500 cursor-pointer"
                            />
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        })()}

        {/* Ranking (Interactive ordered list) */}
        {qType === 'ranking' && (() => {
          const items: { id: string; label: string }[] = Array.isArray(options) ? options : [];
          // value is ordered array of item ids: string[]
          const orderedIds: string[] = Array.isArray(value) && value.length === items.length
            ? value
            : items.map((it) => it.id);
          const itemMap = new Map(items.map((it) => [it.id, it.label]));

          const handleMove = (index: number, direction: 'up' | 'down') => {
            if (disabled) return;
            const targetIndex = direction === 'up' ? index - 1 : index + 1;
            if (targetIndex < 0 || targetIndex >= orderedIds.length) return;
            const newList = [...orderedIds];
            const temp = newList[index];
            newList[index] = newList[targetIndex];
            newList[targetIndex] = temp;
            handleChange(newList);
          };

          return (
            <div className="space-y-2 pt-2">
              <span className="text-xs text-slate-400 block mb-1">
                Sử dụng các mũi tên để thay đổi thứ tự ưu tiên (Vị trí 1 là ưu tiên cao nhất)
              </span>
              <div className="space-y-2">
                {orderedIds.map((itemId, idx) => (
                  <div
                    key={itemId}
                    className="flex items-center justify-between p-3 rounded-xl border border-slate-200 bg-white hover:border-indigo-300 transition-all text-sm shadow-xs"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full bg-indigo-50 text-indigo-700 font-bold text-xs flex items-center justify-center shrink-0">
                        #{idx + 1}
                      </span>
                      <span className="font-medium text-slate-800">
                        {itemMap.get(itemId) || itemId}
                      </span>
                    </div>

                    {!disabled && (
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          disabled={idx === 0}
                          onClick={() => handleMove(idx, 'up')}
                          className="p-1 rounded-lg hover:bg-slate-100 text-slate-500 disabled:opacity-20"
                          title="Chuyển lên"
                        >
                          <ChevronUp className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          disabled={idx === orderedIds.length - 1}
                          onClick={() => handleMove(idx, 'down')}
                          className="p-1 rounded-lg hover:bg-slate-100 text-slate-500 disabled:opacity-20"
                          title="Chuyển xuống"
                        >
                          <ChevronDown className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })()}
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
