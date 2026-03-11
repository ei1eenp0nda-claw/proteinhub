-- ProteinHub 数据库 Schema
-- PostgreSQL

-- 蛋白表
CREATE TABLE proteins (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,  -- 蛋白名称，如 PLIN2
    family VARCHAR(50),                -- 家族，如 PLIN, CIDE
    uniprot_id VARCHAR(20),            -- UniProt ID
    description TEXT,                  -- 功能描述
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 蛋白互作表（15万对数据）
CREATE TABLE protein_interactions (
    id SERIAL PRIMARY KEY,
    protein_a_id INTEGER REFERENCES proteins(id),
    protein_b_id INTEGER REFERENCES proteins(id),
    interaction_score FLOAT,           -- Rosetta PPI 预测得分
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(protein_a_id, protein_b_id)
);

-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    research_area VARCHAR(200),        -- 研究方向
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 帖子表（文献解读）
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    protein_id INTEGER REFERENCES proteins(id),
    title VARCHAR(500) NOT NULL,       -- 标题党标题
    summary TEXT,                      -- AI生成的摘要
    source_url VARCHAR(500),           -- PubMed原文链接
    source_title VARCHAR(500),         -- 原文标题
    author_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户关注蛋白表
CREATE TABLE user_protein_follows (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    protein_id INTEGER REFERENCES proteins(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, protein_id)
);

-- 用户行为表（点赞、收藏）
CREATE TABLE user_actions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    post_id INTEGER REFERENCES posts(id),
    action_type VARCHAR(20) CHECK (action_type IN ('click', 'save', 'share')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_proteins_family ON proteins(family);
CREATE INDEX idx_interactions_score ON protein_interactions(interaction_score DESC);
CREATE INDEX idx_posts_protein ON posts(protein_id);
CREATE INDEX idx_actions_user ON user_actions(user_id);
