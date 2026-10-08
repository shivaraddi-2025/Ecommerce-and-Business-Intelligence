from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    XGBRegressor = None


class AnalyticsEngine:
	ESTIMATED_PROFIT_MARGIN = 0.30

	def __init__(self, dataset_path: Path) -> None:
		self.dataset_path = dataset_path
		self.source_columns: list[str] = []
		self.status_counts: dict[str, int] = {}
		self.has_profit_data = False
		self.frame = self._load()
		self.daily_frame = self._load_daily_dataset()
		self.custom_regions: set[str] = set()
		self.custom_categories: set[str] = set()
		self.hidden_regions: set[str] = set()
		self.hidden_categories: set[str] = set()

	def _load(self) -> pd.DataFrame:
		frame = pd.read_csv(self.dataset_path)
		self.source_columns = frame.columns.tolist()
		raw_date = frame.get("order_date", frame.get("Order Date"))
		self.source_quality = {
			"records": int(len(frame)),
			"columns": int(len(frame.columns)),
			"missing_values": int(frame.isna().sum().sum()),
			"rows_with_missing": int(frame.isna().any(axis=1).sum()),
			"duplicate_rows": int(frame.duplicated().sum()),
			"invalid_dates": int(pd.to_datetime(raw_date, errors="coerce").isna().sum()) if raw_date is not None else int(len(frame)),
		}
		self.prediction_loss_rate: float | None = None
		self.prediction_loss_basis = "Unavailable because the source has no cost, expense, or loss-status data"
		sales_column = "net_amount" if "net_amount" in frame.columns else "Sales" if "Sales" in frame.columns else None
		if sales_column:
			raw_sales = pd.to_numeric(frame[sales_column], errors="coerce").fillna(0).clip(lower=0)
			total_sales = float(raw_sales.sum())
			profit_column = "Profit" if "Profit" in frame.columns else "profit" if "profit" in frame.columns else None
			status_column = "order_status" if "order_status" in frame.columns else "Return Status" if "Return Status" in frame.columns else None
			if total_sales > 0 and profit_column:
				raw_profit = pd.to_numeric(frame[profit_column], errors="coerce").fillna(0)
				self.prediction_loss_rate = min(max(float((-raw_profit.clip(upper=0)).sum()) / total_sales, 0), 1)
				self.prediction_loss_basis = "Estimated from historical negative profit as a share of sales"
			elif total_sales > 0 and status_column:
				loss_statuses = frame[status_column].fillna("").astype(str).str.strip().str.lower().isin({"returned", "cancelled", "canceled"})
				self.prediction_loss_rate = min(max(float(raw_sales[loss_statuses].sum()) / total_sales, 0), 1)
				self.prediction_loss_basis = "Estimated from historical sales marked returned or cancelled"
		if "order_status" in frame.columns:
			self.status_counts = frame["order_status"].value_counts().astype(int).to_dict()
		self.has_profit_data = "Profit" in frame.columns or "profit" in frame.columns
		if "Order Date" not in frame.columns:
			frame = self._normalize_large_dataset(frame)
		frame["Order Date"] = pd.to_datetime(frame["Order Date"], errors="coerce")
		frame["Region"] = frame["Region"].str.strip().str.title()
		frame["City"] = frame["City"].fillna("").astype(str).str.strip().str.title()
		frame["Discount"] = pd.to_numeric(frame["Discount"], errors="coerce").fillna(0)
		frame["Discount"] = frame["Discount"].where(frame["Discount"].le(1), frame["Discount"] / 100)
		frame["Sales"] = pd.to_numeric(frame["Sales"], errors="coerce").fillna(0)
		frame["Profit"] = pd.to_numeric(frame["Profit"], errors="coerce").fillna(0)
		frame["Quantity"] = pd.to_numeric(frame["Quantity"], errors="coerce").fillna(0)
		frame["Return Flag"] = frame["Return Status"].eq("Returned").astype(int)
		frame["Month"] = frame["Order Date"].dt.to_period("M").astype(str)
		frame["Profit Margin"] = np.where(
			frame["Sales"].ne(0), frame["Profit"] / frame["Sales"], 0
		)
		return frame

	@staticmethod
	def _normalize_large_dataset(frame: pd.DataFrame) -> pd.DataFrame:
		required = {
			"order_id", "order_date", "customer_id", "product_category",
			"product_name", "quantity", "net_amount", "region", "order_status",
		}
		missing = sorted(required.difference(frame.columns))
		if missing:
			raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")

		sales = pd.to_numeric(frame["net_amount"], errors="coerce").fillna(0)
		normalized = pd.DataFrame(
			{
				"Order ID": frame["order_id"],
				"Order Date": frame["order_date"],
				"Customer ID": frame["customer_id"],
				"Customer Name": frame["customer_id"],
				"Product ID": frame["product_name"],
				"Product Name": frame["product_name"],
				"Category": frame["product_category"],
				"Sub-Category": frame["product_category"],
				"Region": frame["region"],
				"State": frame["city"],
				"City": frame["city"],
				"Quantity": frame["quantity"],
				"Sales": sales,
				"Profit": (sales * AnalyticsEngine.ESTIMATED_PROFIT_MARGIN).round(2),
				"Discount": frame.get("discount_pct", 0),
				"Shipping Mode": frame.get("payment_method", "Unknown"),
				"Segment": frame.get("customer_segment", pd.Series("Regular", index=frame.index)).fillna("Regular").astype(str).str.strip().str.title(),
				"Return Status": frame["order_status"].eq("Returned").map(
					{True: "Returned", False: "Not Returned"}
				),
			}
		)
		return normalized

	def _load_daily_dataset(self) -> pd.DataFrame:
		candidate = Path('data/raw/daily_sales_dataset.csv')
		if candidate.exists():
			try:
				frame = pd.read_csv(candidate)
				frame['Order Date'] = pd.to_datetime(frame['Order Date'], errors='coerce')
				return frame.sort_values('Order Date').reset_index(drop=True)
			except Exception:
				pass

		daily = self.frame.assign(
			_order_date=pd.to_datetime(self.frame["Order Date"], errors="coerce").dt.normalize()
		).groupby("_order_date", as_index=False).agg(
			sales=("Sales", "sum"),
			profit=("Profit", "sum"),
			orders=("Order ID", "nunique"),
			return_orders=("Return Flag", "sum"),
		).rename(columns={"_order_date": "Order Date"})
		daily["return_rate"] = np.where(
			daily["orders"].ne(0),
			daily["return_orders"] / daily["orders"] * 100,
			0,
		)
		return daily.sort_values("Order Date").reset_index(drop=True)

	@staticmethod
	def _clean_region(name: str) -> str:
		return " ".join(name.strip().title().split())

	@staticmethod
	def _clean_category(name: str) -> str:
		return " ".join(name.strip().title().split())

	@property
	def categories(self) -> list[str]:
		base = set(self.frame["Category"].dropna().astype(str).str.strip().str.title().unique().tolist())
		base.update(self.custom_categories)
		base.difference_update(self.hidden_categories)
		return sorted(base)

	@property
	def regions(self) -> list[str]:
		base = set(self.frame["Region"].dropna().astype(str).str.strip().str.title().unique().tolist())
		base.update(self.custom_regions)
		base.difference_update(self.hidden_regions)
		return sorted(base)

	@property
	def cities(self) -> list[str]:
		return sorted(
			set(self.frame["City"].dropna().astype(str).str.strip().str.title().unique().tolist())
		)

	@property
	def customer_segments(self) -> list[str]:
		if "Segment" in self.frame.columns:
			return sorted(set(self.frame["Segment"].dropna().astype(str).str.strip().str.title().unique().tolist()))
		return ["Loyal", "New", "Returning"]

	def get_cities(self, region: str | None = None) -> list[str]:
		if not region or not region.strip():
			return self.cities
		reg = region.strip().title()
		matching = self.frame[self.frame["Region"].eq(reg)]["City"].dropna().astype(str).str.strip().str.title().unique().tolist()
		return sorted(set(matching)) if matching else self.cities

	def add_region(self, name: str) -> str:
		value = self._clean_region(name)
		if not value:
			raise ValueError("Region name is required")
		if value in self.regions:
			raise ValueError("Region already exists")
		self.custom_regions.add(value)
		self.hidden_regions.discard(value)
		return value

	def add_category(self, name: str) -> str:
		value = self._clean_category(name)
		if not value:
			raise ValueError("Category name is required")
		if value in self.categories:
			raise ValueError("Category already exists")
		self.custom_categories.add(value)
		self.hidden_categories.discard(value)
		return value

	def delete_region(self, name: str) -> str:
		value = self._clean_region(name)
		if value in self.custom_regions:
			self.custom_regions.remove(value)
			return value
		if value in self.frame["Region"].dropna().astype(str).str.strip().str.title().unique().tolist():
			self.hidden_regions.add(value)
			return value
		raise ValueError("Region not found")

	def delete_category(self, name: str) -> str:
		value = self._clean_category(name)
		if value in self.custom_categories:
			self.custom_categories.remove(value)
			return value
		if value in self.frame["Category"].dropna().astype(str).str.strip().str.title().unique().tolist():
			self.hidden_categories.add(value)
			return value
		raise ValueError("Category not found")

	@staticmethod
	def _parse_filter_values(value: str | None) -> list[str] | None:
		if value is None:
			return None
		text = str(value).strip()
		if '-' in text and not text.startswith('-'):
			parts = [part.strip().title() for part in text.replace(' - ', '-').split('-') if part.strip()]
			if len(parts) == 2:
				items = parts
			else:
				items = [part.strip().title() for part in str(value).split(",") if part.strip()]
		else:
			items = [part.strip().title() for part in str(value).split(",") if part.strip()]
		return items or None

	def filtered(
		self,
		region: str | None = None,
		category: str | None = None,
		year: str | None = None,
		city: str | None = None,
		customer_segment: str | None = None,
	) -> pd.DataFrame:
		frame = self.frame
		regions = self._parse_filter_values(region)
		categories = self._parse_filter_values(category)
		cities = self._parse_filter_values(city)
		segments = self._parse_filter_values(customer_segment)
		if regions:
			frame = frame[frame["Region"].isin(regions)]
		if categories:
			frame = frame[frame["Category"].isin(categories)]
		if cities:
			frame = frame[frame["City"].isin(cities)]
		if segments and "Segment" in frame.columns:
			frame = frame[frame["Segment"].isin(segments)]
		if year:
			try:
				year_value = int(str(year))
				frame = frame[frame["Order Date"].dt.year.eq(year_value)]
			except Exception:
				pass
		return frame

	def kpis(
		self,
		region: str | None = None,
		category: str | None = None,
		year: str | None = None,
		city: str | None = None,
		customer_segment: str | None = None,
	) -> dict[str, float | int]:
		frame = self.filtered(region, category, year, city, customer_segment)
		total_sales = float(frame["Sales"].sum())
		total_profit = float(frame["Profit"].sum())
		return {
			"sales": round(total_sales, 2),
			"profit": round(total_profit, 2),
			"orders": int(frame["Order ID"].nunique()),
			"customers": int(frame["Customer ID"].nunique()),
			"quantity": int(frame["Quantity"].sum()),
			"average_order_value": round(float(frame.groupby("Order ID")["Sales"].sum().mean()), 2),
			"profit_margin": round(total_profit / total_sales * 100, 2) if total_sales else 0,
			"return_rate": round(float(frame["Return Flag"].mean() * 100), 2),
		}

	def trend(self, region: str | None = None, category: str | None = None, year: str | None = None, city: str | None = None) -> list[dict[str, object]]:
		result = self.filtered(region, category, year, city).groupby("Month", as_index=False).agg(
			sales=("Sales", "sum"), profit=("Profit", "sum"), orders=("Order ID", "nunique")
		)
		return result.round(2).to_dict("records")

	def daily_trend(self, region: str | None = None, category: str | None = None, year: str | None = None, city: str | None = None) -> list[dict[str, object]]:
		frame = self.filtered(region, category, year, city).copy()
		frame["Order Date"] = pd.to_datetime(frame["Order Date"], errors="coerce").dt.normalize()
		result = frame.groupby("Order Date", as_index=False).agg(
			sales=("Sales", "sum"),
			profit=("Profit", "sum"),
			orders=("Order ID", "nunique"),
		)
		result = result.sort_values("Order Date").reset_index(drop=True)
		result["Order Date"] = result["Order Date"].dt.strftime("%Y-%m-%d")
		return result.round(2).to_dict("records")

	def daily_performance_report(self, region: str | None = None, category: str | None = None, year: str | None = None, city: str | None = None) -> dict[str, object]:
		frame = self.filtered(region, category, year, city).copy()
		frame["Order Date"] = pd.to_datetime(frame["Order Date"], errors="coerce").dt.normalize()
		daily = frame.groupby("Order Date", as_index=False).agg(
			sales=("Sales", "sum"),
			profit=("Profit", "sum"),
			orders=("Order ID", "nunique"),
			return_orders=("Return Flag", "sum"),
		)
		daily = daily.sort_values("Order Date").reset_index(drop=True)
		daily["Order Date"] = daily["Order Date"].dt.strftime("%Y-%m-%d")
		daily["return_rate"] = (daily["return_orders"] / daily["orders"] * 100).round(2)
		daily = daily.round(2)

		top_day = daily.sort_values("sales", ascending=False).head(1).to_dict("records")
		low_day = daily.sort_values("sales", ascending=True).head(1).to_dict("records")
		risk_days = daily[daily["return_rate"] >= 25].sort_values("return_rate", ascending=False).head(5).to_dict("records")
		return {
			"daily": daily.to_dict("records"),
			"summary": {
				"top_day": top_day[0] if top_day else None,
				"low_day": low_day[0] if low_day else None,
				"risk_days": risk_days,
				"total_sales": round(float(daily["sales"].sum()), 2),
				"total_profit": round(float(daily["profit"].sum()), 2),
				"total_orders": int(daily["orders"].sum()),
				"date_span": {
					"start": daily["Order Date"].min() if not daily.empty else None,
					"end": daily["Order Date"].max() if not daily.empty else None,
				},
			},
		}

	def category_performance(
		self,
		region: str | None = None,
		category: str | None = None,
		year: str | None = None,
		city: str | None = None,
	) -> list[dict[str, object]]:
		frame = self.filtered(region=region, category=category, year=year, city=city)
		if frame.empty:
			return []
		result = frame.groupby("Category", as_index=False).agg(
			sales=("Sales", "sum"),
			profit=("Profit", "sum"),
			orders=("Order ID", "nunique"),
			return_rate=("Return Flag", "mean"),
		)
		result["return_rate"] = (result["return_rate"] * 100).round(2)
		return result.round(2).sort_values("sales", ascending=False).to_dict("records")

	def top_products(
		self,
		limit: int = 10,
		region: str | None = None,
		category: str | None = None,
		year: str | None = None,
		city: str | None = None,
	) -> list[dict[str, object]]:
		frame = self.filtered(region=region, category=category, year=year, city=city)
		if frame.empty:
			return []
		result = frame.groupby(["Product ID", "Product Name"], as_index=False).agg(
			sales=("Sales", "sum"),
			profit=("Profit", "sum"),
			units=("Quantity", "sum"),
			return_rate=("Return Flag", "mean"),
		)
		result["return_rate"] = (result["return_rate"] * 100).round(2)
		return result.sort_values("sales", ascending=False).head(limit).round(2).to_dict("records")

	def customers(
		self,
		limit: int = 10,
		region: str | None = None,
		category: str | None = None,
		year: str | None = None,
		city: str | None = None,
	) -> list[dict[str, object]]:
		frame = self.filtered(region=region, category=category, year=year, city=city)
		if frame.empty:
			return []
		result = frame.groupby(["Customer ID", "Customer Name"], dropna=False, as_index=False).agg(
			sales=("Sales", "sum"),
			profit=("Profit", "sum"),
			orders=("Order ID", "nunique"),
			last_order=("Order Date", "max"),
			returns=("Return Flag", "sum"),
		)
		result["last_order"] = result["last_order"].dt.strftime("%Y-%m-%d")
		return result.sort_values("sales", ascending=False).head(limit).round(2).to_dict("records")

	def recommendations(self, customer_id: str | None = None, limit: int = 5) -> list[dict[str, object]]:
		purchased = set(self.frame.loc[self.frame["Customer ID"].eq(customer_id), "Product ID"]) if customer_id else set()
		result = self.frame.groupby(["Product ID", "Product Name", "Category"], as_index=False).agg(
			sales=("Sales", "sum"), units=("Quantity", "sum"), profit=("Profit", "sum")
		)
		result = result[~result["Product ID"].isin(purchased)]
		result["score"] = (result["sales"].rank(pct=True) * 0.6 + result["profit"].rank(pct=True) * 0.4).round(4)
		return result.sort_values("score", ascending=False).head(limit).round(2).to_dict("records")

	def quality(self) -> dict[str, object]:
		"""Return source-file quality metrics, before normalization fills or estimates values."""
		stats = getattr(self, "source_quality", {})
		records = int(stats.get("records", len(self.frame)))
		columns = int(stats.get("columns", len(self.source_columns)))
		cells = records * columns
		completeness = 100 * (1 - stats.get("missing_values", 0) / cells) if cells else 0.0
		uniqueness = 100 * (1 - stats.get("duplicate_rows", 0) / records) if records else 0.0
		date_validity = 100 * (1 - stats.get("invalid_dates", 0) / records) if records else 0.0
		return {
			"records": records,
			"columns": columns,
			"source_columns": self.source_columns,
			"status_counts": self.status_counts,
			"has_profit_data": self.has_profit_data,
			"profit_is_estimated": not self.has_profit_data,
			"estimated_profit_margin": self.ESTIMATED_PROFIT_MARGIN if not self.has_profit_data else None,
			"missing_values": int(stats.get("missing_values", 0)),
			"rows_with_missing": int(stats.get("rows_with_missing", 0)),
			"duplicate_rows": int(stats.get("duplicate_rows", 0)),
			"invalid_dates": int(stats.get("invalid_dates", 0)),
			"completeness": round(max(0.0, min(100.0, completeness)), 2),
			"uniqueness": round(max(0.0, min(100.0, uniqueness)), 2),
			"date_validity": round(max(0.0, min(100.0, date_validity)), 2),
			"quality_score": round(max(0.0, min(100.0, (completeness + uniqueness + date_validity) / 3)), 2),
			"negative_profit_rows": int((self.frame["Profit"] < 0).sum()),
			"returned_orders": int(self.frame["Return Flag"].sum()),
			"date_min": self.frame["Order Date"].min().strftime("%Y-%m-%d"),
			"date_max": self.frame["Order Date"].max().strftime("%Y-%m-%d"),
		}

	def forecast_daily_sales(
		self,
		selected_date: str | None = None,
		year: str | None = None,
		horizon: int = 1,
		observed_sales: float | None = None,
		model: str | None = None,
	) -> dict[str, object]:
		"""Train on past daily observations and forecast the day after the selected/latest date."""
		horizon = max(1, min(int(horizon), 30))
		empty = {
			"forecast_date": "", "today_sales": 0, "predicted_sales": 0,
			"predicted_revenue": 0, "predicted_profit": 0, "predicted_loss": None, "predicted_orders": 0,
			"confidence": 0, "forecast": [], "basis": "Insufficient daily data for an ML forecast",
			"profit_basis": "Estimated at 30% margin; source has no profit or cost field",
			"loss_basis": "Unavailable because the source has no cost or expense data",
			"return_rate": 0.0,
		}
		if self.daily_frame.empty:
			return empty

		frame = self.daily_frame.copy()
		frame["Order Date"] = pd.to_datetime(frame["Order Date"], errors="coerce").dt.normalize()
		frame["sales"] = pd.to_numeric(frame["sales"], errors="coerce").fillna(0)
		frame["orders"] = pd.to_numeric(frame.get("orders", 0), errors="coerce").fillna(0)
		frame = frame.dropna(subset=["Order Date"]).groupby("Order Date", as_index=False).agg(
			sales=("sales", "sum"), orders=("orders", "sum")
		).sort_values("Order Date").set_index("Order Date")
		if year:
			try:
				frame = frame[frame.index.year == int(year)]
			except (TypeError, ValueError):
				pass
		if frame.empty:
			return {**empty, "basis": "No daily data for selected year"}

		# Fill calendar gaps so lag values always mean consecutive days.
		frame = frame.asfreq("D", fill_value=0)
		if selected_date:
			try:
				base_date = pd.Timestamp(selected_date).normalize()
			except (TypeError, ValueError):
				return {**empty, "basis": "Invalid date; use YYYY-MM-DD"}
			latest_data_date = frame.index[-1]
			if base_date < frame.index[0]:
				return {**empty, "basis": "Selected date is outside the available daily data"}
			if base_date > latest_data_date and observed_sales is None:
				return {**empty, "basis": "Enter today's sales to forecast from a date after the dataset ends"}
			if base_date not in frame.index and observed_sales is None:
				return {**empty, "basis": "Selected date is outside the available daily data"}
		else:
			base_date = frame.index[-1]
		base_pos = frame.index.get_loc(base_date) if base_date in frame.index else len(frame.index) - 1
		if base_pos < 14:
			return {**empty, "basis": "At least 15 days of history are needed for the ML forecast"}

		def features_at(pos: int) -> list[float]:
			# Include sales through `pos` (today) when predicting the following date.
			date = frame.index[pos + 1]
			values = frame["sales"]
			return [
				float(values.iloc[pos - lag + 1]) for lag in (1, 2, 3, 7, 14)
				] + [
				float(values.iloc[pos - 6:pos + 1].mean()),
				float(values.iloc[pos - 13:pos + 1].mean()),
				float(date.dayofweek), float(date.month), float(date.dayofyear),
			]

		# Each training row uses only information available on that date; its label is
		# the following day's sales. Restrict labels to dates at/before the forecast origin.
		train_x = [features_at(pos) for pos in range(14, base_pos)]
		train_y = [float(frame["sales"].iloc[pos + 1]) for pos in range(14, base_pos)]
		if len(train_x) < 10:
			return {**empty, "basis": "At least 25 days of history are needed for the ML forecast"}

		# Hold out the latest 20% of training examples in chronological order.
		split = max(1, int(len(train_x) * 0.8))
		validation_x, validation_y = train_x[split:], np.asarray(train_y[split:], dtype=float)

		model_name = (model or "randomforest").strip().lower()
		if model_name in {"xgboost", "xgb"} and XGBOOST_AVAILABLE:
			forecast_model = XGBRegressor(
				n_estimators=200, max_depth=5, learning_rate=0.1,
				subsample=0.9, colsample_bytree=0.9,
				random_state=42, n_jobs=1, verbosity=0,
			)
			selected_model_name = "xgboost"
		elif model_name in {"xgboost", "xgb"} and not XGBOOST_AVAILABLE:
			forecast_model = RandomForestRegressor(
				n_estimators=300, min_samples_leaf=2, max_features=0.9,
				random_state=42, n_jobs=1,
			)
			selected_model_name = "randomforest"
		else:
			forecast_model = RandomForestRegressor(
				n_estimators=300, min_samples_leaf=2, max_features=0.9,
				random_state=42, n_jobs=1,
			)
			selected_model_name = "randomforest"

		xgb_mae = None
		rf_mae = None
		if len(validation_y):
			forecast_model.fit(train_x[:split], train_y[:split])
			ml_validation = forecast_model.predict(validation_x)
			baseline_validation = np.asarray([row[5] for row in validation_x], dtype=float)
			ml_mae = float(np.mean(np.abs(validation_y - ml_validation)))
			baseline_mae = float(np.mean(np.abs(validation_y - baseline_validation)))
			if selected_model_name == "xgboost":
				xgb_mae = ml_mae
			else:
				rf_mae = ml_mae
		else:
			ml_mae = float('inf')
			baseline_mae = float('inf')
		# Use the ML result only when it beats the 7-day mean on unseen dates.
		use_ml = ml_mae <= baseline_mae
		forecast_model.fit(train_x, train_y)
		last_sales = float(observed_sales) if observed_sales is not None else float(frame["sales"].iloc[base_pos])
		last_orders = float(frame["orders"].iloc[base_pos])
		latest_historical_sales = float(frame["sales"].iloc[base_pos])
		avg_order_value = latest_historical_sales / last_orders if last_orders else 0.0
		avg_orders = float(frame["orders"].iloc[max(0, base_pos - 6):base_pos + 1].mean())
		reference_history = frame["sales"].iloc[:base_pos + 1].astype(float).tolist()
		scale_base = reference_history[-1] if reference_history[-1] > 0 else float(np.mean(reference_history[-7:]))
		forecast_scale = last_sales / scale_base if observed_sales is not None and scale_base > 0 else 1.0
		history_gap_days = max(0, int((base_date - frame.index[base_pos]).days - (0 if base_date == frame.index[base_pos] else 1)))
		forecast_rows: list[dict[str, object]] = []
		loss_rate = self.prediction_loss_rate
		for step in range(horizon):
			forecast_date = base_date + pd.Timedelta(days=step + 1)
			features = [reference_history[-lag] for lag in (1, 2, 3, 7, 14)]
			features.extend([
				float(np.mean(reference_history[-7:])),
				float(np.mean(reference_history[-14:])),
				float(forecast_date.dayofweek),
				float(forecast_date.month),
				float(forecast_date.dayofyear),
			])
			ml_forecast = float(forecast_model.predict([features])[0])
			baseline_forecast = float(np.mean(reference_history[-7:]))
			raw_forecast = max(0.0, ml_forecast if use_ml else baseline_forecast)
			forecast_sales = raw_forecast * forecast_scale
			if forecast_sales <= 0:
				forecast_orders = 0
			elif avg_order_value > 0:
				forecast_orders = max(1, int(round(forecast_sales / avg_order_value)))
			else:
				forecast_orders = max(0, int(round(avg_orders)))
			predicted_loss = round(forecast_sales * loss_rate, 2) if loss_rate is not None else None
			profitable_sales = max(0.0, forecast_sales - (predicted_loss or 0))
			predicted_profit = round(profitable_sales * self.ESTIMATED_PROFIT_MARGIN, 2)
			reference_history.append(raw_forecast)
			forecast_rows.append({
				"date": forecast_date.strftime("%Y-%m-%d"),
				"revenue": round(forecast_sales, 2),
				"predicted_sales": round(forecast_sales, 2),
				"predicted_profit": predicted_profit,
				"predicted_loss": predicted_loss,
				"predicted_orders": forecast_orders,
			})
		forecast_date = base_date + pd.Timedelta(days=1)
		first_forecast = forecast_rows[0]
		basis_text = "Random forest" if selected_model_name == "randomforest" else "XGBoost gradient boosting"
		if not use_ml:
			basis_text = f"7-day average (lower validation MAE than {basis_text.lower()})"
		result = {
			"forecast_date": forecast_date.strftime("%Y-%m-%d"),
			"latest_observed_date": base_date.strftime("%Y-%m-%d"),
			"today_sales": round(last_sales, 2),
			"predicted_sales": first_forecast["predicted_sales"],
			"predicted_revenue": first_forecast["revenue"],
			"predicted_profit": first_forecast["predicted_profit"],
			"predicted_loss": first_forecast["predicted_loss"],
			"predicted_orders": first_forecast["predicted_orders"],
			"forecast": forecast_rows,
			"history_gap_days": history_gap_days,
			"confidence": max(55, min(95, int(round(90 - min(40, (ml_mae if use_ml else baseline_mae) / max(last_sales, 1) * 20))))),
			"basis": basis_text,
			"forecast_scale": round(forecast_scale, 8),
			"validation_mae": round(ml_mae if use_ml else baseline_mae, 2),
			"random_forest_validation_mae": round(ml_mae if selected_model_name == "randomforest" else float('inf'), 2),
			"baseline_validation_mae": round(baseline_mae, 2),
			"validation_days": int(len(validation_y)),
			"profit_basis": "Estimated at 30% margin; source has no profit or cost field",
			"loss_rate": round(loss_rate, 4) if loss_rate is not None else None,
			"loss_basis": f"{self.prediction_loss_basis} ({loss_rate:.1%} historical rate)" if loss_rate is not None else self.prediction_loss_basis,
			"return_rate": round(float(self.frame["Return Flag"].mean() * 100) if "Return Flag" in self.frame.columns else 0.0, 2),
		}
		if selected_model_name == "xgboost" or xgb_mae is not None:
			result["xgboost_validation_mae"] = round(xgb_mae, 2) if xgb_mae is not None else None
		if rf_mae is not None:
			result["random_forest_validation_mae"] = round(rf_mae, 2)
		result["selected_model"] = selected_model_name
		result["xgboost_available"] = XGBOOST_AVAILABLE
		return result

	def predict(self, quantity: int, sales: float, discount: float, category: str, region: str) -> dict[str, object]:
		baseline = self.frame[self.frame["Category"].eq(category) & self.frame["Region"].eq(region)]
		baseline = baseline if not baseline.empty else self.frame
		baseline_sales = float(baseline["Sales"].sum())
		margin = float(baseline["Profit"].sum() / baseline_sales) if baseline_sales else 0
		return_rate = float(baseline["Return Flag"].mean())
		predicted_sales = float(
			sales * (1 + 0.04 * quantity)
			* (1 - max(discount - baseline["Discount"].mean(), 0) * 0.35)
		)
		predicted_profit = predicted_sales * margin
		risk = min(max(return_rate + max(discount - 0.1, 0) * 0.45, 0), 1)
		return {
			"predicted_sales": round(predicted_sales, 2),
			"predicted_profit": round(predicted_profit, 2),
			"return_probability": round(risk, 4),
			"risk_level": "High" if risk >= 0.35 else "Medium" if risk >= 0.18 else "Low",
			"explanations": [
				"Historical category-region margin",
				"Discount level",
				"Observed return behavior",
			],
		}

	def reload(self) -> None:
		self.frame = self._load()
		self.daily_frame = self._load_daily_dataset()

	def get_sales_records(
		self,
		search: str | None = None,
		category: str | None = None,
		region: str | None = None,
		city: str | None = None,
		year: str | None = None,
		limit: int = 20,
		offset: int = 0,
	) -> dict[str, object]:
		df = self.filtered(region=region, category=category, year=year, city=city)
		if search and search.strip():
			q = search.strip().lower()
			cond = (
				df["Order ID"].astype(str).str.lower().str.contains(q, na=False)
				| df["Customer ID"].astype(str).str.lower().str.contains(q, na=False)
				| df["Product Name"].astype(str).str.lower().str.contains(q, na=False)
				| df["City"].astype(str).str.lower().str.contains(q, na=False)
			)
			df = df[cond]

		total = int(len(df))
		sliced = df.iloc[::-1].iloc[offset : offset + limit]

		records: list[dict[str, object]] = []
		for _, row in sliced.iterrows():
			date_val = str(row.get("Order Date", ""))[:10]
			qty = max(int(row.get("Quantity", 1)), 1)
			sales_val = round(float(row.get("Sales", 0)), 2)
			disc = float(row.get("Discount", 0))
			disc_pct = round(disc * 100.0 if disc <= 1.0 else disc, 1)

			records.append({
				"order_id": str(row.get("Order ID", "")),
				"order_date": date_val,
				"customer_id": str(row.get("Customer ID", "")),
				"customer_name": str(row.get("Customer Name", row.get("Customer ID", ""))),
				"product_name": str(row.get("Product Name", "")),
				"category": str(row.get("Category", "")),
				"region": str(row.get("Region", "")),
				"city": str(row.get("City", "")),
				"quantity": qty,
				"unit_price": round(sales_val / qty, 2) if qty > 0 else sales_val,
				"discount_pct": disc_pct,
				"sales": sales_val,
				"profit": round(float(row.get("Profit", 0)), 2),
				"order_status": str(row.get("Return Status", "Delivered")),
				"payment_method": str(row.get("Shipping Mode", "Credit Card")),
			})

		return {
			"total": total,
			"offset": offset,
			"limit": limit,
			"records": records,
		}

	def create_sale(self, payload: dict[str, object]) -> dict[str, object]:
		raw = pd.read_csv(self.dataset_path)

		order_id = str(payload.get("order_id") or "").strip()
		if not order_id:
			if "order_id" in raw.columns:
				max_id = 100000 + len(raw) + 1
				order_id = f"ORD{max_id}"
			else:
				order_id = f"CA-{datetime.now().year}-{100000 + len(raw) + 1}"

		date_str = str(payload.get("order_date") or "").strip()
		if not date_str:
			date_str = datetime.now().strftime("%Y-%m-%d")
		try:
			dt = pd.to_datetime(date_str)
		except Exception:
			dt = pd.Timestamp.now()
			date_str = dt.strftime("%Y-%m-%d")

		quantity = max(int(payload.get("quantity") or 1), 1)
		unit_price = float(payload.get("unit_price") or 100.0)
		discount_pct = float(payload.get("discount_pct") or 0.0)
		gross_amount = round(quantity * unit_price, 2)
		discount_amount = round(gross_amount * (discount_pct / 100.0), 2)
		net_amount = round(float(payload.get("sales") or (gross_amount - discount_amount)), 2)
		profit = round(float(payload.get("profit") or (net_amount * self.ESTIMATED_PROFIT_MARGIN)), 2)

		category = str(payload.get("product_category") or payload.get("category") or "General").strip().title()
		product_name = str(payload.get("product_name") or "Product").strip()
		region = str(payload.get("region") or "North").strip().title()
		city = str(payload.get("city") or "Mumbai").strip().title()
		customer_id = str(payload.get("customer_id") or "CUST00001").strip()
		customer_segment = str(payload.get("customer_segment") or "Regular").strip()
		payment_method = str(payload.get("payment_method") or "Credit Card").strip()
		order_status = str(payload.get("order_status") or "Delivered").strip()

		if "order_id" in raw.columns:
			new_row = {
				"order_id": order_id,
				"order_date": date_str,
				"order_datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
				"day_of_week": dt.strftime("%A"),
				"month": dt.strftime("%B"),
				"year": int(dt.year),
				"customer_id": customer_id,
				"customer_segment": customer_segment,
				"product_category": category,
				"product_name": product_name,
				"quantity": quantity,
				"unit_price": unit_price,
				"gross_amount": gross_amount,
				"discount_pct": discount_pct,
				"discount_amount": discount_amount,
				"net_amount": net_amount,
				"payment_method": payment_method,
				"region": region,
				"city": city,
				"order_status": order_status,
			}
			new_df = pd.DataFrame([new_row])
			new_df.to_csv(self.dataset_path, mode="a", header=False, index=False)
		else:
			new_row = {
				"Order ID": order_id,
				"Order Date": date_str,
				"Customer ID": customer_id,
				"Customer Name": customer_id,
				"Segment": customer_segment,
				"Country": "India",
				"City": city,
				"State": city,
				"Postal Code": "400001",
				"Region": region,
				"Product ID": product_name,
				"Category": category,
				"Sub-Category": category,
				"Product Name": product_name,
				"Sales": net_amount,
				"Quantity": quantity,
				"Discount": discount_pct / 100.0 if discount_pct > 1 else discount_pct,
				"Profit": profit,
				"Return Status": "Returned" if order_status.lower() in ("returned", "cancelled") else "Not Returned",
			}
			for col in raw.columns:
				if col not in new_row:
					new_row[col] = ""
			new_df = pd.DataFrame([new_row])[raw.columns]
			new_df.to_csv(self.dataset_path, mode="a", header=False, index=False)

		self.reload()
		return {
			"order_id": order_id,
			"order_date": date_str,
			"customer_id": customer_id,
			"product_name": product_name,
			"category": category,
			"region": region,
			"city": city,
			"quantity": quantity,
			"unit_price": unit_price,
			"discount_pct": discount_pct,
			"sales": net_amount,
			"profit": profit,
			"order_status": order_status,
			"payment_method": payment_method,
		}

	def update_sale(self, order_id: str, payload: dict[str, object]) -> dict[str, object]:
		raw = pd.read_csv(self.dataset_path)
		id_col = "order_id" if "order_id" in raw.columns else "Order ID"
		if id_col not in raw.columns:
			raise ValueError("No Order ID column found in dataset")

		mask = raw[id_col].astype(str).str.strip().str.lower() == str(order_id).strip().lower()
		indices = raw[mask].index
		if len(indices) == 0:
			raise ValueError(f"Sale record with Order ID '{order_id}' was not found.")

		idx = indices[0]
		row = raw.loc[idx]

		date_str = str(payload.get("order_date") or row.get("order_date" if "order_date" in raw.columns else "Order Date") or "").strip()[:10]
		try:
			dt = pd.to_datetime(date_str)
		except Exception:
			dt = pd.Timestamp.now()
			date_str = dt.strftime("%Y-%m-%d")

		quantity = int(payload.get("quantity") or row.get("quantity" if "quantity" in raw.columns else "Quantity") or 1)

		if "unit_price" in payload and payload["unit_price"] is not None:
			unit_price = float(payload["unit_price"])
		elif "unit_price" in raw.columns:
			unit_price = float(row.get("unit_price", 100.0))
		else:
			prev_sales = float(row.get("Sales", 100.0))
			unit_price = prev_sales / max(quantity, 1)

		if "discount_pct" in payload and payload["discount_pct"] is not None:
			discount_pct = float(payload["discount_pct"])
		elif "discount_pct" in raw.columns:
			discount_pct = float(row.get("discount_pct", 0.0))
		else:
			d_val = float(row.get("Discount", 0.0))
			discount_pct = d_val * 100.0 if d_val <= 1.0 else d_val

		gross_amount = round(quantity * unit_price, 2)
		discount_amount = round(gross_amount * (discount_pct / 100.0), 2)

		if "sales" in payload and payload["sales"] is not None:
			net_amount = round(float(payload["sales"]), 2)
		else:
			net_amount = round(gross_amount - discount_amount, 2)

		if "profit" in payload and payload["profit"] is not None:
			profit = round(float(payload["profit"]), 2)
		else:
			profit = round(net_amount * self.ESTIMATED_PROFIT_MARGIN, 2)

		category = str(payload.get("product_category") or payload.get("category") or row.get("product_category" if "product_category" in raw.columns else "Category") or "General").strip().title()
		product_name = str(payload.get("product_name") or row.get("product_name" if "product_name" in raw.columns else "Product Name") or "Product").strip()
		region = str(payload.get("region") or row.get("region" if "region" in raw.columns else "Region") or "North").strip().title()
		city = str(payload.get("city") or row.get("city" if "city" in raw.columns else "City") or "Mumbai").strip().title()
		customer_id = str(payload.get("customer_id") or row.get("customer_id" if "customer_id" in raw.columns else "Customer ID") or "CUST00001").strip()
		customer_segment = str(payload.get("customer_segment") or row.get("customer_segment" if "customer_segment" in raw.columns else "Segment") or "Regular").strip()
		payment_method = str(payload.get("payment_method") or row.get("payment_method" if "payment_method" in raw.columns else "Shipping Mode") or "Credit Card").strip()
		order_status = str(payload.get("order_status") or row.get("order_status" if "order_status" in raw.columns else "Return Status") or "Delivered").strip()

		if "order_id" in raw.columns:
			raw.at[idx, "order_date"] = date_str
			raw.at[idx, "order_datetime"] = dt.strftime("%Y-%m-%d %H:%M:%S")
			raw.at[idx, "day_of_week"] = dt.strftime("%A")
			raw.at[idx, "month"] = dt.strftime("%B")
			raw.at[idx, "year"] = int(dt.year)
			raw.at[idx, "customer_id"] = customer_id
			raw.at[idx, "customer_segment"] = customer_segment
			raw.at[idx, "product_category"] = category
			raw.at[idx, "product_name"] = product_name
			raw.at[idx, "quantity"] = quantity
			raw.at[idx, "unit_price"] = unit_price
			raw.at[idx, "gross_amount"] = gross_amount
			raw.at[idx, "discount_pct"] = discount_pct
			raw.at[idx, "discount_amount"] = discount_amount
			raw.at[idx, "net_amount"] = net_amount
			raw.at[idx, "payment_method"] = payment_method
			raw.at[idx, "region"] = region
			raw.at[idx, "city"] = city
			raw.at[idx, "order_status"] = order_status
		else:
			raw.at[idx, "Order Date"] = date_str
			raw.at[idx, "Customer ID"] = customer_id
			raw.at[idx, "Customer Name"] = customer_id
			raw.at[idx, "Segment"] = customer_segment
			raw.at[idx, "City"] = city
			raw.at[idx, "State"] = city
			raw.at[idx, "Region"] = region
			raw.at[idx, "Category"] = category
			raw.at[idx, "Sub-Category"] = category
			raw.at[idx, "Product Name"] = product_name
			raw.at[idx, "Sales"] = net_amount
			raw.at[idx, "Quantity"] = quantity
			raw.at[idx, "Discount"] = discount_pct / 100.0 if discount_pct > 1 else discount_pct
			raw.at[idx, "Profit"] = profit
			raw.at[idx, "Return Status"] = "Returned" if order_status.lower() in ("returned", "cancelled") else "Not Returned"

		raw.to_csv(self.dataset_path, index=False)
		self.reload()

		return {
			"order_id": str(raw.at[idx, id_col]),
			"order_date": date_str,
			"customer_id": customer_id,
			"product_name": product_name,
			"category": category,
			"region": region,
			"city": city,
			"quantity": quantity,
			"unit_price": unit_price,
			"discount_pct": discount_pct,
			"sales": net_amount,
			"profit": profit,
			"order_status": order_status,
			"payment_method": payment_method,
		}

	def delete_sale(self, order_id: str) -> str:
		raw = pd.read_csv(self.dataset_path)
		id_col = "order_id" if "order_id" in raw.columns else "Order ID"
		if id_col not in raw.columns:
			raise ValueError("No Order ID column found in dataset")

		mask = raw[id_col].astype(str).str.strip().str.lower() == str(order_id).strip().lower()
		if not raw[mask].shape[0]:
			raise ValueError(f"Sale record with Order ID '{order_id}' was not found.")

		raw = raw[~mask]
		raw.to_csv(self.dataset_path, index=False)
		self.reload()
		return order_id

	def compare_forecast_models(
		self,
		selected_date: str | None = None,
		year: str | None = None,
		horizon: int = 1,
		observed_sales: float | None = None,
	) -> dict[str, object]:
		rf_result = self.forecast_daily_sales(
			selected_date=selected_date, year=year, horizon=horizon,
			observed_sales=observed_sales, model="randomforest",
		)
		xgb_result = self.forecast_daily_sales(
			selected_date=selected_date, year=year, horizon=horizon,
			observed_sales=observed_sales, model="xgboost",
		) if XGBOOST_AVAILABLE else None

		comparison: dict[str, object] = {
			"randomforest": rf_result,
			"xgboost": xgb_result,
			"xgboost_available": XGBOOST_AVAILABLE,
			"models_tested": ["randomforest"] + (["xgboost"] if XGBOOST_AVAILABLE else []),
		}

		if xgb_result is not None:
			rf_mae = rf_result.get("random_forest_validation_mae")
			xgb_mae = xgb_result.get("xgboost_validation_mae")
			winner = "randomforest"
			if xgb_mae is not None and rf_mae is not None:
				try:
					if float(xgb_mae) < float(rf_mae):
						winner = "xgboost"
				except (TypeError, ValueError):
					pass
			comparison["winner"] = winner
			try:
				rf_mae_val = float(rf_mae) if rf_mae is not None else 0
				xgb_mae_val = float(xgb_mae) if xgb_mae is not None else 0
				comparison["mae_diff"] = round(abs(rf_mae_val - xgb_mae_val), 2)
			except (TypeError, ValueError):
				comparison["mae_diff"] = 0
			try:
				rf_pred = float(rf_result.get("predicted_sales", 0))
				xgb_pred = float(xgb_result.get("predicted_sales", 0))
				comparison["predicted_sales_difference"] = round(abs(rf_pred - xgb_pred), 2)
				avg = (rf_pred + xgb_pred) / 2.0
				comparison["predicted_sales_ensemble"] = round(avg, 2)
			except (TypeError, ValueError):
				pass
		return comparison

	def detect_anomalies(
		self,
		region: str | None = None,
		category: str | None = None,
		year: str | None = None,
		city: str | None = None,
		window: int = 7,
		sigma_threshold: float = 3.0,
	) -> dict[str, object]:
		frame = self.filtered(region, category, year, city).copy()
		frame["Order Date"] = pd.to_datetime(frame["Order Date"], errors="coerce").dt.normalize()
		daily = frame.groupby("Order Date", as_index=False).agg(
			sales=("Sales", "sum"),
			profit=("Profit", "sum"),
			orders=("Order ID", "nunique"),
			returns=("Return Flag", "sum"),
		)
		daily = daily.sort_values("Order Date").reset_index(drop=True)

		if daily.empty or len(daily) < max(window + 1, 5):
			return {
				"window": int(window),
				"sigma_threshold": float(sigma_threshold),
				"total_days": int(len(daily)),
				"anomalies": [],
				"anomaly_count": 0,
				"basis": "Insufficient daily data for rolling anomaly detection",
			}

		window = max(3, min(int(window), 90))
		sigma_threshold = max(1.0, min(float(sigma_threshold), 6.0))

		daily["rolling_mean"] = daily["sales"].rolling(window=window, min_periods=max(3, window // 2)).mean()
		daily["rolling_std"] = daily["sales"].rolling(window=window, min_periods=max(3, window // 2)).std()
		daily["z_score"] = np.where(
			daily["rolling_std"].fillna(0).gt(0),
			(daily["sales"] - daily["rolling_mean"]) / daily["rolling_std"],
			0.0,
		)
		daily["is_anomaly"] = daily["z_score"].abs().gt(sigma_threshold)
		daily["anomaly_direction"] = np.where(
			daily["is_anomaly"],
			np.where(daily["z_score"] > 0, "spike", "drop"),
			"normal",
		)
		daily["lower_bound"] = daily["rolling_mean"] - sigma_threshold * daily["rolling_std"].fillna(0)
		daily["upper_bound"] = daily["rolling_mean"] + sigma_threshold * daily["rolling_std"].fillna(0)
		daily["lower_bound"] = daily["lower_bound"].clip(lower=0)

		anomaly_mask = daily["is_anomaly"].fillna(False)
		anomalies_df = daily[anomaly_mask].copy()
		anomalies_df["date"] = anomalies_df["Order Date"].dt.strftime("%Y-%m-%d")
		anomaly_records = anomalies_df[[
			"date", "sales", "profit", "orders", "returns",
			"rolling_mean", "rolling_std", "z_score", "anomaly_direction",
			"lower_bound", "upper_bound",
		]].round(2).to_dict("records")

		daily["Order Date"] = daily["Order Date"].dt.strftime("%Y-%m-%d")
		daily_records = daily[[
			"Order Date", "sales", "rolling_mean", "lower_bound", "upper_bound", "z_score", "is_anomaly",
		]].round(2).rename(columns={"Order Date": "date"}).to_dict("records")

		return {
			"window": int(window),
			"sigma_threshold": float(sigma_threshold),
			"total_days": int(len(daily)),
			"anomaly_count": int(len(anomaly_records)),
			"spike_count": int(sum(1 for a in anomaly_records if a.get("anomaly_direction") == "spike")),
			"drop_count": int(sum(1 for a in anomaly_records if a.get("anomaly_direction") == "drop")),
			"anomalies": anomaly_records,
			"daily_series": daily_records,
			"basis": f"{window}-day rolling mean ± {sigma_threshold}σ anomaly detection",
		}

	def ai_advisor_insights(
		self,
		region: str | None = None,
		category: str | None = None,
		year: str | None = None,
		city: str | None = None,
	) -> dict[str, object]:
		frame = self.filtered(region, category, year, city)
		kpis = self.kpis(region, category, year, city)
		insights: list[dict[str, object]] = []
		warnings: list[dict[str, object]] = []
		opportunities: list[dict[str, object]] = []

		total_sales = float(kpis.get("sales", 0))
		total_profit = float(kpis.get("profit", 0))
		return_rate = float(kpis.get("return_rate", 0))
		margin = float(kpis.get("profit_margin", 0))
		total_orders = int(kpis.get("orders", 0))
		total_customers = int(kpis.get("customers", 0))
		aov = float(kpis.get("average_order_value", 0))

		if return_rate >= 15:
			warnings.append({
				"type": "high_return_rate",
				"severity": "high",
				"metric": "return_rate",
				"value": round(return_rate, 2),
				"threshold": 15.0,
				"message": f"Return rate is {return_rate:.1f}% — well above the 15% acceptable threshold.",
				"recommendation": "Investigate top returned categories and regions; review product quality descriptions and sizing info.",
			})
		elif return_rate >= 10:
			warnings.append({
				"type": "elevated_return_rate",
				"severity": "medium",
				"metric": "return_rate",
				"value": round(return_rate, 2),
				"threshold": 10.0,
				"message": f"Return rate is {return_rate:.1f}% — above the 10% watch level.",
				"recommendation": "Monitor return trends and identify root causes for the elevated rate.",
			})

		if total_sales > 0 and margin < 5:
			warnings.append({
				"type": "low_profit_margin",
				"severity": "high",
				"metric": "profit_margin",
				"value": round(margin, 2),
				"threshold": 5.0,
				"message": f"Profit margin is only {margin:.1f}% — below the 5% healthy floor.",
				"recommendation": "Review discount strategy and product costs; prioritize high-margin categories.",
			})
		elif total_sales > 0 and margin < 15:
			opportunities.append({
				"type": "margin_improvement",
				"severity": "low",
				"metric": "profit_margin",
				"value": round(margin, 2),
				"threshold": 15.0,
				"message": f"Profit margin is {margin:.1f}% — there is room to improve toward 15%+.",
				"recommendation": "Shift sales mix toward higher-margin products and optimize discount depth.",
			})

		cat_perf = self.category_performance(region=region, category=category, year=year, city=city)
		if cat_perf:
			low_margin_cats = [c for c in cat_perf if float(c.get("margin_pct", 0) or 0) < 5 and float(c.get("sales", 0)) > 0]
			if low_margin_cats:
				worst_cat = min(low_margin_cats, key=lambda c: float(c.get("margin_pct", 0) or 0))
				warnings.append({
					"type": "low_margin_category",
					"severity": "medium",
					"metric": "category_margin",
					"category": worst_cat.get("Category"),
					"value": round(float(worst_cat.get("margin_pct", 0) or 0), 2),
					"threshold": 5.0,
					"message": f"Category '{worst_cat.get('Category')}' has a low margin of {float(worst_cat.get('margin_pct', 0) or 0):.1f}%.",
					"recommendation": "Consider pricing adjustments or cost improvements for this category.",
				})
			top_cats = sorted(cat_perf, key=lambda c: float(c.get("sales", 0)), reverse=True)[:3]
			if top_cats:
				insights.append({
					"type": "top_performing_categories",
					"severity": "info",
					"categories": [c.get("Category") for c in top_cats],
					"message": f"Top categories by revenue: {', '.join(str(c.get('Category')) for c in top_cats)}.",
					"recommendation": "Double down on top categories with additional inventory, marketing, and merchandising focus.",
				})

		cust_list = self.customers(limit=10, region=region, category=category, year=year, city=city)
		if cust_list and total_customers > 0:
			top_cust_total = sum(float(c.get("sales", 0)) for c in cust_list[:5])
			if total_sales > 0 and top_cust_total / total_sales > 0.4:
				insights.append({
					"type": "customer_concentration",
					"severity": "info",
					"metric": "top5_customer_share",
					"value": round(top_cust_total / total_sales * 100, 2),
					"threshold": 40.0,
					"message": f"Top 5 customers account for {top_cust_total / total_sales * 100:.1f}% of revenue.",
					"recommendation": "Nurture these VIP relationships with loyalty programs while diversifying the customer base.",
				})

		if total_orders > 0 and aov > 0:
			if aov < 50:
				opportunities.append({
					"type": "aov_upsell_opportunity",
					"severity": "low",
					"metric": "average_order_value",
					"value": round(aov, 2),
					"threshold": 50.0,
					"message": f"Average order value is ${aov:.2f} — below $50.",
					"recommendation": "Implement product bundling, cross-sell, and free-shipping-threshold campaigns to lift AOV.",
				})
			elif aov >= 100:
				insights.append({
					"type": "strong_aov",
					"severity": "info",
					"metric": "average_order_value",
					"value": round(aov, 2),
					"threshold": 100.0,
					"message": f"Average order value is ${aov:.2f} — healthy ticket size.",
					"recommendation": "Maintain strong AOV with premium product positioning and effective upsell tactics.",
				})

		total_items = int(kpis.get("quantity", 0))
		if total_orders > 0 and total_items > 0:
			upo = total_items / total_orders
			if upo < 1.5:
				opportunities.append({
					"type": "cross_sell_opportunity",
					"severity": "low",
					"metric": "units_per_order",
					"value": round(upo, 2),
					"threshold": 1.5,
					"message": f"Customers average only {upo:.2f} units per order.",
					"recommendation": "Deploy 'Frequently Bought Together' widgets and multi-buy discounts to increase basket size.",
				})

		if not insights and not warnings and not opportunities:
			insights.append({
				"type": "business_health_good",
				"severity": "info",
				"message": "All key business metrics are within healthy ranges.",
				"recommendation": "Continue current strategy and monitor trends weekly.",
			})

		overall_risk = "low"
		high_count = sum(1 for w in warnings if w.get("severity") == "high")
		med_count = sum(1 for w in warnings if w.get("severity") == "medium")
		if high_count >= 2 or (high_count >= 1 and med_count >= 2):
			overall_risk = "high"
		elif high_count >= 1 or med_count >= 1:
			overall_risk = "medium"

		return {
			"kpis": kpis,
			"overall_risk": overall_risk,
			"insights_count": len(insights),
			"warnings_count": len(warnings),
			"opportunities_count": len(opportunities),
			"insights": insights,
			"warnings": warnings,
			"opportunities": opportunities,
			"summary": {
				"high_severity_warnings": high_count,
				"medium_severity_warnings": med_count,
				"action_items": len(warnings) + len(opportunities),
			},
		}

	def customer_rfm_predictions(
		self,
		limit: int = 50,
		region: str | None = None,
		category: str | None = None,
		year: str | None = None,
		city: str | None = None,
	) -> dict[str, object]:
		frame = self.filtered(region, category, year, city).copy()
		if frame.empty:
			return {
				"total_customers": 0,
				"segment_counts": {},
				"top_customers": [],
				"at_risk_customers": [],
				"churn_candidates": [],
				"basis": "No customer data available for RFM analysis",
			}

		frame["Order Date"] = pd.to_datetime(frame["Order Date"], errors="coerce")
		max_date = frame["Order Date"].max()
		if pd.isna(max_date):
			max_date = pd.Timestamp.now()

		rfm = frame.groupby("Customer ID", dropna=False).agg(
			customer_name=("Customer Name", "first"),
			recency_days=("Order Date", lambda x: (max_date - x.max()).days if x.notna().any() else 9999),
			frequency=("Order ID", "nunique"),
			monetary=("Sales", "sum"),
			total_orders=("Order ID", "count"),
			total_profit=("Profit", "sum"),
			returns=("Return Flag", "sum"),
		).reset_index()

		rfm["recency_days"] = pd.to_numeric(rfm["recency_days"], errors="coerce").fillna(9999).astype(int)
		rfm["frequency"] = pd.to_numeric(rfm["frequency"], errors="coerce").fillna(0).astype(int)
		rfm["monetary"] = pd.to_numeric(rfm["monetary"], errors="coerce").fillna(0.0).astype(float)
		rfm["total_profit"] = pd.to_numeric(rfm["total_profit"], errors="coerce").fillna(0.0).astype(float)
		rfm["returns"] = pd.to_numeric(rfm["returns"], errors="coerce").fillna(0).astype(int)
		rfm["return_rate"] = np.where(rfm["total_orders"] > 0, (rfm["returns"] / rfm["total_orders"] * 100).round(2), 0.0)
		rfm["avg_order_value"] = np.where(rfm["frequency"] > 0, (rfm["monetary"] / rfm["frequency"]).round(2), 0.0)

		total_cust = len(rfm)
		if total_cust > 0:
			rfm["r_score"] = pd.qcut(rfm["recency_days"].rank(method="first"), q=min(5, total_cust), labels=[5, 4, 3, 2, 1], duplicates="drop").astype(int)
			rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), q=min(5, total_cust), labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
			rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), q=min(5, total_cust), labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
		else:
			rfm["r_score"] = 3
			rfm["f_score"] = 3
			rfm["m_score"] = 3

		rfm["rfm_score"] = (rfm["r_score"] * 0.4 + rfm["f_score"] * 0.3 + rfm["m_score"] * 0.3).round(2)
		rfm["rfm_total"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]

		def _segment(row: pd.Series) -> str:
			r, f, m = int(row["r_score"]), int(row["f_score"]), int(row["m_score"])
			total = r + f + m
			if r >= 4 and f >= 4 and m >= 4:
				return "Champions"
			elif r >= 4 and f >= 3 and m >= 3:
				return "Loyal Customers"
			elif r >= 5 and total >= 10:
				return "Recent High Value"
			elif r >= 4 and total >= 7:
				return "Potential Loyalists"
			elif r == 5 and f <= 2 and m <= 2:
				return "New Customers"
			elif r <= 2 and f >= 4 and m >= 4:
				return "At Risk"
			elif r <= 2 and total <= 6:
				return "Churn Candidates"
			elif r >= 3 and total >= 6:
				return "Needs Attention"
			else:
				return "Others"

		rfm["segment"] = rfm.apply(_segment, axis=1)

		rfm["predicted_next_purchase_days"] = np.where(
			rfm["frequency"] >= 2,
			np.clip(round((rfm["recency_days"] * 0.5 + (365.0 / rfm["frequency"]) * 0.5), 0), 1, 365),
			np.clip(round(30.0 + rfm["recency_days"] * 0.5, 0), 7, 365),
		).astype(int)

		rfm["predicted_next_order_value"] = np.where(
			rfm["frequency"] >= 2,
			round(rfm["avg_order_value"] * (1.0 + (5 - rfm["r_score"]) * 0.03), 2),
			round(rfm["avg_order_value"] * 0.9, 2),
		)

		churn_base = 0.1
		rfm["churn_probability"] = np.clip((
			churn_base
			+ np.where(rfm["r_score"] <= 2, 0.35, 0.0)
			+ np.where(rfm["r_score"] == 3, 0.15, 0.0)
			+ np.where(rfm["f_score"] <= 2, 0.15, 0.0)
			+ np.where(rfm["m_score"] <= 2, 0.05, 0.0)
			+ np.where(rfm["return_rate"] > 20, 0.10, 0.0)
		).round(4), 0.01, 0.99)

		purchase_interval = np.where(
			rfm["frequency"] >= 2,
			365.0 / rfm["frequency"].clip(lower=1),
			rfm["recency_days"] + 30.0,
		)
		purchases_per_year = np.minimum(12.0, 365.0 / np.maximum(purchase_interval, 30.0))
		rfm["clv_12m_predicted"] = np.where(
			rfm["frequency"] >= 1,
			(rfm["monetary"] * (1.0 - rfm["churn_probability"]) * np.maximum(1.0, purchases_per_year)).round(2),
			0.0,
		)

		def _action(seg: str) -> str:
			return {
				"Champions": "Reward with exclusive offers and early access; ask for referrals.",
				"Loyal Customers": "Upsell higher-value products; engage with loyalty program.",
				"Recent High Value": "Personalized product recommendations; premium support.",
				"Potential Loyalists": "Send targeted discounts and membership offers.",
				"New Customers": "Onboarding nurture campaign; welcome discount for second purchase.",
				"At Risk": "Aggressive win-back campaign; personalized re-engagement email.",
				"Churn Candidates": "Last chance offer; survey to understand departure reason.",
				"Needs Attention": "Limited-time promotions; remind of brand value.",
				"Others": "Broad engagement campaign; test different messaging.",
			}.get(seg, "Continue standard engagement.")

		rfm["recommended_action"] = rfm["segment"].apply(_action)

		segment_counts = rfm["segment"].value_counts().to_dict()

		top_customers = rfm.sort_values("rfm_score", ascending=False).head(min(limit, total_cust)).copy()
		top_customers["customer_id"] = top_customers["Customer ID"].astype(str)
		top_customers["customer_name"] = top_customers["customer_name"].fillna(top_customers["customer_id"]).astype(str)
		top_records = top_customers[[
			"customer_id", "customer_name", "segment", "rfm_score", "r_score", "f_score", "m_score",
			"recency_days", "frequency", "monetary", "total_profit", "avg_order_value",
			"predicted_next_purchase_days", "predicted_next_order_value",
			"churn_probability", "clv_12m_predicted", "recommended_action", "return_rate",
		]].round(2).to_dict("records")

		at_risk = rfm[rfm["segment"].isin(["At Risk", "Needs Attention"])].sort_values("rfm_score", ascending=True).head(min(limit // 2, total_cust))
		at_risk["customer_id"] = at_risk["Customer ID"].astype(str)
		at_risk["customer_name"] = at_risk["customer_name"].fillna(at_risk["customer_id"]).astype(str)
		at_risk_records = at_risk[[
			"customer_id", "customer_name", "segment", "rfm_score", "recency_days",
			"monetary", "churn_probability", "recommended_action",
		]].round(2).to_dict("records")

		churn = rfm[rfm["segment"] == "Churn Candidates"].sort_values("monetary", ascending=False).head(min(limit // 2, total_cust))
		churn["customer_id"] = churn["Customer ID"].astype(str)
		churn["customer_name"] = churn["customer_name"].fillna(churn["customer_id"]).astype(str)
		churn_records = churn[[
			"customer_id", "customer_name", "segment", "rfm_score", "recency_days",
			"monetary", "churn_probability", "recommended_action",
		]].round(2).to_dict("records")

		return {
			"total_customers": total_cust,
			"segment_counts": segment_counts,
			"rfm_range": {"min_score": float(rfm["rfm_score"].min()) if total_cust else 0.0, "max_score": float(rfm["rfm_score"].max()) if total_cust else 0.0},
			"top_customers": top_records,
			"at_risk_customers": at_risk_records,
			"churn_candidates": churn_records,
			"basis": "Heuristic RFM scoring (Recency 40%, Frequency 30%, Monetary 30%) with rule-based segmentation",
			"average_clv_12m": round(float(rfm["clv_12m_predicted"].mean()), 2) if total_cust else 0.0,
			"average_churn_probability": round(float(rfm["churn_probability"].mean() * 100), 2) if total_cust else 0.0,
		}
