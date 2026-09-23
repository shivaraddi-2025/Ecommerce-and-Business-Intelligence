from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


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
	) -> pd.DataFrame:
		frame = self.frame
		regions = self._parse_filter_values(region)
		categories = self._parse_filter_values(category)
		cities = self._parse_filter_values(city)
		if regions:
			frame = frame[frame["Region"].isin(regions)]
		if categories:
			frame = frame[frame["Category"].isin(categories)]
		if cities:
			frame = frame[frame["City"].isin(cities)]
		if year:
			try:
				year_value = int(str(year))
				frame = frame[frame["Order Date"].dt.year.eq(year_value)]
			except Exception:
				pass
		return frame

	def kpis(self, region: str | None = None, category: str | None = None, year: str | None = None, city: str | None = None) -> dict[str, float | int]:
		frame = self.filtered(region, category, year, city)
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

	def category_performance(self) -> list[dict[str, object]]:
		result = self.frame.groupby("Category", as_index=False).agg(
			sales=("Sales", "sum"),
			profit=("Profit", "sum"),
			orders=("Order ID", "nunique"),
			return_rate=("Return Flag", "mean"),
		)
		result["return_rate"] = (result["return_rate"] * 100).round(2)
		return result.round(2).sort_values("sales", ascending=False).to_dict("records")

	def top_products(self, limit: int = 10) -> list[dict[str, object]]:
		result = self.frame.groupby(["Product ID", "Product Name"], as_index=False).agg(
			sales=("Sales", "sum"),
			profit=("Profit", "sum"),
			units=("Quantity", "sum"),
			return_rate=("Return Flag", "mean"),
		)
		result["return_rate"] = (result["return_rate"] * 100).round(2)
		return result.sort_values("sales", ascending=False).head(limit).round(2).to_dict("records")

	def customers(self, limit: int = 10) -> list[dict[str, object]]:
		result = self.frame.groupby(["Customer ID", "Customer Name"], dropna=False, as_index=False).agg(
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
	) -> dict[str, object]:
		"""Train on past daily observations and forecast the day after the selected/latest date."""
		horizon = max(1, min(int(horizon), 30))
		empty = {
			"forecast_date": "", "today_sales": 0, "predicted_sales": 0,
			"predicted_revenue": 0, "predicted_profit": 0, "predicted_loss": None, "predicted_orders": 0,
			"confidence": 0, "forecast": [], "basis": "Insufficient daily data for an ML forecast",
			"profit_basis": "Estimated at 30% margin; source has no profit or cost field",
			"loss_basis": "Unavailable because the source has no cost or expense data",
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
		model = RandomForestRegressor(
			n_estimators=300, min_samples_leaf=2, max_features=0.9,
			random_state=42, n_jobs=1,
		)
		if len(validation_y):
			model.fit(train_x[:split], train_y[:split])
			ml_validation = model.predict(validation_x)
			baseline_validation = np.asarray([row[5] for row in validation_x], dtype=float)
			ml_mae = float(np.mean(np.abs(validation_y - ml_validation)))
			baseline_mae = float(np.mean(np.abs(validation_y - baseline_validation)))
		else:
			ml_mae = float('inf')
			baseline_mae = float('inf')
		# Use the ML result only when it beats the 7-day mean on unseen dates.
		use_ml = ml_mae <= baseline_mae
		model.fit(train_x, train_y)
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
			ml_forecast = float(model.predict([features])[0])
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
		return {
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
			"confidence": 0,
			"basis": "Random forest" if use_ml else "7-day average (lower validation MAE than random forest)",
			"forecast_scale": round(forecast_scale, 8),
			"validation_mae": round(ml_mae if use_ml else baseline_mae, 2),
			"random_forest_validation_mae": round(ml_mae, 2),
			"baseline_validation_mae": round(baseline_mae, 2),
			"validation_days": int(len(validation_y)),
			"profit_basis": "Estimated at 30% margin; source has no profit or cost field",
			"loss_rate": round(loss_rate, 4) if loss_rate is not None else None,
			"loss_basis": f"{self.prediction_loss_basis} ({loss_rate:.1%} historical rate)" if loss_rate is not None else self.prediction_loss_basis,
		}

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
