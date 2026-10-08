import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Bar,
  Line,
  Pie,
  Doughnut,
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
  { key: 'overview', label: 'Overview', icon: '📊' },
  { key: 'segments', label: 'Segment Analysis', icon: '🧭' },
  { key: 'sales', label: 'Sales Analytics', icon: '📈' },
  { key: 'customers', label: 'Customers', icon: '👥' },
  { key: 'risk', label: 'Returns & Risk', icon: '⚠️' },
  { key: 'recommendations', label: 'Recommendations', icon: '💡' },
  { key: 'quality', label: 'Data Quality', icon: '✅' },
];

const navGroups = [
  {
    label: 'WORKSPACE',
    items: [
      { key: 'overview', label: 'Overview', icon: '📊' },
      { key: 'sales', label: 'Sales Analytics', icon: '📈' },
      { key: 'profitability', label: 'Profitability', icon: '💰' },
      { key: 'products', label: 'Product Analytics', icon: '📦' },
      { key: 'custintel', label: 'Customer Intelligence', icon: '👥' },
      { key: 'segments', label: 'Segment Analysis', icon: '🎯' },
      { key: 'geographic', label: 'Geographic Analysis', icon: '🗺️' },
      { key: 'risk', label: 'Returns & Risk', icon: '↩️' },
      { key: 'recommendations', label: 'Recommendations', icon: '💡' },
    ],
  },
  {
    label: 'AI & PREDICTIVE',
    items: [
      { key: 'forecast', label: 'Sales Forecast', icon: '🔮' },
      { key: 'anomalies', label: 'Anomaly Detection', icon: '🚨' },
      { key: 'advisor', label: 'AI Business Advisor', icon: '🤖' },
      { key: 'custpred', label: 'Customer Prediction', icon: '🎯' },
    ],
  },
  {
    label: 'DATA MANAGEMENT',
    items: [
      { key: 'database', label: 'Database', icon: '🗄️' },
      { key: 'dataimport', label: 'Data Import', icon: '📥' },
      { key: 'quality', label: 'Data Quality', icon: '✅' },
      { key: 'export', label: 'Export & Reports', icon: '📤' },
    ],
  },
  {
    label: 'ADMINISTRATION',
    items: [
      { key: 'audit', label: 'Audit Logs', icon: '📋' },
      { key: 'users', label: 'Users & Roles', icon: '👤' },
      { key: 'settings', label: 'Settings', icon: '⚙️' },
    ],
  },
];

const Icon = ({ name }) => {
  const icons = {
    rupee: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 3h12M6 8h12M6 13l9 8M6 13H5l8-5H6"/></svg>,
    upload: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>,
    refresh: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>,
    logout: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>,
    filter: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>,
    file: <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>,
    check: <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>,
    spark: <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>,
  };
  return icons[name] || null;
};

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

function toCsv(rows) {
  if (!Array.isArray(rows) || !rows.length) return '';
  const headers = Array.from(rows.reduce((acc, r) => { Object.keys(r || {}).forEach((k) => acc.add(k)); return acc; }, new Set()));
  const esc = (v) => {
    if (v === null || v === undefined) return '';
    const s = String(v).replace(/"/g, '""');
    return /[",\n\r]/.test(s) ? `"${s}"` : s;
  };
  const lines = [headers.map(esc).join(',')];
  for (const r of rows) {
    lines.push(headers.map((h) => esc(r?.[h])).join(','));
  }
  return lines.join('\r\n');
}

async function apiRequest(path, token, options = {}, returnBlob = false) {
  const headers = { ...(options.headers || {}) };
  if (!returnBlob) headers.Accept = 'application/json';

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

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem('nexus_token');
      localStorage.removeItem('nexus_role');
      window.dispatchEvent(new CustomEvent('nexus:unauthorized'));
    }
    let detail = 'Request failed';
    try {
      const ct = response.headers.get('content-type') || '';
      const p = ct.includes('application/json') ? await response.json() : await response.text();
      detail = typeof p === 'string' ? p : p?.detail || p?.message || 'Request failed';
    } catch { /* ignore */ }
    throw new Error(detail);
  }

  if (returnBlob) {
    return await response.blob();
  }

  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();

  return payload;
}

function auditLog(action, status = 'success', extra = {}) {
  try {
    const existing = JSON.parse(localStorage.getItem('nexus_audit') || '[]');
    const entry = {
      timestamp: new Date().toISOString(),
      actor: localStorage.getItem('nexus_role') || 'Viewer',
      action,
      status,
      ...extra,
    };
    existing.push(entry);
    localStorage.setItem('nexus_audit', JSON.stringify(existing.slice(-500)));
  } catch (e) {
    // non-breaking
  }
}

const defaultFilters = { region: '', city: '', category: '', customer_segment: '', year: '' };

const VIEW_LABELS = {
  overview: 'Overview',
  segments: 'Segment Analysis',
  sales: 'Sales Analytics',
  customers: 'Customers',
  risk: 'Returns & Risk',
  recommendations: 'Recommendations',
  quality: 'Data Quality',
  profitability: 'Profitability',
  products: 'Product Analytics',
  custintel: 'Customer Intelligence',
  geographic: 'Geographic Analysis',
  forecast: 'Sales Forecast',
  anomalies: 'Anomaly Detection',
  advisor: 'AI Business Advisor',
  custpred: 'Customer Prediction',
  database: 'Database',
  dataimport: 'Data Import',
  export: 'Export & Reports',
  audit: 'Audit Logs',
  users: 'Users & Roles',
  settings: 'Settings',
};

const buildQuery = (filters) => {
  const params = new URLSearchParams();
  if (filters.region) params.set('region', filters.region);
  if (filters.city) params.set('city', filters.city);
  if (filters.category) params.set('category', filters.category);
  if (filters.customer_segment) params.set('customer_segment', filters.customer_segment);
  if (filters.year) params.set('year', filters.year);
  return params.toString() ? `?${params.toString()}` : '';
};

function playSmsChime() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, ctx.currentTime);
    osc.frequency.setValueAtTime(880, ctx.currentTime + 0.09);
    gain.gain.setValueAtTime(0.12, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.38);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.39);
  } catch (e) {
    // Non-blocking
  }
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('nexus_token') || '');
  const [role, setRole] = useState(localStorage.getItem('nexus_role') || 'Viewer');
  const [activeView, setActiveView] = useState('overview');
  const [filters, setFilters] = useState(defaultFilters);
  const [meta, setMeta] = useState({ regions: [], categories: [], cities: [], customer_segments: [], years: [] });
  const [dashboard, setDashboard] = useState({
    kpis: {},
    trend: [],
    categoryPerformance: [],
    topProducts: [],
    topCustomers: [],
    recommendations: [],
    quality: {},
    dailyReport: { summary: {} },
    anomalies: [],
    advisor: null,
    custpred: null,
    dbstatus: null,
  });
  const [segments, setSegments] = useState({
    regions: [],
    cities: [],
    categories: [],
    customer_segments: [],
    category_region_matrix: [],
    totals: {},
  });
  const [segmentFocusMode, setSegmentFocusMode] = useState('auto');
  const [tableDimension, setTableDimension] = useState('regions');
  const [baseLoading, setBaseLoading] = useState(false);
  const [viewLoading, setViewLoading] = useState(false);
  const [status, setStatus] = useState('Ready');
  const [dataVersion, setDataVersion] = useState(0);
  const [viewLoadedAt, setViewLoadedAt] = useState({});
  const [viewRefresh, setViewRefresh] = useState({});
  const [loginForm, setLoginForm] = useState({ email: 'demo@example.com', password: 'demo-password' });
  const [authStatus, setAuthStatus] = useState({ type: '', message: '' });

  const [authLoading, setAuthLoading] = useState(false);
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
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState({ type: '', message: '' });
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const [salesModalOpen, setSalesModalOpen] = useState(false);
  const [salesModalTab, setSalesModalTab] = useState('create');
  const [salesRecords, setSalesRecords] = useState([]);
  const [salesTotal, setSalesTotal] = useState(0);
  const [salesLoading, setSalesLoading] = useState(false);
  const [salesSearch, setSalesSearch] = useState('');
  const [salesPage, setSalesPage] = useState(0);
  const [salesPageSize] = useState(8);
  const [refreshingAll, setRefreshingAll] = useState(false);
  const [salesActionStatus, setSalesActionStatus] = useState({ type: '', message: '' });
  const [saleSubmitting, setSaleSubmitting] = useState(false);
  const [saleLookupId, setSaleLookupId] = useState('');
  const [saleLookupLoading, setSaleLookupLoading] = useState(false);
  const [forecastCompare, setForecastCompare] = useState(null);
  const [forecastModel, setForecastModel] = useState('RandomForest');
  const [syncStatus, setSyncStatus] = useState({ type: '', message: '' });
  const [usersList, setUsersList] = useState(null);
  const [usersEdit, setUsersEdit] = useState({});
  const [inviteForm, setInviteForm] = useState({ email: '', password: '', role: 'Viewer' });
  const [usersSaving, setUsersSaving] = useState({});
  const [inviteSubmitting, setInviteSubmitting] = useState(false);
  const [appSettings, setAppSettings] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('nexus_settings') || '{}') || { theme: 'dark', forecastHorizon: 7 };
    } catch {
      return { theme: 'dark', forecastHorizon: 7 };
    }
  });
  const [healthInfo, setHealthInfo] = useState(null);

  useEffect(() => {
    if (typeof document !== 'undefined') {
      const theme = appSettings?.theme || 'dark';
      document.body.setAttribute('data-theme', theme);
      document.documentElement.setAttribute('data-theme', theme);
    }
  }, [appSettings?.theme]);

  const defaultSaleForm = useMemo(() => {
    const today = new Date();
    return {
      order_id: '',
      order_date: `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`,
      customer_id: 'CUST01001',
      customer_segment: 'Regular',
      product_name: 'Wireless Bluetooth Earbuds',
      product_category: 'Electronics',
      quantity: 1,
      unit_price: 1899,
      discount_pct: 10,
      sales: 1709.1,
      profit: 512.73,
      payment_method: 'Credit Card',
      region: 'North',
      city: 'Delhi',
      order_status: 'Delivered',
    };
  }, []);

  const [saleForm, setSaleForm] = useState(defaultSaleForm);

  const updateSaleFormField = (field, val) => {
    setSaleForm((prev) => {
      const next = { ...prev, [field]: val };
      if (field === 'quantity' || field === 'unit_price' || field === 'discount_pct') {
        const q = Math.max(1, Number(field === 'quantity' ? val : prev.quantity) || 1);
        const p = Math.max(0, Number(field === 'unit_price' ? val : prev.unit_price) || 0);
        const d = Math.max(0, Math.min(100, Number(field === 'discount_pct' ? val : prev.discount_pct) || 0));
        const gross = q * p;
        const discountAmt = gross * (d / 100);
        const calculatedSales = Math.round((gross - discountAmt) * 100) / 100;
        const calculatedProfit = Math.round(calculatedSales * 0.3 * 100) / 100;
        next.sales = calculatedSales;
        next.profit = calculatedProfit;
      }
      return next;
    });
  };

  const loadSalesRecords = async (page = salesPage, search = salesSearch) => {
    if (!token) return;
    try {
      setSalesLoading(true);
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (filters.region) params.append('region', filters.region);
      if (filters.city) params.append('city', filters.city);
      if (filters.category) params.append('category', filters.category);
      if (filters.year) params.append('year', filters.year);
      params.append('limit', String(salesPageSize));
      params.append('offset', String(page * salesPageSize));
      const res = await apiRequest(`/api/sales/records?${params.toString()}`, token);
      setSalesRecords(res.records || []);
      setSalesTotal(res.total || 0);
    } catch (err) {
      console.error('Failed to load sales records:', err);
    } finally {
      setSalesLoading(false);
    }
  };

  const lookupOrderForUpdate = async (idToSearch) => {
    const id = (idToSearch || saleLookupId).trim();
    if (!id) return;
    setSaleLookupLoading(true);
    setSalesActionStatus({ type: '', message: '' });
    try {
      const res = await apiRequest(`/api/sales/records?search=${encodeURIComponent(id)}&limit=1`, token);
      if (res.records && res.records.length > 0) {
        const found = res.records.find((r) => r.order_id.toLowerCase() === id.toLowerCase()) || res.records[0];
        setSaleForm({
          order_id: found.order_id,
          order_date: found.order_date,
          customer_id: found.customer_id,
          customer_segment: found.customer_segment || 'Regular',
          product_name: found.product_name,
          product_category: found.category,
          quantity: found.quantity || 1,
          unit_price: found.unit_price || (found.sales / (found.quantity || 1)),
          discount_pct: found.discount_pct || 0,
          sales: found.sales || 0,
          profit: found.profit || Math.round(found.sales * 0.3 * 100) / 100,
          payment_method: found.payment_method || 'Credit Card',
          region: found.region || 'North',
          city: found.city || 'Mumbai',
          order_status: found.order_status || 'Delivered',
        });
        setSalesActionStatus({ type: 'info', message: `Order ${found.order_id} loaded. Make your updates below and save.` });
      } else {
        setSalesActionStatus({ type: 'error', message: `Order "${id}" not found in dataset.` });
      }
    } catch (err) {
      setSalesActionStatus({ type: 'error', message: err.message || 'Lookup failed' });
    } finally {
      setSaleLookupLoading(false);
    }
  };

  const handleEditRecord = (record) => {
    setSaleForm({
      order_id: record.order_id,
      order_date: record.order_date,
      customer_id: record.customer_id,
      customer_segment: record.customer_segment || 'Regular',
      product_name: record.product_name,
      product_category: record.category,
      quantity: record.quantity || 1,
      unit_price: record.unit_price || (record.sales / (record.quantity || 1)),
      discount_pct: record.discount_pct || 0,
      sales: record.sales || 0,
      profit: record.profit || Math.round(record.sales * 0.3 * 100) / 100,
      payment_method: record.payment_method || 'Credit Card',
      region: record.region || 'North',
      city: record.city || 'Mumbai',
      order_status: record.order_status || 'Delivered',
    });
    setSaleLookupId(record.order_id);
    setSalesModalTab('update');
    setSalesActionStatus({ type: '', message: '' });
    setSalesModalOpen(true);
  };

  const handleDeleteRecord = async (orderId) => {
    if (!window.confirm(`Are you sure you want to delete order ${orderId}? This cannot be undone.`)) return;
    try {
      await apiRequest(`/api/sales/records/${encodeURIComponent(orderId)}`, token, { method: 'DELETE' });
      setDataVersion((v) => v + 1);
      loadSalesRecords(salesPage, salesSearch);
      setStatus(`Order ${orderId} deleted successfully`);
      auditLog('delete_record', 'success', { order_id: orderId });
    } catch (err) {
      setStatus(`Failed to delete order: ${err.message}`);
      auditLog('delete_record', 'error', { order_id: orderId, error: err.message });
    }
  };

  const handleSaveSale = async (e) => {
    e.preventDefault();
    setSaleSubmitting(true);
    setSalesActionStatus({ type: '', message: '' });
    try {
      const isUpdate = salesModalTab === 'update';
      const orderId = saleForm.order_id?.trim();
      if (isUpdate && !orderId) {
        throw new Error('Please specify an Order ID to update.');
      }

      const payload = {
        order_id: orderId || undefined,
        order_date: saleForm.order_date,
        customer_id: saleForm.customer_id,
        customer_segment: saleForm.customer_segment,
        product_name: saleForm.product_name,
        product_category: saleForm.product_category,
        quantity: Number(saleForm.quantity) || 1,
        unit_price: Number(saleForm.unit_price) || 0,
        discount_pct: Number(saleForm.discount_pct) || 0,
        sales: Number(saleForm.sales) || undefined,
        profit: Number(saleForm.profit) || undefined,
        payment_method: saleForm.payment_method,
        region: saleForm.region,
        city: saleForm.city,
        order_status: saleForm.order_status,
      };

      let res;
      if (isUpdate) {
        res = await apiRequest(`/api/sales/records/${encodeURIComponent(orderId)}`, token, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
      } else {
        res = await apiRequest('/api/sales/records', token, {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      }

      setSalesActionStatus({
        type: 'success',
        message: res.message || (isUpdate ? 'Sale updated successfully!' : 'Sale created successfully!'),
      });
      setDataVersion((v) => v + 1);
      loadSalesRecords(0, salesSearch);
      setTimeout(() => {
        setSalesModalOpen(false);
        setSalesActionStatus({ type: '', message: '' });
      }, 1400);
    } catch (err) {
      setSalesActionStatus({
        type: 'error',
        message: err.message || 'Operation failed. Please check inputs.',
      });
    } finally {
      setSaleSubmitting(false);
    }
  };

  const handleRefreshAll = async () => {
    if (refreshingAll || !token) return;
    setRefreshingAll(true);
    setStatus('Refreshing all sales datasets and neural models…');
    try {
      const res = await apiRequest('/api/sales/refresh', token, { method: 'POST' });
      setDataVersion((v) => v + 1);
      loadSalesRecords(0, '');
      setStatus(res.message || 'All sales data refreshed!');
    } catch (err) {
      setStatus(`Refresh failed: ${err.message}`);
    } finally {
      setRefreshingAll(false);
    }
  };


  const authenticated = Boolean(token);
  const loading = baseLoading || viewLoading;
  const activeFilterCount = [filters.region, filters.city, filters.category, filters.customer_segment, filters.year].filter(Boolean).length;
  const cacheKey = useMemo(() => JSON.stringify(filters) + '|' + dataVersion, [filters, dataVersion]);
  const viewKey = useMemo(() => cacheKey + '|v' + (viewRefresh[activeView] || 0), [cacheKey, viewRefresh, activeView]);
  const isViewFresh = viewLoadedAt[activeView] === viewKey;

  useEffect(() => {
    const handleUnauthorized = () => {
      setToken('');
      setRole('Viewer');
      setLoginError('Session expired. Please sign in again.');
    };
    window.addEventListener('nexus:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('nexus:unauthorized', handleUnauthorized);
  }, []);

  useEffect(() => {
    if (!authenticated) return;

    const loadBase = async () => {
      try {
        setBaseLoading(true);
        setStatus('Loading filters & KPIs…');
        const query = buildQuery(filters);
        const [kpisData, qualityData] = await Promise.all([
          apiRequest(`/api/dashboard/kpis${query}`, token),
          apiRequest('/api/data/quality', token),
        ]);
        setDashboard((prev) => ({
          ...prev,
          kpis: kpisData.kpis || {},
          quality: qualityData || {},
        }));
        setMeta((prev) => ({
          ...prev,
          regions: kpisData.filters?.regions || [],
          categories: kpisData.filters?.categories || [],
          cities: kpisData.filters?.cities || [],
          customer_segments: kpisData.filters?.customer_segments || ['Loyal', 'New', 'Returning'],
        }));
        setViewLoadedAt({});
        setStatus('Filters ready · choose a section below');
      } catch (error) {
        setStatus(error.message || 'Unable to load base data');
      } finally {
        setBaseLoading(false);
      }
    };

    loadBase();
  }, [authenticated, token, filters, dataVersion]);

  useEffect(() => {
    if (!authenticated) return;
    if (isViewFresh) {
      setStatus(`${VIEW_LABELS[activeView] || activeView} · already loaded`);
      return;
    }

    const loadView = async () => {
      try {
        setViewLoading(true);
        setStatus(`Loading ${VIEW_LABELS[activeView] || activeView}…`);
        const query = buildQuery(filters);

        switch (activeView) {
          case 'overview': {
            const [trendData, categoryData, productsData] = await Promise.all([
              apiRequest(`/api/sales/trend${query}`, token),
              apiRequest(`/api/sales/category${query}`, token),
              apiRequest(`/api/products/top${query}`, token),
            ]);
            setDashboard((prev) => ({
              ...prev,
              trend: trendData || [],
              categoryPerformance: categoryData || [],
              topProducts: productsData || [],
            }));
            setMeta((prev) => {
              const years = Array.from(
                new Set((trendData || []).map((item) => String(item.Month || '').slice(0, 4)).filter(Boolean)),
              ).sort();
              return { ...prev, years: years.length ? years : prev.years };
            });
            break;
          }
          case 'segments': {
            setStatus('Computing segment calculations + charts for current filters…');
            const data = await apiRequest(`/api/segments/breakdown${query}`, token);
            setSegments({
              regions: data?.regions || [],
              cities: data?.cities || [],
              categories: data?.categories || [],
              customer_segments: data?.customer_segments || [],
              category_region_matrix: data?.category_region_matrix || [],
              totals: data?.totals || {},
            });
            break;
          }
          case 'sales': {
            const recParams = new URLSearchParams();
            if (filters.region) recParams.set('region', filters.region);
            if (filters.city) recParams.set('city', filters.city);
            if (filters.category) recParams.set('category', filters.category);
            if (filters.year) recParams.set('year', filters.year);
            recParams.set('limit', String(salesPageSize));
            recParams.set('offset', String(salesPage * salesPageSize));

            const [trendData, categoryData, productsData, recordsData] = await Promise.all([
              apiRequest(`/api/sales/trend${query}`, token),
              apiRequest(`/api/sales/category${query}`, token),
              apiRequest(`/api/products/top${query}`, token),
              apiRequest(`/api/sales/records?${recParams.toString()}`, token).catch(() => ({ records: [], total: 0 })),
            ]);
            setDashboard((prev) => ({
              ...prev,
              trend: trendData || [],
              categoryPerformance: categoryData || [],
              topProducts: productsData || [],
            }));
            if (recordsData) {
              setSalesRecords(recordsData.records || []);
              setSalesTotal(recordsData.total || 0);
            }
            setMeta((prev) => {
              const years = Array.from(
                new Set((trendData || []).map((item) => String(item.Month || '').slice(0, 4)).filter(Boolean)),
              ).sort();
              return { ...prev, years: years.length ? years : prev.years };
            });
            break;
          }
          case 'customers': {
            const customersData = await apiRequest(`/api/customers/top${query}`, token);
            setDashboard((prev) => ({ ...prev, topCustomers: customersData || [] }));
            break;
          }
          case 'risk': {
            const dailyReportData = await apiRequest(`/api/sales/daily/report${query}`, token);
            setDashboard((prev) => ({ ...prev, dailyReport: dailyReportData || { summary: {} } }));
            break;
          }
          case 'recommendations': {
            const recommendationData = await apiRequest('/api/recommendations', token);
            setDashboard((prev) => ({ ...prev, recommendations: recommendationData || [] }));
            break;
          }
          case 'quality': {
            const qualityData = await apiRequest('/api/data/quality', token).catch(() => null);
            setDashboard((prev) => ({ ...prev, quality: qualityData || prev.quality || {} }));
            break;
          }
          case 'profitability':
          case 'custintel': {
            const [segData, custData, catData, trendData] = await Promise.all([
              apiRequest(`/api/segments/breakdown${query}`, token).catch(() => null),
              apiRequest(`/api/customers/top${query}`, token).catch(() => []),
              apiRequest(`/api/sales/category${query}`, token).catch(() => []),
              apiRequest(`/api/sales/trend${query}`, token).catch(() => []),
            ]);
            if (segData) {
              setSegments({
                regions: segData.regions || [],
                cities: segData.cities || [],
                categories: segData.categories || [],
                customer_segments: segData.customer_segments || [],
                category_region_matrix: segData.category_region_matrix || [],
                totals: segData.totals || {},
              });
            }
            setDashboard((prev) => ({
              ...prev,
              topCustomers: custData || [],
              categoryPerformance: catData || [],
              trend: trendData || [],
            }));
            break;
          }
          case 'products':
          case 'geographic': {
            const [prodData, segData] = await Promise.all([
              apiRequest(`/api/products/top${query}`, token).catch(() => []),
              apiRequest(`/api/segments/breakdown${query}`, token).catch(() => null),
            ]);
            setDashboard((prev) => ({ ...prev, topProducts: prodData || [] }));
            if (segData) {
              setSegments({
                regions: segData.regions || [],
                cities: segData.cities || [],
                categories: segData.categories || [],
                customer_segments: segData.customer_segments || [],
                category_region_matrix: segData.category_region_matrix || [],
                totals: segData.totals || {},
              });
            }
            break;
          }
          case 'forecast': {
            if (forecastModel === 'Compare') {
              const horizon = appSettings.forecastHorizon || 7;
              const sep = query ? '&' : '?';
              const cmp = await apiRequest(`/api/sales/daily/forecast/compare${query}${query ? '&' : '?'}days=${horizon}`, token).catch(() => null);
              setForecastCompare(cmp);
              setSalesForecast(null);
            } else {
              const horizon = appSettings.forecastHorizon || 7;
              const modelParam = forecastModel === 'XGBoost' ? 'xgboost' : 'randomforest';
              const fc = await apiRequest(`/api/sales/daily/forecast?horizon=${horizon}&model=${modelParam}${query.replace('?', '&')}`, token).catch(() => null);
              setSalesForecast(fc);
              setForecastCompare(null);
            }
            break;
          }
          case 'anomalies': {
            const anom = await apiRequest(`/api/sales/anomalies${query}`, token).catch(() => null);
            setDashboard((prev) => ({ ...prev, anomalies: anom?.anomalies || [], anomalySeries: anom?.daily_series || [] }));
            break;
          }
          case 'advisor': {
            const adv = await apiRequest('/api/ai/advisor', token).catch(() => null);
            setDashboard((prev) => ({ ...prev, advisor: adv }));
            break;
          }
          case 'custpred': {
            const cp = await apiRequest(`/api/customers/rfm${query}`, token).catch(() => null);
            setDashboard((prev) => ({ ...prev, custpred: cp }));
            break;
          }
          case 'database': {
            const [st, hl] = await Promise.all([
              apiRequest('/api/db/status', token).catch(() => null),
              apiRequest('/api/health', token).catch(() => null),
            ]);
            setDashboard((prev) => ({ ...prev, dbstatus: st }));
            setHealthInfo(hl);
            break;
          }
          case 'users': {
            if (role === 'Admin' || role === 'Business Manager') {
              const ul = await apiRequest('/api/management/users', token).catch(() => null);
              setUsersList(ul);
            }
            break;
          }
          case 'settings': {
            const [st, hl] = await Promise.all([
              apiRequest('/api/db/status', token).catch(() => null),
              apiRequest('/api/health', token).catch(() => null),
            ]);
            setDashboard((prev) => ({ ...prev, dbstatus: st }));
            setHealthInfo(hl);
            break;
          }
        }

        setViewLoadedAt((prev) => ({ ...prev, [activeView]: viewKey }));
        setStatus(`${VIEW_LABELS[activeView] || activeView} ready`);
      } catch (error) {
        setStatus(error.message || `Unable to load ${VIEW_LABELS[activeView] || activeView}`);
      } finally {
        setViewLoading(false);
      }
    };

    loadView();
  }, [authenticated, token, activeView, viewKey, isViewFresh]);

  const refreshCurrentView = () => {
    setViewRefresh((prev) => ({ ...prev, [activeView]: (prev[activeView] || 0) + 1 }));
  };

  const salesTrend = useMemo(() => {
    const labels = (dashboard.trend || []).map((point) => String(point.Month || '').slice(0, 7));
    const values = (dashboard.trend || []).map((point) => Number(point.sales || 0));
    return {
      labels,
      datasets: [{
        label: 'Net sales',
        data: values,
        borderColor: '#ff6b35',
        borderWidth: 3,
        backgroundColor: (ctx) => {
          const { chart: { ctx: c, chartArea } } = ctx;
          if (!chartArea) return 'rgba(255,107,53,0.18)';
          const gradient = c.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
          gradient.addColorStop(0, 'rgba(255,107,53,0.0)');
          gradient.addColorStop(0.5, 'rgba(255,107,53,0.18)');
          gradient.addColorStop(1, 'rgba(130,88,255,0.45)');
          return gradient;
        },
        tension: 0.42,
        fill: true,
        pointRadius: 3.5,
        pointHoverRadius: 7,
        pointBackgroundColor: '#fff',
        pointBorderColor: '#ff6b35',
        pointBorderWidth: 2,
      }],
    };
  }, [dashboard.trend]);

  const categoryChart = useMemo(() => {
    const top = (dashboard.categoryPerformance || []).slice(0, 7);
    const palette = ['#ff6b35', '#8258ff', '#00c2a8', '#ffc857', '#5b8def', '#ff7ab6', '#7fbf3f'];
    return {
      labels: top.map((item) => item.Category || 'Unknown'),
      datasets: [{
        label: 'Sales',
        data: top.map((item) => Number(item.sales || 0)),
        backgroundColor: palette,
        borderRadius: 10,
        borderSkipped: false,
      }],
    };
  }, [dashboard.categoryPerformance]);

  const categoryPieChart = useMemo(() => ({
    labels: categoryChart.labels,
    datasets: [{
      label: 'Sales mix',
      data: categoryChart.datasets[0].data,
      backgroundColor: categoryChart.datasets[0].backgroundColor,
      borderColor: 'transparent',
      borderWidth: 6,
      hoverOffset: 14,
    }],
  }), [categoryChart]);

  const qualityMetrics = useMemo(() => {
    const q = dashboard.quality || {};
    const records = Number(q.records || 0);
    const columns = Number(q.columns || 0);
    const totalCells = records * columns;
    const completeness = q.completeness != null ? Number(q.completeness) : totalCells > 0 ? (1 - Number(q.missing_values || 0) / totalCells) * 100 : 0;
    const uniqueness = q.uniqueness != null ? Number(q.uniqueness) : records > 0 ? (1 - Number(q.duplicate_rows || 0) / records) * 100 : 0;
    const dateValidity = q.date_validity != null ? Number(q.date_validity) : q.invalid_dates != null && records > 0 ? (1 - Number(q.invalid_dates || 0) / records) * 100 : q.date_min && q.date_max ? 100 : 0;
    const score = q.quality_score != null ? Number(q.quality_score) : (completeness + uniqueness + dateValidity) / 3;
    return {
      available: records > 0 && columns > 0,
      completeness: Math.max(0, Math.min(100, completeness)),
      uniqueness: Math.max(0, Math.min(100, uniqueness)),
      dateValidity: Math.max(0, Math.min(100, dateValidity)),
      score: Math.max(0, Math.min(100, score)),
    };
  }, [dashboard.quality]);

  const qualityBreakdown = useMemo(() => {
    const chunks = [
      { label: 'Completeness', value: qualityMetrics.completeness, color: '#00c2a8' },
      { label: 'Unique records', value: qualityMetrics.uniqueness, color: '#5b8def' },
      { label: 'Valid dates', value: qualityMetrics.dateValidity, color: '#ff6b35' },
    ];
    return {
      labels: chunks.map((item) => item.label),
      datasets: [{
        data: chunks.map((item) => item.value),
        backgroundColor: chunks.map((item) => item.color),
        borderRadius: 8,
      }],
    };
  }, [qualityMetrics]);

  const doughnutData = useMemo(() => ({
    labels: qualityBreakdown.labels,
    datasets: [{
      data: qualityBreakdown.datasets[0].data,
      backgroundColor: qualityBreakdown.datasets[0].backgroundColor,
      borderWidth: 0,
      hoverOffset: 12,
      cutout: '70%',
    }],
  }), [qualityBreakdown]);

  const chartOpts = (type = 'line') => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: { intersect: false, mode: type === 'line' ? 'index' : 'nearest' },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(14, 21, 32, 0.94)',
        titleColor: '#fff',
        bodyColor: '#cdd7e3',
        borderColor: 'rgba(255,255,255,0.08)',
        borderWidth: 1,
        padding: 12,
        cornerRadius: 10,
        titleFont: { size: 13, weight: '600' },
        callbacks: {
          label: (ctx) => type === 'category'
            ? ` Sales: ${formatCurrency(ctx.parsed.y ?? ctx.parsed)}`
            : type === 'pie'
              ? ` ${ctx.label}: ${formatCurrency(ctx.parsed)}`
              : ` Net sales: ${formatCurrency(ctx.parsed.y)}`,
        },
      },
    },
    scales: type === 'line' || type === 'bar' ? {
      x: {
        grid: { color: 'rgba(255,255,255,0.04)' },
        ticks: { color: '#8fa2b6', maxRotation: 0, autoSkip: true, maxTicksLimit: 10, font: { size: 11 } },
        border: { display: false },
      },
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(255,255,255,0.04)' },
        ticks: {
          color: '#8fa2b6',
          font: { size: 11 },
          callback: (value) => formatCurrency(value),
        },
        border: { display: false },
      },
    } : undefined,
  });

  const forecastChartData = useMemo(() => {
    const predictions = salesForecast?.forecast || [];
    return {
      labels: [salesForecast?.latest_observed_date, ...predictions.map((item) => item.date)],
      datasets: [
        {
          label: 'Actual sales',
          data: [Number(salesForecast?.today_sales || 0), ...predictions.map(() => null)],
          borderColor: '#5b8def',
          backgroundColor: '#5b8def',
          pointRadius: 8,
          pointHoverRadius: 12,
          showLine: false,
          pointStyle: 'rectRot',
        },
        {
          label: 'Predicted sales',
          data: [Number(salesForecast?.today_sales || 0), ...predictions.map((item) => Number(item.predicted_sales || 0))],
          borderColor: '#ff6b35',
          backgroundColor: 'rgba(255,107,53,0.12)',
          borderDash: [7, 5],
          tension: 0.35,
          borderWidth: 3,
          fill: false,
          pointRadius: 4,
        },
      ],
    };
  }, [salesForecast]);

  const forecastChartOptions = {
    ...chartOpts('line'),
    plugins: {
      ...chartOpts('line').plugins,
      legend: { display: true, position: 'top', align: 'end', labels: { color: '#b8c6d6', usePointStyle: true, pointStyle: 'circle', boxWidth: 8, font: { size: 12 }, padding: 18 } },
    },
  };

  const doughnutOpts = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '70%',
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(14, 21, 32, 0.94)',
        padding: 12,
        cornerRadius: 10,
        callbacks: { label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toFixed(1)}%` },
      },
    },
  };

  const handleLogin = async (event) => {
    event.preventDefault();
    setAuthLoading(true);
    setLoginError('');
    setAuthStatus({ type: '', message: '' });
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
      auditLog('login', 'success', { email: loginForm.email, role: result.role || 'Viewer' });
    } catch (error) {
      setLoginError(error.message?.includes('Failed to fetch') || error.message?.includes('ECONNREFUSED')
        ? 'Cannot reach backend. Start the backend server first.'
        : error.message || 'Unable to sign in');
      auditLog('login', 'error', { email: loginForm.email, error: error.message || 'Unable to sign in' });
    } finally {
      setAuthLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('nexus_token');
    localStorage.removeItem('nexus_role');
    setToken('');
    setRole('Viewer');
    setFilters(defaultFilters);
  };

  const runDailyForecast = async (event) => {
    event.preventDefault();
    if (!forecastDate) { setForecastError('Select the date to forecast from.'); return; }
    setForecastLoading(true);
    setForecastError('');
    try {
      const params = new URLSearchParams({ date: forecastDate, days: String(forecastDays) });
      if (forecastSalesInput !== '') params.set('sales', forecastSalesInput);
      if (forecastModel && forecastModel !== 'Compare') params.set('model', forecastModel === 'XGBoost' ? 'xgboost' : 'randomforest');
      const result = await apiRequest(`/api/sales/daily/forecast?${params}`, token);
      setSalesForecast(result);
      if (!(result.forecast || []).length) setForecastError(result.basis || 'No forecast available for this date.');
    } catch (error) {
      setForecastError(error.message || 'Unable to calculate forecast');
      setSalesForecast(null);
    } finally {
      setForecastLoading(false);
    }
  };

  const handleAdminAction = async (endpoint, method, payload, successText) => {
    try {
      const response = await apiRequest(endpoint, token, { method, body: payload ? JSON.stringify(payload) : undefined });
      setStatus(`${response.status || 'done'}: ${response.name || successText}`);
      setAdminForm({ region: '', category: '' });
    } catch (error) {
      setStatus(error.message || 'Admin action failed');
    }
  };

  const handleFilePick = (files) => {
    const file = files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadStatus({ type: 'error', message: 'Please upload a CSV file only.' });
      return;
    }
    setUploadFile(file);
    setUploadStatus({ type: '', message: '' });
  };

  const handleUpload = async () => {
    if (!uploadFile) {
      setUploadStatus({ type: 'error', message: 'Select a CSV file first.' });
      return;
    }
    setUploading(true);
    setUploadStatus({ type: 'info', message: 'Uploading dataset… please wait.' });
    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      const result = await apiRequest('/api/data/upload', token, {
        method: 'POST',
        body: formData,
      });
      setUploadStatus({
        type: 'success',
        message: `✅ Uploaded "${result.filename}" successfully. Reloading dashboard…`,
      });
      setUploadFile(null);
      setDataVersion((v) => v + 1);
      setTimeout(() => {
        setUploadStatus({ type: '', message: '' });
      }, 2800);
      auditLog('data_upload', 'success', { filename: result.filename || uploadFile.name, size: uploadFile.size });
    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error.message || 'Upload failed. Only Admins can upload data.',
      });
      auditLog('data_upload', 'error', { filename: uploadFile.name, error: error.message || 'Upload failed' });
    } finally {
      setUploading(false);
    }
  };

  const kpiGradient = (i) => {
    const gradients = [
      'linear-gradient(135deg, #ff6b35 0%, #f7931e 50%, #ffc857 100%)',
      'linear-gradient(135deg, #8258ff 0%, #5b8def 50%, #00c2a8 100%)',
      'linear-gradient(135deg, #00c2a8 0%, #7fbf3f 50%, #c4e85e 100%)',
      'linear-gradient(135deg, #ff4081 0%, #ff7ab6 50%, #f7b8d4 100%)',
    ];
    return gradients[i % gradients.length];
  };

  const overviewCards = [
    { label: 'Net Sales Revenue', value: formatCurrency(dashboard.kpis.sales), suffix: 'Total revenue', icon: 'rupee' },
    { label: dashboard.quality.profit_is_estimated ? 'Estimated Profit' : 'Net Profit', value: formatCurrency(dashboard.kpis.profit), suffix: dashboard.quality.profit_is_estimated ? '30% margin estimate' : 'Gross profit', icon: 'rupee' },
    { label: 'Total Orders', value: formatNumber(dashboard.kpis.orders), suffix: 'Unique purchase orders', icon: 'rupee' },
    { label: 'Unique Customers', value: formatNumber(dashboard.kpis.customers), suffix: 'Active shopper base', icon: 'rupee' },
  ];

  const regionBarChart = useMemo(() => {
    const regs = segments.regions || [];
    return {
      labels: regs.map((r) => r.Region || 'Unknown'),
      datasets: [
        {
          label: 'Sales (₹)',
          data: regs.map((r) => Number(r.sales || 0)),
          backgroundColor: 'rgba(255, 107, 53, 0.88)',
          borderRadius: 10,
          borderSkipped: false,
          order: 2,
        },
        {
          label: 'Profit (₹)',
          data: regs.map((r) => Number(r.profit || 0)),
          backgroundColor: 'rgba(0, 194, 168, 0.88)',
          borderRadius: 10,
          borderSkipped: false,
          order: 1,
        },
      ],
    };
  }, [segments.regions]);

  const regionDonutChart = useMemo(() => {
    const palette = ['#ff6b35', '#8258ff', '#00c2a8', '#ffc857', '#5b8def', '#ff7ab6', '#7fbf3f', '#c27a00'];
    const regs = segments.regions || [];
    return {
      labels: regs.map((r) => `${r.Region || 'Unknown'} — ${formatPercent(r.market_share_pct)}`),
      datasets: [{
        label: 'Market Share',
        data: regs.map((r) => Number(r.sales || 0)),
        backgroundColor: palette.slice(0, Math.max(regs.length, 1)),
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 4,
        hoverOffset: 14,
      }],
    };
  }, [segments.regions]);

  const topCitiesBarChart = useMemo(() => {
    const cities = (segments.cities || []).slice(0, 10);
    const palette = ['#8258ff', '#5b8def', '#00c2a8', '#ffc857', '#ff6b35', '#ff7ab6', '#7fbf3f', '#c27a00', '#00a2c7', '#b664ff'];
    return {
      labels: cities.map((c) => `${c.City || 'Unknown'}, ${c.Region || ''}`.replace(/,\s*$/, '')),
      datasets: [{
        label: 'Sales (₹)',
        data: cities.map((c) => Number(c.sales || 0)),
        backgroundColor: palette,
        borderRadius: 10,
        borderSkipped: false,
      }],
    };
  }, [segments.cities]);

  const categoryBarChart = useMemo(() => {
    const cats = segments.categories || [];
    const palette = ['#ff6b35', '#8258ff', '#00c2a8', '#ffc857', '#5b8def', '#ff7ab6', '#7fbf3f', '#00a2c7', '#b664ff', '#c27a00'];
    return {
      labels: cats.map((c) => c.Category || 'Unknown'),
      datasets: [
        {
          label: 'Sales',
          data: cats.map((c) => Number(c.sales || 0)),
          backgroundColor: 'rgba(255,107,53,0.9)',
          borderRadius: 10,
          borderSkipped: false,
          order: 2,
        },
        {
          label: 'Profit',
          data: cats.map((c) => Number(c.profit || 0)),
          backgroundColor: 'rgba(130,88,255,0.88)',
          borderRadius: 10,
          borderSkipped: false,
          order: 1,
        },
      ],
    };
  }, [segments.categories]);

  const categoryDonut = useMemo(() => {
    const cats = segments.categories || [];
    const palette = ['#ff6b35', '#8258ff', '#00c2a8', '#ffc857', '#5b8def', '#ff7ab6', '#7fbf3f', '#00a2c7', '#b664ff', '#c27a00'];
    return {
      labels: cats.map((c) => `${c.Category || 'Unknown'} — ${formatPercent(c.market_share_pct)}`),
      datasets: [{
        label: 'Revenue mix',
        data: cats.map((c) => Number(c.sales || 0)),
        backgroundColor: palette,
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 4,
        hoverOffset: 14,
      }],
    };
  }, [segments.categories]);

  const customerSegmentBarChart = useMemo(() => {
    const segs = segments.customer_segments || [];
    return {
      labels: segs.map((s) => s.Segment || 'Unknown'),
      datasets: [
        {
          label: 'Sales (₹)',
          data: segs.map((s) => Number(s.sales || 0)),
          backgroundColor: 'rgba(130, 88, 255, 0.88)',
          borderRadius: 10,
          borderSkipped: false,
          order: 2,
        },
        {
          label: 'Profit (₹)',
          data: segs.map((s) => Number(s.profit || 0)),
          backgroundColor: 'rgba(0, 194, 168, 0.88)',
          borderRadius: 10,
          borderSkipped: false,
          order: 1,
        },
      ],
    };
  }, [segments.customer_segments]);

  const customerSegmentDonutChart = useMemo(() => {
    const segs = segments.customer_segments || [];
    const palette = ['#8258ff', '#00c2a8', '#ff6b35', '#ffc857', '#5b8def'];
    return {
      labels: segs.map((s) => `${s.Segment || 'Unknown'} — ${formatPercent(s.market_share_pct)}`),
      datasets: [{
        label: 'Customer Mix',
        data: segs.map((s) => Number(s.sales || 0)),
        backgroundColor: palette.slice(0, Math.max(segs.length, 1)),
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 4,
        hoverOffset: 14,
      }],
    };
  }, [segments.customer_segments]);

  const heatmapMatrix = useMemo(() => {
    const rows = {};
    (segments.category_region_matrix || []).forEach((cell) => {
      const cat = String(cell.Category || 'Unknown');
      const reg = String(cell.Region || 'Unknown');
      rows[cat] = rows[cat] || {};
      rows[cat][reg] = {
        sales: Number(cell.sales || 0),
        profit: Number(cell.profit || 0),
        margin_pct: Number(cell.margin_pct || 0),
        return_pct: Number(cell.return_pct || 0),
        intensity: Number(cell.intensity || 0),
        orders: Number(cell.orders || 0),
      };
    });
    const categoryOrder = (segments.categories || []).map((c) => c.Category).filter(Boolean);
    const regionOrder = (segments.regions || []).map((r) => r.Region).filter(Boolean);
    return { rows, categoryOrder, regionOrder };
  }, [segments.category_region_matrix, segments.categories, segments.regions]);

  const renderView = () => {
    if (viewLoading && !isViewFresh) {
      const counts = {
        overview: { charts: 3, tables: 1 },
        segments: { charts: 2, tables: 1 },
        sales: { charts: 3, tables: 2 },
        customers: { charts: 0, tables: 1 },
        risk: { charts: 0, tables: 2 },
        recommendations: { charts: 0, tables: 0 },
        quality: { charts: 2, tables: 0 },
        profitability: { charts: 3, tables: 2 },
        products: { charts: 3, tables: 1 },
        custintel: { charts: 2, tables: 1 },
        geographic: { charts: 2, tables: 2 },
        forecast: { charts: 2, tables: 1 },
        anomalies: { charts: 1, tables: 1 },
        advisor: { charts: 0, tables: 0 },
        custpred: { charts: 1, tables: 1 },
        database: { charts: 1, tables: 0 },
        dataimport: { charts: 0, tables: 0 },
        export: { charts: 0, tables: 0 },
        audit: { charts: 0, tables: 1 },
        users: { charts: 0, tables: 1 },
        settings: { charts: 0, tables: 0 },
      };
      const c = counts[activeView] || { charts: 2, tables: 1 };
      return <ViewSkeleton charts={c.charts} tables={c.tables} />;
    }
    switch (activeView) {
      case 'segments': {
        // Automatic dimension detection from active filters
        const activeFocus = (() => {
          if (segmentFocusMode && segmentFocusMode !== 'auto') {
            return segmentFocusMode;
          }
          const hasCategory = Boolean(filters.category);
          const hasRegion = Boolean(filters.region);
          const hasCity = Boolean(filters.city);
          const hasCustSeg = Boolean(filters.customer_segment);

          if ((hasCategory && hasRegion) || (hasCategory && hasCity) || (hasRegion && hasCustSeg)) {
            return 'cross';
          }
          if (hasCategory) return 'categories';
          if (hasRegion) return 'regions';
          if (hasCity) return 'cities';
          if (hasCustSeg) return 'customer_segments';
          return 'all';
        })();

        const activeMeta = {
          all: {
            title: 'Comprehensive Segment Intelligence',
            badge: '🧭 ALL SEGMENTS DASHBOARD',
            desc: 'Consolidated performance across all geographies, product categories, and customer tiers.',
          },
          regions: {
            title: filters.region ? `Region Deep Dive: ${filters.region}` : 'Geographic Regions Breakdown',
            badge: filters.region ? '⚡ AUTO-SWITCHED: REGION FOCUS' : '🌏 REGION BREAKDOWN',
            desc: filters.region
              ? `Performance, category mix, and city metrics specifically for the ${filters.region} region.`
              : 'Sales, profit, margin %, and market share per geography.',
          },
          cities: {
            title: filters.city ? `City / Place Deep Dive: ${filters.city}` : 'Top Cities Breakdown',
            badge: filters.city ? '⚡ AUTO-SWITCHED: CITY FOCUS' : '🏙️ CITY / PLACE BREAKDOWN',
            desc: filters.city
              ? `Performance and category demand within ${filters.city}.`
              : 'Cities ranked by revenue, volume, and customer reach.',
          },
          categories: {
            title: filters.category ? `Category Deep Dive: ${filters.category}` : 'Product Category Breakdown',
            badge: filters.category ? '⚡ AUTO-SWITCHED: CATEGORY FOCUS' : '🛒 CATEGORY BREAKDOWN',
            desc: filters.category
              ? `Geographic distribution, top buyer cities, and margin profile for ${filters.category}.`
              : 'Product-category breakdowns, profit margins, and revenue mix.',
          },
          customer_segments: {
            title: filters.customer_segment ? `Customer Segment: ${filters.customer_segment}` : 'Customer Segment Breakdown',
            badge: filters.customer_segment ? '⚡ AUTO-SWITCHED: CUSTOMER SEGMENT' : '👥 CUSTOMER SEGMENT BREAKDOWN',
            desc: filters.customer_segment
              ? `Spending patterns, category preferences, and regional spread for ${filters.customer_segment} customers.`
              : 'Comparison between Loyal, New, and Returning customer segments.',
          },
          cross: {
            title: `Cross-Segment Intersection: ${[filters.region, filters.city, filters.category, filters.customer_segment].filter(Boolean).join(' × ')}`,
            badge: '🎯 CROSS-SEGMENT INTERSECTION',
            desc: 'Filtered cross-section metrics and localized performance calculations.',
          },
          matrix: {
            title: 'Category × Region Matrix Heatmap',
            badge: '🎯 CROSS-SEGMENT HEATMAP',
            desc: 'Cross-segment intensity, margin %, and returns matrix.',
          },
        }[activeFocus] || {
          title: 'Segment Analysis',
          badge: '🧭 SEGMENT INTELLIGENCE',
          desc: 'Live segment calculations and visual analytics.',
        };

        const totals = segments.totals || {};
        const effectiveRegionOrder = (segments.regions || []).map((r) => r.Region).filter(Boolean);
        const effectiveCategoryOrder = (segments.categories || []).map((c) => c.Category).filter(Boolean);

        return (
          <div className="content-grid">
            {/* Dynamic Hero Panel reflecting Filter Selection */}
            <section className="panel wide hero-panel segment-hero">
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> {activeMeta.badge}</div>
                  <h1 className="hero-title">{activeMeta.title}</h1>
                  <p className="hero-subtitle">
                    {activeMeta.desc}
                    {Object.keys(filters).some((k) => Boolean(filters[k])) && (
                      <span className="active-filter-chips">
                        <span className="muted small">Filters applied:</span>
                        {filters.region && (
                          <span className="filter-chip">
                            Region: <strong>{filters.region}</strong>
                            <button className="filter-chip-remove" onClick={() => setFilters((p) => ({ ...p, region: '', city: '' }))} title="Remove filter">×</button>
                          </span>
                        )}
                        {filters.city && (
                          <span className="filter-chip">
                            City: <strong>{filters.city}</strong>
                            <button className="filter-chip-remove" onClick={() => setFilters((p) => ({ ...p, city: '' }))} title="Remove filter">×</button>
                          </span>
                        )}
                        {filters.category && (
                          <span className="filter-chip">
                            Category: <strong>{filters.category}</strong>
                            <button className="filter-chip-remove" onClick={() => setFilters((p) => ({ ...p, category: '' }))} title="Remove filter">×</button>
                          </span>
                        )}
                        {filters.customer_segment && (
                          <span className="filter-chip">
                            Segment: <strong>{filters.customer_segment}</strong>
                            <button className="filter-chip-remove" onClick={() => setFilters((p) => ({ ...p, customer_segment: '' }))} title="Remove filter">×</button>
                          </span>
                        )}
                        {filters.year && (
                          <span className="filter-chip">
                            Year: <strong>{filters.year}</strong>
                            <button className="filter-chip-remove" onClick={() => setFilters((p) => ({ ...p, year: '' }))} title="Remove filter">×</button>
                          </span>
                        )}
                      </span>
                    )}
                  </p>
                  <div className="hero-stats">
                    <div>
                      <strong>{formatCurrency(totals?.sales)}</strong>
                      <span>Total Revenue</span>
                    </div>
                    <div className="divider" />
                    <div>
                      <strong>{formatPercent(totals?.margin_pct)}</strong>
                      <span>Profit Margin</span>
                    </div>
                    <div className="divider" />
                    <div>
                      <strong>{formatNumber(totals?.orders)}</strong>
                      <span>Total Orders</span>
                    </div>
                    <div className="divider" />
                    <div>
                      <strong>{formatCurrency(totals?.aov)}</strong>
                      <span>Avg Order Value</span>
                    </div>
                    <div className="divider" />
                    <div>
                      <strong>{formatPercent(totals?.return_pct)}</strong>
                      <span>Return Rate</span>
                    </div>
                  </div>
                </div>
                <div className="hero-chart hero-segment-summary">
                  <div className="segment-summary-card">
                    <div className="summary-orb" />
                    <div>
                      <div className="summary-label">Live Calculation Scope</div>
                      <div className="summary-row"><span>Active Focus</span><strong style={{ color: '#ff6b35' }}>{activeFocus.toUpperCase()}</strong></div>
                      <div className="summary-row"><span>Customers</span><strong>{formatNumber(totals?.customers)}</strong></div>
                      <div className="summary-row"><span>Units Sold</span><strong>{formatNumber(totals?.quantity)}</strong></div>
                      <div className="summary-row"><span>Total Profit</span><strong style={{ color: '#00c2a8' }}>{formatCurrency(totals?.profit)}</strong></div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* View Mode 1: CATEGORY FOCUS */}
            {activeFocus === 'categories' && (
              <>
                <section className="panel wide">
                  <div className="panel-head">
                    <div>
                      <div className="panel-eyebrow">CATEGORY FOCUS · {filters.category || 'ALL CATEGORIES'}</div>
                      <h2>🛒 Regional Performance for {filters.category || 'Category'}</h2>
                      <p className="panel-subtitle">Revenue and profit generation across different geographic regions for your selected category.</p>
                    </div>
                  </div>
                  <div className="segment-charts-row">
                    <div className="chart-frame wide-chart"><Bar data={regionBarChart} options={chartOpts('bar')} /></div>
                    <div className="chart-frame donut-chart"><Doughnut data={regionDonutChart} options={doughnutOpts} /></div>
                  </div>
                </section>

                <section className="panel wide">
                  <div className="panel-head">
                    <div>
                      <div className="panel-eyebrow">TOP BUYER LOCATIONS · {filters.category || 'ALL'}</div>
                      <h2>🏙️ Top Cities Purchasing {filters.category || 'This Category'}</h2>
                      <p className="panel-subtitle">Locations delivering the highest volume and revenue for this product segment.</p>
                    </div>
                  </div>
                  <div className="chart-frame tall"><Bar data={topCitiesBarChart} options={{ ...chartOpts('bar'), indexAxis: 'y' }} /></div>
                </section>
              </>
            )}

            {/* View Mode 2: REGION FOCUS */}
            {activeFocus === 'regions' && (
              <>
                <section className="panel wide">
                  <div className="panel-head">
                    <div>
                      <div className="panel-eyebrow">REGION PERFORMANCE · {filters.region || 'ALL REGIONS'}</div>
                      <h2>🌏 Product Category Demand in {filters.region || 'Region'}</h2>
                      <p className="panel-subtitle">How different product categories perform in revenue, profit, and margin in this geographic zone.</p>
                    </div>
                  </div>
                  <div className="segment-charts-row">
                    <div className="chart-frame wide-chart"><Bar data={categoryBarChart} options={chartOpts('bar')} /></div>
                    <div className="chart-frame donut-chart"><Doughnut data={categoryDonut} options={doughnutOpts} /></div>
                  </div>
                </section>

                <section className="panel wide">
                  <div className="panel-head">
                    <div>
                      <div className="panel-eyebrow">HUB CITIES · {filters.region || 'ALL'}</div>
                      <h2>🏙️ Top Revenue Cities in {filters.region || 'Region'}</h2>
                      <p className="panel-subtitle">Highest volume hubs within this geographic territory.</p>
                    </div>
                  </div>
                  <div className="chart-frame tall"><Bar data={topCitiesBarChart} options={{ ...chartOpts('bar'), indexAxis: 'y' }} /></div>
                </section>
              </>
            )}

            {/* View Mode 3: CITY FOCUS */}
            {activeFocus === 'cities' && (
              <>
                <section className="panel wide">
                  <div className="panel-head">
                    <div>
                      <div className="panel-eyebrow">CITY BREAKDOWN · {filters.city}</div>
                      <h2>🏙️ Category & Customer Segment Breakdown in {filters.city}</h2>
                      <p className="panel-subtitle">Product demand and customer tier distributions for this specific location.</p>
                    </div>
                  </div>
                  <div className="segment-charts-row">
                    <div className="chart-frame wide-chart"><Bar data={categoryBarChart} options={chartOpts('bar')} /></div>
                    <div className="chart-frame donut-chart"><Doughnut data={customerSegmentDonutChart} options={doughnutOpts} /></div>
                  </div>
                </section>
              </>
            )}

            {/* View Mode 4: CUSTOMER SEGMENT FOCUS */}
            {activeFocus === 'customer_segments' && (
              <>
                <section className="panel wide">
                  <div className="panel-head">
                    <div>
                      <div className="panel-eyebrow">CUSTOMER SEGMENT ANALYSIS · {filters.customer_segment || 'ALL TIERS'}</div>
                      <h2>👥 Sales & Profit by Customer Segment</h2>
                      <p className="panel-subtitle">Revenue contribution, margins, and order frequency across Loyal, New, and Returning tiers.</p>
                    </div>
                  </div>
                  <div className="segment-charts-row">
                    <div className="chart-frame wide-chart"><Bar data={customerSegmentBarChart} options={chartOpts('bar')} /></div>
                    <div className="chart-frame donut-chart"><Doughnut data={customerSegmentDonutChart} options={doughnutOpts} /></div>
                  </div>
                </section>

                <section className="panel wide">
                  <div className="panel-head">
                    <div>
                      <div className="panel-eyebrow">PRODUCT PREFERENCES · {filters.customer_segment || 'ALL'}</div>
                      <h2>🛒 What {filters.customer_segment || 'Customers'} Buy Most</h2>
                      <p className="panel-subtitle">Category preferences and revenue spread for this customer group.</p>
                    </div>
                  </div>
                  <div className="chart-frame wide-chart"><Bar data={categoryBarChart} options={chartOpts('bar')} /></div>
                </section>
              </>
            )}

            {/* View Mode 5: CROSS-FILTER INTERSECTION */}
            {activeFocus === 'cross' && (
              <>
                <section className="panel wide">
                  <div className="panel-head">
                    <div>
                      <div className="panel-eyebrow">CROSS-SEGMENT INTERSECTION</div>
                      <h2>🎯 Multi-Filter Scoped Performance</h2>
                      <p className="panel-subtitle">Detailed breakdown across categories and hub cities for your exact filtered intersection.</p>
                    </div>
                  </div>
                  <div className="segment-charts-row">
                    <div className="chart-frame wide-chart"><Bar data={categoryBarChart} options={chartOpts('bar')} /></div>
                    <div className="chart-frame donut-chart"><Doughnut data={regionDonutChart} options={doughnutOpts} /></div>
                  </div>
                </section>

                <section className="panel wide">
                  <div className="panel-head">
                    <div>
                      <div className="panel-eyebrow">HUB RANKINGS</div>
                      <h2>🏙️ Top Cities in Filter Scope</h2>
                    </div>
                  </div>
                  <div className="chart-frame tall"><Bar data={topCitiesBarChart} options={{ ...chartOpts('bar'), indexAxis: 'y' }} /></div>
                </section>
              </>
            )}

            {/* View Mode 6: ALL SEGMENTS OVERVIEW (Default when no filter is selected) */}
            {activeFocus === 'all' && (
              <>
                <section className="panel wide">
                  <div className="panel-head">
                    <div>
                      <div className="panel-eyebrow">GEOGRAPHIC PERFORMANCE</div>
                      <h2>🌏 Sales & Profit by Region</h2>
                      <p className="panel-subtitle">Top-line revenue compared with bottom-line profit and overall regional market share.</p>
                    </div>
                  </div>
                  <div className="segment-charts-row">
                    <div className="chart-frame wide-chart"><Bar data={regionBarChart} options={chartOpts('bar')} /></div>
                    <div className="chart-frame donut-chart"><Doughnut data={regionDonutChart} options={doughnutOpts} /></div>
                  </div>
                </section>

                <section className="panel wide">
                  <div className="panel-head">
                    <div>
                      <div className="panel-eyebrow">PRODUCT PERFORMANCE</div>
                      <h2>🛒 Sales & Profit by Product Category</h2>
                      <p className="panel-subtitle">Revenue generation and margins across product categories.</p>
                    </div>
                  </div>
                  <div className="segment-charts-row">
                    <div className="chart-frame wide-chart"><Bar data={categoryBarChart} options={chartOpts('bar')} /></div>
                    <div className="chart-frame donut-chart"><Doughnut data={categoryDonut} options={doughnutOpts} /></div>
                  </div>
                </section>

                <section className="panel wide">
                  <div className="panel-head">
                    <div>
                      <div className="panel-eyebrow">CITY RANKINGS & CUSTOMER TIERS</div>
                      <h2>🏙️ Top Cities & Customer Mix</h2>
                      <p className="panel-subtitle">Leading geographical commerce hubs and customer segment revenue distribution.</p>
                    </div>
                  </div>
                  <div className="segment-charts-row">
                    <div className="chart-frame wide-chart"><Bar data={topCitiesBarChart} options={{ ...chartOpts('bar'), indexAxis: 'y' }} /></div>
                    <div className="chart-frame donut-chart"><Doughnut data={customerSegmentDonutChart} options={doughnutOpts} /></div>
                  </div>
                </section>
              </>
            )}

            {/* CROSS-SEGMENT MATRIX HEATMAP (Shown in 'all', 'cross', or 'matrix' modes) */}
            {(activeFocus === 'all' || activeFocus === 'cross' || activeFocus === 'matrix') && effectiveRegionOrder.length > 0 && effectiveCategoryOrder.length > 0 && (
              <section className="panel wide">
                <div className="panel-head">
                  <div>
                    <div className="panel-eyebrow">CATEGORY × REGION CROSS-SEGMENT HEATMAP</div>
                    <h2>🎯 Cross-Segment Performance Matrix</h2>
                    <p className="panel-subtitle">Color intensity indicates sales volume in each category-region intersection. Hover cell for live margins and returns.</p>
                  </div>
                </div>
                <div className="table-wrap">
                  <table className="heatmap-table">
                    <thead>
                      <tr>
                        <th className="heatmap-corner">Category × Region</th>
                        {effectiveRegionOrder.map((reg) => <th key={`th-${reg}`}>{reg}</th>)}
                        <th className="heatmap-total-col">Category Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {effectiveCategoryOrder.map((cat, i) => {
                        const rowTotal = (segments.categories || []).find((x) => x.Category === cat);
                        return (
                          <tr key={`hmr-${cat}`}>
                            <td className="heatmap-rowlabel"><span className="rank-badge mini" style={{ background: kpiGradient(i) }}>{i + 1}</span> <strong>{cat}</strong></td>
                            {effectiveRegionOrder.map((reg) => {
                              const cell = heatmapMatrix.rows[cat]?.[reg];
                              const intensity = cell ? Number(cell.intensity) : 0;
                              const sales = cell ? Number(cell.sales) : 0;
                              const margin = cell ? Number(cell.margin_pct) : 0;
                              const ret = cell ? Number(cell.return_pct) : 0;
                              const orders = cell ? Number(cell.orders) : 0;
                              return (
                                <td key={`${cat}-${reg}`} className="heatmap-cell" title={`${cat} in ${reg}\nSales: ${formatCurrency(sales)}\nOrders: ${formatNumber(orders)}\nMargin: ${formatPercent(margin)}\nReturn: ${formatPercent(ret)}`}
                                    style={{
                                      background: `linear-gradient(135deg, rgba(255,107,53,${0.12 + intensity * 0.72}) 0%, rgba(130,88,255,${0.08 + intensity * 0.58}) 100%)`,
                                      outline: intensity > 0.35 ? '1px solid rgba(255,255,255,0.22)' : 'none',
                                    }}>
                                  {cell ? (
                                    <div className="heatmap-inner">
                                      <strong>{formatCurrency(sales)}</strong>
                                      <span className="heatmap-sub">{orders > 0 ? `${formatNumber(orders)} orders` : ''}</span>
                                      <span className="heatmap-meta">
                                        <em style={{ color: '#00c2a8' }}>{formatPercent(margin)}</em>
                                        <em style={{ color: ret > 10 ? '#ff6b35' : '#ffc857' }}>↩{formatPercent(ret)}</em>
                                      </span>
                                    </div>
                                  ) : <span className="heatmap-empty">—</span>}
                                </td>
                              );
                            })}
                            <td className="heatmap-total-col">
                              <strong>{formatCurrency(rowTotal?.sales)}</strong>
                              <div className="share-bar"><div style={{ width: `${Math.min(100, Number(rowTotal?.market_share_pct || 0))}%`, background: kpiGradient(i + 2) }} /></div>
                              <span className={'score-pill small ' + (Number(rowTotal?.margin_pct) > 25 ? 'good' : Number(rowTotal?.margin_pct) > 10 ? 'ok' : 'low')}>{formatPercent(rowTotal?.margin_pct)}</span>
                            </td>
                          </tr>
                        );
                      })}
                      <tr className="heatmap-totalrow">
                        <td className="heatmap-rowlabel"><strong>Region Total</strong></td>
                        {effectiveRegionOrder.map((reg, i) => {
                          const r = (segments.regions || []).find((x) => x.Region === reg);
                          return (
                            <td key={`tm-${reg}`} style={{ background: 'rgba(255,255,255,0.04)' }}>
                              <strong>{formatCurrency(r?.sales)}</strong>
                              <div className="share-bar"><div style={{ width: `${Math.min(100, Number(r?.market_share_pct || 0))}%`, background: kpiGradient(i + 3) }} /></div>
                              <span className={'score-pill small ' + (Number(r?.margin_pct) > 25 ? 'good' : Number(r?.margin_pct) > 10 ? 'ok' : 'low')}>{formatPercent(r?.margin_pct)}</span>
                            </td>
                          );
                        })}
                        <td className="heatmap-total-col grand"><strong>{formatCurrency(totals?.sales)}</strong><span className={'score-pill small ' + (Number(totals?.margin_pct) > 25 ? 'good' : Number(totals?.margin_pct) > 10 ? 'ok' : 'low')}>{formatPercent(totals?.margin_pct)}</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {/* DETAILED SEGMENT CALCULATIONS TABLE WITH DIMENSION SWITCHER */}
            <section className="panel wide">
              <div className="panel-head">
                <div>
                  <div className="panel-eyebrow">DETAILED CALCULATIONS & FINANCIAL METRICS</div>
                  <h2>📋 Segment Performance Breakdown Table</h2>
                  <p className="panel-subtitle">Comprehensive mathematical calculations (Sales, Profit, Profit Margin %, AOV, Units/Order, Return Rate, Market Share) computed live for your filter scope.</p>
                </div>
                <div className="table-dimension-pills">
                  <button
                    className={`table-dim-pill ${(tableDimension === 'regions' || activeFocus === 'regions') && tableDimension !== 'categories' && tableDimension !== 'cities' && tableDimension !== 'customer_segments' ? 'active' : ''}`}
                    onClick={() => setTableDimension('regions')}
                  >
                    🌏 By Region
                  </button>
                  <button
                    className={`table-dim-pill ${tableDimension === 'categories' || (activeFocus === 'categories' && tableDimension === 'regions') ? 'active' : ''}`}
                    onClick={() => setTableDimension('categories')}
                  >
                    🛒 By Category
                  </button>
                  <button
                    className={`table-dim-pill ${tableDimension === 'cities' || (activeFocus === 'cities' && tableDimension === 'regions') ? 'active' : ''}`}
                    onClick={() => setTableDimension('cities')}
                  >
                    🏙️ By City
                  </button>
                  <button
                    className={`table-dim-pill ${tableDimension === 'customer_segments' || (activeFocus === 'customer_segments' && tableDimension === 'regions') ? 'active' : ''}`}
                    onClick={() => setTableDimension('customer_segments')}
                  >
                    👥 By Customer Segment
                  </button>
                </div>
              </div>

              {/* Regions Table */}
              {((tableDimension === 'regions' && activeFocus !== 'categories' && activeFocus !== 'cities' && activeFocus !== 'customer_segments') || (tableDimension === 'regions' && activeFocus === 'all')) && (
                <div className="table-wrap">
                  <table className="styled-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Region</th>
                        <th>Sales</th>
                        <th>Profit</th>
                        <th>Margin</th>
                        <th>Orders</th>
                        <th>AOV</th>
                        <th>Market Share</th>
                        <th>Return %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(segments.regions || []).map((r, i) => (
                        <tr key={`r-${r.Region}`}>
                          <td><span className="rank-badge mini" style={{ background: kpiGradient(i) }}>{i + 1}</span></td>
                          <td><strong>{r.Region || 'Unknown'}</strong><small>{formatNumber(r.customers)} customers · {formatNumber(r.quantity)} units</small></td>
                          <td>{formatCurrency(r.sales)}</td>
                          <td style={{ color: '#00c2a8' }}>{formatCurrency(r.profit)}</td>
                          <td><span className={'score-pill ' + (Number(r.margin_pct) > 25 ? 'good' : Number(r.margin_pct) > 10 ? 'ok' : 'low')}>{formatPercent(r.margin_pct)}</span></td>
                          <td>{formatNumber(r.orders)}</td>
                          <td>{formatCurrency(r.aov)}</td>
                          <td>
                            <div className="share-row">
                              <strong>{formatPercent(r.market_share_pct)}</strong>
                              <div className="share-bar"><div style={{ width: `${Math.min(100, Number(r.market_share_pct))}%`, background: kpiGradient(i) }} /></div>
                            </div>
                          </td>
                          <td><span className={'risk-chip ' + (Number(r.return_pct) > 12 ? 'high' : Number(r.return_pct) > 6 ? 'mid' : '')}>{formatPercent(r.return_pct)}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Categories Table */}
              {(tableDimension === 'categories' || (activeFocus === 'categories' && tableDimension === 'regions')) && (
                <div className="table-wrap">
                  <table className="styled-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Category</th>
                        <th>Sales</th>
                        <th>Profit</th>
                        <th>Margin</th>
                        <th>Orders</th>
                        <th>AOV</th>
                        <th>Revenue Share</th>
                        <th>Return %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(segments.categories || []).map((c, i) => (
                        <tr key={`cat-${c.Category}`}>
                          <td><span className="rank-badge mini" style={{ background: kpiGradient(i) }}>{i + 1}</span></td>
                          <td><strong>{c.Category || 'Unknown'}</strong><small>{formatNumber(c.quantity)} units · {formatNumber(c.customers)} buyers</small></td>
                          <td>{formatCurrency(c.sales)}</td>
                          <td style={{ color: '#8258ff' }}>{formatCurrency(c.profit)}</td>
                          <td><span className={'score-pill ' + (Number(c.margin_pct) > 25 ? 'good' : Number(c.margin_pct) > 10 ? 'ok' : 'low')}>{formatPercent(c.margin_pct)}</span></td>
                          <td>{formatNumber(c.orders)}</td>
                          <td>{formatCurrency(c.aov)}</td>
                          <td>
                            <div className="share-row">
                              <strong>{formatPercent(c.market_share_pct)}</strong>
                              <div className="share-bar"><div style={{ width: `${Math.min(100, Number(c.market_share_pct))}%`, background: kpiGradient(i + 1) }} /></div>
                            </div>
                          </td>
                          <td><span className={'risk-chip ' + (Number(c.return_pct) > 12 ? 'high' : Number(c.return_pct) > 6 ? 'mid' : '')}>{formatPercent(c.return_pct)}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Cities Table */}
              {(tableDimension === 'cities' || (activeFocus === 'cities' && tableDimension === 'regions')) && (
                <div className="table-wrap">
                  <table className="styled-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>City</th>
                        <th>Region</th>
                        <th>Sales</th>
                        <th>Margin</th>
                        <th>Orders</th>
                        <th>AOV</th>
                        <th>Units / Order</th>
                        <th>Return %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(segments.cities || []).slice(0, 30).map((c, i) => (
                        <tr key={`c-${c.Region}-${c.City}`}>
                          <td><span className="rank-badge mini" style={{ background: kpiGradient(i) }}>{i + 1}</span></td>
                          <td><strong>{c.City || 'Unknown'}</strong></td>
                          <td><span className="city-region">{c.Region || '-'}</span></td>
                          <td>{formatCurrency(c.sales)}</td>
                          <td><span className={'score-pill ' + (Number(c.margin_pct) > 25 ? 'good' : Number(c.margin_pct) > 10 ? 'ok' : 'low')}>{formatPercent(c.margin_pct)}</span></td>
                          <td>{formatNumber(c.orders)}</td>
                          <td>{formatCurrency(c.aov)}</td>
                          <td>{Number(c.units_per_order || 0).toFixed(2)}</td>
                          <td><span className={'risk-chip ' + (Number(c.return_pct) > 12 ? 'high' : Number(c.return_pct) > 6 ? 'mid' : '')}>{formatPercent(c.return_pct)}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Customer Segments Table */}
              {(tableDimension === 'customer_segments' || (activeFocus === 'customer_segments' && tableDimension === 'regions')) && (
                <div className="table-wrap">
                  <table className="styled-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Customer Segment</th>
                        <th>Sales</th>
                        <th>Profit</th>
                        <th>Margin</th>
                        <th>Orders</th>
                        <th>Customers</th>
                        <th>AOV</th>
                        <th>Market Share</th>
                        <th>Return %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(segments.customer_segments || []).map((s, i) => (
                        <tr key={`cs-${s.Segment}`}>
                          <td><span className="rank-badge mini" style={{ background: kpiGradient(i) }}>{i + 1}</span></td>
                          <td><strong>{s.Segment || 'Unknown'}</strong></td>
                          <td>{formatCurrency(s.sales)}</td>
                          <td style={{ color: '#00c2a8' }}>{formatCurrency(s.profit)}</td>
                          <td><span className={'score-pill ' + (Number(s.margin_pct) > 25 ? 'good' : Number(s.margin_pct) > 10 ? 'ok' : 'low')}>{formatPercent(s.margin_pct)}</span></td>
                          <td>{formatNumber(s.orders)}</td>
                          <td>{formatNumber(s.customers)}</td>
                          <td>{formatCurrency(s.aov)}</td>
                          <td>
                            <div className="share-row">
                              <strong>{formatPercent(s.market_share_pct)}</strong>
                              <div className="share-bar"><div style={{ width: `${Math.min(100, Number(s.market_share_pct))}%`, background: kpiGradient(i) }} /></div>
                            </div>
                          </td>
                          <td><span className={'risk-chip ' + (Number(s.return_pct) > 12 ? 'high' : Number(s.return_pct) > 6 ? 'mid' : '')}>{formatPercent(s.return_pct)}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </div>
        );
      }
      case 'sales':
        return (
          <div className="content-grid">
            {/* Sales Management & Live Records Operations Panel */}
            <section className="panel wide sales-management-panel">
              <div className="panel-head">
                <div>
                  <div className="panel-eyebrow" style={{ color: '#00c2a8' }}>DATA OPERATIONS & LIVE RECORDS</div>
                  <h2>Sales Data Management</h2>
                  <p className="panel-subtitle">Record new sales transactions, modify existing orders, or sync and recalculate all pipeline statistics.</p>
                </div>
                <div className="sales-head-actions">
                  <button
                    className="primary-cta small"
                    onClick={() => {
                      setSalesModalTab('create');
                      setSaleForm(defaultSaleForm);
                      setSalesActionStatus({ type: '', message: '' });
                      setSalesModalOpen(true);
                    }}
                  >
                    ➕ Record New Sale
                  </button>
                  <button
                    className="secondary-cta small"
                    onClick={() => {
                      setSalesModalTab('update');
                      setSalesActionStatus({ type: '', message: '' });
                      setSalesModalOpen(true);
                    }}
                  >
                    ✏️ Update Existing Sale
                  </button>
                  <button
                    className="secondary-cta small"
                    onClick={handleRefreshAll}
                    disabled={refreshingAll}
                    title="Reloads CSV dataset and updates all models"
                  >
                    <span className={refreshingAll ? 'icon-spin spinning' : ''}>⚡</span> {refreshingAll ? 'Recalculating…' : 'Update & Refresh All'}
                  </button>
                </div>
              </div>

              {/* Table search & count controls */}
              <div className="sales-table-controls">
                <div className="sales-search-wrap">
                  <span className="search-icon">🔍</span>
                  <input
                    type="text"
                    placeholder="Search by Order ID, customer, product, city…"
                    value={salesSearch}
                    onChange={(e) => setSalesSearch(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        setSalesPage(0);
                        loadSalesRecords(0, salesSearch);
                      }
                    }}
                  />
                  <button
                    className="action-btn-pill small"
                    style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                    onClick={() => {
                      setSalesPage(0);
                      loadSalesRecords(0, salesSearch);
                    }}
                  >
                    Search
                  </button>
                </div>
                <div className="sales-count-badge">
                  Total Transactions: <strong>{formatNumber(salesTotal)}</strong>
                </div>
              </div>

              {/* Interactive Records Table */}
              <div className="table-wrap">
                <table className="styled-table compact">
                  <thead>
                    <tr>
                      <th>Order ID</th>
                      <th>Date</th>
                      <th>Customer</th>
                      <th>Product</th>
                      <th>Category</th>
                      <th>Region / City</th>
                      <th>Qty</th>
                      <th>Sales Amount</th>
                      <th>Discount</th>
                      <th>Profit</th>
                      <th>Status</th>
                      <th style={{ textAlign: 'center' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {salesLoading ? (
                      <tr>
                        <td colSpan="12" style={{ textAlign: 'center', padding: '24px' }}>
                          <span className="icon-spin spinning" style={{ marginRight: 8 }}>⏳</span> Loading live sales records…
                        </td>
                      </tr>
                    ) : salesRecords.length === 0 ? (
                      <tr>
                        <td colSpan="12" style={{ textAlign: 'center', padding: '24px', color: 'var(--muted)' }}>
                          No sales records matching your query. Click <strong>"➕ Record New Sale"</strong> to add one!
                        </td>
                      </tr>
                    ) : (
                      salesRecords.map((item) => (
                        <tr key={item.order_id}>
                          <td><strong>{item.order_id}</strong></td>
                          <td>{item.order_date}</td>
                          <td>
                            <div>{item.customer_id}</div>
                            {item.customer_name && item.customer_name !== item.customer_id && (
                              <div className="muted small">{item.customer_name}</div>
                            )}
                          </td>
                          <td>
                            <strong>{item.product_name}</strong>
                          </td>
                          <td><span className="badge-chip">{item.category}</span></td>
                          <td>{item.region} · {item.city}</td>
                          <td>{item.quantity}</td>
                          <td><strong style={{ color: '#ffc857' }}>{formatCurrency(item.sales)}</strong></td>
                          <td>{item.discount_pct}%</td>
                          <td style={{ color: '#00c2a8' }}>{formatCurrency(item.profit)}</td>
                          <td>
                            <span className={`badge-status ${(item.order_status || 'delivered').toLowerCase()}`}>
                              {item.order_status || 'Delivered'}
                            </span>
                          </td>
                          <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                            <button
                              className="edit-row-btn"
                              title="Update this sale record"
                              onClick={() => handleEditRecord(item)}
                            >
                              ✏️ Edit
                            </button>
                            <button
                              className="del-row-btn"
                              title="Delete record"
                              onClick={() => handleDeleteRecord(item.order_id)}
                            >
                              🗑️
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination bar */}
              <div className="sales-pagination">
                <span>
                  Showing {salesTotal === 0 ? 0 : salesPage * salesPageSize + 1} -{' '}
                  {Math.min((salesPage + 1) * salesPageSize, salesTotal)} of {formatNumber(salesTotal)} orders
                </span>
                <div className="pagination-actions">
                  <button
                    className="pagination-btn"
                    disabled={salesPage === 0 || salesLoading}
                    onClick={() => {
                      const nextP = salesPage - 1;
                      setSalesPage(nextP);
                      loadSalesRecords(nextP, salesSearch);
                    }}
                  >
                    ← Previous
                  </button>
                  <button
                    className="pagination-btn"
                    disabled={(salesPage + 1) * salesPageSize >= salesTotal || salesLoading}
                    onClick={() => {
                      const nextP = salesPage + 1;
                      setSalesPage(nextP);
                      loadSalesRecords(nextP, salesSearch);
                    }}
                  >
                    Next →
                  </button>
                </div>
              </div>
            </section>

            <section className="panel wide">
              <div className="panel-head">
                <div><div className="panel-eyebrow">MOMENTUM</div><h2>Monthly Net Sales Trend</h2><p className="panel-subtitle">{dashboard.trend.length} months of historical performance</p></div>
                <span className="badge-good">{formatCurrency(dashboard.kpis.sales)} TOTAL</span>
              </div>
              <div className="chart-frame tall"><Line data={salesTrend} options={chartOpts('line')} /></div>
            </section>

            <section className="panel">
              <div className="panel-head">
                <div><div className="panel-eyebrow">CATEGORY</div><h2>Top Categories by Sales</h2></div>
              </div>
              <div className="chart-frame"><Bar data={categoryChart} options={chartOpts('bar')} /></div>
            </section>

            <section className="panel">
              <div className="panel-head">
                <div><div className="panel-eyebrow">COMPOSITION</div><h2>Sales Mix Share</h2></div>
              </div>
              <div className="chart-frame"><Doughnut data={categoryPieChart} options={doughnutOpts} /></div>
              <div className="legend-grid">
                {categoryPieChart.labels.map((label, i) => (
                  <div key={label} className="legend-chip">
                    <span className="legend-dot" style={{ backgroundColor: categoryPieChart.datasets[0].backgroundColor[i] }} />
                    {label}
                  </div>
                ))}
              </div>
            </section>

            <section className="panel">
              <div className="panel-head"><div className="panel-eyebrow">BEST SELLERS</div><h2>Top Products</h2></div>
              <div className="table-wrap">
                <table className="styled-table compact">
                  <thead><tr><th>Product</th><th>Revenue</th><th>Units</th></tr></thead>
                  <tbody>
                    {(dashboard.topProducts || []).slice(0, 5).map((item, i) => (
                      <tr key={`${item['Product ID']}-${item['Product Name']}`}>
                        <td>
                          <div className="product-cell">
                            <span className="rank-badge" style={{ background: kpiGradient(i) }}>#{i + 1}</span>
                            {item['Product Name']}
                          </div>
                        </td>
                        <td><strong>{formatCurrency(item.sales)}</strong></td>
                        <td>{formatNumber(item.units)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        );
      case 'customers':
        return (
          <div className="content-grid">
            <section className="panel wide">
              <div className="panel-head">
                <div><div className="panel-eyebrow">VIP SEGMENT</div><h2>Top Customers by Lifetime Value</h2></div>
              </div>
              <div className="table-wrap">
                <table className="styled-table">
                  <thead><tr><th>Rank</th><th>Customer</th><th>Orders</th><th>Total Spend</th><th>Last Purchase</th><th>Returns</th></tr></thead>
                  <tbody>
                    {(dashboard.topCustomers || []).slice(0, 10).map((item, i) => (
                      <tr key={`${item['Customer ID']}-${item['Customer Name']}`}>
                        <td><span className="rank-badge" style={{ background: kpiGradient(i) }}>#{i + 1}</span></td>
                        <td><strong>{item['Customer Name']}</strong><div className="muted small">{item['Customer ID']}</div></td>
                        <td>{formatNumber(item.orders)}</td>
                        <td><strong style={{ color: '#ffc857' }}>{formatCurrency(item.sales)}</strong></td>
                        <td>{item.last_order}</td>
                        <td>{formatNumber(item.returns || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        );
      case 'risk':
        return (
          <div className="content-grid">
            <section className="panel">
              <div className="panel-head"><div className="panel-eyebrow">PERFORMANCE SPIKES</div><h2>Daily Extremes</h2></div>
              <div className="stat-stack">
                <div className="metric-box gold">
                  <span>🏆 Best Day — Revenue</span>
                  <strong>{dashboard.dailyReport.summary?.top_day?.['Order Date'] || '—'}</strong>
                  <small>{formatCurrency(dashboard.dailyReport.summary?.top_day?.sales)}</small>
                </div>
                <div className="metric-box slate">
                  <span>📉 Lowest Day — Revenue</span>
                  <strong>{dashboard.dailyReport.summary?.low_day?.['Order Date'] || '—'}</strong>
                  <small>{formatCurrency(dashboard.dailyReport.summary?.low_day?.sales)}</small>
                </div>
                <div className="metric-box orange">
                  <span>⚠️ Overall Return Rate</span>
                  <strong>{formatPercent(dashboard.kpis.return_rate)}</strong>
                  <small>{formatNumber(dashboard.quality.returned_orders || 0)} returned orders</small>
                </div>
              </div>
            </section>
            <section className="panel">
              <div className="panel-head"><div className="panel-eyebrow">HIGH-RISK DAYS</div><h2>Return Hotspots (≥ 25%)</h2></div>
              <div className="table-wrap">
                <table className="styled-table compact">
                  <thead><tr><th>Date</th><th>Return %</th><th>Sales at Risk</th></tr></thead>
                  <tbody>
                    {(dashboard.dailyReport.summary?.risk_days || []).slice(0, 5).map((item) => (
                      <tr key={item['Order Date']}>
                        <td><strong>{item['Order Date']}</strong></td>
                        <td><span className="risk-chip high">{formatPercent(item.return_rate)}</span></td>
                        <td>{formatCurrency(item.sales)}</td>
                      </tr>
                    ))}
                    {(dashboard.dailyReport.summary?.risk_days || []).length === 0 && (
                      <tr><td colSpan={3} className="empty-row">✨ No high-return days detected. Solid operations!</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        );
      case 'recommendations':
        return (
          <div className="content-grid">
            <section className="panel wide">
              <div className="panel-head">
                <div><div className="panel-eyebrow">AI CURATED</div><h2>Recommended Products to Promote</h2><p className="panel-subtitle">Ranked by composite sales + profit momentum score</p></div>
              </div>
              <div className="rec-grid">
                {(dashboard.recommendations || []).slice(0, 12).map((item, i) => (
                  <div key={`${item['Product ID']}-${item['Product Name']}`} className="rec-card" style={{ background: `linear-gradient(145deg, rgba(255,255,255,0.06), rgba(130,88,255,0.08) 80%)` }}>
                    <div className="rec-head">
                      <span className="rank-badge" style={{ background: kpiGradient(i) }}>#{i + 1}</span>
                      <span className="score-pill"><Icon name="spark" /> {Number(item.score || 0).toFixed(3)}</span>
                    </div>
                    <h3 className="rec-name">{item['Product Name']}</h3>
                    <div className="muted small" style={{ marginTop: 4 }}>📂 {item.Category || 'Uncategorized'}</div>
                    <div className="rec-stats">
                      <div>
                        <span>Revenue</span>
                        <strong style={{ color: '#ffc857' }}>{formatCurrency(item.sales)}</strong>
                      </div>
                      <div>
                        <span>Units</span>
                        <strong>{formatNumber(item.units)}</strong>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        );
      case 'quality':
        return (
          <div className="content-grid">
            <section className="panel quality-score-panel">
              <div className="panel-head"><div className="panel-eyebrow">OVERALL HEALTH</div><h2>Data Quality Index</h2></div>
              <div className="quality-score-wrap">
                <div className="quality-doughnut">
                  <Doughnut data={{ labels: ['Score', 'Gap'], datasets: [{ data: [qualityMetrics.available ? qualityMetrics.score : 0, Math.max(0, 100 - (qualityMetrics.available ? qualityMetrics.score : 0))], backgroundColor: ['#00c2a8', 'rgba(255,255,255,0.04)'], borderWidth: 0, cutout: '78%' }] }} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { enabled: false } } }} />
                  <div className="quality-center">
                    <strong>{qualityMetrics.available ? `${qualityMetrics.score.toFixed(1)}%` : '—'}</strong>
                    <span>Quality Score</span>
                  </div>
                </div>
                <div className="quality-breakdown-list">
                  <QualityRow label="Completeness" value={qualityMetrics.completeness} color="#00c2a8" />
                  <QualityRow label="Row Uniqueness" value={qualityMetrics.uniqueness} color="#5b8def" />
                  <QualityRow label="Valid Dates" value={qualityMetrics.dateValidity} color="#ff6b35" />
                </div>
              </div>
              <p className="muted panel-sub">Average across source-data integrity metrics for {formatNumber(dashboard.quality.records || 0)} records.</p>
            </section>

            <section className="panel">
              <div className="panel-head"><div className="panel-eyebrow">PIPELINE AUDIT</div><h2>Known Issues</h2></div>
              <div className="stat-stack">
                <div className="metric-box"><span>🧩 Missing Values (cells)</span><strong style={{ color: Number(dashboard.quality.missing_values) > 0 ? '#ff6b35' : '#00c2a8' }}>{formatNumber(dashboard.quality.missing_values || 0)}</strong><small>{formatNumber(dashboard.quality.rows_with_missing || 0)} rows affected</small></div>
                <div className="metric-box"><span>🔁 Duplicate Rows</span><strong style={{ color: Number(dashboard.quality.duplicate_rows) > 0 ? '#ff6b35' : '#00c2a8' }}>{formatNumber(dashboard.quality.duplicate_rows || 0)}</strong></div>
                <div className="metric-box"><span>📅 Unparseable Dates</span><strong style={{ color: Number(dashboard.quality.invalid_dates) > 0 ? '#ff6b35' : '#00c2a8' }}>{formatNumber(dashboard.quality.invalid_dates || 0)}</strong><small>Valid range {dashboard.quality.date_min || '-'} → {dashboard.quality.date_max || '-'}</small></div>
              </div>
              {dashboard.quality.profit_is_estimated && (
                <div className="insight">ℹ️ <strong>Profit is estimated</strong> using a 30% planning margin because the source dataset has no cost or profit column. Add a "Profit" column to your CSV for exact figures.</div>
              )}
            </section>
          </div>
        );
      case 'profitability': {
        const kpis = dashboard.kpis || {};
        const cats = dashboard.categoryPerformance || [];
        const totalProfit = (kpis.sales || 0) * (kpis.profit_margin || 0) / 100;
        const avgProfitOrder = kpis.orders ? totalProfit / kpis.orders : 0;
        const returnImpact = (kpis.sales || 0) * (kpis.return_rate || 0) / 100;
        const profitBars = {
          labels: cats.map((c) => c.Category || c.category || c['Product Category'] || ''),
          datasets: [{
            label: 'Est. Profit',
            data: cats.map((c) => (Number(c.sales || 0) * 0.3) - (Number(c.sales || 0) * (kpis.return_rate || 0) / 100)),
            backgroundColor: ['#5b8def', '#ff6b35', '#00c2a8', '#ffc857', '#a78bfa', '#f472b6', '#34d399'],
            borderRadius: 8,
          }],
        };
        const monthlyProfit = {
          labels: (dashboard.trend || []).map((p) => String(p.Month || '').slice(0, 7)),
          datasets: [{
            label: 'Est. Profit',
            data: (dashboard.trend || []).map((p) => Number(p.sales || 0) * 0.3),
            borderColor: '#00c2a8',
            backgroundColor: 'rgba(0,194,168,0.12)',
            tension: 0.4,
            fill: true,
            borderWidth: 3,
          }],
        };
        const heatRows = heatmapMatrix;
        const matData = heatRows.rows || {};
        const catsOrdered = heatRows.categoryOrder || [];
        const regsOrdered = heatRows.regionOrder || [];
        return (
          <div className="content-grid">
            <section className="panel hero-panel wide" style={{ background: 'linear-gradient(135deg, rgba(0,194,168,0.12), rgba(91,141,239,0.12) 70%, rgba(167,139,250,0.1))' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> PROFITABILITY CONTROL TOWER</div>
                  <h1 className="hero-title">Profit margins, costs, and return impact on revenue</h1>
                  <p className="hero-subtitle">Revenue-weighted margins mapped across categories, regions, and cohorts.</p>
                  <div className="hero-stats">
                    <div><strong style={{ color: '#00c2a8' }}>{formatCurrency(totalProfit)}</strong><span>Total Est. Profit</span></div>
                    <div className="divider" />
                    <div><strong>{formatPercent(kpis.profit_margin)}</strong><span>Avg Margin</span></div>
                    <div className="divider" />
                    <div><strong style={{ color: '#ff6b35' }}>-{formatCurrency(returnImpact)}</strong><span>Return Impact</span></div>
                    <div className="divider" />
                    <div><strong>{formatCurrency(avgProfitOrder)}</strong><span>Avg Profit / Order</span></div>
                  </div>
                </div>
                <div className="hero-chart"><div className="chart-frame"><Line data={monthlyProfit} options={chartOpts('line')} /></div></div>
              </div>
            </section>
            <section className="panel"><div className="panel-head"><div><div className="panel-eyebrow">CATEGORY</div><h2>Est. Profit by Category</h2></div></div><div className="chart-frame"><Bar data={profitBars} options={chartOpts('bar')} /></div></section>
            <section className="panel"><div className="panel-head"><div><div className="panel-eyebrow">CUSTOMER</div><h2>Top 10 Customers by Profit</h2></div></div>
              <div className="table-wrap">
                <table className="styled-table compact">
                  <thead><tr><th>#</th><th>Customer</th><th>Sales</th><th>Est. Profit</th></tr></thead>
                  <tbody>
                    {(dashboard.topCustomers || []).slice(0, 10).map((c, i) => (
                      <tr key={`pf-c-${i}-${c['Customer ID']}`}>
                        <td><span className="rank-badge mini" style={{ background: kpiGradient(i) }}>#{i + 1}</span></td>
                        <td><strong>{c['Customer Name']}</strong><div className="muted small">{c['Customer ID']}</div></td>
                        <td>{formatCurrency(c.sales)}</td>
                        <td style={{ color: '#00c2a8' }}><strong>{formatCurrency(Number(c.sales || 0) * 0.3 * (1 - (kpis.return_rate || 0) / 100))}</strong></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">MATRIX</div><h2>Category × Region Profit Heatmap</h2></div></div>
              <div className="heatmap-wrap" style={{ overflowX: 'auto' }}>
                <table className="heatmat">
                  <thead><tr><th>Category ↓ / Region →</th>{regsOrdered.map((r) => <th key={r}>{r}</th>)}</tr></thead>
                  <tbody>
                    {catsOrdered.map((cat, ci) => (
                      <tr key={cat}>
                        <td className="heat-label"><strong>{cat}</strong></td>
                        {regsOrdered.map((reg) => {
                          const cell = matData[cat]?.[reg] || {};
                          const prof = Number(cell.profit || 0);
                          const intensity = Math.min(1, Math.abs(prof) / 500000);
                          const bg = prof >= 0 ? `rgba(0,194,168,${0.12 + intensity * 0.6})` : `rgba(255,107,53,${0.12 + intensity * 0.6})`;
                          return <td key={`${cat}-${reg}`} style={{ background: bg, color: intensity > 0.4 ? '#fff' : '#cbd5e1' }}>{prof ? formatCurrency(prof) : '—'}</td>;
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">PRODUCT</div><h2>Top 10 Products by Estimated Profit</h2></div></div>
              <div className="table-wrap">
                <table className="styled-table">
                  <thead><tr><th>#</th><th>Product</th><th>Revenue</th><th>Units</th><th>Return %</th><th>Est. Profit</th></tr></thead>
                  <tbody>
                    {(dashboard.topProducts || []).slice(0, 10).map((p, i) => (
                      <tr key={`pf-p-${i}-${p['Product ID']}`}>
                        <td><span className="rank-badge" style={{ background: kpiGradient(i) }}>#{i + 1}</span></td>
                        <td><div className="product-cell"><span>{p['Product Name']}</span><div className="muted small">{p.Category}</div></div></td>
                        <td>{formatCurrency(p.sales)}</td><td>{formatNumber(p.units)}</td>
                        <td><span className="risk-chip">{formatPercent((p.returns || 0) / Math.max(1, p.units))}</span></td>
                        <td style={{ color: '#00c2a8' }}><strong>{formatCurrency(Number(p.sales || 0) * 0.27)}</strong></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        );
      }
      case 'products': {
        const prods = dashboard.topProducts || [];
        const catSales = {};
        const catReturns = {};
        const catUnits = {};
        prods.forEach((p) => {
          const c = p.Category || 'Uncategorized';
          catSales[c] = (catSales[c] || 0) + Number(p.sales || 0);
          catReturns[c] = (catReturns[c] || 0) + Number(p.returns || 0);
          catUnits[c] = (catUnits[c] || 0) + Number(p.units || 0);
        });
        const catLabels = Object.keys(catSales);
        const catPie = { labels: catLabels, datasets: [{ data: catLabels.map((c) => catSales[c]), backgroundColor: ['#5b8def', '#ff6b35', '#00c2a8', '#ffc857', '#a78bfa', '#f472b6', '#34d399'], borderWidth: 0 }] };
        const retBars = { labels: catLabels, datasets: [{ label: 'Return Rate %', data: catLabels.map((c) => (100 * (catReturns[c] || 0) / Math.max(1, catUnits[c] || 0))), backgroundColor: '#ff6b35', borderRadius: 8 }] };
        const unitsVsSales = {
          labels: prods.slice(0, 15).map((p) => (p['Product Name'] || '').slice(0, 20)),
          datasets: [
            { type: 'bar', label: 'Sales (₹L)', data: prods.slice(0, 15).map((p) => Number(p.sales || 0) / 100000), backgroundColor: 'rgba(91,141,239,0.7)', borderRadius: 6, yAxisID: 'y' },
            { type: 'line', label: 'Units', data: prods.slice(0, 15).map((p) => Number(p.units || 0)), borderColor: '#ffc857', borderWidth: 3, pointBackgroundColor: '#ffc857', tension: 0.35, yAxisID: 'y1' },
          ],
        };
        const uvsOpts = {
          responsive: true, maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true, position: 'left', title: { display: true, text: 'Sales ₹L', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#cbd5e1' } },
            y1: { beginAtZero: true, position: 'right', title: { display: true, text: 'Units', color: '#94a3b8' }, grid: { drawOnChartArea: false }, ticks: { color: '#cbd5e1' } },
            x: { ticks: { color: '#94a3b8', maxRotation: 45, minRotation: 30 }, grid: { color: 'rgba(255,255,255,0.05)' } },
          },
          plugins: { legend: { labels: { color: '#e2e8f0' } } },
        };
        return (
          <div className="content-grid">
            <section className="panel wide hero-panel" style={{ background: 'linear-gradient(135deg, rgba(255,200,87,0.08), rgba(255,107,53,0.12) 70%)' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> PRODUCT ANALYTICS</div>
                  <h1 className="hero-title">Top products, return rates, and sales by category</h1>
                  <p className="hero-subtitle">{formatNumber(prods.length)} unique products ranked by revenue, units, and margin-adjusted quality.</p>
                </div>
                <div className="hero-stats">
                  <div><strong>{formatNumber(Object.values(catUnits).reduce((a, b) => a + b, 0))}</strong><span>Total Units</span></div>
                  <div className="divider" />
                  <div><strong>{catLabels.length}</strong><span>Categories</span></div>
                  <div className="divider" />
                  <div><strong>{formatNumber(prods.length)}</strong><span>Products Loaded</span></div>
                </div>
              </div>
            </section>
            <section className="panel"><div className="panel-head"><div><div className="panel-eyebrow">CATEGORY MIX</div><h2>Revenue Share</h2></div></div><div className="chart-frame"><Doughnut data={catPie} options={doughnutOpts} /></div></section>
            <section className="panel"><div className="panel-head"><div><div className="panel-eyebrow">QUALITY</div><h2>Return Rate by Category</h2></div></div><div className="chart-frame"><Bar data={retBars} options={chartOpts('bar')} /></div></section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">COMBO</div><h2>Units Sold vs Revenue (Top 15 SKUs)</h2><p className="panel-subtitle">Bars = sales ₹L · Line = units shipped</p></div></div><div className="chart-frame tall"><Bar data={unitsVsSales} options={uvsOpts} /></div></section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">RANKING</div><h2>Top Products Detail</h2></div></div>
              <div className="table-wrap">
                <table className="styled-table">
                  <thead><tr><th>#</th><th>Product</th><th>Category</th><th>Revenue</th><th>Units</th><th>Return Rate</th><th>Est. Profit</th></tr></thead>
                  <tbody>
                    {prods.map((p, i) => {
                      const rr = (100 * (p.returns || 0) / Math.max(1, p.units || 0));
                      return (
                        <tr key={`prod-${i}-${p['Product ID']}`}>
                          <td><span className="rank-badge" style={{ background: kpiGradient(i) }}>#{i + 1}</span></td>
                          <td><strong>{p['Product Name']}</strong></td>
                          <td>{p.Category}</td>
                          <td>{formatCurrency(p.sales)}</td>
                          <td>{formatNumber(p.units)}</td>
                          <td><span className={`risk-chip ${rr > 20 ? 'high' : rr > 10 ? 'medium' : ''}`}>{formatPercent(rr / 100)}</span></td>
                          <td style={{ color: '#00c2a8' }}><strong>{formatCurrency(Number(p.sales || 0) * 0.3)}</strong></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        );
      }
      case 'custintel': {
        const cust = dashboard.topCustomers || [];
        const segs = segments.customer_segments || [];
        const totalOrders = (dashboard.kpis.orders || 0);
        const repeatCustCount = cust.filter((c) => Number(c.orders || 0) > 1).length;
        const repeatRate = totalOrders ? (repeatCustCount / Math.min(cust.length || 1, 50)) * 100 : 0;
        const segLabels = segs.map((s) => s.Segment || s.customer_segment || s['Customer Segment'] || 'Segment');
        const segAOV = segs.map((s) => Number(s.AOV || s.aov || 0));
        const segCounts = segs.map((s) => Number(s.Customers || s.customers || s.Count || 0));
        const aovBar = { labels: segLabels, datasets: [{ label: 'AOV (₹)', data: segAOV, backgroundColor: ['#5b8def', '#ff6b35', '#00c2a8', '#ffc857', '#a78bfa', '#f472b6'], borderRadius: 8 }] };
        const segDonut = { labels: segLabels, datasets: [{ data: segCounts.length ? segCounts : cust.map((c) => c['Customer Segment'] || 'Unknown').reduce((acc, v) => (acc[v] = (acc[v] || 0) + 1, acc), {}), backgroundColor: ['#00c2a8', '#5b8def', '#ff6b35', '#ffc857', '#a78bfa', '#f472b6', '#34d399'], borderWidth: 0 }] };
        const donutLabels = Object.keys((cust.map((c) => c['Customer Segment'] || 'Unknown').reduce((acc, v) => (acc[v] = (acc[v] || 0) + 1, acc), {})));
        if (segLabels.length === 0 && donutLabels.length) {
          const counter = cust.map((c) => c['Customer Segment'] || 'Unknown').reduce((acc, v) => (acc[v] = (acc[v] || 0) + 1, acc), {});
          segDonut.labels = Object.keys(counter);
          segDonut.datasets[0].data = Object.values(counter);
        }
        return (
          <div className="content-grid">
            <section className="panel hero-panel wide" style={{ background: 'linear-gradient(135deg, rgba(167,139,250,0.1), rgba(91,141,239,0.14) 70%)' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> CUSTOMER INTELLIGENCE</div>
                  <h1 className="hero-title">Customer orders, loyalty, and lifetime spending</h1>
                  <p className="hero-subtitle">Segment-level AOV, repeat-customer behaviour, and VIP roster.</p>
                  <div className="hero-stats">
                    <div><strong>{formatNumber(cust.length)}</strong><span>Top Customers</span></div>
                    <div className="divider" />
                    <div><strong>{formatPercent(repeatRate / 100)}</strong><span>Repeat Rate (Top N)</span></div>
                    <div className="divider" />
                    <div><strong>{formatCurrency((segAOV.reduce((a, b) => a + b, 0) / Math.max(1, segAOV.length)) || (dashboard.kpis.average_order_value || 0))}</strong><span>Avg Order Value</span></div>
                  </div>
                </div>
                <div className="hero-chart"><div className="chart-frame"><Bar data={aovBar} options={chartOpts('bar')} /></div></div>
              </div>
            </section>
            <section className="panel"><div className="panel-head"><div><div className="panel-eyebrow">SEGMENTS</div><h2>Customer Segment Mix</h2></div></div><div className="chart-frame"><Doughnut data={segDonut} options={doughnutOpts} /></div></section>
            <section className="panel"><div className="panel-head"><div><div className="panel-eyebrow">SUMMARY</div><h2>Key Metrics</h2></div></div>
              <div className="metric-grid">
                <div className="metric-box"><span>🧾 Avg Order Value</span><strong>{formatCurrency(dashboard.kpis.average_order_value)}</strong></div>
                <div className="metric-box"><span>🛍️ Units per Order</span><strong>{formatNumber(dashboard.kpis.units_per_order, 2)}</strong></div>
                <div className="metric-box"><span>🔁 Repeat Customer Rate</span><strong style={{ color: repeatRate > 40 ? '#00c2a8' : '#ffc857' }}>{formatPercent(repeatRate / 100)}</strong></div>
                <div className="metric-box"><span>📊 Segments</span><strong>{Math.max(segLabels.length, donutLabels.length)}</strong></div>
              </div>
            </section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">VIP ROSTER</div><h2>Top Customers with Purchase Behaviour</h2></div></div>
              <div className="table-wrap">
                <table className="styled-table">
                  <thead><tr><th>#</th><th>Customer</th><th>Segment</th><th>Orders</th><th>Last Purchase</th><th>Total Spend</th><th>Returns</th></tr></thead>
                  <tbody>
                    {cust.slice(0, 30).map((c, i) => (
                      <tr key={`ci-${i}-${c['Customer ID']}`}>
                        <td><span className="rank-badge" style={{ background: kpiGradient(i) }}>#{i + 1}</span></td>
                        <td><strong>{c['Customer Name']}</strong><div className="muted small">{c['Customer ID']}</div></td>
                        <td><span className="badge-accent">{c['Customer Segment'] || '—'}</span></td>
                        <td>{formatNumber(c.orders)}</td>
                        <td>{c.last_order || '—'}</td>
                        <td><strong style={{ color: '#ffc857' }}>{formatCurrency(c.sales)}</strong></td>
                        <td>{formatNumber(c.returns || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        );
      }
      case 'geographic': {
        const regions = segments.regions || [];
        const cities = (segments.cities || []).slice(0, 15);
        const heatRows = heatmapMatrix;
        const matData = heatRows.rows || {};
        const catsOrdered = heatRows.categoryOrder || [];
        const regsOrdered = heatRows.regionOrder || regions.map((r) => r.Region).filter(Boolean);
        const top5Cities = cities.slice(0, 5);
        const citiesBarData = {
          labels: cities.map((c) => c.City || c.city || ''),
          datasets: [{ label: 'Sales', data: cities.map((c) => Number(c.Sales || c.sales || 0)), backgroundColor: '#5b8def', borderRadius: 8 }],
        };
        return (
          <div className="content-grid">
            <section className="panel wide hero-panel" style={{ background: 'linear-gradient(135deg, rgba(52,211,153,0.08), rgba(91,141,239,0.16) 70%)' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> GEOGRAPHIC ANALYSIS</div>
                  <h1 className="hero-title">Sales by region and city</h1>
                  <p className="hero-subtitle">{regsOrdered.length} regions, {cities.length} cities, ranked by revenue and category intensity.</p>
                </div>
                <div className="hero-stats">
                  <div><strong>{regsOrdered.length}</strong><span>Regions</span></div>
                  <div className="divider" />
                  <div><strong>{cities.length}</strong><span>Cities</span></div>
                  <div className="divider" />
                  <div><strong>{formatCurrency(regions.reduce((a, r) => a + Number(r.Sales || r.sales || 0), 0))}</strong><span>Geo-Total</span></div>
                </div>
              </div>
            </section>
            <section className="panel wide">
              <div className="panel-head"><div><div className="panel-eyebrow">TOP 5 CITIES</div><h2>Highest Performing Cities</h2></div></div>
              <div className="kpi-list">
                {top5Cities.map((c, i) => (
                  <div key={`geo-c-${i}`} className="kpi-card" style={{ background: `linear-gradient(135deg, rgba(91,141,239,0.18), rgba(${100 + i * 30},${100 + i * 20},255,0.12) 80%)` }}>
                    <div className="kpi-label"><span className="rank-badge mini" style={{ background: kpiGradient(i) }}>#{i + 1}</span> {c.City || c.city}</div>
                    <div className="kpi-value">{formatCurrency(c.Sales || c.sales || 0)}</div>
                    <div className="kpi-sub">{formatNumber(c.Orders || c.orders || 0)} orders · {formatNumber(c.Customers || c.customers || 0)} customers</div>
                  </div>
                ))}
              </div>
            </section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">CITIES RANK</div><h2>Top 15 Cities by Sales</h2></div></div><div className="chart-frame wide"><Bar data={citiesBarData} options={{ ...chartOpts('bar'), indexAxis: 'y' }} /></div></section>
            <section className="panel"><div className="panel-head"><div><div className="panel-eyebrow">REGIONS</div><h2>Regions Ranking</h2></div></div>
              <div className="table-wrap">
                <table className="styled-table compact">
                  <thead><tr><th>#</th><th>Region</th><th>Sales</th><th>Orders</th><th>Customers</th><th>Margin</th></tr></thead>
                  <tbody>
                    {regions.map((r, i) => (
                      <tr key={`geo-r-${i}`}>
                        <td><span className="rank-badge mini" style={{ background: kpiGradient(i) }}>#{i + 1}</span></td>
                        <td><strong>{r.Region}</strong></td>
                        <td>{formatCurrency(r.Sales)}</td><td>{formatNumber(r.Orders)}</td><td>{formatNumber(r.Customers)}</td>
                        <td style={{ color: '#00c2a8' }}>{formatPercent((r['Margin %'] || 0) / 100)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">CATEGORY × REGION</div><h2>Demand Heatmap</h2></div></div>
              <div className="heatmap-wrap" style={{ overflowX: 'auto' }}>
                <table className="heatmat">
                  <thead><tr><th>Category ↓ / Region →</th>{regsOrdered.map((r) => <th key={r}>{r}</th>)}</tr></thead>
                  <tbody>
                    {catsOrdered.map((cat, ci) => (
                      <tr key={cat}>
                        <td className="heat-label"><strong>{cat}</strong></td>
                        {regsOrdered.map((reg) => {
                          const cell = matData[cat]?.[reg] || {};
                          const intensity = Number(cell.intensity || 0);
                          const bg = `rgba(91,141,239,${0.1 + intensity * 0.55})`;
                          return <td key={`${cat}-${reg}`} style={{ background: bg, color: intensity > 0.55 ? '#fff' : '#cbd5e1' }}>{cell.orders ? `${formatNumber(cell.orders)} orders` : cell.sales ? formatCurrency(cell.sales) : '—'}</td>;
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        );
      }
      case 'forecast': {
        const models = ['RandomForest', 'XGBoost', 'Compare'];
        const compare = forecastCompare;
        const rfFcast = compare?.randomforest?.forecast || [];
        const xgFcast = compare?.xgboost?.forecast || [];
        const single = salesForecast?.forecast || [];
        const rfLine = {
          labels: rfFcast.map((f) => f.date),
          datasets: [{ label: 'RandomForest', data: rfFcast.map((f) => Number(f.revenue || 0)), borderColor: '#5b8def', backgroundColor: 'rgba(91,141,239,0.15)', borderWidth: 3, tension: 0.4, fill: true }],
        };
        const xgLine = xgFcast.length ? {
          labels: xgFcast.map((f) => f.date),
          datasets: [{ label: 'XGBoost', data: xgFcast.map((f) => Number(f.revenue || 0)), borderColor: '#ff6b35', backgroundColor: 'rgba(255,107,53,0.15)', borderWidth: 3, tension: 0.4, fill: true }],
        } : {
          labels: rfFcast.map((f) => f.date),
          datasets: [{ label: 'XGBoost (Not Installed)', data: rfFcast.map(() => null), borderColor: '#ff6b35', backgroundColor: 'transparent', borderWidth: 0 }],
        };
        const comboLine = {
          labels: rfFcast.length ? rfFcast.map((f) => f.date) : single.map((f) => f.date),
          datasets: [
            rfFcast.length ? { label: 'RandomForest', data: rfFcast.map((f) => Number(f.revenue || 0)), borderColor: '#5b8def', borderWidth: 3, tension: 0.4, pointRadius: 3 } : null,
            xgFcast.length ? { label: 'XGBoost', data: xgFcast.map((f) => Number(f.revenue || 0)), borderColor: '#ff6b35', borderWidth: 3, tension: 0.4, pointRadius: 3 } : null,
            (!rfFcast.length && single.length) ? { label: forecastModel, data: single.map((f) => Number(f.revenue || 0)), borderColor: '#00c2a8', backgroundColor: 'rgba(0,194,168,0.18)', borderWidth: 3, tension: 0.4, fill: true } : null,
          ].filter(Boolean),
        };
        return (
          <div className="content-grid">
            <section className="panel hero-panel wide" style={{ background: 'linear-gradient(135deg, rgba(130,88,255,0.1), rgba(91,141,239,0.18) 70%)' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> AI FORECAST SUITE</div>
                  <h1 className="hero-title">Sales forecast using Random Forest and XGBoost</h1>
                  <p className="panel-subtitle">Lag features (1/2/3/7/14-day lags, rolling MA, DoW/MoM/DoY) train supervised learners. Compare both outputs side-by-side and use the lower-MAE ensemble winner.</p>
                  <div className="segment-focus-tag" style={{ display: 'inline-flex', gap: 6, marginTop: 10, flexWrap: 'wrap' }}>
                    {models.map((m) => (
                      <button key={m} className={`ghost-button ${forecastModel === m ? 'active' : ''}`} style={{ padding: '6px 12px', borderRadius: 10, border: forecastModel === m ? '1.5px solid #a78bfa' : '1px solid rgba(255,255,255,0.1)', background: forecastModel === m ? 'rgba(167,139,250,0.2)' : 'rgba(255,255,255,0.02)', color: forecastModel === m ? '#fff' : '#cbd5e1', fontWeight: forecastModel === m ? 600 : 400 }} onClick={() => { setForecastModel(m); setViewRefresh((p) => ({ ...p, forecast: (p.forecast || 0) + 1 })); }}>
                        {m === 'Compare' ? '🆚 Side-by-Side Compare' : m === 'XGBoost' ? '⚡ XGBoost' : '🌲 Random Forest'}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="hero-stats">
                  <div><strong>{appSettings.forecastHorizon || 7}d</strong><span>Forecast Horizon</span></div>
                  <div className="divider" />
                  {compare?.winner && (
                    <>
                      <div><strong style={{ color: compare?.winner === 'ensemble' ? '#a78bfa' : compare?.winner === 'xgboost' ? '#ff6b35' : '#5b8def' }}>{(compare.winner || '').toUpperCase()}</strong><span>Winner Model</span></div>
                      <div className="divider" />
                    </>
                  )}
                  <div><strong>{salesForecast?.confidence || compare?.randomforest?.confidence || compare?.xgboost?.confidence || 0}%</strong><span>Confidence</span></div>
                </div>
              </div>
            </section>
            {(forecastModel === 'Compare' && !compare) && <ViewSkeleton charts={2} tables={0} />}
            {(forecastModel !== 'Compare' && !single.length && !salesForecast) && <ViewSkeleton charts={1} tables={0} />}
            {forecastModel === 'Compare' && compare && (
              <>
                <section className="panel">
                  <div className="panel-head"><div><div className="panel-eyebrow">🌲 RANDOM FOREST</div><h2>RF Projection</h2></div><span className="badge-good">MAE {compare.randomforest?.validation_mae ? formatCurrency(compare.randomforest.validation_mae) : '—'}</span></div>
                  <div className="chart-frame"><Line data={rfLine} options={chartOpts('line')} /></div>
                </section>
                <section className="panel">
                  <div className="panel-head"><div><div className="panel-eyebrow">⚡ XGBOOST</div><h2>XGB Projection</h2></div>
                    {compare.xgboost ? <span className="badge-good">MAE {formatCurrency(compare.xgboost.validation_mae || 0)}</span> : <span className="badge-accent">XGBoost not installed</span>}
                  </div>
                  {compare.xgboost && xgFcast.length ? (
                    <div className="chart-frame"><Line data={xgLine} options={chartOpts('line')} /></div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '48px 24px', gap: 16, opacity: 0.7 }}>
                      <span style={{ fontSize: 48 }}>⚡</span>
                      <p style={{ color: '#94a3b8', textAlign: 'center', maxWidth: 380, lineHeight: 1.6 }}>XGBoost library not detected in the backend.<br/>Install it to enable side-by-side model comparison.</p>
                      <code style={{ background: 'rgba(255,255,255,0.06)', padding: '8px 16px', borderRadius: 8, color: '#fbbf24', fontSize: 13 }}>pip install "xgboost&gt;=2,&lt;3"</code>
                      <p style={{ color: '#64748b', fontSize: 12 }}>RandomForest is always available.</p>
                    </div>
                  )}
                </section>
                <section className="panel wide">
                  <div className="panel-head"><div><div className="panel-eyebrow">🆚 OVERLAY</div><h2>Both Models + Winner Badge</h2></div>
                    <span className={`badge-accent`}>🏆 Winner: {(compare.winner || 'ensemble').toUpperCase()} · Diff {formatCurrency(compare.mae_diff || 0)}</span>
                  </div>
                  <div className="chart-frame tall"><Line data={comboLine} options={chartOpts('line')} /></div>
                </section>
                <section className="panel wide">
                  <div className="panel-head"><div><div className="panel-eyebrow">TABLE</div><h2>Daily Projections</h2></div></div>
                  <div className="table-wrap"><table className="styled-table"><thead><tr><th>Date</th><th>RandomForest</th><th>XGBoost</th><th>Ensemble Avg</th></tr></thead>
                    <tbody>{rfFcast.map((f, i) => (
                      <tr key={f.date}>
                        <td><strong>{f.date}</strong></td>
                        <td>{formatCurrency(f.revenue)}</td>
                        <td>{xgFcast[i] ? formatCurrency(xgFcast[i].revenue) : '—'}</td>
                        <td style={{ color: '#a78bfa' }}><strong>{formatCurrency(((Number(f.revenue || 0)) + (Number(xgFcast[i]?.revenue || 0))) / 2)}</strong></td>
                      </tr>
                    ))}</tbody>
                  </table></div>
                </section>
              </>
            )}
            {forecastModel !== 'Compare' && (
              <>
                <section className="panel forecast-control-panel">
                  <div className="panel-head"><div><div className="panel-eyebrow">ENGINE CONTROLS</div><h2>Run {forecastModel} Forecast</h2><p className="panel-subtitle">Specify base date and horizon. Horizon setting also saved in Settings.</p></div><span className="badge-accent">{forecastModel}</span></div>
                  <form className="forecast-inputs" onSubmit={runDailyForecast}>
                    <label><span>Base Date</span><input type="date" value={forecastDate} onChange={(e) => setForecastDate(e.target.value)} required /></label>
                    <label><span>Today's Sales (optional)</span><input type="number" min="0" step="0.01" value={forecastSalesInput} onChange={(e) => setForecastSalesInput(e.target.value)} placeholder="For dates outside dataset" /></label>
                    <label><span>Horizon</span>
                      <select value={forecastDays} onChange={(e) => setForecastDays(Number(e.target.value))}>
                        <option value={1}>📅 Tomorrow</option><option value={7}>📆 7 days</option><option value={14}>🗓️ 14 days</option><option value={30}>📊 30 days</option>
                      </select>
                    </label>
                    <button className="primary-cta forecast-submit" type="submit" disabled={forecastLoading}>{forecastLoading ? '⏳ Training model…' : `🔮 Run ${forecastModel}`}</button>
                  </form>
                  <p className="muted forecast-data-range">Dataset <strong>{dashboard.quality.date_min || 'unknown'}</strong> → <strong>{dashboard.quality.date_max || 'unknown'}</strong></p>
                </section>
                <section className="panel forecast-result-panel">
                  {single.length ? (<>
                    <div className="forecast-result-heading"><div><span className="forecast-eyebrow">📈 OUTLOOK</span><h2>{single[0].date}</h2></div><span className="forecast-method-pill">{salesForecast.basis}</span></div>
                    <strong className="forecast-hero-value">{formatForecastCurrency(single[0].revenue)}</strong>
                    <span className="muted forecast-sub">Predicted Revenue</span>
                    <div className="forecast-result-metrics">
                      <div><span>Today's Actual</span><strong>{formatForecastCurrency(salesForecast.today_sales)}</strong></div>
                      <div><span>Est. Profit</span><strong style={{ color: '#00c2a8' }}>{formatForecastCurrency(single[0].predicted_profit)}</strong></div>
                      <div><span>Risk / Loss</span><strong style={{ color: single[0].predicted_loss > 0 ? '#ff6b35' : '#00c2a8' }}>{single[0].predicted_loss == null ? 'N/A' : single[0].predicted_loss > 0 ? formatForecastCurrency(single[0].predicted_loss) : 'None'}</strong></div>
                    </div>
                  </>) : (<div className="forecast-empty-state"><span className="forecast-eyebrow">🔮 READY</span><h2>Your {forecastModel} forecast appears here</h2><p className="muted">Use the controls or set a horizon in Settings.</p></div>)}
                </section>
                {single.length > 1 && (
                  <section className="panel wide forecast-detail-panel">
                    <div className="panel-head"><div><div className="panel-eyebrow">VISUAL PROJECTION</div><h2>{single.length}-Day Horizon</h2></div><span className="badge-conf">Confidence {salesForecast.confidence || 0}%</span></div>
                    <div className="chart-frame"><Line data={forecastChartData} options={forecastChartOptions} /></div>
                  </section>
                )}
                {single.length > 0 && (
                  <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">DAILY TABLE</div></div></div>
                    <div className="table-wrap"><table className="styled-table"><thead><tr><th>📅 Date</th><th>💰 Predicted Revenue</th><th>💚 Est. Profit</th><th>⚠️ Est. Loss</th><th>📦 Predicted Orders</th></tr></thead><tbody>
                      {single.map((item) => (
                        <tr key={item.date}>
                          <td><strong>{item.date}</strong></td>
                          <td>{formatForecastCurrency(item.revenue)}</td>
                          <td style={{ color: '#00c2a8' }}>{formatForecastCurrency(item.predicted_profit)}</td>
                          <td>{item.predicted_loss == null ? '—' : item.predicted_loss > 0 ? <span style={{ color: '#ff6b35' }}>{formatForecastCurrency(item.predicted_loss)}</span> : <span style={{ color: '#00c2a8' }}>None</span>}</td>
                          <td>{formatNumber(item.predicted_orders)}</td>
                        </tr>
                      ))}
                    </tbody></table></div>
                  </section>
                )}
              </>
            )}
          </div>
        );
      }
      case 'anomalies': {
        const series = dashboard.anomalySeries || [];
        const anomalies = dashboard.anomalies || [];
        const labels = series.map((s) => s.date || s['Order Date'] || s.day || '');
        const salesArr = series.map((s) => Number(s.sales || s.revenue || 0));
        const ub = series.map((s) => Number(s.upper_band || s.upper || 0));
        const lb = series.map((s) => Number(s.lower_band || s.lower || 0));
        const anomMap = {};
        anomalies.forEach((a) => { anomMap[a.date || a.day || ''] = a; });
        const anomPoints = labels.map((l) => (anomMap[l] ? anomMap[l].sales || anomMap[l].revenue : null));
        const chartData = {
          labels,
          datasets: [
            { label: 'Revenue', data: salesArr, borderColor: '#5b8def', backgroundColor: 'rgba(91,141,239,0.12)', borderWidth: 3, tension: 0.35, fill: false, order: 1 },
            { label: 'Upper Band (μ+3σ)', data: ub, borderColor: 'rgba(255,107,53,0.6)', borderDash: [6, 6], borderWidth: 2, pointRadius: 0, fill: '+1', backgroundColor: 'rgba(255,107,53,0.07)', order: 2 },
            { label: 'Lower Band (μ-3σ)', data: lb, borderColor: 'rgba(0,194,168,0.6)', borderDash: [6, 6], borderWidth: 2, pointRadius: 0, fill: false, order: 3 },
            { label: 'Anomalies', data: anomPoints, borderColor: 'transparent', backgroundColor: '#ff2d55', pointRadius: 8, pointHoverRadius: 12, pointStyle: 'circle', showLine: false, order: 0 },
          ],
        };
        return (
          <div className="content-grid">
            <section className="panel hero-panel wide" style={{ background: 'linear-gradient(135deg, rgba(255,45,85,0.08), rgba(255,107,53,0.14) 70%)' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> ANOMALY DETECTION</div>
                  <h1 className="hero-title">Detect unusual spikes or drops in daily sales</h1>
                  <p className="panel-subtitle">Flags daily spikes and drops outside expected revenue distribution; z-score and directional severity included.</p>
                </div>
                <div className="hero-stats">
                  <div><strong>{anomalies.length}</strong><span>Anomalies</span></div>
                  <div className="divider" />
                  <div><strong>{series.length}d</strong><span>Window Scanned</span></div>
                  <div className="divider" />
                  <div><strong>{anomalies.filter((a) => (a.direction || a.z_score) > 0).length} ↑ / {anomalies.filter((a) => (a.direction || a.z_score) < 0).length} ↓</strong><span>Spike / Drop</span></div>
                </div>
              </div>
            </section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">SIGNAL</div><h2>Revenue + Control Bands + Anomaly Markers</h2></div></div><div className="chart-frame tall"><Line data={chartData} options={chartOpts('line')} /></div></section>
            <section className="panel wide">
              <div className="panel-head"><div><div className="panel-eyebrow">TOP ANOMALIES</div><h2>Top 5 Most Severe</h2></div></div>
              <div className="rec-grid">
                {[...anomalies].sort((a, b) => Math.abs(b.z_score) - Math.abs(a.z_score)).slice(0, 5).map((a, i) => (
                  <div key={`anom-${i}`} className="rec-card" style={{ background: `linear-gradient(145deg, ${(a.z_score || 0) >= 0 ? 'rgba(255,107,53,0.08)' : 'rgba(0,194,168,0.08)'}, rgba(130,88,255,0.08) 80%)` }}>
                    <div className="rec-head">
                      <span className="rank-badge" style={{ background: kpiGradient(i) }}>#{i + 1}</span>
                      <span className="score-pill">z={(a.z_score || 0).toFixed(2)}</span>
                    </div>
                    <h3 className="rec-name">{a.date || a.day || '—'}</h3>
                    <div className="muted small" style={{ marginTop: 4 }}>{(a.z_score || 0) >= 0 ? '📈 Positive Spike' : '📉 Drop / Low Outlier'}</div>
                    <div className="rec-stats">
                      <div><span>Revenue</span><strong>{formatCurrency(a.sales || a.revenue || 0)}</strong></div>
                      <div><span>Deviation</span><strong style={{ color: (a.deviation_pct || 0) >= 0 ? '#ff6b35' : '#00c2a8' }}>{formatPercent((a.deviation_pct || 0) / 100)}</strong></div>
                    </div>
                  </div>
                ))}
                {anomalies.length === 0 && <div className="empty-row" style={{ gridColumn: '1 / -1', padding: 24 }}>✨ No anomalies detected in current window. Operations within normal bands.</div>}
              </div>
            </section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">FULL TABLE</div><h2>All Anomalies ({anomalies.length})</h2></div></div>
              <div className="table-wrap"><table className="styled-table"><thead><tr><th>Date</th><th>Revenue</th><th>Z-Score</th><th>Deviation %</th><th>Direction</th></tr></thead><tbody>
                {anomalies.map((a, i) => (
                  <tr key={`an-row-${i}-${a.date}`}>
                    <td><strong>{a.date || a.day}</strong></td>
                    <td>{formatCurrency(a.sales || a.revenue || 0)}</td>
                    <td><span className="risk-chip high">{(a.z_score || 0).toFixed(2)}σ</span></td>
                    <td style={{ color: (a.deviation_pct || 0) >= 0 ? '#ff6b35' : '#00c2a8' }}>{formatPercent((a.deviation_pct || 0) / 100)}</td>
                    <td>{(a.direction || a.z_score || 0) >= 0 ? '⬆ Spike' : '⬇ Drop'}</td>
                  </tr>
                ))}
                {anomalies.length === 0 && <tr><td colSpan={5} className="empty-row">✨ No anomalies detected</td></tr>}
              </tbody></table></div>
            </section>
          </div>
        );
      }
      case 'advisor': {
        const adv = dashboard.advisor;
        const insights = adv?.insights || [];
        const warnings = adv?.warnings || [];
        const opportunities = adv?.opportunities || [];
        const actions = adv?.action_items || [];
        const riskScore = Number(adv?.overall_risk || adv?.overall?.risk || 0);
        const riskColor = riskScore > 65 ? '#ff2d55' : riskScore > 40 ? '#ffc857' : '#00c2a8';
        const renderCard = (it, i, type) => {
          const color = type === 'strength' ? '#00c2a8' : type === 'weakness' ? '#ff6b35' : type === 'risk' ? '#ff2d55' : '#a78bfa';
          return (
            <div key={`${type}-${i}`} className="rec-card" style={{ background: `linear-gradient(145deg, ${color}14, rgba(130,88,255,0.06) 80%)`, border: `1px solid ${color}33` }}>
              <div className="rec-head">
                <span className="badge-accent" style={{ color, borderColor: color }}>{type.toUpperCase()}</span>
                {it.severity && <span className="score-pill">{it.severity}</span>}
              </div>
              <h3 className="rec-name">{it.title || it.name || it.category || 'Insight'}</h3>
              <div className="muted small" style={{ marginTop: 6, lineHeight: 1.5 }}>{it.message || it.description || it.detail || ''}</div>
              {it.current_value != null && <div className="muted small" style={{ marginTop: 8 }}>Current: <strong style={{ color: '#fff' }}>{typeof it.current_value === 'number' && (it.current_value < 1 && it.current_value > -1) ? formatPercent(it.current_value) : String(it.current_value)}</strong>{it.threshold != null && <> · Threshold: <strong>{typeof it.threshold === 'number' && (it.threshold < 1 && it.threshold > -1) ? formatPercent(it.threshold) : String(it.threshold)}</strong></>}</div>}
            </div>
          );
        };
        return (
          <div className="content-grid">
            <section className="panel hero-panel wide" style={{ background: 'linear-gradient(135deg, rgba(167,139,250,0.12), rgba(130,88,255,0.18) 70%, rgba(91,141,239,0.14))' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> AI BUSINESS ADVISOR</div>
                  <h1 className="hero-title">Business insights and recommended actions</h1>
                  <p className="panel-subtitle">Threshold checks across return rate, margin, AOV, UPO, customer concentration — surfaced as Strengths / Weaknesses / Risks / Opportunities.</p>
                </div>
                <div className="hero-chart" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ position: 'relative', width: 180, height: 180 }}>
                    <Doughnut
                      data={{ labels: ['Risk', 'Headroom'], datasets: [{ data: [riskScore, Math.max(0, 100 - riskScore)], backgroundColor: [riskColor, 'rgba(255,255,255,0.04)'], borderWidth: 0, cutout: '74%' }] }}
                      options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { enabled: false } } }}
                    />
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
                      <strong style={{ fontSize: 30, color: riskColor }}>{riskScore.toFixed(0)}</strong>
                      <span className="muted small">Overall Risk</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">STRENGTHS</div><h2>What's Working ({insights.filter((i) => i.type === 'strength' || !i.type).length})</h2></div></div>
              <div className="rec-grid">{insights.map((it, i) => renderCard(it, i, it.type || 'strength'))}</div>
            </section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">WARNINGS</div><h2>Weaknesses to Address ({warnings.length})</h2></div></div>
              <div className="rec-grid">{warnings.map((it, i) => renderCard(it, i, it.type || 'weakness'))}</div>
              {warnings.length === 0 && <div className="empty-row">✅ No warnings detected.</div>}
            </section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">OPPORTUNITIES</div><h2>High-Impact Actions ({opportunities.length})</h2></div></div>
              <div className="rec-grid">{opportunities.map((it, i) => renderCard(it, i, it.type || 'opportunity'))}</div>
              {opportunities.length === 0 && <div className="empty-row">💡 Opportunity scan will return recommendations as KPIs change.</div>}
            </section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">ACTION ITEMS</div><h2>Prioritized Action List</h2></div></div>
              <div className="table-wrap"><table className="styled-table"><thead><tr><th>#</th><th>Priority</th><th>Action</th><th>Owner</th><th>Category</th></tr></thead><tbody>
                {actions.map((a, i) => (
                  <tr key={`act-${i}`}>
                    <td><span className="rank-badge mini" style={{ background: kpiGradient(i) }}>{i + 1}</span></td>
                    <td><span className={`risk-chip ${(a.priority || '').toLowerCase() === 'high' ? 'high' : (a.priority || '').toLowerCase() === 'medium' ? 'medium' : ''}`}>{a.priority || 'Normal'}</span></td>
                    <td><strong>{a.title || a.action || a.name}</strong><div className="muted small">{a.reason || a.description || ''}</div></td>
                    <td>{a.owner || a.team || 'Operations'}</td>
                    <td>{a.category || a.type || 'General'}</td>
                  </tr>
                ))}
                {actions.length === 0 && <tr><td colSpan={5} className="empty-row">🎯 No actions at this time.</td></tr>}
              </tbody></table></div>
            </section>
          </div>
        );
      }
      case 'custpred': {
        const cp = dashboard.custpred;
        const topCustomers = cp?.top_customers || [];
        const tierSegs = cp?.customer_segments || cp?.segments || cp?.segment_counts || [];
        let tierList = tierSegs;
        if (!tierList.length) {
          const counter = {};
          topCustomers.forEach((c) => { const k = c.tier || 'Others'; counter[k] = (counter[k] || 0) + 1; });
          tierList = Object.entries(counter).map(([segment, count]) => ({ segment, count }));
        }
        const totalPredRevenue = topCustomers.reduce((a, c) => a + Number(c.predicted_next_value || c.predicted_revenue || c.clv_12m || 0), 0);
        const avgLtv = topCustomers.length ? totalPredRevenue / topCustomers.length : 0;
        const highValueCount = topCustomers.filter((c) => (c.tier || '').toLowerCase().includes('champion') || (c.tier || '').toLowerCase().includes('loyal') || (c.tier || '').toLowerCase().includes('high')).length;
        const atRiskCount = topCustomers.filter((c) => String(c.tier || '').toLowerCase().includes('risk') || String(c.tier || '').toLowerCase().includes('churn') || Number(c.churn_probability || 0) > 0.5).length;
        const top10Pred = [...topCustomers].sort((a, b) => Number(b.predicted_next_value || b.predicted_revenue || b.clv_12m || 0) - Number(a.predicted_next_value || a.predicted_revenue || a.clv_12m || 0)).slice(0, 10);
        const predBars = {
          labels: top10Pred.map((c) => (c.customer_name || c['Customer Name'] || c.name || '').slice(0, 18)),
          datasets: [{ label: 'Predicted Next Value', data: top10Pred.map((c) => Number(c.predicted_next_value || c.predicted_revenue || c.clv_12m || 0)), backgroundColor: ['#a78bfa', '#5b8def', '#00c2a8', '#ff6b35', '#ffc857', '#f472b6', '#34d399', '#fb7185', '#60a5fa', '#f59e0b'], borderRadius: 8 }],
        };
        const tierColor = (t) => { const s = String(t || '').toLowerCase(); if (s.includes('champion')) return '#ffc857'; if (s.includes('loyal')) return '#00c2a8'; if (s.includes('risk') || s.includes('churn')) return '#ff2d55'; if (s.includes('attention') || s.includes('new')) return '#5b8def'; return '#a78bfa'; };
        return (
          <div className="content-grid">
            <section className="panel hero-panel wide" style={{ background: 'linear-gradient(135deg, rgba(91,141,239,0.1), rgba(167,139,250,0.18) 70%)' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> CUSTOMER RFM PREDICTIONS</div>
                  <h1 className="hero-title">Customer behavior, churn risk, and predicted value</h1>
                  <p className="panel-subtitle">Recency 40% · Frequency 30% · Monetary 30% weighted scoring → 9-tier segments → heuristics drive churn probability + CLV.</p>
                </div>
                <div className="hero-stats">
                  <div><strong>{formatCurrency(totalPredRevenue)}</strong><span>Total Pred. 12m Revenue</span></div>
                  <div className="divider" />
                  <div><strong style={{ color: '#ffc857' }}>{highValueCount}</strong><span>High Value</span></div>
                  <div className="divider" />
                  <div><strong style={{ color: '#ff2d55' }}>{atRiskCount}</strong><span>At Risk</span></div>
                  <div className="divider" />
                  <div><strong>{formatCurrency(avgLtv)}</strong><span>Avg LTV</span></div>
                </div>
              </div>
            </section>
            <section className="panel"><div className="panel-head"><div><div className="panel-eyebrow">RANK</div><h2>Top 10 Predicted Next Value</h2></div></div><div className="chart-frame tall"><Bar data={predBars} options={chartOpts('bar')} /></div></section>
            <section className="panel">
              <div className="panel-head"><div><div className="panel-eyebrow">SEGMENTS</div><h2>Customer Tiers</h2></div></div>
              <div className="stat-stack">
                {tierList.slice(0, 9).map((s, i) => (
                  <div key={`seg-${i}`} className="metric-box">
                    <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span style={{ width: 10, height: 10, borderRadius: '50%', background: tierColor(s.segment || s.Segment || s.tier) }} />{s.segment || s.Segment || s.tier}</span>
                    <strong style={{ color: tierColor(s.segment || s.Segment || s.tier) }}>{formatNumber(s.count || s.Count || s.customers || 0)}</strong>
                    <small>{s.clv || s.CLV ? `Avg CLV ${formatCurrency(s.clv || s.CLV)}` : s.churn_share ? `Churn share ${formatPercent(Number(s.churn_share || 0) / 100)}` : 'customers'}</small>
                  </div>
                ))}
              </div>
            </section>
            <section className="panel wide">
              <div className="panel-head"><div><div className="panel-eyebrow">RFM TABLE</div><h2>Top 50 Customers — Predictions, Churn, Actions</h2></div></div>
              <div className="table-wrap"><table className="styled-table"><thead><tr><th>#</th><th>Customer</th><th>Tier</th><th>RFM Score</th><th>Churn Prob.</th><th>Pred. Next Value</th><th>CLV 12m</th><th>Recommended Action</th></tr></thead><tbody>
                {[...topCustomers].sort((a, b) => Number(b.rfm_score || b.score || 0) - Number(a.rfm_score || a.score || 0)).slice(0, 50).map((c, i) => (
                  <tr key={`cp-${i}-${c.customer_id || c['Customer ID']}`}>
                    <td><span className="rank-badge mini" style={{ background: kpiGradient(i) }}>#{i + 1}</span></td>
                    <td><strong>{c.customer_name || c['Customer Name'] || c.name}</strong><div className="muted small">{c.customer_id || c['Customer ID']}</div></td>
                    <td><span className="badge-accent" style={{ color: tierColor(c.tier), borderColor: tierColor(c.tier), textTransform: 'uppercase', letterSpacing: 0.6, fontSize: 11 }}>{c.tier || c.segment || '—'}</span></td>
                    <td><strong>{c.rfm_score ?? c.score ?? '—'}</strong> / 1000</td>
                    <td><span className={`risk-chip ${Number(c.churn_probability || 0) > 0.6 ? 'high' : Number(c.churn_probability || 0) > 0.3 ? 'medium' : ''}`}>{formatPercent(c.churn_probability || 0)}</span></td>
                    <td style={{ color: '#5b8def' }}><strong>{formatCurrency(c.predicted_next_value || c.predicted_revenue || 0)}</strong></td>
                    <td style={{ color: '#a78bfa' }}>{formatCurrency(c.clv_12m || c.clv || 0)}</td>
                    <td>{c.recommended_action || c.action || '—'}</td>
                  </tr>
                ))}
                {topCustomers.length === 0 && <tr><td colSpan={8} className="empty-row">⚙️ RFM prediction engine is processing…</td></tr>}
              </tbody></table></div>
            </section>
          </div>
        );
      }
      case 'database': {
        const st = dashboard.dbstatus;
        const hl = healthInfo;
        const tables = st?.tables || st?.table_counts || {};
        const tEntries = Object.entries(tables).sort((a, b) => Number(b[1]) - Number(a[1]));
        const barData = { labels: tEntries.map(([n]) => n), datasets: [{ label: 'Rows', data: tEntries.map(([, v]) => Number(v || 0)), backgroundColor: ['#5b8def', '#00c2a8', '#ff6b35', '#ffc857', '#a78bfa', '#f472b6', '#34d399', '#fb7185'], borderRadius: 8 }] };
        const backend = st?.backend || hl?.backend || 'unknown';
        const connected = st?.connected ?? hl?.status === 'ok';
        const csvRecords = st?.csv_records ?? dashboard.quality.records ?? 0;
        const dbOrders = st?.orders_count ?? tables.orders ?? tables.order_items ?? 0;
        const diff = Number(csvRecords || 0) - Number(dbOrders || 0);
        const handleSync = async () => {
          if (role !== 'Admin') return;
          setSyncStatus({ type: 'info', message: 'Syncing CSV → MySQL star-schema…' });
          try {
            const r = await apiRequest('/api/db/sync', token, { method: 'POST' });
            auditLog('db_sync', 'success', { details: r });
            setSyncStatus({ type: 'success', message: `Sync complete · ${r?.tables_synced || Object.keys(r || {}).length} tables updated` });
            setViewRefresh((p) => ({ ...p, database: (p.database || 0) + 1 }));
          } catch (e) {
            auditLog('db_sync', 'fail', { error: e.message });
            setSyncStatus({ type: 'error', message: e.message || 'Sync failed' });
          }
        };
        return (
          <div className="content-grid">
            <section className="panel hero-panel wide" style={{ background: 'linear-gradient(135deg, rgba(91,141,239,0.1), rgba(0,194,168,0.14) 70%)' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> DATABASE CONTROL TOWER</div>
                  <h1 className="hero-title">Database connection status and data sync</h1>
                  <p className="panel-subtitle">Star-schema tables: orders / customers / products / locations / returns / daily_sales_agg / order_items. Auto-syncs on Admin upload and via /api/db/sync.</p>
                </div>
                <div className="hero-stats">
                  <div><strong style={{ color: connected ? '#00c2a8' : '#ff2d55' }}>{connected ? 'CONNECTED' : 'FALLBACK'}</strong><span>{backend} backend</span></div>
                  <div className="divider" />
                  <div><strong>{tEntries.length}</strong><span>Tables</span></div>
                  <div className="divider" />
                  <div><strong>{formatNumber(tEntries.reduce((a, [, v]) => a + Number(v || 0), 0))}</strong><span>Total Rows</span></div>
                </div>
              </div>
            </section>
            <section className="panel">
              <div className="panel-head"><div><div className="panel-eyebrow">STATUS</div><h2>Connection &amp; Engine</h2></div><span className={`badge-${connected ? 'good' : 'accent'}`}>{connected ? '✓ Online' : '⚠ SQLite Fallback'}</span></div>
              <div className="stat-stack">
                <div className="metric-box gold"><span>Backend</span><strong style={{ textTransform: 'uppercase' }}>{backend}</strong><small>{st?.database || st?.db_name || hl?.database || 'nexus_commerce_bi'}</small></div>
                <div className="metric-box slate"><span>Dataset</span><strong>{st?.dataset_name || st?.active_dataset || 'active'}</strong><small>{hl?.records != null ? `${formatNumber(hl.records)} records` : `${formatNumber(csvRecords)} CSV rows`}</small></div>
                <div className="metric-box orange"><span>Version</span><strong>v{hl?.version || '1.0'}</strong><small>{hl?.uptime || '—'}</small></div>
              </div>
              {role === 'Admin' && (
                <div style={{ marginTop: 16 }}>
                  <button className="primary-cta" onClick={handleSync} disabled={syncStatus.type === 'info'}>{syncStatus.type === 'info' ? '⏳ Syncing…' : '🔁 Sync Now (CSV → DB)'}</button>
                  {syncStatus.message && <div className={`upload-msg ${syncStatus.type}`} style={{ marginTop: 10 }}>{syncStatus.message}</div>}
                </div>
              )}
            </section>
            <section className="panel wide">
              <div className="panel-head"><div><div className="panel-eyebrow">ROW COUNTS</div><h2>Rows Per Table</h2></div></div>
              <div className="chart-frame"><Bar data={barData} options={chartOpts('bar')} /></div>
            </section>
            <section className="panel">
              <div className="panel-head"><div><div className="panel-eyebrow">PARITY</div><h2>CSV vs DB — Orders</h2></div>{diff === 0 ? <span className="badge-good">MATCHED</span> : <span className="badge-accent">{diff > 0 ? `${diff} CSV-only` : `${-diff} DB-only`}</span>}</div>
              <div className="metric-grid">
                <div className="metric-box"><span>📄 CSV records</span><strong>{formatNumber(csvRecords)}</strong></div>
                <div className="metric-box"><span>🗄️ DB orders</span><strong>{formatNumber(dbOrders)}</strong></div>
                <div className="metric-box"><span>Δ Difference</span><strong style={{ color: diff === 0 ? '#00c2a8' : '#ff6b35' }}>{diff >= 0 ? `+${formatNumber(diff)}` : formatNumber(diff)}</strong></div>
                <div className="metric-box"><span>Health</span><strong style={{ color: Math.abs(diff) < 5 ? '#00c2a8' : Math.abs(diff) < 50 ? '#ffc857' : '#ff2d55' }}>{Math.abs(diff) < 5 ? 'Excellent' : Math.abs(diff) < 50 ? 'Sync Recommended' : 'Out of Sync'}</strong></div>
              </div>
            </section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">DETAIL</div><h2>Table Inventory</h2></div></div>
              <div className="table-wrap"><table className="styled-table"><thead><tr><th>Table</th><th>Rows</th><th>Engine</th><th>Notes</th></tr></thead><tbody>
                {tEntries.map(([name, rows], i) => (
                  <tr key={name}>
                    <td><span className="rank-badge mini" style={{ background: kpiGradient(i) }}>#{i + 1}</span> <strong>{name}</strong></td>
                    <td>{formatNumber(rows)}</td>
                    <td><span className="badge-accent">{backend}</span></td>
                    <td className="muted small">{String(name).toLowerCase().includes('daily') ? 'Aggregate summary' : String(name).toLowerCase().includes('orders') ? 'Fact table' : String(name).toLowerCase().includes('customer') || String(name).toLowerCase().includes('product') || String(name).toLowerCase().includes('location') ? 'Dimension' : ''}</td>
                  </tr>
                ))}
                {tEntries.length === 0 && <tr><td colSpan={4} className="empty-row">⚙️ Connect to MySQL or run sync to populate table stats.</td></tr>}
              </tbody></table></div>
            </section>
          </div>
        );
      }
      case 'dataimport': {
        const isAdmin = role === 'Admin';
        return (
          <div className="content-grid">
            <section className="panel hero-panel wide" style={{ background: 'linear-gradient(135deg, rgba(255,200,87,0.1), rgba(255,107,53,0.14) 70%)' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> DATA IMPORT CENTER</div>
                  <h1 className="hero-title">{isAdmin ? 'Upload a new CSV dataset to refresh the entire platform' : 'Data import is available for Administrators'}</h1>
                  <p className="panel-subtitle">Files must contain: <code>order_id, order_date, customer_id, product_category, product_name, quantity, net_amount, region, order_status</code>.</p>
                </div>
                <div className="hero-stats">
                  <div><strong>{formatNumber(dashboard.quality.records || 0)}</strong><span>Current Rows</span></div>
                  <div className="divider" />
                  <div><strong>{dashboard.quality.date_min || '—'}</strong><span>Start</span></div>
                  <div className="divider" />
                  <div><strong>{dashboard.quality.date_max || '—'}</strong><span>End</span></div>
                </div>
              </div>
            </section>
            {isAdmin ? (
              <section className="panel upload-panel wide">
                <div className="upload-head">
                  <div className="upload-head-text">
                    <div className="panel-eyebrow" style={{ color: '#ffc857' }}>⚡ CSV UPLOAD</div>
                    <h2>Drop new dataset</h2>
                    <p className="panel-subtitle">Upload will refresh KPIs, retrain models, sync to MySQL (if connected), and increment data version.</p>
                  </div>
                </div>
                <div className={`dropzone ${isDragOver ? 'drag-over' : ''} ${uploadFile ? 'has-file' : ''}`} onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }} onDragLeave={() => setIsDragOver(false)} onDrop={(e) => { e.preventDefault(); setIsDragOver(false); handleFilePick(e.dataTransfer.files); }} onClick={() => fileInputRef.current?.click()}>
                  <input ref={fileInputRef} type="file" accept=".csv,text/csv" style={{ display: 'none' }} onChange={(e) => handleFilePick(e.target.files)} />
                  {uploadFile ? (
                    <div className="dropzone-content filled">
                      <div className="file-card">
                        <div className="file-icon-wrap"><Icon name="file" /></div>
                        <div className="file-info">
                          <strong>{uploadFile.name}</strong>
                          <div className="muted small">{(uploadFile.size / 1024 / 1024).toFixed(2)} MB · Ready to upload</div>
                        </div>
                        <button className="primary-cta" onClick={(e) => { e.stopPropagation(); handleUpload(); }} disabled={uploading}>{uploading ? '⏳ Uploading…' : (<><Icon name="upload" /> Upload &amp; Refresh</>)}</button>
                      </div>
                    </div>
                  ) : (
                    <div className="dropzone-content">
                      <div className="dz-icon-orb"><Icon name="upload" /></div>
                      <div className="dz-title">{isDragOver ? 'Drop the CSV file now' : 'Drag & drop your CSV file here'}</div>
                      <div className="dz-sub">or <span className="dz-link">browse from your computer</span></div>
                      <div className="dz-tags">
                        <span className="dz-chip">📦 order_id · order_date · customer_id · product_category · product_name · quantity · net_amount · region · order_status</span>
                      </div>
                    </div>
                  )}
                </div>
                {uploadStatus.message && (
                  <div className={`upload-msg ${uploadStatus.type}`}>
                    {uploadStatus.type === 'success' && <span className="msg-icon ok"><Icon name="check" /></span>}
                    {uploadStatus.type === 'error' && <span className="msg-icon bad">⚠️</span>}
                    {uploadStatus.type === 'info' && <span className="msg-icon info">⏳</span>}
                    {uploadStatus.message}
                  </div>
                )}
              </section>
            ) : (
              <section className="panel wide"><div className="panel-head"><div><h2>🔒 Admin access required</h2><p className="panel-subtitle">Contact your workspace Administrator to import datasets.</p></div></div></section>
            )}
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">RECENT IMPORT HISTORY</div><h2>Recent Actions</h2></div></div>
              <div className="table-wrap"><table className="styled-table"><thead><tr><th>When</th><th>Actor</th><th>Action</th><th>Status</th></tr></thead><tbody>
                {(JSON.parse(localStorage.getItem('nexus_audit') || '[]')).filter((e) => /upload|sync|import/i.test(e.action)).slice().reverse().slice(0, 10).map((e, i) => (
                  <tr key={`ih-${i}`}>
                    <td>{new Date(e.timestamp).toLocaleString()}</td>
                    <td>{e.actor}</td>
                    <td>{e.action}</td>
                    <td><span className={`risk-chip ${e.status === 'success' ? '' : 'high'}`}>{e.status}</span></td>
                  </tr>
                ))}
                {!JSON.parse(localStorage.getItem('nexus_audit') || '[]').filter((e) => /upload|sync|import/i.test(e.action)).length && <tr><td colSpan={4} className="empty-row">No recent import activity.</td></tr>}
              </tbody></table></div>
            </section>
          </div>
        );
      }
      case 'export': {
        const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const downloadCsv = (csvText, filename) => {
          const bom = '\uFEFF';
          const blob = new Blob([bom + csvText], { type: 'text/csv;charset=utf-8' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename.replace('{{TS}}', stamp);
          document.body.appendChild(a);
          a.click();
          a.remove();
          setTimeout(() => URL.revokeObjectURL(url), 1000);
        };
        const doExport = async (endpoint, filename, extractor) => {
          try {
            setStatus(`Exporting ${filename}…`);
            const extra = buildQuery(filters);
            const url = extra ? (endpoint.includes('?') ? `${endpoint}${extra.replace('?', '&')}` : `${endpoint}${extra}`) : endpoint;
            const data = await apiRequest(url, token);
            const rows = extractor ? extractor(data) : (Array.isArray(data) ? data : (data?.records || data?.daily || data?.days || data?.rows || data?.items || data?.data || []));
            if (!Array.isArray(rows) || rows.length === 0) {
              throw new Error('No rows returned for export.');
            }
            const csv = toCsv(rows);
            downloadCsv(csv, filename);
            auditLog('export', 'success', { filename, rows: rows.length });
            setStatus(`Exported ${filename} (${formatNumber(rows.length)} rows)`);
          } catch (e) {
            const msg = e?.message || String(e) || 'Unknown error';
            auditLog('export', 'fail', { filename, error: msg });
            setStatus(`Export failed: ${msg}`);
          }
        };
        const doFullReport = async () => {
          setStatus('Running full report…');
          const jobs = [
            { endpoint: '/api/sales/records?limit=500000', filename: 'report-sales-{{TS}}.csv', extractor: salesExtractor },
            { endpoint: '/api/sales/daily/report', filename: 'report-daily-{{TS}}.csv', extractor: dailyExtractor },
            { endpoint: '/api/products/top?limit=500', filename: 'report-products-{{TS}}.csv' },
            { endpoint: '/api/customers/top?limit=500', filename: 'report-customers-{{TS}}.csv' },
          ];
          const results = await Promise.allSettled(jobs.map((j) => doExport(j.endpoint, j.filename, j.extractor)));
          const ok = results.filter((r) => r.status === 'fulfilled').length;
          auditLog('report', ok === jobs.length ? 'success' : 'partial', { files: jobs.length, ok });
          setStatus(`Report complete: ${ok}/${jobs.length} generated`);
        };
        const salesExtractor = (d) => d?.records || d || [];
        const dailyExtractor = (d) => {
          if (Array.isArray(d?.daily)) return d.daily;
          if (Array.isArray(d?.summary)) return d.summary;
          return Object.entries(d?.summary || d || {}).map((pair) => ({ metric: pair[0], value: pair[1] }));
        };
        return (
          <div className="content-grid">
            <section className="panel hero-panel wide" style={{ background: 'linear-gradient(135deg, rgba(52,211,153,0.1), rgba(91,141,239,0.16) 70%)' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> EXPORT &amp; REPORTS</div>
                  <h1 className="hero-title">Download reports and export data</h1>
                  <p className="panel-subtitle">All exports honour the current Filters (region, category, segment, year). Reports include timestamp.</p>
                </div>
                <div className="hero-stats">
                  <div><strong>4</strong><span>Exporters</span></div>
                  <div className="divider" />
                  <div><strong>CSV</strong><span>Format</span></div>
                  <div className="divider" />
                  <div><strong>{stamp.slice(0, 10)}</strong><span>Generated</span></div>
                </div>
              </div>
            </section>
            <section className="panel"><div className="panel-head"><div><div className="panel-eyebrow">DOWNLOADS</div><h2>Data Extracts</h2></div></div>
              <div className="stat-stack">
                <button className="metric-box gold" onClick={() => doExport('/api/sales/records?limit=500000', `nexus-sales-{{TS}}.csv`, salesExtractor)} style={{ textAlign: 'left', cursor: 'pointer' }}><span>📄 Sales Records (CSV)</span><strong>All rows</strong><small>Filtered; up to 500k rows</small></button>
                <button className="metric-box slate" onClick={() => doExport('/api/products/top?limit=500', `nexus-top-products-{{TS}}.csv`)} style={{ textAlign: 'left', cursor: 'pointer' }}><span>🏆 Top Products (CSV)</span><strong>Ranked</strong><small>By revenue, units, margin</small></button>
                <button className="metric-box orange" onClick={() => doExport('/api/customers/top?limit=500', `nexus-top-customers-{{TS}}.csv`)} style={{ textAlign: 'left', cursor: 'pointer' }}><span>👥 Top Customers (CSV)</span><strong>VIP roster</strong><small>With LTV, orders, segment</small></button>
                <button className="metric-box" onClick={() => doExport('/api/sales/daily/report', `nexus-daily-agg-{{TS}}.csv`, dailyExtractor)} style={{ textAlign: 'left', cursor: 'pointer' }}><span>📊 Daily Aggregates (CSV)</span><strong>Rollup</strong><small>Per-day sales, returns, margin</small></button>
              </div>
            </section>
            <section className="panel"><div className="panel-head"><div><div className="panel-eyebrow">FULL REPORT</div><h2>Generate Comprehensive Report</h2></div></div>
              <div className="insight" style={{ marginBottom: 14 }}>📦 Runs 4 exports in parallel and packages a complete snapshot with KPIs, segment breakdown, daily aggregates, top buyers, and SKU rankings.</div>
              <button className="primary-cta" onClick={doFullReport}>🗂️ Generate Full Report (4 files)</button>
            </section>
            <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">HISTORY</div><h2>Recent Exports</h2></div></div>
              <div className="table-wrap"><table className="styled-table"><thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Status</th></tr></thead><tbody>
                {(JSON.parse(localStorage.getItem('nexus_audit') || '[]')).filter((e) => /export|report/i.test(e.action)).slice().reverse().slice(0, 10).map((e, i) => (
                  <tr key={`eh-${i}`}><td>{new Date(e.timestamp).toLocaleString()}</td><td>{e.actor}</td><td>{e.action}</td><td><span className={`risk-chip ${e.status === 'success' ? '' : 'high'}`}>{e.status}</span></td></tr>
                ))}
                {!JSON.parse(localStorage.getItem('nexus_audit') || '[]').filter((e) => /export|report/i.test(e.action)).length && <tr><td colSpan={4} className="empty-row">No exports yet — click any extract above to begin.</td></tr>}
              </tbody></table></div>
            </section>
          </div>
        );
      }
      case 'audit': {
        const raw = (() => { try { return JSON.parse(localStorage.getItem('nexus_audit') || '[]'); } catch { return []; } })();
        const rows = [...raw].reverse();
        const clear = () => { if (role === 'Admin') { localStorage.removeItem('nexus_audit'); setViewRefresh((p) => ({ ...p, audit: (p.audit || 0) + 1 })); auditLog('audit_clear', 'success'); } };
        return (
          <div className="content-grid">
            <section className="panel hero-panel wide" style={{ background: 'linear-gradient(135deg, rgba(244,114,182,0.08), rgba(130,88,255,0.16) 70%)' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> AUDIT LOGS</div>
                  <h1 className="hero-title">Recent activity log</h1>
                  <p className="panel-subtitle">Captured via auditLog() helper. Persists in localStorage <code>nexus_audit</code>. Admin-only clear.</p>
                </div>
                <div className="hero-stats">
                  <div><strong>{formatNumber(rows.length)}</strong><span>Events</span></div>
                  <div className="divider" />
                  <div><strong>{formatNumber(rows.filter((r) => r.status !== 'success').length)}</strong><span>Failures</span></div>
                  <div className="divider" />
                  <div><strong>{new Set(rows.map((r) => r.actor)).size}</strong><span>Actors</span></div>
                </div>
              </div>
            </section>
            <section className="panel wide">
              <div className="panel-head"><div><div className="panel-eyebrow">EVENTS</div><h2>Event Stream</h2></div>{role === 'Admin' && <button className="ghost-button" onClick={clear}>🗑️ Clear Audit</button>}</div>
              <div className="table-wrap"><table className="styled-table"><thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Status</th><th>Details</th></tr></thead><tbody>
                {rows.map((r, i) => (
                  <tr key={`aud-${i}-${r.timestamp}-${r.action}`}>
                    <td>{new Date(r.timestamp).toLocaleString()}</td>
                    <td><span className="badge-accent">{r.actor || 'Viewer'}</span></td>
                    <td><strong>{r.action}</strong></td>
                    <td><span className={`risk-chip ${r.status === 'success' ? '' : r.status === 'fail' ? 'high' : 'medium'}`}>{r.status || '—'}</span></td>
                    <td className="muted small">{r.email || r.filename || r.details || (r.error ? String(r.error).slice(0, 80) : '') || '—'}</td>
                  </tr>
                ))}
                {rows.length === 0 && <tr><td colSpan={5} className="empty-row">No audit events yet.</td></tr>}
              </tbody></table></div>
            </section>
          </div>
        );
      }
      case 'users': {
        const elevated = role === 'Admin' || role === 'Business Manager';
        const isAdmin = role === 'Admin';
        const currentEmail = String(localStorage.getItem('nexus_email') || '').toLowerCase();
        const raw = usersList || {};
        const list = Array.isArray(raw.records) ? raw.records : (Array.isArray(raw.users) ? raw.users : (Array.isArray(raw.list) ? raw.list : (Array.isArray(usersList) ? usersList : [])));
        const total = Number.isFinite(raw.total) ? raw.total : list.length;
        const serverRoleCounts = raw.role_counts && typeof raw.role_counts === 'object' ? raw.role_counts : null;
        const byRole = serverRoleCounts
          ? { ...serverRoleCounts }
          : list.reduce((acc, u) => {
              const r = u.role || u.Role || 'Viewer';
              acc[r] = (acc[r] || 0) + 1;
              return acc;
            }, {});
        const roleColor = (r) => { const s = String(r || '').toLowerCase(); if (s.includes('admin')) return '#a78bfa'; if (s.includes('business') || s.includes('manager')) return '#5b8def'; if (s.includes('analyst')) return '#00c2a8'; return '#94a3b8'; };
        const ROLES = ['Admin', 'Business Manager', 'Analyst', 'Viewer'];
        const refreshUsers = async () => {
          try {
            const ul = await apiRequest('/api/management/users', token);
            setUsersList(ul);
          } catch {}
        };
        const saveRole = async (u) => {
          const patchRole = usersEdit[u.id] && ROLES.includes(usersEdit[u.id]) ? usersEdit[u.id] : null;
          if (!patchRole || patchRole === u.role) {
            setUsersEdit((prev) => { const copy = { ...prev }; delete copy[u.id]; return copy; });
            return;
          }
          try {
            setUsersSaving((prev) => ({ ...prev, [u.id]: 'saving' }));
            await apiRequest(`/api/management/users/${u.id}/role`, token, { method: 'PATCH', body: JSON.stringify({ role: patchRole }) });
            setUsersEdit((prev) => { const copy = { ...prev }; delete copy[u.id]; return copy; });
            setStatus(`${u.email} role updated to ${patchRole}`);
            await refreshUsers();
          } catch (err) {
            setStatus(err.message || 'Failed to update role');
          } finally {
            setUsersSaving((prev) => { const copy = { ...prev }; delete copy[u.id]; return copy; });
          }
        };
        const deleteUser = async (u) => {
          const ok = window.confirm(`Remove user ${u.email}? This cannot be undone.`);
          if (!ok) return;
          try {
            setUsersSaving((prev) => ({ ...prev, [u.id]: 'deleting' }));
            await apiRequest(`/api/management/users/${u.id}`, token, { method: 'DELETE' });
            setStatus(`Removed ${u.email}`);
            await refreshUsers();
          } catch (err) {
            setStatus(err.message || 'Failed to remove user');
          } finally {
            setUsersSaving((prev) => { const copy = { ...prev }; delete copy[u.id]; return copy; });
          }
        };
        const submitInvite = async (e) => {
          if (e) e.preventDefault();
          if (!inviteForm.email || !inviteForm.password) {
            setStatus('Email and password are required to invite a user');
            return;
          }
          try {
            setInviteSubmitting(true);
            await apiRequest('/api/management/users/invite', token, {
              method: 'POST',
              body: JSON.stringify({ email: inviteForm.email, password: inviteForm.password, role: inviteForm.role || 'Viewer' }),
            });
            setInviteForm({ email: '', password: '', role: 'Viewer' });
            setStatus('Invite created');
            await refreshUsers();
          } catch (err) {
            setStatus(err.message || 'Failed to create invite');
          } finally {
            setInviteSubmitting(false);
          }
        };
        return (
          <div className="content-grid">
            <section className="panel hero-panel wide" style={{ background: 'linear-gradient(135deg, rgba(167,139,250,0.12), rgba(244,114,182,0.1) 70%)' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> USERS &amp; ROLES</div>
                  <h1 className="hero-title">{elevated ? 'Workspace membership and role assignments' : 'User visibility limited to Admins and Business Managers'}</h1>
                  <p className="panel-subtitle">Roles: <span style={{ color: '#a78bfa' }}>Admin</span> · <span style={{ color: '#5b8def' }}>Business Manager</span> · <span style={{ color: '#00c2a8' }}>Analyst</span> · <span style={{ color: '#94a3b8' }}>Viewer</span></p>
                </div>
                <div className="hero-stats">
                  <div><strong>{formatNumber(total || Object.values(byRole).reduce((a, b) => a + b, 0))}</strong><span>Total Users</span></div>
                  <div className="divider" />
                  <div><strong style={{ color: '#a78bfa' }}>{byRole.Admin || 0}</strong><span>Admins</span></div>
                  <div className="divider" />
                  <div><strong style={{ color: '#5b8def' }}>{byRole['Business Manager'] || byRole.Manager || 0}</strong><span>Managers</span></div>
                  <div className="divider" />
                  <div><strong style={{ color: '#00c2a8' }}>{byRole.Analyst || 0}</strong><span>Analysts</span></div>
                </div>
              </div>
            </section>
            {elevated ? (
              <>
                <section className="panel" style={{ minWidth: 340 }}>
                  <div className="panel-head"><div><div className="panel-eyebrow">INVITE</div><h2>Add team member</h2></div></div>
                  <form onSubmit={submitInvite} className="stat-stack" style={{ gap: 10 }}>
                    <div className="field" style={{ marginTop: 4 }}>
                      <label>Work email</label>
                      <input value={inviteForm.email} onChange={(e) => setInviteForm((p) => ({ ...p, email: e.target.value }))} placeholder="name@company.com" />
                    </div>
                    <div className="field" style={{ marginTop: 4 }}>
                      <label>Temporary password</label>
                      <input type="password" value={inviteForm.password} onChange={(e) => setInviteForm((p) => ({ ...p, password: e.target.value }))} placeholder="Min 8 characters" />
                    </div>
                    <div className="field" style={{ marginTop: 4 }}>
                      <label>Role</label>
                      <select value={inviteForm.role || 'Viewer'} onChange={(e) => setInviteForm((p) => ({ ...p, role: e.target.value }))}>
                        {ROLES.map((rr) => <option key={rr} value={rr}>{rr}</option>)}
                      </select>
                    </div>
                    <button type="submit" className="cta-primary" style={{ marginTop: 6 }} disabled={inviteSubmitting}>
                      {inviteSubmitting ? 'Creating…' : '+ Invite user'}
                    </button>
                    <div className="insight" style={{ marginTop: 6 }}>🔐 Password is hashed (sha256 + salt) before storage. Share the password securely with the new user.</div>
                  </form>
                </section>
                <section className="panel wide"><div className="panel-head"><div><div className="panel-eyebrow">DIRECTORY</div><h2>All Users</h2><div className="panel-subtitle" style={{ marginTop: 4 }}>{isAdmin ? 'Click a ROLE badge to edit it, then save. Remove users with the 🗑️ action. You cannot edit or delete yourself.' : 'Only Admins can change roles and delete users.'}</div></div><span className="badge-good">{formatNumber(total || list.length)} members</span></div>
                  <div className="table-wrap"><table className="styled-table"><thead><tr><th>#</th><th>Email</th><th>Role</th><th>Created</th><th style={{ width: 180 }}>Actions</th></tr></thead><tbody>
                    {list.map((u, i) => {
                      const isSelf = String(u.email || '').toLowerCase() === currentEmail;
                      const savingState = usersSaving[u.id];
                      const editing = Object.prototype.hasOwnProperty.call(usersEdit, u.id);
                      const roleValue = editing ? (usersEdit[u.id] || u.role) : (u.role || u.Role || 'Viewer');
                      const color = roleColor(roleValue);
                      return (
                        <tr key={`u-${i}-${u.id || u.email}`}>
                          <td><span className="rank-badge mini" style={{ background: kpiGradient(i) }}>#{i + 1}</span></td>
                          <td><strong>{u.email || u.Email || '—'}</strong>{isSelf && <span className="muted small" style={{ marginLeft: 8 }}>(you)</span>}</td>
                          <td>
                            {editing && isAdmin && !isSelf ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <select value={roleValue} onChange={(e) => setUsersEdit((p) => ({ ...p, [u.id]: e.target.value }))}>
                                  {ROLES.map((rr) => <option key={rr} value={rr}>{rr}</option>)}
                                </select>
                                <button className="cta-primary" style={{ padding: '6px 10px', fontSize: 12 }} onClick={() => saveRole(u)} disabled={savingState === 'saving'}>
                                  {savingState === 'saving' ? 'Saving…' : 'Save'}
                                </button>
                                <button className="cta-secondary" style={{ padding: '6px 10px', fontSize: 12 }} onClick={() => setUsersEdit((p) => { const copy = { ...p }; delete copy[u.id]; return copy; })}>Cancel</button>
                              </div>
                            ) : (
                              <span
                                className="badge-accent"
                                style={{ color, borderColor: color, textTransform: 'uppercase', letterSpacing: 0.6, fontSize: 11, cursor: isAdmin && !isSelf ? 'pointer' : 'default' }}
                                title={isAdmin && !isSelf ? 'Click to edit role' : (isSelf ? 'You cannot modify your own role' : 'Only Admins can change roles')}
                                onClick={() => { if (isAdmin && !isSelf) setUsersEdit((p) => ({ ...p, [u.id]: u.role || 'Viewer' })); }}
                              >{roleValue}</span>
                            )}
                          </td>
                          <td className="muted small">{u.created_at || u.CreatedAt || u['Created At'] || '—'}</td>
                          <td style={{ textAlign: 'right' }}>
                            {isAdmin && !isSelf ? (
                              <button className="cta-secondary" style={{ padding: '6px 10px', fontSize: 12, color: '#ff6b35', borderColor: 'rgba(255,107,53,0.35)' }} onClick={() => deleteUser(u)} disabled={savingState === 'deleting'}>
                                {savingState === 'deleting' ? 'Deleting…' : '🗑️ Remove'}
                              </button>
                            ) : (
                              <span className="muted small">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                    {list.length === 0 && <tr><td colSpan={5} className="empty-row">⚙️ Loading or no users returned.</td></tr>}
                  </tbody></table></div>
                </section>
              </>
            ) : (
              <section className="panel wide">
                <div className="kpi-list"><div className="kpi-card"><div className="kpi-label">👤 Current User</div><div className="kpi-value" style={{ fontSize: 18 }}>{localStorage.getItem('nexus_email') || 'demo@example.com'}</div><div className="kpi-sub">Role: {role}</div></div></div>
                <div className="insight" style={{ marginTop: 16 }}>🔒 Contact an Admin to request elevated access or manage the workspace directory.</div>
              </section>
            )}
          </div>
        );
      }
      case 'settings': {
        const saveSettings = (patch) => {
          const next = { ...appSettings, ...patch };
          setAppSettings(next);
          try { localStorage.setItem('nexus_settings', JSON.stringify(next)); } catch {}
          setStatus(`Settings updated`);
        };
        const toggleTheme = () => saveSettings({ theme: appSettings.theme === 'light' ? 'dark' : 'light' });
        let dsPath = '—';
        try {
          dsPath = dashboard.dbstatus?.dataset_path || dashboard.dbstatus?.dataset_name || dashboard.dbstatus?.active_dataset || 'Default dataset';
        } catch {}
        return (
          <div className="content-grid">
            <section className="panel hero-panel wide" style={{ background: 'linear-gradient(135deg, rgba(91,141,239,0.1), rgba(130,88,255,0.16) 70%)' }}>
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> WORKSPACE SETTINGS</div>
                  <h1 className="hero-title">App settings and preferences</h1>
                  <p className="panel-subtitle">Persisted in localStorage <code>nexus_settings</code>.</p>
                </div>
                <div className="hero-stats">
                  <div><strong style={{ textTransform: 'capitalize' }}>{appSettings.theme || 'dark'}</strong><span>Theme</span></div>
                  <div className="divider" />
                  <div><strong>{appSettings.forecastHorizon || 7}d</strong><span>Forecast Horizon</span></div>
                  <div className="divider" />
                  <div><strong>{role}</strong><span>Your Role</span></div>
                </div>
              </div>
            </section>
            <section className="panel">
              <div className="panel-head"><div><div className="panel-eyebrow">APPEARANCE</div><h2>Theme</h2></div></div>
              <div className="stat-stack">
                <button className="metric-box" onClick={toggleTheme} style={{ cursor: 'pointer', textAlign: 'left' }}>
                  <span>🎨 Current theme</span>
                  <strong style={{ textTransform: 'capitalize' }}>{appSettings.theme || 'dark'}</strong>
                  <small>Click to toggle between light and dark</small>
                </button>
              </div>
            </section>
            <section className="panel">
              <div className="panel-head"><div><div className="panel-eyebrow">FORECASTING</div><h2>Default Forecast Horizon</h2></div></div>
              <div className="field" style={{ marginTop: 4 }}>
                <label>Horizon (days)</label>
                <select value={appSettings.forecastHorizon || 7} onChange={(e) => saveSettings({ forecastHorizon: Number(e.target.value) })}>
                  <option value={1}>1 day (tomorrow only)</option>
                  <option value={7}>7 days (1 week)</option>
                  <option value={14}>14 days (2 weeks)</option>
                  <option value={30}>30 days (1 month)</option>
                </select>
              </div>
              <div className="insight" style={{ marginTop: 12 }}>💡 Used by the dedicated Forecast page for both RandomForest and XGBoost.</div>
            </section>
            <section className="panel wide">
              <div className="panel-head"><div><div className="panel-eyebrow">INFORMATION</div><h2>System Information</h2></div></div>
              <div className="metric-grid">
                <div className="metric-box"><span>📁 Active Dataset</span><strong style={{ fontSize: 15, wordBreak: 'break-all' }}>{dsPath}</strong></div>
                <div className="metric-box"><span>🗄️ Database Backend</span><strong style={{ textTransform: 'uppercase' }}>{dashboard.dbstatus?.backend || healthInfo?.backend || 'SQLite Fallback'}</strong><small>{dashboard.dbstatus?.database || dashboard.dbstatus?.db_name || 'nexus_commerce_bi'}</small></div>
                <div className="metric-box"><span>🔐 App Secret</span><strong>••••••••••••</strong><small>HMAC signed tokens · 8h expiry</small></div>
                <div className="metric-box"><span>📈 Records Indexed</span><strong>{formatNumber(dashboard.quality?.records || 0)}</strong><small>{dashboard.quality?.date_min || '—'} → {dashboard.quality?.date_max || '—'}</small></div>
              </div>
            </section>
            <section className="panel wide">
              <div className="panel-head"><div><div className="panel-eyebrow">ACCOUNT</div><h2>Current Session</h2></div></div>
              <div className="metric-grid">
                <div className="metric-box"><span>🧑 Email</span><strong>{localStorage.getItem('nexus_email') || 'demo@example.com'}</strong></div>
                <div className="metric-box"><span>🎖️ Role</span><strong style={{ color: '#a78bfa' }}>{role}</strong></div>
                <div className="metric-box"><span>🪙 Token Status</span><strong style={{ color: token ? '#00c2a8' : '#ff2d55' }}>{token ? 'Valid · Present' : 'Missing'}</strong></div>
                <div className="metric-box"><span>🚪 Sign Out</span><strong style={{ cursor: 'pointer', color: '#ff6b35' }} onClick={logout}>Click here</strong></div>
              </div>
            </section>
          </div>
        );
      }
      case 'overview':
      default:
        return (
          <div className="content-grid">
            <section className="panel wide hero-panel">
              <div className="hero-inner">
                <div>
                  <div className="hero-badge"><Icon name="spark" /> LIVE INTELLIGENCE</div>
                  <h1 className="hero-title">Business Performance Overview</h1>
                  <p className="hero-subtitle">
                    Monitor <strong>{formatNumber(dashboard.quality.records || 0)}</strong> rows of commerce data across{' '}
                    <strong>{meta.regions.length}</strong> regions,{' '}
                    <strong>{meta.categories.length}</strong> categories,{' '}
                    <strong>{formatNumber(dashboard.kpis.orders)}</strong> orders.
                  </p>
                  <div className="hero-stats">
                    <div>
                      <strong>{formatCurrency(dashboard.kpis.sales)}</strong>
                      <span>Total Revenue</span>
                    </div>
                    <div className="divider" />
                    <div>
                      <strong>{formatPercent(dashboard.kpis.profit_margin)}</strong>
                      <span>Margin</span>
                    </div>
                    <div className="divider" />
                    <div>
                      <strong>{formatPercent(dashboard.kpis.return_rate)}</strong>
                      <span>Return Rate</span>
                    </div>
                  </div>
                </div>
                <div className="hero-chart">
                  <div className="chart-frame"><Line data={salesTrend} options={chartOpts('line')} /></div>
                </div>
              </div>
            </section>

            <section className="panel">
              <div className="panel-head"><div className="panel-eyebrow">CATEGORY SPLIT</div><h2>Revenue by Category</h2></div>
              <div className="chart-frame"><Bar data={categoryChart} options={chartOpts('bar')} /></div>
            </section>

            <section className="panel">
              <div className="panel-head"><div className="panel-eyebrow">PORTFOLIO MIX</div><h2>Revenue Composition</h2></div>
              <div className="chart-frame"><Doughnut data={categoryPieChart} options={doughnutOpts} /></div>
            </section>

            <section className="panel">
              <div className="panel-head"><div className="panel-eyebrow">KEY METRICS</div><h2>Business Snapshot</h2></div>
              <div className="metric-grid">
                <div className="metric-box"><span>💰 Profit Margin</span><strong>{formatPercent(dashboard.kpis.profit_margin)}</strong></div>
                <div className="metric-box"><span>🛒 Avg Order Value</span><strong>{formatCurrency(dashboard.kpis.average_order_value)}</strong></div>
                <div className="metric-box"><span>↩️ Return Rate</span><strong style={{ color: Number(dashboard.kpis.return_rate) > 10 ? '#ff6b35' : '#00c2a8' }}>{formatPercent(dashboard.kpis.return_rate)}</strong></div>
                <div className="metric-box"><span>📦 Units Sold</span><strong>{formatNumber(dashboard.kpis.quantity)}</strong></div>
              </div>
            </section>

            <section className="panel">
              <div className="panel-head"><div className="panel-eyebrow">TOP PERFORMERS</div><h2>Best Selling Products</h2></div>
              <div className="table-wrap">
                <table className="styled-table compact">
                  <thead><tr><th>#</th><th>Product</th><th>Revenue</th></tr></thead>
                  <tbody>
                    {(dashboard.topProducts || []).slice(0, 5).map((item, i) => (
                      <tr key={`${item['Product ID']}-${item['Product Name']}`}>
                        <td><span className="rank-badge mini" style={{ background: kpiGradient(i) }}>{i + 1}</span></td>
                        <td><strong>{item['Product Name']}</strong></td>
                        <td>{formatCurrency(item.sales)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        );
    }
  };

  if (!authenticated) {
    return (
      <div className="login-shell">
        <div className="login-bg-orb orb-a" />
        <div className="login-bg-orb orb-b" />
        <div className="login-panel panel">
          <div className="login-logo">
            <div className="logo-gem">
              <Icon name="spark" />
            </div>
            <div>
              <div className="eyebrow">Nexus Intelligence</div>
              <h1 style={{ fontSize: 26, marginTop: 2 }}>Commerce BI</h1>
            </div>
          </div>
          <p className="login-lead">
            Sign in to access your commerce decision-support workspace.
          </p>

          {/* Status Banners */}
          {loginError && <div className="status-alert error" style={{ marginBottom: 16 }}>⚠️ {loginError}</div>}
          {authStatus.message && (
            <div className={`status-alert ${authStatus.type}`} style={{ marginBottom: 16 }}>
              {authStatus.type === 'success' ? '✅ ' : '⚠️ '}
              {authStatus.message}
            </div>
          )}

          <form onSubmit={handleLogin}>
              <label>
                <span>Email</span>
                <input
                  type="email"
                  value={loginForm.email}
                  onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                  placeholder="you@company.com"
                  required
                />
              </label>
              <label>
                <span>Password</span>
                <input
                  type="password"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                  placeholder="••••••••"
                  required
                />
              </label>
              <button type="submit" className="primary-cta" disabled={authLoading}>
                {authLoading ? 'Signing in…' : 'Enter Workspace ⚡'}
              </button>
            </form>

          <div className="login-hint" style={{ marginTop: 22 }}>
            <strong>Demo Admin:</strong> demo@example.com · demo-password
            <div style={{ marginTop: 4, fontSize: '0.75rem', color: 'var(--muted)' }}>
              💾 All accounts & passwords automatically save to SQL Database
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-gem"><Icon name="spark" /></div>
          <div>
            <div className="brand-name">Nexus</div>
            <div className="brand-sub">Commerce BI Platform</div>
          </div>
        </div>
        <div className="sidebar-scroll">
          {navGroups.map((group) => (
            <div key={group.label}>
              <div className="nav-label">{group.label}</div>
            <nav>
              {group.items.map((item) => (
                <button key={item.key} className={item.key === activeView ? 'active' : ''} onClick={() => setActiveView(item.key)}>
                  <span className="nav-icon">{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              ))}
            </nav>
          </div>
          ))}
        </div>
        <div className="sidebar-footer">
          <div className="footer-stat">
            <span className="footer-dot online" />
            <span>Backend · Online</span>
          </div>
          <div className="footer-stat muted">
            {formatNumber(dashboard.quality.records || 0)} records indexed
          </div>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <div className="eyebrow">Executive Workspace</div>
            <h1>{activeView === 'overview' ? 'Good day, decision maker 👋' : VIEW_LABELS[activeView] || activeView}</h1>
          </div>
          <div className="topbar-controls">
            <button
              className="action-btn-pill refresh-btn"
              title="Refresh and recalculate all sales data and models"
              onClick={handleRefreshAll}
              disabled={refreshingAll}
            >
              <span className={`icon-spin ${refreshingAll ? 'spinning' : ''}`}>🔄</span>
              <span>{refreshingAll ? 'Refreshing…' : 'Refresh All Data'}</span>
            </button>
            <button
              className="action-btn-pill primary-pill"
              title="Add or update a sales transaction"
              onClick={() => {
                setSalesModalTab('create');
                setSaleForm(defaultSaleForm);
                setSalesActionStatus({ type: '', message: '' });
                setSalesModalOpen(true);
              }}
            >
              <span>➕ Update / Add Sale</span>
            </button>
            <div className="user-chip">
              <span className="chip-icon">🗄️</span>
              Live dataset · <strong>{formatNumber(dashboard.quality.records || 0)}</strong> rows
            </div>
            <div className="role-badge">{role}</div>
            <button className="icon-button" title="Sign out" onClick={logout}>
              <Icon name="logout" />
            </button>
          </div>
        </header>

        <div className="toolbar">
          <div className="toolbar-head">
            <div className="toolbar-title">
              <Icon name="filter" /> <strong>Filters</strong>
              <span className="muted small"> · Scope the dashboard to any segment</span>
              {activeFilterCount > 0 && (
                <span className="active-filters-count-tag">{activeFilterCount} active</span>
              )}
              {activeView === 'segments' && (
                <span className="segment-focus-tag">
                  ⚡ Auto-Focus: <strong>{
                    segmentFocusMode !== 'auto'
                      ? segmentFocusMode.replace('_', ' ').toUpperCase()
                      : filters.category
                        ? `Category (${filters.category})`
                        : filters.region
                          ? `Region (${filters.region})`
                          : filters.city
                            ? `City (${filters.city})`
                            : filters.customer_segment
                              ? `Segment (${filters.customer_segment})`
                              : 'All Segments'
                  }</strong>
                </span>
              )}
            </div>
            <div className="toolbar-actions">
              <button className="ghost-button" onClick={refreshCurrentView} title="Reload data for current section">🔄 Reload {VIEW_LABELS[activeView] || activeView}</button>
              <button
                className="ghost-button"
                onClick={() => setFilters(defaultFilters)}
                disabled={activeFilterCount === 0}
                style={{ opacity: activeFilterCount === 0 ? 0.6 : 1 }}
              >
                <Icon name="refresh" /> Reset all
              </button>
              <span className={`status-pill ${loading ? 'loading' : activeFilterCount > 0 ? 'filtered' : 'ready'}`}>
                {loading
                  ? 'Recalculating…'
                  : activeFilterCount > 0
                    ? `${activeFilterCount} active ${activeFilterCount === 1 ? 'filter' : 'filters'} · ${formatNumber(dashboard.kpis?.orders ?? 0)} orders`
                    : `All data · ${formatNumber(dashboard.kpis?.orders ?? 0)} orders`}
              </span>
            </div>
          </div>
          <div className="toolbar-fields">
            <div className="field">
              <label>🌍 Region</label>
              <select
                value={filters.region}
                onChange={(e) => {
                  const newRegion = e.target.value;
                  setFilters((prev) => ({
                    ...prev,
                    region: newRegion,
                    city: '', // Reset city so invalid cross-region combinations don't zero out data
                  }));
                }}
              >
                <option value="">All regions</option>
                {meta.regions.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div className="field">
              <label>🏙️ City</label>
              <select value={filters.city} onChange={(e) => setFilters({ ...filters, city: e.target.value })}>
                <option value="">All places</option>
                {meta.cities.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="field">
              <label>🛍️ Category</label>
              <select value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })}>
                <option value="">All categories</option>
                {meta.categories.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="field">
              <label>👥 Customer Segment</label>
              <select
                value={filters.customer_segment}
                onChange={(e) => setFilters({ ...filters, customer_segment: e.target.value })}
              >
                <option value="">All customer segments</option>
                {(meta.customer_segments || ['Loyal', 'New', 'Returning']).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>📅 Year</label>
              <select value={filters.year} onChange={(e) => setFilters({ ...filters, year: e.target.value })}>
                <option value="">All years</option>
                {meta.years.map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
            {activeView === 'segments' && (
              <div className="field focus-dimension-field">
                <label>🎯 Analysis Focus</label>
                <select
                  value={segmentFocusMode}
                  onChange={(e) => setSegmentFocusMode(e.target.value)}
                  title="Choose a specific segment focus or let it auto-detect from your filters"
                >
                  <option value="auto">⚡ Auto (Follows chosen filters)</option>
                  <option value="all">📊 All Segments Combined</option>
                  <option value="regions">🌏 Region Breakdown</option>
                  <option value="cities">🏙️ City / Place Breakdown</option>
                  <option value="categories">🛒 Category Breakdown</option>
                  <option value="customer_segments">👥 Customer Segment Breakdown</option>
                  <option value="matrix">🎯 Category × Region Matrix</option>
                </select>
              </div>
            )}
          </div>
        </div>



        <div className="kpilist">
          {overviewCards.map((card, i) => (
            <div key={card.label} className="kpi-card" style={{ background: kpiGradient(i) }}>
              <div className="kpi-glow" />
              <div className="kpi-content">
                <label>{card.label}</label>
                <strong>{card.value}</strong>
                <div className="kpi-foot">
                  <span className="kpi-suffix">{card.suffix}</span>
                  <span className="kpi-live">
                    <span className="live-dot" /> LIVE
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {renderView()}

        {/* Sales Create / Update Modal Dialog */}
        {salesModalOpen && (
          <div className="modal-overlay" onClick={() => setSalesModalOpen(false)}>
            <div className="sales-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <div className="panel-eyebrow" style={{ color: '#8258ff' }}>TRANSACTION OPERATIONS</div>
                  <h2>{salesModalTab === 'create' ? 'Record New Sales Order' : 'Update Existing Sales Order'}</h2>
                  <p className="panel-subtitle" style={{ margin: '4px 0 0' }}>
                    {salesModalTab === 'create'
                      ? 'Add a new sales entry directly into the live dataset. Metrics will update instantly.'
                      : 'Edit order parameters, discounts, quantities, or statuses and persist to the dataset.'}
                  </p>
                </div>
                <button
                  className="modal-close-btn"
                  title="Close modal"
                  onClick={() => setSalesModalOpen(false)}
                >
                  ✕
                </button>
              </div>

              {/* Tab Bar: Create vs Update */}
              <div className="modal-tab-bar">
                <button
                  type="button"
                  className={`modal-tab-pill ${salesModalTab === 'create' ? 'active' : ''}`}
                  onClick={() => {
                    setSalesModalTab('create');
                    setSalesActionStatus({ type: '', message: '' });
                  }}
                >
                  ➕ Create New Sale
                </button>
                <button
                  type="button"
                  className={`modal-tab-pill ${salesModalTab === 'update' ? 'active' : ''}`}
                  onClick={() => {
                    setSalesModalTab('update');
                    setSalesActionStatus({ type: '', message: '' });
                  }}
                >
                  ✏️ Update Existing Sale
                </button>
              </div>

              {/* Status banner */}
              {salesActionStatus.message && (
                <div className={`status-alert ${salesActionStatus.type}`}>
                  {salesActionStatus.type === 'success' && '✅ '}
                  {salesActionStatus.type === 'error' && '⚠️ '}
                  {salesActionStatus.type === 'info' && 'ℹ️ '}
                  {salesActionStatus.message}
                </div>
              )}

              {/* Order lookup bar if in Update mode */}
              {salesModalTab === 'update' && (
                <div className="order-lookup-bar">
                  <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Order ID:</span>
                  <input
                    type="text"
                    placeholder="Enter Order ID to fetch (e.g. ORD179999)…"
                    value={saleLookupId}
                    onChange={(e) => setSaleLookupId(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        lookupOrderForUpdate();
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="action-btn-pill refresh-btn"
                    style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                    onClick={() => lookupOrderForUpdate()}
                    disabled={saleLookupLoading}
                  >
                    {saleLookupLoading ? 'Loading…' : '🔍 Load Order'}
                  </button>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSaveSale}>
                <div className="sales-form-grid">
                  <div className="form-group">
                    <label>Order ID</label>
                    <input
                      type="text"
                      placeholder={salesModalTab === 'create' ? 'Auto-generated if left blank' : 'Required for update (e.g. ORD100000)'}
                      value={saleForm.order_id}
                      onChange={(e) => updateSaleFormField('order_id', e.target.value)}
                      required={salesModalTab === 'update'}
                    />
                  </div>

                  <div className="form-group">
                    <label>Order Date</label>
                    <input
                      type="date"
                      value={saleForm.order_date}
                      onChange={(e) => updateSaleFormField('order_date', e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Customer ID</label>
                    <input
                      type="text"
                      placeholder="e.g. CUST01147"
                      value={saleForm.customer_id}
                      onChange={(e) => updateSaleFormField('customer_id', e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Customer Segment</label>
                    <select
                      value={saleForm.customer_segment}
                      onChange={(e) => updateSaleFormField('customer_segment', e.target.value)}
                    >
                      <option value="Regular">Regular</option>
                      <option value="Loyal">Loyal</option>
                      <option value="VIP">VIP</option>
                      <option value="New">New</option>
                      <option value="Consumer">Consumer</option>
                      <option value="Corporate">Corporate</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Product Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Noise Cancelling Headphones"
                      value={saleForm.product_name}
                      onChange={(e) => updateSaleFormField('product_name', e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Product Category</label>
                    <input
                      type="text"
                      list="categories-list"
                      placeholder="e.g. Electronics, Fashion..."
                      value={saleForm.product_category}
                      onChange={(e) => updateSaleFormField('product_category', e.target.value)}
                      required
                    />
                    <datalist id="categories-list">
                      {(meta.categories || ['Electronics', 'Fashion', 'Home & Kitchen', 'Beauty', 'Sports']).map((cat) => (
                        <option key={cat} value={cat} />
                      ))}
                    </datalist>
                  </div>

                  <div className="form-group">
                    <label>Region</label>
                    <input
                      type="text"
                      list="regions-list"
                      placeholder="e.g. North, South, East, West..."
                      value={saleForm.region}
                      onChange={(e) => updateSaleFormField('region', e.target.value)}
                      required
                    />
                    <datalist id="regions-list">
                      {(meta.regions || ['North', 'South', 'East', 'West', 'Central']).map((reg) => (
                        <option key={reg} value={reg} />
                      ))}
                    </datalist>
                  </div>

                  <div className="form-group">
                    <label>City</label>
                    <input
                      type="text"
                      list="cities-list"
                      placeholder="e.g. Mumbai, Delhi, Bengaluru..."
                      value={saleForm.city}
                      onChange={(e) => updateSaleFormField('city', e.target.value)}
                      required
                    />
                    <datalist id="cities-list">
                      {(meta.cities || ['Mumbai', 'Delhi', 'Bengaluru', 'Kolkata', 'Hyderabad', 'Pune', 'Chennai']).map((c) => (
                        <option key={c} value={c} />
                      ))}
                    </datalist>
                  </div>

                  <div className="form-group">
                    <label>Quantity</label>
                    <input
                      type="number"
                      min="1"
                      max="10000"
                      value={saleForm.quantity}
                      onChange={(e) => updateSaleFormField('quantity', e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Unit Price (₹)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={saleForm.unit_price}
                      onChange={(e) => updateSaleFormField('unit_price', e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Discount (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="100"
                      value={saleForm.discount_pct}
                      onChange={(e) => updateSaleFormField('discount_pct', e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label>Payment Method</label>
                    <select
                      value={saleForm.payment_method}
                      onChange={(e) => updateSaleFormField('payment_method', e.target.value)}
                    >
                      <option value="Credit Card">Credit Card</option>
                      <option value="Debit Card">Debit Card</option>
                      <option value="UPI">UPI</option>
                      <option value="Net Banking">Net Banking</option>
                      <option value="Cash on Delivery">Cash on Delivery</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Order Status</label>
                    <select
                      value={saleForm.order_status}
                      onChange={(e) => updateSaleFormField('order_status', e.target.value)}
                    >
                      <option value="Delivered">Delivered</option>
                      <option value="Shipped">Shipped</option>
                      <option value="Processing">Processing</option>
                      <option value="Returned">Returned</option>
                      <option value="Cancelled">Cancelled</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Net Sales (₹ - Calculated or Override)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={saleForm.sales}
                      onChange={(e) => updateSaleFormField('sales', e.target.value)}
                    />
                  </div>

                  {/* Reactive Financial Summary */}
                  <div className="calc-summary-box">
                    <div className="calc-metric">
                      <span>Gross Total</span>
                      <strong>{formatCurrency(Number(saleForm.quantity || 1) * Number(saleForm.unit_price || 0))}</strong>
                    </div>
                    <div className="calc-metric">
                      <span>Discount ({saleForm.discount_pct}%)</span>
                      <strong style={{ color: '#ff6b35' }}>
                        - {formatCurrency(Number(saleForm.quantity || 1) * Number(saleForm.unit_price || 0) * (Number(saleForm.discount_pct || 0) / 100))}
                      </strong>
                    </div>
                    <div className="calc-metric">
                      <span>Net Sales</span>
                      <strong style={{ color: '#ffc857' }}>{formatCurrency(saleForm.sales)}</strong>
                    </div>
                    <div className="calc-metric">
                      <span>Estimated Profit</span>
                      <strong style={{ color: '#00c2a8' }}>{formatCurrency(saleForm.profit)}</strong>
                    </div>
                  </div>
                </div>

                <div className="modal-actions">
                  <button
                    type="button"
                    className="secondary-cta"
                    onClick={() => setSalesModalOpen(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="primary-cta"
                    disabled={saleSubmitting}
                  >
                    {saleSubmitting
                      ? 'Saving…'
                      : salesModalTab === 'create'
                      ? '➕ Create Sale Order'
                      : '💾 Save & Update Sale'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

      </main>

      <footer className="app-footer">
        <span>Built by <strong>Shivaraddi</strong></span>
        <span className="app-footer-dot">·</span>
        <span>Nexus Commerce Intelligence</span>
        <span className="app-footer-dot">·</span>
        <span>{new Date().getFullYear()}</span>
      </footer>

    </div>
  );
}

function QualityRow({ label, value, color }) {
  return (
    <div className="quality-row">
      <div className="quality-row-head">
        <span className="muted small">{label}</span>
        <strong>{value.toFixed(1)}%</strong>
      </div>
      <div className="qualitybar">
        <i style={{ width: `${value}%`, background: color }} />
      </div>
    </div>
  );
}

function ViewSkeleton({ title, subtitle, charts = 2, tables = 1 }) {
  const chartBoxes = Array.from({ length: charts }, (_, i) => i);
  const tableBoxes = Array.from({ length: tables }, (_, i) => i);
  return (
    <div className="content-grid">
      <section className="panel wide hero-panel skeleton-panel">
        <div className="hero-inner">
          <div style={{ width: '55%' }}>
            <div className="skeleton badge" style={{ width: 220, height: 20, marginBottom: 16 }} />
            <div className="skeleton h1" style={{ width: '85%', height: 38, marginBottom: 12 }} />
            <div className="skeleton p" style={{ width: '100%', height: 18, marginBottom: 24 }} />
            <div style={{ display: 'flex', gap: 24 }}>
              <div><div className="skeleton strong" style={{ width: 120, height: 28 }} /><div className="skeleton small" style={{ width: 90, height: 14, marginTop: 6 }} /></div>
              <div><div className="skeleton strong" style={{ width: 100, height: 28 }} /><div className="skeleton small" style={{ width: 70, height: 14, marginTop: 6 }} /></div>
              <div><div className="skeleton strong" style={{ width: 110, height: 28 }} /><div className="skeleton small" style={{ width: 80, height: 14, marginTop: 6 }} /></div>
            </div>
          </div>
          <div className="skeleton chart" style={{ width: '42%', height: 200, borderRadius: 16 }} />
        </div>
      </section>
      {chartBoxes.map((i) => (
        <section key={`sc-${i}`} className="panel">
          <div className="skeleton eyebrow" style={{ width: 140, height: 14, marginBottom: 10 }} />
          <div className="skeleton h2" style={{ width: '70%', height: 26, marginBottom: 20 }} />
          <div className="skeleton chart" style={{ width: '100%', height: 280, borderRadius: 12 }} />
        </section>
      ))}
      {tableBoxes.map((i) => (
        <section key={`st-${i}`} className="panel wide">
          <div className="skeleton eyebrow" style={{ width: 160, height: 14, marginBottom: 10 }} />
          <div className="skeleton h2" style={{ width: '60%', height: 26, marginBottom: 20 }} />
          <div className="skeleton table" style={{ width: '100%', height: 260, borderRadius: 12 }} />
        </section>
      ))}
    </div>
  );
}
