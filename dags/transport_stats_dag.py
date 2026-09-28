"""
cambodia_trade_and_transport_monthly
------------------------------------
Orchestrates the monthly extraction, transformation, and database loading for all 4
Cambodia GDCE trade data pillars:
  1. Transport Mode Statistics   (fact_transportation_stats)
  2. Partner Country Trade       (fact_country_trade)
  3. SITC Sector Trade           (fact_trade_by_sitc)
  4. HS-2 Product Chapter Trade  (fact_trade_by_hs)

Scheduled monthly, backfilling from 2016-01-01 (catchup=True).
Runs parallel TaskGroups for high-throughput execution.
"""
from datetime import datetime, timedelta
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

sys.path.insert(0, "/opt/airflow/src")

from scrapers.transport import scrape_transport_month  # noqa: E402
from scrapers.country import scrape_country_month      # noqa: E402
from scrapers.sitc import scrape_sitc_month            # noqa: E402
from scrapers.hs import scrape_hs_month                # noqa: E402

from transform import (                                # noqa: E402
    transform_transport_month,
    transform_country_month,
    transform_sitc_month,
    transform_hs_month,
)
from load import (                                     # noqa: E402
    load_transport_month,
    load_country_month,
    load_sitc_month,
    load_hs_month,
)

default_args = {
    "owner": "data-eng",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}


# --- 1. TRANSPORT MODE TASKS -------------------------------------------------

def _scrape_transport(**context):
    start = context["data_interval_start"].date().isoformat()
    end = context["data_interval_end"].date().isoformat()
    raw_path = scrape_transport_month(start, end)
    context["ti"].xcom_push(key="raw_path", value=raw_path)


def _transform_transport(**context):
    raw_path = context["ti"].xcom_pull(key="raw_path", task_ids="transport_mode.scrape_transport")
    processed_path = transform_transport_month(raw_path)
    context["ti"].xcom_push(key="processed_path", value=processed_path)


def _load_transport(**context):
    raw_path = context["ti"].xcom_pull(key="raw_path", task_ids="transport_mode.scrape_transport")
    processed_path = context["ti"].xcom_pull(key="processed_path", task_ids="transport_mode.transform_transport")
    start = context["data_interval_start"].date().isoformat()
    end = context["data_interval_end"].date().isoformat()
    load_transport_month(
        processed_csv_path=processed_path,
        raw_json_path=raw_path,
        dag_run_id=context["run_id"],
        data_interval_start=start,
        data_interval_end=end,
    )


# --- 2. PARTNER COUNTRY TASKS ------------------------------------------------

def _scrape_country(**context):
    start = context["data_interval_start"].date().isoformat()
    end = context["data_interval_end"].date().isoformat()
    raw_path = scrape_country_month(start, end)
    context["ti"].xcom_push(key="raw_path", value=raw_path)


def _transform_country(**context):
    raw_path = context["ti"].xcom_pull(key="raw_path", task_ids="partner_country.scrape_country")
    processed_path = transform_country_month(raw_path)
    context["ti"].xcom_push(key="processed_path", value=processed_path)


def _load_country(**context):
    raw_path = context["ti"].xcom_pull(key="raw_path", task_ids="partner_country.scrape_country")
    processed_path = context["ti"].xcom_pull(key="processed_path", task_ids="partner_country.transform_country")
    load_country_month(processed_csv_path=processed_path, raw_json_path=raw_path)


# --- 3. SITC SECTOR TASKS ----------------------------------------------------

def _scrape_sitc(**context):
    start = context["data_interval_start"].date().isoformat()
    end = context["data_interval_end"].date().isoformat()
    raw_path = scrape_sitc_month(start, end)
    context["ti"].xcom_push(key="raw_path", value=raw_path)


def _transform_sitc(**context):
    raw_path = context["ti"].xcom_pull(key="raw_path", task_ids="sitc_sectors.scrape_sitc")
    processed_path = transform_sitc_month(raw_path)
    context["ti"].xcom_push(key="processed_path", value=processed_path)


def _load_sitc(**context):
    raw_path = context["ti"].xcom_pull(key="raw_path", task_ids="sitc_sectors.scrape_sitc")
    processed_path = context["ti"].xcom_pull(key="processed_path", task_ids="sitc_sectors.transform_sitc")
    load_sitc_month(processed_csv_path=processed_path, raw_json_path=raw_path)


# --- 4. HS CHAPTER TASKS -----------------------------------------------------

def _scrape_hs(**context):
    start = context["data_interval_start"].date().isoformat()
    end = context["data_interval_end"].date().isoformat()
    raw_path = scrape_hs_month(start, end)
    context["ti"].xcom_push(key="raw_path", value=raw_path)


def _transform_hs(**context):
    raw_path = context["ti"].xcom_pull(key="raw_path", task_ids="hs_chapters.scrape_hs")
    processed_path = transform_hs_month(raw_path)
    context["ti"].xcom_push(key="processed_path", value=processed_path)


def _load_hs(**context):
    raw_path = context["ti"].xcom_pull(key="raw_path", task_ids="hs_chapters.scrape_hs")
    processed_path = context["ti"].xcom_pull(key="processed_path", task_ids="hs_chapters.transform_hs")
    load_hs_month(processed_csv_path=processed_path, raw_json_path=raw_path)


# --- DAG DEFINITION ----------------------------------------------------------

with DAG(
    dag_id="cambodia_trade_and_transport_monthly",
    description="Full monthly ETL for Cambodia GDCE Transport, Country, SITC, and HS-2 statistics",
    default_args=default_args,
    start_date=datetime(2016, 1, 1),
    schedule="@monthly",
    catchup=True,
    max_active_runs=4,
    tags=["etl", "cambodia", "gdce", "customs", "transport", "country", "sitc", "hs"],
) as dag:

    # 1. Transport Mode TaskGroup
    with TaskGroup("transport_mode", tooltip="Transport Mode pipeline") as tg_transport:
        t_scrape = PythonOperator(task_id="scrape_transport", python_callable=_scrape_transport)
        t_transform = PythonOperator(task_id="transform_transport", python_callable=_transform_transport)
        t_load = PythonOperator(task_id="load_transport", python_callable=_load_transport)
        t_scrape >> t_transform >> t_load

    # 2. Partner Country TaskGroup
    with TaskGroup("partner_country", tooltip="Partner Country trade pipeline") as tg_country:
        c_scrape = PythonOperator(task_id="scrape_country", python_callable=_scrape_country)
        c_transform = PythonOperator(task_id="transform_country", python_callable=_transform_country)
        c_load = PythonOperator(task_id="load_country", python_callable=_load_country)
        c_scrape >> c_transform >> c_load

    # 3. SITC Sector TaskGroup
    with TaskGroup("sitc_sectors", tooltip="SITC Sectors trade pipeline") as tg_sitc:
        s_scrape = PythonOperator(task_id="scrape_sitc", python_callable=_scrape_sitc)
        s_transform = PythonOperator(task_id="transform_sitc", python_callable=_transform_sitc)
        s_load = PythonOperator(task_id="load_sitc", python_callable=_load_sitc)
        s_scrape >> s_transform >> s_load

    # 4. HS Chapters TaskGroup
    with TaskGroup("hs_chapters", tooltip="HS Chapters trade pipeline") as tg_hs:
        h_scrape = PythonOperator(task_id="scrape_hs", python_callable=_scrape_hs)
        h_transform = PythonOperator(task_id="transform_hs", python_callable=_transform_hs)
        h_load = PythonOperator(task_id="load_hs", python_callable=_load_hs)
        h_scrape >> h_transform >> h_load
