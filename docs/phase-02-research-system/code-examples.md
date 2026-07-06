# Phase 02 Code Examples

Run research for a topic:

```bash
curl -X POST "http://127.0.0.1:8000/api/research/start/{topic_id}?max_sources=4"
```

Read research:

```bash
curl "http://127.0.0.1:8000/api/research/{topic_id}"
```

Generate a script after research:

```bash
curl -X POST "http://127.0.0.1:8000/api/scripts/{topic_id}/generate"
```
