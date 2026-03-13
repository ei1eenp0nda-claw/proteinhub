# ProteinHub 笔记系统 API 文档

对标小红书的蛋白质科研笔记平台 REST API

## 基础信息

- **Base URL**: `/api`
- **Content-Type**: `application/json`
- **认证**: Mock认证（目前user_id=1）

## 响应格式

所有API返回统一格式：

```json
{
  "success": true/false,
  "data": { ... },
  "message": "提示信息",
  "error": "错误信息"  // 仅在失败时返回
}
```

---

## 笔记相关 API

### 1. 获取笔记Feed流

```
GET /api/notes/feed
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| per_page | int | 否 | 每页数量，默认20，最大50 |

**响应示例：**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "title": "🔬 CIDEA蛋白最新研究进展",
        "preview": "今天读了篇关于CIDEA的Nature Communications...",
        "author": {
          "id": 1,
          "username": "科研达人",
          "avatar_url": null
        },
        "like_count": 448,
        "favorite_count": 111,
        "comment_count": 0,
        "tags": ["CIDE", "代谢", "脂滴", "文献解读"],
        "created_at": "2024-03-10T12:00:00"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 6,
      "pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

---

### 2. 获取笔记详情

```
GET /api/notes/<id>
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "🔬 CIDEA蛋白最新研究进展",
    "preview": "...",
    "content": "完整内容...",
    "author": { "id": 1, "username": "科研达人", "avatar_url": null },
    "like_count": 448,
    "favorite_count": 111,
    "comment_count": 1,
    "tags": ["CIDE", "代谢", "脂滴", "文献解读"],
    "paper_info": {
      "title": "The rhythmic coupling of Egr-1 and Cidea regulates...",
      "authors": [],
      "journal": "Nature Communications",
      "pub_date": "2023-03",
      "doi": null,
      "pmid": "36964140",
      "url": null
    },
    "media_urls": [],
    "is_liked": true,
    "is_favorited": true,
    "created_at": "2024-03-10T12:00:00",
    "updated_at": "2024-03-10T12:00:00"
  }
}
```

---

### 3. 获取相关笔记

```
GET /api/notes/<id>/related
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | int | 否 | 返回数量，默认10，最大20 |

**响应示例：**
```json
{
  "success": true,
  "data": [ /* 笔记列表 */ ],
  "count": 5
}
```

---

### 4. 创建笔记

```
POST /api/notes
```

**请求体：**
```json
{
  "title": "笔记标题",
  "content": "笔记内容",
  "paper_title": "论文标题",
  "paper_authors": ["Author A", "Author B"],
  "paper_journal": "期刊名",
  "paper_pub_date": "2024-01",
  "paper_pmid": "12345678",
  "media_urls": ["https://..."],
  "tags": ["标签1", "标签2"],
  "is_public": true
}
```

---

### 5. 更新笔记

```
PUT /api/notes/<id>
```

---

### 6. 删除笔记

```
DELETE /api/notes/<id>
```

---

## 互动相关 API

### 7. 点赞/取消点赞

```
POST /api/notes/<id>/like
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "is_liked": true,
    "like_count": 449
  },
  "message": "点赞成功"
}
```

---

### 8. 收藏/取消收藏

```
POST /api/notes/<id>/favorite
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "is_favorited": true,
    "favorite_count": 112
  },
  "message": "收藏成功"
}
```

---

### 9. 获取评论列表

```
GET /api/notes/<id>/comments
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| per_page | int | 否 | 每页数量，默认20 |
| sort | string | 否 | 排序方式：newest(最新)/hottest(最热) |

**响应示例：**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "content": "这是一条测试评论！",
        "author": {
          "id": 1,
          "username": "科研达人",
          "avatar_url": null
        },
        "like_count": 0,
        "parent_id": null,
        "created_at": "2024-03-13T03:54:00",
        "replies": [],
        "reply_count": 0
      }
    ],
    "pagination": { ... }
  }
}
```

---

### 10. 发表评论

```
POST /api/notes/<id>/comments
```

**请求体：**
```json
{
  "content": "评论内容",
  "parent_id": null  // 可选，回复某条评论
}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "content": "这是一条测试评论！",
    "author": {
      "id": 1,
      "username": "科研达人",
      "avatar_url": null
    },
    "like_count": 0,
    "parent_id": null,
    "created_at": "2024-03-13T03:54:00"
  },
  "message": "评论发布成功"
}
```

---

### 11. 删除评论

```
DELETE /api/comments/<id>
```

---

## Tag相关 API

### 12. 获取热门标签

```
GET /api/tags
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | int | 否 | 返回数量，默认50，最大100 |
| sort | string | 否 | 排序：hot(热门)/name(名称) |

**响应示例：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "CIDE",
      "description": "CIDE家族蛋白",
      "usage_count": 3
    }
  ],
  "count": 8
}
```

---

### 13. 获取标签下的笔记

```
GET /api/tags/<tag>/notes
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| per_page | int | 否 | 每页数量，默认20 |

**响应示例：**
```json
{
  "success": true,
  "data": {
    "tag": {
      "id": 1,
      "name": "CIDE",
      "description": "CIDE家族蛋白",
      "usage_count": 3
    },
    "items": [ /* 笔记列表 */ ],
    "pagination": { ... }
  }
}
```

---

## 用户相关 API

### 14. 获取用户的笔记列表

```
GET /api/users/<user_id>/notes
```

---

### 15. 获取用户的收藏列表

```
GET /api/users/<user_id>/favorites
```

---

### 16. 获取用户的点赞列表

```
GET /api/users/<user_id>/likes
```

---

## 数据模型

### Note (笔记)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 笔记ID |
| title | string | 标题 |
| content | text | 完整内容 |
| preview | text | 预览文本 |
| author | object | 作者信息 |
| like_count | int | 点赞数 |
| favorite_count | int | 收藏数 |
| comment_count | int | 评论数 |
| view_count | int | 浏览数 |
| tags | array | 标签列表 |
| paper_info | object | 关联论文信息 |
| is_liked | bool | 当前用户是否点赞 |
| is_favorited | bool | 当前用户是否收藏 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

### Tag (标签)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 标签ID |
| name | string | 标签名 |
| description | string | 描述 |
| usage_count | int | 使用次数 |

### Comment (评论)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 评论ID |
| content | string | 内容 |
| author | object | 作者信息 |
| like_count | int | 点赞数 |
| parent_id | int | 父评论ID（回复） |
| replies | array | 回复列表 |
| reply_count | int | 回复数 |
| created_at | string | 创建时间 |

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（需要登录） |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
