# Phase 02 API Reference

## Start Research

`POST /api/research/start/{topic_id}?max_sources=4`

Starts a background research job. The topic must be `APPROVED`, `RESEARCHING`, or `RESEARCH_COMPLETE`.

Response:

```json
{
  "message": "Research started",
  "topic_id": "uuid",
  "job_id": "uuid"
}
```

## Get Research

`GET /api/research/{topic_id}`

Response:

```json
{
  "topic_id": "uuid",
  "sources": [],
  "facts": [],
  "timeline": [],
  "conflicts": []
}
```
