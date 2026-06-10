from __future__ import annotations


class ProviderSyncJob:
    def __init__(self, provider_id: str | None) -> None:
        self.provider_id = provider_id


def run_scheduled_job(provider_id: str | None) -> dict[str, str]:
    if provider_id is None:
        return {"status": "skipped", "reason": "missing provider_id"}
    return {"status": "queued", "provider_id": provider_id}


def render_report_title(total_records: int) -> str:
    return f"Report for {total_records} items"


def update_report_wording(title: str) -> str:
    return title.replace("items", "records")
