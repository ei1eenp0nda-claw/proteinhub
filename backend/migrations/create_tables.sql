-- ProteinHub Database Schema Migration
-- 学术笔记平台数据库建表脚本
-- PostgreSQL 15+

-- 创建扩展（如果需要）
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- 1. 用户表 (users)
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    bio TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一约束
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email UNIQUE (email)
);

-- 用户表索引
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_created_at ON users(created_at);

COMMENT ON TABLE users IS '用户表 - 存储平台注册用户的基本信息';
COMMENT ON COLUMN users.id IS '主键ID';
COMMENT ON COLUMN users.username IS '用户名';
COMMENT ON COLUMN users.email IS '邮箱地址';
COMMENT ON COLUMN users.password_hash IS '密码哈希值';
COMMENT ON COLUMN users.avatar_url IS '头像URL';
COMMENT ON COLUMN users.bio IS '个人简介';
COMMENT ON COLUMN users.created_at IS '创建时间';


-- =====================================================
-- 2. 笔记表 (notes)
-- =====================================================
CREATE TABLE IF NOT EXISTS notes (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    author_id BIGINT NOT NULL,
    
    -- 论文元数据
    paper_title VARCHAR(500),
    paper_venue VARCHAR(255),
    paper_year INTEGER,
    paper_doi VARCHAR(100),
    paper_pmid VARCHAR(20),
    
    -- 标签和统计
    tags TEXT,  -- JSON数组或逗号分隔的标签列表
    like_count INTEGER NOT NULL DEFAULT 0,
    favorite_count INTEGER NOT NULL DEFAULT 0,
    comment_count INTEGER NOT NULL DEFAULT 0,
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    CONSTRAINT fk_notes_author_id 
        FOREIGN KEY (author_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE
);

-- 笔记表索引
CREATE INDEX IF NOT EXISTS ix_notes_author_id ON notes(author_id);
CREATE INDEX IF NOT EXISTS ix_notes_created_at ON notes(created_at);
CREATE INDEX IF NOT EXISTS ix_notes_updated_at ON notes(updated_at);
CREATE INDEX IF NOT EXISTS ix_notes_like_count ON notes(like_count);
CREATE INDEX IF NOT EXISTS ix_notes_paper_year ON notes(paper_year);
CREATE INDEX IF NOT EXISTS ix_notes_paper_doi ON notes(paper_doi);

-- 更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为 notes 表添加更新时间触发器
DROP TRIGGER IF EXISTS tr_notes_updated_at ON notes;
CREATE TRIGGER tr_notes_updated_at
    BEFORE UPDATE ON notes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE notes IS '笔记表 - 存储用户发布的学术笔记';
COMMENT ON COLUMN notes.id IS '主键ID';
COMMENT ON COLUMN notes.title IS '笔记标题';
COMMENT ON COLUMN notes.content IS '笔记内容';
COMMENT ON COLUMN notes.author_id IS '作者ID';
COMMENT ON COLUMN notes.paper_title IS '论文标题';
COMMENT ON COLUMN notes.paper_venue IS '发表期刊/会议';
COMMENT ON COLUMN notes.paper_year IS '发表年份';
COMMENT ON COLUMN notes.paper_doi IS 'DOI编号';
COMMENT ON COLUMN notes.paper_pmid IS 'PubMed ID';
COMMENT ON COLUMN notes.tags IS '标签列表';
COMMENT ON COLUMN notes.like_count IS '点赞数';
COMMENT ON COLUMN notes.favorite_count IS '收藏数';
COMMENT ON COLUMN notes.comment_count IS '评论数';
COMMENT ON COLUMN notes.created_at IS '创建时间';
COMMENT ON COLUMN notes.updated_at IS '更新时间';


-- =====================================================
-- 3. 点赞表 (likes)
-- =====================================================
CREATE TABLE IF NOT EXISTS likes (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    note_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一约束：每个用户对同一笔记只能点赞一次
    CONSTRAINT uq_likes_user_note UNIQUE (user_id, note_id),
    
    -- 外键约束
    CONSTRAINT fk_likes_user_id 
        FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_likes_note_id 
        FOREIGN KEY (note_id) 
        REFERENCES notes(id) 
        ON DELETE CASCADE
);

-- 点赞表索引
CREATE INDEX IF NOT EXISTS ix_likes_user_id ON likes(user_id);
CREATE INDEX IF NOT EXISTS ix_likes_note_id ON likes(note_id);
CREATE INDEX IF NOT EXISTS ix_likes_created_at ON likes(created_at);

COMMENT ON TABLE likes IS '点赞表 - 记录用户对笔记的点赞行为';
COMMENT ON COLUMN likes.id IS '主键ID';
COMMENT ON COLUMN likes.user_id IS '用户ID';
COMMENT ON COLUMN likes.note_id IS '笔记ID';
COMMENT ON COLUMN likes.created_at IS '点赞时间';


-- =====================================================
-- 4. 收藏表 (favorites)
-- =====================================================
CREATE TABLE IF NOT EXISTS favorites (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    note_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一约束：每个用户对同一笔记只能收藏一次
    CONSTRAINT uq_favorites_user_note UNIQUE (user_id, note_id),
    
    -- 外键约束
    CONSTRAINT fk_favorites_user_id 
        FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_favorites_note_id 
        FOREIGN KEY (note_id) 
        REFERENCES notes(id) 
        ON DELETE CASCADE
);

-- 收藏表索引
CREATE INDEX IF NOT EXISTS ix_favorites_user_id ON favorites(user_id);
CREATE INDEX IF NOT EXISTS ix_favorites_note_id ON favorites(note_id);
CREATE INDEX IF NOT EXISTS ix_favorites_created_at ON favorites(created_at);

COMMENT ON TABLE favorites IS '收藏表 - 记录用户收藏的笔记';
COMMENT ON COLUMN favorites.id IS '主键ID';
COMMENT ON COLUMN favorites.user_id IS '用户ID';
COMMENT ON COLUMN favorites.note_id IS '笔记ID';
COMMENT ON COLUMN favorites.created_at IS '收藏时间';


-- =====================================================
-- 5. 评论表 (comments)
-- =====================================================
CREATE TABLE IF NOT EXISTS comments (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    note_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    parent_id BIGINT,  -- 父评论ID，用于回复功能
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    CONSTRAINT fk_comments_user_id 
        FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_comments_note_id 
        FOREIGN KEY (note_id) 
        REFERENCES notes(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_comments_parent_id 
        FOREIGN KEY (parent_id) 
        REFERENCES comments(id) 
        ON DELETE CASCADE
);

-- 评论表索引
CREATE INDEX IF NOT EXISTS ix_comments_user_id ON comments(user_id);
CREATE INDEX IF NOT EXISTS ix_comments_note_id ON comments(note_id);
CREATE INDEX IF NOT EXISTS ix_comments_parent_id ON comments(parent_id);
CREATE INDEX IF NOT EXISTS ix_comments_created_at ON comments(created_at);

COMMENT ON TABLE comments IS '评论表 - 存储用户对笔记的评论，支持嵌套回复';
COMMENT ON COLUMN comments.id IS '主键ID';
COMMENT ON COLUMN comments.user_id IS '评论者ID';
COMMENT ON COLUMN comments.note_id IS '被评论笔记ID';
COMMENT ON COLUMN comments.content IS '评论内容';
COMMENT ON COLUMN comments.parent_id IS '父评论ID(用于回复)';
COMMENT ON COLUMN comments.created_at IS '评论时间';


-- =====================================================
-- 可选：创建视图方便查询
-- =====================================================

-- 用户统计视图
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.username,
    u.email,
    u.created_at,
    COUNT(DISTINCT n.id) AS note_count,
    COUNT(DISTINCT l.id) AS like_given_count,
    COUNT(DISTINCT f.id) AS favorite_count,
    COUNT(DISTINCT c.id) AS comment_count
FROM users u
LEFT JOIN notes n ON u.id = n.author_id
LEFT JOIN likes l ON u.id = l.user_id
LEFT JOIN favorites f ON u.id = f.user_id
LEFT JOIN comments c ON u.id = c.user_id
GROUP BY u.id, u.username, u.email, u.created_at;

COMMENT ON VIEW user_stats IS '用户统计视图 - 汇总用户的笔记、点赞、收藏和评论数量';
