-- AI Documentary Studio — SQLite Schema (Phase 1+)

-- Topics Table
CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'General',
    status TEXT NOT NULL DEFAULT 'DISCOVERED',
    interest_score REAL DEFAULT 0.0,
    uniqueness_score REAL DEFAULT 0.0,
    source_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    published_at TIMESTAMP,
    embedding BLOB
);

-- Scripts Table
CREATE TABLE IF NOT EXISTS scripts (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL,
    content TEXT,
    status TEXT NOT NULL DEFAULT 'DRAFTED',
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);

-- Scenes Table (Phase 3)
CREATE TABLE IF NOT EXISTS scenes (
    id TEXT PRIMARY KEY,
    script_id TEXT NOT NULL,
    order_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    image_path TEXT,
    audio_path TEXT,
    duration REAL DEFAULT 8.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (script_id) REFERENCES scripts(id)
);

-- Jobs Table (async work queue)
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    topic_id TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    payload TEXT,
    result TEXT,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);

-- Research Sources Table (Phase 2)
CREATE TABLE IF NOT EXISTS research_sources (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL,
    url TEXT,
    title TEXT,
    content TEXT,
    credibility_score REAL DEFAULT 0.5,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);

-- Research Facts Table (Phase 2)
CREATE TABLE IF NOT EXISTS research_facts (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL,
    source_id TEXT,
    fact TEXT NOT NULL,
    confidence REAL DEFAULT 0.7,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id),
    FOREIGN KEY (source_id) REFERENCES research_sources(id)
);

-- Videos Table (Phase 3)
CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL,
    script_id TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    file_path TEXT,
    duration_seconds INTEGER,
    file_size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id),
    FOREIGN KEY (script_id) REFERENCES scripts(id)
);

-- YouTube Uploads Table (Phase 4)
CREATE TABLE IF NOT EXISTS youtube_uploads (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    youtube_id TEXT,
    title TEXT,
    description TEXT,
    tags TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    scheduled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_at TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

-- Analytics Table (Phase 5)
CREATE TABLE IF NOT EXISTS analytics (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    youtube_id TEXT,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    watch_time_seconds INTEGER DEFAULT 0,
    click_through_rate REAL DEFAULT 0.0,
    topic_score REAL DEFAULT 0.0,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id)
);

-- Assets Table (Phase 3)
CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('image', 'audio', 'thumbnail')),
    file_path TEXT NOT NULL,
    topic_id TEXT NOT NULL,
    scene_id TEXT,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id),
    FOREIGN KEY (scene_id) REFERENCES scenes(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_topics_status ON topics(status);
CREATE INDEX IF NOT EXISTS idx_scripts_topic_id ON scripts(topic_id);
CREATE INDEX IF NOT EXISTS idx_scenes_script_id ON scenes(script_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_research_sources_topic_id ON research_sources(topic_id);
CREATE INDEX IF NOT EXISTS idx_research_facts_topic_id ON research_facts(topic_id);
CREATE INDEX IF NOT EXISTS idx_videos_topic_id ON videos(topic_id);
CREATE INDEX IF NOT EXISTS idx_youtube_uploads_video_id ON youtube_uploads(video_id);
CREATE INDEX IF NOT EXISTS idx_youtube_uploads_status ON youtube_uploads(status);
CREATE INDEX IF NOT EXISTS idx_analytics_video_id ON analytics(video_id);
