import { useEffect, useMemo, useState } from 'react';
import {
  Bar,
  Line,
  Pie,
} from 'react-chartjs-2';
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
);

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
const navItems = [
  { key: 'overview', label: 'Overview' },
  { key: 'sales', label: 'Sales analytics' },
  { key: 'customers', label: 'Customer intelligence' },
  { key: 'risk', label: 'Returns & risk' },
  { key: 'recommendations', label: 'Recommendations' },
  { key: 'quality', label: 'Data quality' },
];

function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

function formatForecastCurrency(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-US').format(Number(value || 0));
}

function formatPercent(value) {
  return `${Number(value || 0).toFixed(2)}%`;
}

async function apiRequest(path, token, options = {}) {
  const headers = { Accept: 'application/json', ...(options.headers || {}) };

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = typeof payload === 'string' ? payload : payload?.detail || 'Request failed';
    throw new Error(detail);
  }

  return payload;
}

const defaultFilters = { region: '', city: '', category: '', year: '' };

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('nexus_token') || '');
  const [role, setRole] = useState(localStorage.getItem('nexus_role') || 'Viewer');
  const [activeView, setActiveView] = useState('overview');
  const [filters, setFilters] = useState(defaultFilters);
  const [meta, setMeta] = useState({ regions: [], categories: [], cities: [], years: [] });
  const [dashboard, setDashboard] = useState({
    kpis: {},
    trend: [],
    categoryPerformance: [],
    topProducts: [],
    topCustomers: [],
    recommendations: [],
    quality: {},
    dailyReport: { summary: {} },
  });
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('Ready');
  const [loginForm, setLoginForm] = useState({ email: 'demo@example.com', password: 'demo-password' });
  const [loginError, setLoginError] = useState('');
  const [adminForm, setAdminForm] = useState({ region: '', category: '' });
  const [forecastDays, setForecastDays] = useState(1);
  const [forecastDate, setForecastDate] = useState(() => {
    const today = new Date();
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  });
  const [forecastSalesInput, setForecastSalesInput] = useState('');
  const [salesForecast, setSalesForecast] = useState(null);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [forecastError, setForecastError] = useState('');

  const authenticated = Boolean(token);

  useEffect(() => {
    if (!authenticated) {
      return;
    }

    const loadDashboard = async () => {
      try {
        setLoading(true);
        setStatus('Loading dashboard data...');

        const params = new URLSearchParams();
        if (filters.region) params.set('region', filters.region);
        if (filters.city) params.set('city', filters.city);
        if (filters.category) params.set('category', filters.category);
        if (filters.year) params.set('year', filters.year);

        const query = params.toString() ? `?${params.toString()}` : '';

        const [kpisData, trendData, categoryData, productsData, customersData, recommendationData, qualityData, dailyReportData] = await Promise.all([
          apiRequest(`/api/dashboard/kpis${query}`, token),
          apiRequest(`/api/sales/trend${query}`, token),
          apiRequest('/api/sales/category', token),
          apiRequest('/api/products/top', token),
          apiRequest('/api/customers/top', token),
          apiRequest('/api/recommendations', token),
          apiRequest('/api/data/quality', token),
          apiRequest(`/api/sales/daily/report${query}`, token),
        ]);

        setDashboard({
          kpis: kpisData.kpis || {},
          trend: trendData || [],
          categoryPerformance: categoryData || [],
          topProducts: productsData || [],
          topCustomers: customersData || [],
          recommendations: recommendationData || [],
          quality: qualityData || {},
          dailyReport: dailyReportData || { summary: {} },
        });

        const years = Array.from(
          new Set((trendData || []).map((item) => String(item.Month || '').slice(0, 4)).filter(Boolean)),
        ).sort();

        setMeta({
          regions: kpisData.filters?.regions || [],
          categories: kpisData.filters?.categories || [],
          cities: kpisData.filters?.cities || [],
          years,
        });

        setStatus('Dashboard ready');
      } catch (error) {
        setStatus(error.message || 'Unable to load dashboard');
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, [authenticated, token, filters]);

  const salesTrend = useMemo(() => {
    const labels = (dashboard.trend || []).map((point) => String(point.Month || '').slice(0, 7));
    const values = (dashboard.trend || []).map((point) => Number(point.sales || 0));

    return {
      labels,
      datasets: [
        {
          label: 'Net sales',
          data: values,
          borderColor: '#ed7654',
          backgroundColor: 'rgba(237, 118, 84, 0.18)',
          tension: 0.32,
          fill: true,
        },
      ],
    };
  }, [dashboard.trend]);

  const categoryChart = useMemo(() => {
    const top = (dashboard.categoryPerformance || []).slice(0, 6);
    return {
      labels: top.map((item) => item.Category || 'Unknown'),
      datasets: [
        {
          label: 'Sales by category',
          data: top.map((item) => Number(item.sales || 0)),
          backgroundColor: ['#ed7654', '#5ec8a6', '#7ea7d8', '#7f8ae6', '#ffc857', '#69b3a2'],
        },
      ],
    };
  }, [dashboard.categoryPerformance]);

  const categoryPieChart = useMemo(() => ({
    labels: categoryChart.labels,
    datasets: [
      {
        label: 'Sales mix',
        data: categoryChart.datasets[0].data,
        backgroundColor: categoryChart.datasets[0].backgroundColor,
        borderColor: '#14212a',
        borderWidth: 3,
      },
    ],
  }), [categoryChart]);

  const qualityMetrics = useMemo(() => {
    const quality = dashboard.quality || {};
    const records = Number(quality.records || 0);
    const columns = Number(quality.columns || 0);
    const totalCells = records * columns;
    const completeness = quality.completeness != null
      ? Number(quality.completeness)
      : totalCells > 0
        ? (1 - Number(quality.missing_values || 0) / totalCells) * 100
        : 0;
    const uniqueness = quality.uniqueness != null
      ? Number(quality.uniqueness)
      : records > 0
        ? (1 - Number(quality.duplicate_rows || 0) / records) * 100
        : 0;
    const dateValidity = quality.date_validity != null
      ? Number(quality.date_validity)
      : quality.invalid_dates != null && records > 0
        ? (1 - Number(quality.invalid_dates || 0) / records) * 100
        : quality.date_min && quality.date_max
          ? 100
          : 0;
    const qualityScore = quality.quality_score != null
      ? Number(quality.quality_score)
      : (completeness + uniqueness + dateValidity) / 3;

    return {
      available: records > 0 && columns > 0,
      completeness: Math.max(0, Math.min(100, completeness)),
      uniqueness: Math.max(0, Math.min(100, uniqueness)),
      dateValidity: Math.max(0, Math.min(100, dateValidity)),
      score: Math.max(0, Math.min(100, qualityScore)),
    };
  }, [dashboard.quality]);

  const qualityBreakdown = useMemo(() => {
    const chunks = [
      { label: 'Completeness', value: qualityMetrics.completeness },
      { label: 'Unique records', value: qualityMetrics.uniqueness },
      { label: 'Valid dates', value: qualityMetrics.dateValidity },
    ];
    return {
      labels: chunks.map((item) => item.label),
      datasets: [
        {
          data: chunks.map((item) => item.value),
          backgroundColor: ['#69b3a2', '#7398c7', '#ed7654'],
        },
      ],
    };
  }, [qualityMetrics]);

  const qualityChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    scales: {
      x: {
        min: 0,
        max: 100,
        grid: { color: 'rgba(140, 155, 165, 0.12)' },
        ticks: { color: '#8c9ba5', callback: (value) => `${value}%` },
      },
      y: {
        grid: { display: false },
        ticks: { color: '#d5dde1' },
      },
    },
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (context) => `${context.parsed.x.toFixed(2)}%` } },
    },
  };

  const salesChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { intersect: false, mode: 'index' },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) => ` Net sales: ${formatCurrency(context.parsed.y)}`,
        },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(140, 155, 165, 0.12)' },
        ticks: { color: '#8c9ba5', maxRotation: 0, autoSkip: true, maxTicksLimit: 12 },
      },
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(140, 155, 165, 0.12)' },
        ticks: {
          color: '#8c9ba5',
          callback: (value) => formatCurrency(value),
        },
      },
    },
  };

  const forecastChartData = useMemo(() => {
    const predictions = salesForecast?.forecast || [];
    return {
      labels: [salesForecast?.latest_observed_date, ...predictions.map((item) => item.date)],
      datasets: [
        {
          label: 'Latest actual sales',
          data: [Number(salesForecast?.today_sales || 0), ...predictions.map(() => null)],
          borderColor: '#7398c7',
          backgroundColor: '#7398c7',
          pointRadius: 4,
          showLine: false,
        },
        {
          label: 'Predicted sales',
          data: [Number(salesForecast?.today_sales || 0), ...predictions.map((item) => Number(item.predicted_sales || 0))],
          borderColor: '#ed7654',
          backgroundColor: 'rgba(237, 118, 84, 0.12)',
          borderDash: [5, 4],
          tension: 0.25,
          fill: false,
        },
      ],
    };
  }, [salesForecast]);

  const forecastChartOptions = {
    ...salesChartOptions,
    plugins: {
      ...salesChartOptions.plugins,
      legend: { display: true, labels: { color: '#c7d2d8', usePointStyle: true } },
      tooltip: {
        callbacks: {
          label: (context) => ` ${context.dataset.label}: ${formatForecastCurrency(context.parsed.y)}`,
        },
      },
    },
    scales: {
      ...salesChartOptions.scales,
      y: { ...salesChartOptions.scales.y, ticks: { ...salesChartOptions.scales.y.ticks, callback: (value) => formatForecastCurrency(value) } },
    },
  };

  const categoryBarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) => ` Sales: ${formatCurrency(context.parsed.y)}`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#8c9ba5', maxRotation: 35, minRotation: 0 },
      },
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(140, 155, 165, 0.12)' },
        ticks: {
          color: '#8c9ba5',
          callback: (value) => formatCurrency(value),
        },
      },
    },
  };

  const categoryPieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: '#c7d2d8', padding: 14, usePointStyle: true },
      },
      tooltip: {
        callbacks: {
          label: (context) => ` ${context.label}: ${formatCurrency(context.parsed)}`,
        },
      },
    },
  };

  const handleLogin = async (event) => {
    event.preventDefault();
    try {
      const result = await apiRequest('/api/auth/login', '', {
        method: 'POST',
        body: JSON.stringify(loginForm),
      });

      localStorage.setItem('nexus_token', result.access_token);
      localStorage.setItem('nexus_role', result.role || 'Viewer');
      setToken(result.access_token);
      setRole(result.role || 'Viewer');
      setLoginError('');
    } catch (error) {
      setLoginError(error.message || 'Unable to sign in');
    }
  };

  const logout = () => {
    localStorage.removeItem('nexus_token');
    localStorage.removeItem('nexus_role');
    setToken('');
    setRole('Viewer');
    setFilters(defaultFilters);
  };

  const applyFilters = () => {
    setStatus('Applying filters...');
  };

  const runDailyForecast = async (event) => {
    event.preventDefault();
    if (!forecastDate) {
      setForecastError('Select the date to forecast from.');
      return;
    }

    setForecastLoading(true);
    setForecastError('');
    try {
      const params = new URLSearchParams({
        date: forecastDate,
        days: String(forecastDays),
      });
      if (forecastSalesInput !== '') params.set('sales', forecastSalesInput);
      const result = await apiRequest(`/api/sales/daily/forecast?${params}`, token);
      setSalesForecast(result);
      if (!(result.forecast || []).length) setForecastError(result.basis || 'No forecast is available for this date.');
    } catch (error) {
      setForecastError(error.message || 'Unable to calculate the forecast');
      setSalesForecast(null);
    } finally {
      setForecastLoading(false);
    }
  };

  const handleAdminAction = async (endpoint, method, payload, successText) => {
    try {
      const response = await apiRequest(endpoint, token, {
        method,
        body: payload ? JSON.stringify(payload) : undefined,
      });
      setStatus(response.status ? `${response.status}: ${response.name || successText}` : successText);
      setAdminForm({ region: '', category: '' });
      setFilters((current) => ({ ...current }));
    } catch (error) {
      setStatus(error.message || 'Admin action failed');
    }
  };

  const overviewCards = [
    { label: 'Net sales', value: formatCurrency(dashboard.kpis.sales) },
    {
      label: dashboard.quality.profit_is_estimated ? 'Estimated profit' : 'Profit',
      value: formatCurrency(dashboard.kpis.profit),
    },
    { label: 'Orders', value: formatNumber(dashboard.kpis.orders) },
    { label: 'Customers', value: formatNumber(dashboard.kpis.customers) },
  ];

  const renderView = () => {
    switch (activeView) {
      case 'sales':
        return (
          <div className="content-grid">
            <section className="panel forecast-control-panel">
              <div className="panel-head"><div><h2>Sales forecast</h2><span className="muted">Set the latest date and sales</span></div></div>
              <form className="forecast-inputs" onSubmit={runDailyForecast}>
                <label>Date<input type="date" value={forecastDate} onChange={(event) => setForecastDate(event.target.value)} required /></label>
                <label>Today's sales / revenue (if not in dataset)<input type="number" min="0" step="0.01" value={forecastSalesInput} onChange={(event) => setForecastSalesInput(event.target.value)} placeholder="Optional when date is in dataset" /></label>
                <label>Forecast period
                  <select value={forecastDays} onChange={(event) => setForecastDays(Number(event.target.value))}>
                    <option value={1}>Tomorrow only</option>
                    <option value={7}>7 days</option>
                    <option value={14}>14 days</option>
                    <option value={30}>30 days</option>
                  </select>
                </label>
                <button className="action-button forecast-submit" type="submit" disabled={forecastLoading}>{forecastLoading ? 'Calculating...' : 'Predict sales'}</button>
              </form>
              <p className="muted forecast-data-range">
                Dataset dates: {dashboard.quality.date_min || 'unknown'} to {dashboard.quality.date_max || 'unknown'}. Dates in this range use recorded sales. For a newer date, enter that day's sales; after editing the CSV, restart the backend to reload it.
              </p>
              {forecastError && <p className="error-text">{forecastError}</p>}
            </section>
            <section className="panel forecast-result-panel">
              {(salesForecast?.forecast || []).length ? (
                <>
                  <div className="forecast-result-heading">
                    <div><span className="forecast-eyebrow">TOMORROW'S FORECAST</span><h2>{salesForecast.forecast[0].date}</h2></div>
                    <span className="forecast-method-pill">{salesForecast.basis}</span>
                  </div>
                  <strong className="forecast-hero-value">{formatForecastCurrency(salesForecast.forecast[0].revenue)}</strong>
                  <span className="muted">Predicted sales / revenue</span>
                  <div className="forecast-result-metrics">
                    <div><span>Today's sales</span><strong>{formatForecastCurrency(salesForecast.today_sales)}</strong></div>
                    <div><span>Estimated profit</span><strong>{formatForecastCurrency(salesForecast.forecast[0].predicted_profit)}</strong></div>
                    <div><span>Estimated loss</span><strong>{salesForecast.forecast[0].predicted_loss == null ? 'Unavailable' : salesForecast.forecast[0].predicted_loss > 0 ? formatForecastCurrency(salesForecast.forecast[0].predicted_loss) : 'None predicted'}</strong></div>
                  </div>
                  <p className="forecast-note">Profit uses an estimated 30% margin. {salesForecast.loss_basis}</p>
                  {salesForecast.history_gap_days > 7 && <p className="insight">There are {salesForecast.history_gap_days} days between the entered date and the latest dataset date. The prediction has limited recent history.</p>}
                </>
              ) : (
                <div className="forecast-empty-state">
                  <span className="forecast-eyebrow">NEXT-DAY OUTLOOK</span>
                  <h2>{forecastLoading ? 'Calculating forecast...' : 'Your forecast will appear here'}</h2>
                  <p className="muted">Choose a date and enter sales if that date is not already in the dataset.</p>
                  {forecastError && <p className="error-text">{forecastError}</p>}
                </div>
              )}
            </section>
            {(salesForecast?.forecast || []).length > 0 && (
              <section className="panel wide forecast-detail-panel">
                <div className="panel-head"><div><h2>Daily sales outlook</h2><span className="muted">Actual input followed by datewise predictions</span></div></div>
                {salesForecast.forecast.length > 1 && <div className="chart-frame"><Line data={forecastChartData} options={forecastChartOptions} /></div>}
                  <table>
                    <thead><tr><th>Forecast date</th><th>Predicted sales / revenue</th><th>Estimated profit</th><th>Est. return/cancellation loss</th><th>Predicted orders</th></tr></thead>
                    <tbody>
                      {salesForecast.forecast.map((item) => (
                        <tr key={item.date}>
                          <td>{item.date}</td>
                          <td>{formatForecastCurrency(item.revenue)}</td>
                          <td>{formatForecastCurrency(item.predicted_profit)}</td>
                          <td>{item.predicted_loss == null ? 'Unavailable' : item.predicted_loss > 0 ? formatForecastCurrency(item.predicted_loss) : 'No loss predicted'}</td>
                          <td>{formatNumber(item.predicted_orders)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                <p className="muted">For periods longer than one day, each predicted day becomes input to the next.</p>
              </section>
            )}
            <section className="panel wide">
              <div className="panel-head">
                <h2>Sales performance</h2>
                <span className="muted">Monthly trend</span>
              </div>
              <div className="chart-frame"><Line data={salesTrend} options={salesChartOptions} /></div>
            </section>
            <section className="panel">
              <div className="panel-head">
                <h2>Sales by category</h2>
                <span className="muted">Bar chart</span>
              </div>
              <div className="chart-frame"><Bar data={categoryChart} options={categoryBarOptions} /></div>
            </section>
            <section className="panel">
              <div className="panel-head">
                <h2>Category sales mix</h2>
                <span className="muted">Pie chart</span>
              </div>
              <div className="chart-frame"><Pie data={categoryPieChart} options={categoryPieOptions} /></div>
            </section>
            <section className="panel">
              <div className="panel-head">
                <h2>Top products</h2>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Sales</th>
                    <th>Units</th>
                  </tr>
                </thead>
                <tbody>
                  {(dashboard.topProducts || []).slice(0, 5).map((item) => (
                    <tr key={`${item['Product ID']}-${item['Product Name']}`}>
                      <td>{item['Product Name']}</td>
                      <td>{formatCurrency(item.sales)}</td>
                      <td>{formatNumber(item.units)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>
        );
      case 'customers':
        return (
          <div className="content-grid">
            <section className="panel wide">
              <div className="panel-head">
                <h2>Top customers</h2>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Customer</th>
                    <th>Orders</th>
                    <th>Sales</th>
                    <th>Last order</th>
                  </tr>
                </thead>
                <tbody>
                  {(dashboard.topCustomers || []).slice(0, 8).map((item) => (
                    <tr key={`${item['Customer ID']}-${item['Customer Name']}`}>
                      <td>{item['Customer Name']}</td>
                      <td>{formatNumber(item.orders)}</td>
                      <td>{formatCurrency(item.sales)}</td>
                      <td>{item.last_order}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>
        );
      case 'risk':
        return (
          <div className="content-grid">
            <section className="panel">
              <div className="panel-head">
                <h2>Daily risk signal</h2>
              </div>
              <div className="stat-stack">
                <div className="metric-box">
                  <span>Best day</span>
                  <strong>{dashboard.dailyReport.summary?.top_day?.['Order Date'] || '—'}</strong>
                  <small>{formatCurrency(dashboard.dailyReport.summary?.top_day?.sales)}</small>
                </div>
                <div className="metric-box">
                  <span>Lowest day</span>
                  <strong>{dashboard.dailyReport.summary?.low_day?.['Order Date'] || '—'}</strong>
                  <small>{formatCurrency(dashboard.dailyReport.summary?.low_day?.sales)}</small>
                </div>
                <div className="metric-box">
                  <span>Return rate</span>
                  <strong>{formatPercent(dashboard.kpis.return_rate)}</strong>
                  <small>{formatNumber(dashboard.quality.returned_orders || 0)} returned orders</small>
                </div>
              </div>
            </section>
            <section className="panel">
              <div className="panel-head">
                <h2>Risk days</h2>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Return rate</th>
                    <th>Sales</th>
                  </tr>
                </thead>
                <tbody>
                  {(dashboard.dailyReport.summary?.risk_days || []).slice(0, 5).map((item) => (
                    <tr key={item['Order Date']}>
                      <td>{item['Order Date']}</td>
                      <td>{formatPercent(item.return_rate)}</td>
                      <td>{formatCurrency(item.sales)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>
        );
      case 'recommendations':
        return (
          <div className="content-grid">
            <section className="panel wide">
              <div className="panel-head">
                <h2>Recommended products</h2>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Category</th>
                    <th>Sales</th>
                    <th>Units</th>
                    <th>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {(dashboard.recommendations || []).map((item) => (
                    <tr key={`${item['Product ID']}-${item['Product Name']}`}>
                      <td>{item['Product Name']}</td>
                      <td>{item.Category}</td>
                      <td>{formatCurrency(item.sales)}</td>
                      <td>{formatNumber(item.units)}</td>
                      <td><span className="pill">{Number(item.score || 0).toFixed(3)}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>
        );
      case 'quality':
        return (
          <div className="content-grid">
            <section className="panel">
              <div className="panel-head">
                <h2>Data quality score</h2>
              </div>
              <div className="quality-summary">
                <strong>{qualityMetrics.available ? `${qualityMetrics.score.toFixed(1)}%` : '—'}</strong>
                <div className="qualitybar"><i style={{ width: `${qualityMetrics.available ? qualityMetrics.score : 0}%` }} /></div>
                <p className="muted">Average of source completeness, row uniqueness, and valid dates across {formatNumber(dashboard.quality.records || 0)} records.</p>
              </div>
            </section>
            <section className="panel">
              <div className="panel-head">
                <h2>Quality breakdown</h2>
              </div>
              {qualityMetrics.available ? (
                <div className="chart-frame">
                  <Bar data={qualityBreakdown} options={qualityChartOptions} />
                </div>
              ) : <p className="muted">Quality metrics are unavailable. Check that the backend is running and signed in.</p>}
            </section>
            <section className="panel">
              <div className="panel-head"><h2>Data issues</h2></div>
              <div className="stat-stack">
                <div className="metric-box"><span>Missing cells</span><strong>{formatNumber(dashboard.quality.missing_values || 0)}</strong><small>{formatNumber(dashboard.quality.rows_with_missing || 0)} rows affected</small></div>
                <div className="metric-box"><span>Duplicate rows</span><strong>{formatNumber(dashboard.quality.duplicate_rows || 0)}</strong></div>
                <div className="metric-box"><span>Invalid dates</span><strong>{formatNumber(dashboard.quality.invalid_dates || 0)}</strong><small>{dashboard.quality.date_min || '-'} to {dashboard.quality.date_max || '-'}</small></div>
                {dashboard.quality.profit_is_estimated && <p className="muted">Profit is estimated because the source data has no profit column.</p>}
              </div>
            </section>
          </div>
        );
      default:
        return (
          <div className="content-grid">
            <section className="panel wide">
              <div className="panel-head">
                <h2>Net sales pulse</h2>
                <span className="muted">{dashboard.trend.length} monthly points</span>
              </div>
              <div className="chart-frame"><Line data={salesTrend} options={salesChartOptions} /></div>
            </section>
            <section className="panel">
              <div className="panel-head">
                <h2>Sales by category</h2>
                <span className="muted">Bar chart</span>
              </div>
              <div className="chart-frame"><Bar data={categoryChart} options={categoryBarOptions} /></div>
            </section>
            <section className="panel">
              <div className="panel-head">
                <h2>Category sales mix</h2>
                <span className="muted">Pie chart</span>
              </div>
              <div className="chart-frame"><Pie data={categoryPieChart} options={categoryPieOptions} /></div>
            </section>
            <section className="panel">
              <div className="panel-head">
                <h2>Business snapshot</h2>
              </div>
              {dashboard.quality.profit_is_estimated ? (
                <p className="insight">Profit is estimated using a 30% planning margin because the source dataset has no cost field.</p>
              ) : null}
              <div className="metric-grid">
                <div className="metric-box">
                  <span>Profit margin</span>
                  <strong>{formatPercent(dashboard.kpis.profit_margin)}</strong>
                </div>
                <div className="metric-box">
                  <span>Average order value</span>
                  <strong>{formatCurrency(dashboard.kpis.average_order_value)}</strong>
                </div>
                <div className="metric-box">
                  <span>Return rate</span>
                  <strong>{formatPercent(dashboard.kpis.return_rate)}</strong>
                </div>
                <div className="metric-box">
                  <span>Total units</span>
                  <strong>{formatNumber(dashboard.kpis.quantity)}</strong>
                </div>
              </div>
            </section>
            <section className="panel">
              <div className="panel-head">
                <h2>Top products</h2>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Sales</th>
                  </tr>
                </thead>
                <tbody>
                  {(dashboard.topProducts || []).slice(0, 5).map((item) => (
                    <tr key={`${item['Product ID']}-${item['Product Name']}`}>
                      <td>{item['Product Name']}</td>
                      <td>{formatCurrency(item.sales)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>
        );
    }
  };

  if (!authenticated) {
    return (
      <div className="login-shell">
        <div className="login-panel panel">
          <div className="eyebrow">Nexus Intelligence</div>
          <h1>Sign in</h1>
          <p className="muted">Decision support for your commerce business.</p>
          <form onSubmit={handleLogin}>
            <label>
              <span>Email</span>
              <input
                type="email"
                value={loginForm.email}
                onChange={(event) => setLoginForm((current) => ({ ...current, email: event.target.value }))}
                placeholder="Email"
              />
            </label>
            <label>
              <span>Password</span>
              <input
                type="password"
                value={loginForm.password}
                onChange={(event) => setLoginForm((current) => ({ ...current, password: event.target.value }))}
                placeholder="Password"
              />
            </label>
            <button type="submit" className="primary-button">Enter workspace</button>
          </form>
          {loginError ? <p className="error-text">{loginError}</p> : null}
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">E-commerce Sales and Business Intelligence</div>
        <div className="nav-label">Workspace</div>
        <nav>
          {navItems.map((item) => (
            <button
              key={item.key}
              className={item.key === activeView ? 'active' : ''}
              onClick={() => setActiveView(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <div className="eyebrow">Executive workspace</div>
            <h1>{activeView === 'overview' ? 'Good morning, decision maker.' : 'E-commerce intelligence'}</h1>
          </div>
          <div className="topbar-controls">
            <div className="user-chip">Live dataset · <strong>{formatNumber(dashboard.quality.records || 0)}</strong> rows</div>
            <button className="secondary-button" onClick={logout}>Sign out</button>
          </div>
        </header>

        <div className="toolbar">
          <div className="field">
            <label>Region</label>
            <select value={filters.region} onChange={(event) => setFilters((current) => ({ ...current, region: event.target.value }))}>
              <option value="">All regions</option>
              {meta.regions.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Place / city</label>
            <select value={filters.city} onChange={(event) => setFilters((current) => ({ ...current, city: event.target.value }))}>
              <option value="">All places</option>
              {meta.cities.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Category</label>
            <select value={filters.category} onChange={(event) => setFilters((current) => ({ ...current, category: event.target.value }))}>
              <option value="">All categories</option>
              {meta.categories.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Year</label>
            <select value={filters.year} onChange={(event) => setFilters((current) => ({ ...current, year: event.target.value }))}>
              <option value="">All years</option>
              {meta.years.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </div>

          <button className="action-button" onClick={applyFilters}>Apply filters</button>
          <button className="ghost-button" onClick={() => setFilters(defaultFilters)}>Reset</button>
          <span className="status-text">{loading ? 'Loading...' : status}</span>
        </div>

        {role === 'Admin' ? (
          <div className="toolbar admin-toolbar">
            <div className="field">
              <label>Add region</label>
              <input value={adminForm.region} onChange={(event) => setAdminForm((current) => ({ ...current, region: event.target.value }))} placeholder="e.g. Europe" />
            </div>
            <button className="action-button" onClick={() => handleAdminAction('/api/admin/regions', 'POST', { name: adminForm.region }, 'Region added')}>Add region</button>

            <div className="field">
              <label>Add category</label>
              <input value={adminForm.category} onChange={(event) => setAdminForm((current) => ({ ...current, category: event.target.value }))} placeholder="e.g. Home Care" />
            </div>
            <button className="action-button" onClick={() => handleAdminAction('/api/admin/categories', 'POST', { name: adminForm.category }, 'Category added')}>Add category</button>
          </div>
        ) : null}

        <div className="kpilist">
          {overviewCards.map((card) => (
            <div className="kpi-card" key={card.label}>
              <label>{card.label}</label>
              <strong>{card.value}</strong>
              <div className="delta">Updated live</div>
            </div>
          ))}
        </div>

        {renderView()}
      </main>
    </div>
  );
}
