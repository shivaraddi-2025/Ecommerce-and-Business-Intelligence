from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


class AnalyticsEngine:
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
				"Sales": frame["net_amount"],
				"Profit": 0.0,
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
		return {
			"records": int(len(self.frame)),
			"columns": len(self.source_columns),
			"source_columns": self.source_columns,
			"status_counts": self.status_counts,
			"has_profit_data": self.has_profit_data,
			"missing_values": int(self.frame.isna().sum().sum()),
			"duplicate_rows": int(self.frame.duplicated().sum()),
			"negative_profit_rows": int((self.frame["Profit"] < 0).sum()),
			"returned_orders": int(self.frame["Return Flag"].sum()),
			"date_min": self.frame["Order Date"].min().strftime("%Y-%m-%d"),
			"date_max": self.frame["Order Date"].max().strftime("%Y-%m-%d"),
		}

	def forecast_daily_sales(self, selected_date: str | None = None, year: str | None = None) -> dict[str, object]:
		estimated_margin = 0.30
		if self.daily_frame.empty:
			return {
				"forecast_date": "",
				"today_sales": 0,
				"predicted_sales": 0,
				"predicted_profit": 0,
				"predicted_loss": 0,
				"predicted_orders": 0,
				"confidence": 0,
				"basis": "No daily dataset available",
				"profit_basis": "Estimated at 30% margin; source has no profit or cost field",
			}

		frame = self.daily_frame.copy()
		frame['Order Date'] = pd.to_datetime(frame['Order Date'], errors='coerce')
		frame = frame.sort_values('Order Date').dropna(subset=['Order Date']).reset_index(drop=True)
		if frame.empty:
			return {
				"forecast_date": "",
				"today_sales": 0,
				"predicted_sales": 0,
				"predicted_profit": 0,
				"predicted_loss": 0,
				"predicted_orders": 0,
				"confidence": 0,
				"basis": "No daily dataset available",
				"profit_basis": "Estimated at 30% margin; source has no profit or cost field",
			}

		if year:
			try:
				year_value = int(str(year))
				frame = frame[frame['Order Date'].dt.year.eq(year_value)].copy()
			except Exception:
				pass

		if frame.empty:
			return {
				"forecast_date": "",
				"today_sales": 0,
				"predicted_sales": 0,
				"predicted_profit": 0,
				"predicted_loss": 0,
				"predicted_orders": 0,
				"confidence": 0,
				"basis": "No daily data for selected year",
				"profit_basis": "Estimated at 30% margin; source has no profit or cost field",
			}

		base_date = pd.Timestamp(frame['Order Date'].iloc[-1])
		if selected_date:
			try:
				selected = pd.Timestamp(selected_date).normalize()
				filtered = frame[frame['Order Date'] <= selected].copy()
				if filtered.empty:
					frame = self.daily_frame.copy()
					frame['Order Date'] = pd.to_datetime(frame['Order Date'], errors='coerce')
					frame = frame.sort_values('Order Date').dropna(subset=['Order Date']).reset_index(drop=True)
					if year:
						try:
							year_value = int(str(year))
							frame = frame[frame['Order Date'].dt.year.eq(year_value)].copy()
						except Exception:
							pass
					if frame.empty:
						return {
							"forecast_date": "",
							"today_sales": 0,
							"predicted_sales": 0,
							"predicted_profit": 0,
							"predicted_loss": 0,
							"predicted_orders": 0,
							"confidence": 0,
							"basis": "No daily data for selected date/year",
							"profit_basis": "Estimated at 30% margin; source has no profit or cost field",
						}
					base_date = pd.Timestamp(frame['Order Date'].iloc[-1])
				else:
					frame = filtered
					base_date = pd.Timestamp(selected)
			except Exception:
				selected = None

		if frame.empty:
			return {
				"forecast_date": "",
				"today_sales": 0,
				"predicted_sales": 0,
				"predicted_profit": 0,
				"predicted_loss": 0,
				"predicted_orders": 0,
				"confidence": 0,
				"basis": "No daily data for selected date/year",
				"profit_basis": "Estimated at 30% margin; source has no profit or cost field",
			}

		last_day = frame.tail(1).iloc[0]
		last_sales = float(last_day.get('sales', 0) or 0)
		last_profit = float(last_day.get('profit', 0) or 0)
		last_orders = int(last_day.get('orders', 0) or 0)
		last_return_rate = float(last_day.get('return_rate', 0) or 0)

		# Use a 7-day moving average as the sales and profit baseline and then apply a mild growth
		# correction based on the latest change in the last two observed days.
		window = min(7, len(frame))
		last_window = frame.tail(window)
		moving_sales = float(last_window['sales'].mean())
		moving_profit = float(last_window['profit'].mean())
		moving_orders = float(last_window['orders'].mean())

		trend_growth = 0.0
		if len(frame) >= 2:
			last_two = frame.tail(2)
			previous_sales = float(last_two.iloc[0].get('sales', 0) or 0)
			trend_growth = (last_sales - previous_sales) / previous_sales if previous_sales else 0.0

		forecast_sales = moving_sales * (1 + max(min(trend_growth, 0.08), -0.03))
		forecast_profit = max(forecast_sales * estimated_margin, 0)
		forecast_loss = max(-forecast_sales * estimated_margin, 0)
		forecast_orders = max(int(round(moving_orders)), 1)

		# Confidence dampens when the latest return rate is high, which matches the risk-aware
		# dashboard language already used elsewhere in the daily report.
		return_pressure = min(max(last_return_rate, 0), 100)
		confidence = max(55, min(98, int(round(92 - (return_pressure * 0.5)))))
		forecast_date = pd.Timestamp(base_date) + pd.Timedelta(days=1)

		return {
			"forecast_date": forecast_date.strftime('%Y-%m-%d'),
			"today_sales": round(last_sales, 2),
			"predicted_sales": round(forecast_sales, 2),
			"predicted_profit": round(forecast_profit, 2),
			"predicted_loss": round(forecast_loss, 2),
			"predicted_orders": int(forecast_orders),
			"confidence": int(confidence),
			"basis": "moving 7-day average with latest growth adjustment",
			"profit_basis": "Estimated at 30% margin; source has no profit or cost field",
			"return_rate": round(last_return_rate, 2),
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
