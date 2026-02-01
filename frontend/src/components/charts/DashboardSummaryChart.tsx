'use client';

import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { CHART_COLORS } from '@/utils/constants';

interface DashboardSummaryChartProps {
  data: Array<Record<string, string | number>>;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const income = data.Income || 0;
    
    // Calculate total expenses from all category values
    const expenseCategories: Array<{ name: string; value: number; color: string }> = [];
    let totalExpenses = 0;
    
    payload.forEach((entry: any) => {
      if (entry.dataKey !== 'Income' && entry.value > 0) {
        expenseCategories.push({
          name: entry.name,
          value: entry.value,
          color: entry.color,
        });
        totalExpenses += entry.value;
      }
    });

    const savings = income - totalExpenses;

    return (
      <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-lg">
        <p className="text-sm font-semibold text-gray-900 mb-3">{label}</p>
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-4 pb-2 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-sm text-gray-600">Income:</span>
            </div>
            <span className="text-sm font-semibold text-green-600">
              ₹{Number(income).toLocaleString()}
            </span>
          </div>
          
          {expenseCategories.length > 0 && (
            <>
              <div className="space-y-1.5">
                {expenseCategories.map((cat, idx) => (
                  <div key={idx} className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded"
                        style={{ backgroundColor: cat.color }}
                      />
                      <span className="text-sm text-gray-600">{cat.name}:</span>
                    </div>
                    <span className="text-sm font-medium text-gray-900">
                      ₹{Number(cat.value).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
              
              <div className="pt-2 border-t border-gray-100 mt-2">
                <div className="flex items-center justify-between gap-4">
                  <span className="text-sm font-medium text-gray-700">Total Expenses:</span>
                  <span className="text-sm font-semibold text-red-600">
                    ₹{Number(totalExpenses).toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-4 mt-1">
                  <span className="text-sm font-medium text-gray-700">Savings:</span>
                  <span className={`text-sm font-semibold ${savings >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {savings >= 0 ? '+' : ''}₹{Number(savings).toLocaleString()}
                  </span>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    );
  }
  return null;
};

const CustomLegend = ({ payload }: any) => {
  if (!payload) return null;

  // Separate Income (line) from expense categories (bars)
  const incomeEntry = payload.find((entry: any) => entry.dataKey === 'Income');
  const expenseEntries = payload.filter((entry: any) => entry.dataKey !== 'Income');

  return (
    <div className="flex flex-wrap justify-center gap-6 mt-6">
      {incomeEntry && (
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-green-500"></div>
          <span className="text-sm text-gray-600 font-medium">{incomeEntry.value}</span>
        </div>
      )}
      {expenseEntries.map((entry: any, index: number) => (
        <div key={index} className="flex items-center gap-2">
          <div
            className="w-4 h-4 rounded"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-sm text-gray-600">{entry.value}</span>
        </div>
      ))}
    </div>
  );
};

export function DashboardSummaryChart({ data }: DashboardSummaryChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 bg-gray-50/50 rounded-xl border border-dashed border-gray-200">
        No data available. Add transactions to see your financial summary.
      </div>
    );
  }

  // Extract all unique category names (excluding 'month' and 'Income')
  const categoryKeys = new Set<string>();
  data.forEach((item) => {
    Object.keys(item).forEach((key) => {
      if (key !== 'month' && key !== 'Income') {
        categoryKeys.add(key);
      }
    });
  });

  const categories = Array.from(categoryKeys);
  const colorMap: Record<string, string> = {};
  categories.forEach((cat, idx) => {
    colorMap[cat] = CHART_COLORS[idx % CHART_COLORS.length];
  });

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ComposedChart
        data={data}
        margin={{ top: 10, right: 20, left: 10, bottom: 10 }}
      >
        <defs>
          {categories.map((cat) => (
            <linearGradient
              key={cat}
              id={`gradient-${cat}`}
              x1="0"
              y1="0"
              x2="0"
              y2="1"
            >
              <stop offset="0%" stopColor={colorMap[cat]} stopOpacity={0.9} />
              <stop offset="100%" stopColor={colorMap[cat]} stopOpacity={0.6} />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#e5e7eb"
          strokeOpacity={0.5}
          vertical={false}
        />
        <XAxis
          dataKey="month"
          tick={{ fill: '#6b7280', fontSize: 12, fontFamily: 'Inter, system-ui, sans-serif' }}
          axisLine={{ stroke: '#e5e7eb' }}
          tickLine={false}
          height={40}
        />
        <YAxis
          tick={{ fill: '#6b7280', fontSize: 12, fontFamily: 'Inter, system-ui, sans-serif' }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(value) =>
            `₹${value >= 1000 ? (value / 1000).toFixed(1) + 'k' : value.toLocaleString()}`
          }
          width={60}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend content={<CustomLegend />} />
        
        {/* Stacked bars for expense categories */}
        {categories.map((category) => (
          <Bar
            key={category}
            dataKey={category}
            stackId="expenses"
            fill={`url(#gradient-${category})`}
            name={category}
            radius={[0, 0, 0, 0]}
          />
        ))}
        
        {/* Line for Income */}
        <Line
          type="monotone"
          dataKey="Income"
          stroke="#10b981"
          strokeWidth={3}
          dot={{ fill: '#10b981', r: 4 }}
          activeDot={{ r: 6 }}
          name="Income"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
