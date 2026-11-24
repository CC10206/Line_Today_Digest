"""init: article + click_event tables (PRD 第 6 節)

Revision ID: 0001
Revises:
Create Date: 2026-11-24
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE EXTENSION IF NOT EXISTS vector;

    CREATE TABLE article (
        id              BIGSERIAL PRIMARY KEY,
        url             TEXT        NOT NULL UNIQUE,
        source          VARCHAR(64) NOT NULL,
        title           TEXT        NOT NULL,
        content         TEXT,
        image_url       TEXT,
        published_at    TIMESTAMPTZ NOT NULL,
        summary         TEXT,
        category        VARCHAR(16),
        keywords        TEXT[],
        embedding       vector(1536),
        status          VARCHAR(16) NOT NULL DEFAULT 'PENDING',
        retry_count     INT         NOT NULL DEFAULT 0,
        last_error      TEXT,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        enriched_at     TIMESTAMPTZ
    );

    CREATE INDEX idx_article_status    ON article (status, created_at);
    CREATE INDEX idx_article_published ON article (published_at DESC);
    CREATE INDEX idx_article_category  ON article (category, published_at DESC);
    CREATE INDEX idx_article_embedding ON article USING hnsw (embedding vector_cosine_ops);

    CREATE TABLE click_event (
        id            BIGSERIAL PRIMARY KEY,
        line_user_id  VARCHAR(64) NOT NULL,
        article_id    BIGINT      NOT NULL REFERENCES article(id),
        action        VARCHAR(16) NOT NULL,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX idx_click_user ON click_event (line_user_id, created_at DESC);
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS click_event;
    DROP TABLE IF EXISTS article;
    """)
