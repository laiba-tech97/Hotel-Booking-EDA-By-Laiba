# Hotel Booking Analysis Dashboard

An interactive Streamlit dashboard based on the analysis in [`main.ipynb`](./main.ipynb). The dashboard explores booking volume, cancellations, hotel performance, customer groups, country of origin, arrival trends, pricing, lead time, guest composition, and source-data quality.

## Project Overview

The Jupyter notebook analyzes a hotel booking demand dataset using pandas, NumPy, Matplotlib, and Seaborn. This project turns the notebook's questions, cleaning steps, visualizations, and recorded findings into an interactive Plotly dashboard.

The dashboard uses the same hotel-booking CSV as the notebook. The dataset is not included in this repository, so provide it by uploading the CSV in the dashboard or placing a CSV in the project folder. The original notebook and dataset are not modified.

## Project Objectives

- Understand booking and cancellation patterns across City Hotel and Resort Hotel.
- Compare average daily rates (ADR), lead times, guest totals, and hotel types.
- Explore customer types, countries, and market segments.
- Track booking activity by arrival year and month.
- Surface missing values, duplicates, and ADR outliers without hiding or changing the source data.
- Make the notebook findings easy to explore with interactive filters and charts.

## Dataset Description

The notebook loads the **Hotel Booking Demand** CSV. Each row represents a hotel reservation and includes hotel type, cancellation status, lead time, arrival fields, guests, market segment, country, room, customer, pricing, and reservation-status details.

The source schema also contains customer name, email, phone number, and masked credit-card fields. The dashboard does not display those personal/contact fields in its preview or charts.

### Dataset Information

The notebook's executed `df.shape` output reports **119,390 rows and 36 columns**. This is the actual shape reported for the CSV loaded by the notebook. The notebook's introductory data card says 32 columns; that conflicts with the loaded CSV's 36-column output, so the executed shape is used here. The data card also labels duplicates as present, while the notebook's executed duplicate check found **0** exact duplicate rows.

The notebook reports 16 integer, 4 floating-point, and 16 string columns before cleaning. The main analysis fields include:

| Category | Fields |
|---|---|
| Booking and hotel | `hotel`, `is_canceled`, `reservation_status` |
| Arrival timing | `arrival_date_year`, `arrival_date_month`, `arrival_date_week_number`, `arrival_date_day_of_month` |
| Guests and stay | `adults`, `children`, `babies`, `stays_in_weekend_nights`, `stays_in_week_nights` |
| Pricing and booking | `adr`, `lead_time`, `booking_changes`, `deposit_type` |
| Customer and channel | `country`, `customer_type`, `market_segment`, `distribution_channel` |
| Requests and history | `total_of_special_requests`, `is_repeated_guest`, `previous_cancellations` |

The repository does not contain the CSV. Its name in the notebook is `hotel_booking.csv`; provide the matching dataset when running the dashboard.

## Technologies and Libraries Used

- Python
- Jupyter Notebook
- Streamlit
- pandas and NumPy
- Plotly
- Matplotlib and Seaborn (used in the original notebook)

## Data Cleaning Process

The notebook's cleaning process and the dashboard's analysis copy follow these steps:

1. Inspect column names, data types, descriptive statistics, and missing values.
2. Fill missing `children` values with `0`.
3. Fill missing `country` values with the most frequent country.
4. Fill missing `agent` and `company` values with `0`.
5. Check for exact duplicate rows and remove duplicates from the analysis copy. The notebook found no exact duplicates in its loaded data.
6. Convert `reservation_status_date` to a date value for analysis.
7. Calculate guest totals from adults, children, and babies.
8. Use the IQR rule to identify ADR outliers; do not remove them from the analysis.

In the notebook's pre-cleaning `df.info()` output, the missing counts were: `children` 4, `country` 488, `agent` 16,340, and `company` 112,593. The dashboard computes these counts from the CSV supplied at runtime rather than assuming that a future file has identical data quality.

## Exploratory Data Analysis

The notebook inspects the data shape, column list, types, head/tail, descriptive statistics, distinct values, nulls, and duplicate rows. It visualizes outliers in ADR, lead time, and total guests, then answers booking, cancellation, hotel, customer, and pricing questions with charts.

## Key Questions Answered

- How many bookings were canceled and not canceled?
- Which hotel type has more bookings?
- What is the lead-time distribution and average lead time?
- Which market segment has the most bookings?
- How are lead time and ADR related?
- Does the number of special requests relate to cancellations?
- Which hotel type has the higher average ADR?
- Which customer type has the highest cancellation rate?

## Dashboard Features

- Sidebar navigation across overview, hotel performance, cancellations, customers/countries, trends, ADR/lead time, guest distribution, and data quality.
- Upload a CSV or automatically choose a CSV from the project folder.
- Interactive filters for hotel type, arrival year, arrival month, market segment, customer type, and booking status.
- KPI cards for total bookings, cancellations, cancellation rate, average ADR, and total guests.
- Responsive Plotly charts with clear labels, legends, and contextual summaries.
- A privacy-safe booking preview that excludes guest names, email, phone, and card fields.
- Clear errors for unreadable CSV files and missing required columns.
- Data quality reporting based on the supplied file; charts use cleaned copies and do not write to the source file.

## Visualizations

- Hotel booking counts, cancellation rates, and average ADR by hotel type.
- Canceled versus not-canceled bookings.
- Cancellation rate by customer type, market segment, and special-request count.
- Top booking countries, customer type mix, and market segments.
- Monthly arrivals by hotel type and yearly booking totals.
- ADR and lead-time distributions, lead-time-versus-ADR scatter plot, and ADR by hotel.
- Guest party-size distribution and adult/child/baby composition.
- Missing-value counts and IQR-flagged ADR outliers.

## Key Insights and Findings from the Notebook

These are the notebook's recorded results for its unfiltered analysis run; dashboard values recalculate against the CSV and selected filters.

- Of **119,390** bookings, **44,224** were canceled and **75,166** were not canceled (about **37.04%** canceled).
- City Hotel had **79,330** bookings; Resort Hotel had **40,060**.
- Average lead time was **104.01 days**.
- Online TA was the largest market segment with **56,477** bookings.
- The lead-time/ADR correlation was **−0.063**, a very weak negative relationship.
- Average ADR was **105.30** for City Hotel and **94.95** for Resort Hotel.
- Transient customers had the highest cancellation rate at about **40.75%**. The notebook also reports that bookings with zero special requests had the highest cancellation rate among request counts.
- The IQR check flagged **3,793 ADR outliers**. The notebook visualizes outliers for ADR, lead time, and total guests; it does not report numeric IQR counts for the latter two.

## Project Folder Structure

```text
Hotel-Booking-EDA-By-Laiba/
├── main.ipynb
├── app.py
├── requirements.txt
├── README.md
└── hotel_booking.csv       # optional local data file; not included
```

## Installation Instructions

Use Python 3.10 or newer. From a terminal opened in the project folder:

```bash
python -m venv .venv
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux, use `source .venv/bin/activate` instead.

Install the requirements:

```bash
python -m pip install -r requirements.txt
```

## How to Run the Dashboard

Run this command from the project folder:

```bash
streamlit run app.py
```

If the CSV is not already in the project folder, upload it using the **Upload hotel booking CSV** control in the sidebar. The dashboard does not rely on the notebook's machine-specific absolute file path.

## Future Improvements

- Add downloadable filtered summaries and chart exports.
- Add more arrival-date and stay-duration breakdowns.
- Add optional deployment instructions and a documented data-source link when the dataset license/source is confirmed.
- Add automated tests using a small, privacy-safe sample CSV.
