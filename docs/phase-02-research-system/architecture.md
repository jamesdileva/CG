# Phase 02 Architecture

## Flow

Approved topic
-> research job
-> source candidates
-> scrape and clean text
-> store sources
-> extract facts
-> derive timeline
-> mark topic `RESEARCH_COMPLETE`
-> script generation consumes facts

## Backend Modules

- `backend/api/research.py` - FastAPI research endpoints.
- `backend/research/scraper.py` - candidate URLs and text scraping.
- `backend/research/sources.py` - persistence orchestration.
- `backend/research/extractor.py` - fact and timeline extraction.
- `backend/research/ranking.py` - lightweight source credibility scoring.

## Frontend

- `renderer/src/pages/Research.tsx`
- `renderer/src/pages/Research.css`
- `renderer/src/api/client.ts`
