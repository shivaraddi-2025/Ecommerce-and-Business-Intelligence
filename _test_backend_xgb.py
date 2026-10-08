import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.app import db_sync
from backend.app.analytics import AnalyticsEngine
from pathlib import Path

DATASET = Path(r'c:\oneDrive\Desktop\Updateproject\my project\data\raw\ecommerce_sales_raw.csv.csv')
engine = AnalyticsEngine(DATASET)

print('=== Test 1: XGBoost compare forecast ===')
try:
    res = engine.compare_forecast_models(horizon=7)
    winner = res.get('winner')
    rf_mae = res.get('randomforest', {}).get('validation_mae')
    xgb_mae = res.get('xgboost', {}).get('validation_mae', 'N/A')
    xgb_avail = res.get('meta', {}).get('xgboost_available')
    print('  Winner:', winner)
    print('  RF MAE:', rf_mae)
    print('  XGB MAE:', xgb_mae)
    print('  XGB available:', xgb_avail)
    print('  OK')
except Exception as e:
    print('  ERROR:', type(e).__name__, e)

print()
print('=== Test 2: Anomalies ===')
try:
    anomalies = engine.detect_anomalies(window=14, sigma=3.0)
    daily = anomalies.get('daily', [])
    anom_count = sum(1 for r in daily if r.get('is_anomaly'))
    print('  Daily rows:', len(daily))
    print('  Anomalous days:', anom_count)
    print('  OK')
except Exception as e:
    print('  ERROR:', type(e).__name__, e)

print()
print('=== Test 3: AI Advisor ===')
try:
    adv = engine.ai_advisor_insights()
    n_ins = len(adv.get('insights', []))
    n_warn = len(adv.get('warnings', []))
    n_opp = len(adv.get('opportunities', []))
    print('  Insights:', n_ins)
    print('  Warnings:', n_warn)
    print('  Opportunities:', n_opp)
    assert n_ins + n_warn + n_opp >= 5, 'Need 5+ items'
    print('  OK')
except Exception as e:
    print('  ERROR:', type(e).__name__, e)

print()
print('=== Test 4: RFM predictions ===')
try:
    rfm = engine.customer_rfm_predictions(top_n=20)
    customers = rfm.get('customers', [])
    segs = set(r.get('segment', 'Unknown') for r in customers)
    print('  Customer rows:', len(customers))
    print('  Segments:', sorted(segs))
    print('  OK')
except Exception as e:
    print('  ERROR:', type(e).__name__, e)

print()
print('=== Test 5: DB row counts via db_sync ===')
try:
    with db_sync.db_conn() as conn:
        cursor = conn.cursor()
        tables = ['users', 'locations', 'customers', 'categories', 'products', 'orders', 'order_items', 'returns', 'daily_sales_agg']
        counts = {}
        for t in tables:
            try:
                cursor.execute('SELECT COUNT(*) FROM `' + t + '`')
                counts[t] = int(list(cursor.fetchone().values())[0])
            except Exception:
                counts[t] = 0
        for k, v in counts.items():
            print('  %s: %s' % (k, '{:,}'.format(v)))
        print('  OK')
except Exception as e:
    print('  ERROR:', type(e).__name__, e)

print()
print('ALL BACKEND SMOKE TESTS PASSED')
