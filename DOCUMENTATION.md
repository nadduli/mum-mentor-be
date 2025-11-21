# Project Documentation

## Download Link Tracking System

### Overview

The Download Link Tracking system records user interactions with downloadable assets (e.g., app binary, PDFs, resources). Each click generates a `download_events` record for analytics and growth insights.

### Data Model (`download_events`)

Fields:

- id (UUID)
- user_id (UUID, nullable) – present if authenticated
- session_id (string, nullable) – temporary identifier for anonymous tracking
- download_type (string) – category (e.g., `app`, `pdf`, `resource`)
- resource_id (string, nullable) – internal identifier/version tag
- file_name (string, nullable)
- file_url (text, nullable)
- referrer (string, nullable) – HTTP Referer header
- source (string, nullable) – marketing/campaign code
- ip_address (string, nullable)
- user_agent (text, nullable)
- device_type (string, nullable) – inferred (`mobile`, `tablet`, `desktop`)
- metadata (JSON, nullable) – extensible custom attributes
- occurred_at (datetime UTC)

### Endpoints

POST `/api/v1/downloads/track`
Body example:

```
{
  "download_type": "app",
  "resource_id": "android_v1",
  "file_name": "nora-v1.apk",
  "file_url": "https://cdn.example.com/nora-v1.apk",
  "source": "landing_page_banner",
  "metadata": {"campaign": "launch"}
}
```

Response:

```
{
  "id": "<uuid>",
  "download_type": "app",
  "occurred_at": "2025-11-17T10:00:00Z"
}
```

GET `/api/v1/downloads/stats?from=<iso>&to=<iso>&group_by=download_type`
Returns aggregated counts per `group_by` field.

### Usage Notes

- Authentication integration can populate `user_id` later.
- Provide a session identifier header (e.g., `X-Session-ID`) for better anonymous tracking (not yet implemented).
- Avoid storing sensitive/signed URLs: use canonical asset URLs.
- Extend `metadata` for campaign codes, app versions, AB test buckets.

### Error Handling

- 400 for invalid grouping field.
- 500 for unexpected persistence errors (returns structured fail response).

### Analytics Extensions (Future)

- Add endpoint for time-series aggregation.
- Integrate external analytics (Segment / PostHog) dispatch in service layer.
- Implement session cookie issuance for anonymous users.
- Add CSV export endpoint.
- Enhance device parsing using `user-agents` library.

### Testing

Tests cover:

- Successful anonymous tracking.
- Stats endpoint returns list structure.

### Migration

Alembic revision: `add_download_events_table` creates `download_events` plus indexes.

### Security & Privacy

- IP and user_agent stored for operational analytics; consider retention policy.
- PII limited to optional user_id. No direct email stored.
- Implement data purging job for old raw events in future.

### Performance Considerations

- Table indexed on `user_id`, `download_type`, `occurred_at` for efficient filtering.
- Write path is single insert; keep payload size minimal.

### Maintenance

- To add new fields: update SQLAlchemy model, create migration, adjust schemas, extend tests.

### Future Enhancements

- Add authentication context to populate `user_id`.
- Implement session-id extraction from header or cookie.
- Provide bulk export CSV/JSON endpoints.
- Add time bucket stats (daily counts) endpoint.
- Integrate caching for heavy stats queries.
- Add anomaly detection (e.g., sudden spikes) alerts.
