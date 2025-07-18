# 多模态智能数据分析平台 - API文档

## 概述

本文档描述了多模态智能数据分析平台的完整API接口，支持文本、图像、音频、视频等多种数据类型的智能分析。

## 基础信息

- **Base URL**: `http://localhost:8008/api/v1`
- **认证方式**: Bearer Token
- **响应格式**: JSON
- **支持的HTTP方法**: GET, POST, PUT, DELETE

## 认证相关

### 用户登录
```http
POST /auth/login
```

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "is_active": true
  }
}
```

### 用户注册
```http
POST /auth/register
```

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

## 项目管理

### 获取项目列表
```http
GET /projects
Authorization: Bearer {token}
```

**响应**:
```json
{
  "projects": [
    {
      "id": 1,
      "name": "项目名称",
      "description": "项目描述",
      "created_at": "2025-07-18T10:30:00Z",
      "updated_at": "2025-07-18T10:30:00Z",
      "user_id": 1
    }
  ]
}
```

### 创建项目
```http
POST /projects
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "name": "新项目名称",
  "description": "项目描述（可选）"
}
```

### 获取项目详情
```http
GET /projects/{project_id}
Authorization: Bearer {token}
```

### 更新项目
```http
PUT /projects/{project_id}
Authorization: Bearer {token}
```

### 删除项目
```http
DELETE /projects/{project_id}
Authorization: Bearer {token}
```

## 数据源管理

### 文件上传
```http
POST /data_sources/upload?project_id={project_id}
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

**请求体**:
```
file: <文件内容>
```

**支持的文件格式**:
- **文本**: .txt, .md, .pdf, .docx, .csv, .xlsx, .json
- **图像**: .jpg, .jpeg, .png, .gif
- **音频**: .mp3, .wav, .m4a, .flac
- **视频**: .mp4, .avi, .mov, .mkv, .wmv, .flv, .webm, .m4v, .3gp

**响应**:
```json
{
  "id": 123,
  "name": "example.mp4",
  "file_type": "mp4",
  "analysis_category": "VIDEO",
  "file_size": 52428800,
  "profile_status": "pending",
  "created_at": "2025-07-18T10:30:00Z",
  "project_id": 1
}
```

### 获取数据源列表
```http
GET /data_sources?project_id={project_id}
Authorization: Bearer {token}
```

### 获取数据源详情
```http
GET /data_sources/{data_source_id}?project_id={project_id}
Authorization: Bearer {token}
```

**响应示例（视频文件）**:
```json
{
  "id": 123,
  "name": "example.mp4",
  "file_type": "mp4",
  "analysis_category": "VIDEO",
  "profile_status": "completed",
  "profiling_result": {
    "analysis_type": "video_enhanced",
    "enhanced_metadata": {
      "width": 1920,
      "height": 1080,
      "fps": 30.0,
      "duration": 134.07,
      "nb_frames": 4022,
      "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
      "bit_rate": 8500000,
      "video_codec": "h264",
      "audio_codec": "aac",
      "has_audio": true
    },
    "primary_thumbnail": "/uploads/1/thumbnails/example_thumbnail.jpg",
    "thumbnails": [
      "/uploads/1/thumbnails/example_start.jpg",
      "/uploads/1/thumbnails/example_middle.jpg",
      "/uploads/1/thumbnails/example_end.jpg"
    ],
    "content_analysis": {
      "brightness_analysis": {
        "average": 128.5,
        "category": "正常亮度"
      },
      "contrast_analysis": {
        "average": 45.2,
        "category": "良好对比度"
      },
      "visual_stability": {
        "brightness_stability": "稳定"
      },
      "analyzed_frames": 120
    }
  }
}
```

### 触发数据分析
```http
POST /data_sources/{data_source_id}/analyze?project_id={project_id}
Authorization: Bearer {token}
```

**响应**:
```json
{
  "task_id": "abc123-def456-ghi789",
  "message": "分析任务已启动",
  "status": "in_progress"
}
```

### 删除数据源
```http
DELETE /data_sources/{data_source_id}?project_id={project_id}
Authorization: Bearer {token}
```

## 视频分析专用API

### 视频深度分析
```http
POST /video-analysis/{data_source_id}/analyze
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "analysis_type": "comprehensive",
  "options": {
    "extract_audio": true,
    "scene_detection": true,
    "visual_analysis": true,
    "multimodal_fusion": true
  }
}
```

**响应**:
```json
{
  "analysis_id": "video_analysis_123",
  "status": "in_progress",
  "estimated_duration": 300,
  "message": "视频深度分析已启动"
}
```

### 获取视频分析状态
```http
GET /video-analysis/{analysis_id}/status
Authorization: Bearer {token}
```

**响应**:
```json
{
  "analysis_id": "video_analysis_123",
  "status": "completed",
  "progress": 100,
  "current_phase": "multimodal_fusion",
  "estimated_remaining": 0,
  "phases": {
    "frame_extraction": "completed",
    "visual_analysis": "completed", 
    "audio_analysis": "completed",
    "multimodal_fusion": "completed"
  }
}
```

### 获取视频分析报告
```http
GET /video-analysis/{analysis_id}/report
Authorization: Bearer {token}
```

**响应**:
```json
{
  "analysis_id": "video_analysis_123",
  "data_source_id": 123,
  "analysis_type": "comprehensive",
  "created_at": "2025-07-18T10:30:00Z",
  "completed_at": "2025-07-18T10:35:00Z",
  "results": {
    "visual_analysis": {
      "scene_count": 8,
      "key_frames": [
        {
          "timestamp": 0.0,
          "frame_path": "/uploads/1/frames/frame_000001.jpg",
          "description": "视频开始场景",
          "objects": ["person", "building", "car"],
          "confidence": 0.95
        }
      ],
      "visual_themes": ["城市", "人物", "交通"],
      "dominant_colors": ["#1a1a1a", "#ffffff", "#ff0000"]
    },
    "audio_analysis": {
      "transcript": "这是视频的语音转录内容...",
      "topics": ["技术", "教育", "演示"],
      "sentiment": {
        "overall": "positive",
        "confidence": 0.85
      },
      "timeline": [
        {
          "start": 0.0,
          "end": 5.2,
          "text": "欢迎观看本次演示",
          "confidence": 0.98
        }
      ]
    },
    "multimodal_analysis": {
      "story_structure": [
        {
          "segment": "introduction",
          "start": 0.0,
          "end": 30.0,
          "description": "视频介绍部分"
        }
      ],
      "key_moments": [
        {
          "timestamp": 45.5,
          "description": "重要转折点",
          "visual_cue": "场景切换",
          "audio_cue": "音调变化"
        }
      ],
      "emotion_timeline": [
        {
          "timestamp": 0.0,
          "emotion": "neutral",
          "confidence": 0.8
        }
      ]
    }
  }
}
```

## 语义搜索

### 项目内搜索
```http
POST /projects/{project_id}/search
Authorization: Bearer {token}
```

**请求体**:
```json
{
  "query": "搜索查询文本",
  "limit": 10,
  "threshold": 0.7
}
```

**响应**:
```json
[
  {
    "data_source_id": 123,
    "text": "匹配的文本内容",
    "score": 0.95,
    "metadata": {
      "file_name": "example.txt",
      "file_type": "text"
    }
  }
]
```

### 相似图像搜索
```http
GET /data_sources/{data_source_id}/similar?project_id={project_id}&threshold={threshold}
Authorization: Bearer {token}
```

**响应**:
```json
[
  {
    "id": 456,
    "name": "similar_image.jpg",
    "similarity_score": 0.92,
    "file_path": "/uploads/1/similar_image.jpg"
  }
]
```

## 任务管理

### 获取任务状态
```http
GET /tasks/{task_id}/status
Authorization: Bearer {token}
```

**响应**:
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "completed",
  "progress": 100,
  "result": {
    "status": "success",
    "message": "分析完成"
  },
  "created_at": "2025-07-18T10:30:00Z",
  "completed_at": "2025-07-18T10:32:00Z"
}
```

## 错误处理

### 错误响应格式
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "field": "email",
      "message": "邮箱格式不正确"
    }
  }
}
```

### 常见错误代码

| 状态码 | 错误代码 | 描述 |
|--------|----------|------|
| 400 | VALIDATION_ERROR | 请求参数验证失败 |
| 401 | UNAUTHORIZED | 未认证或token无效 |
| 403 | FORBIDDEN | 权限不足 |
| 404 | NOT_FOUND | 资源不存在 |
| 413 | FILE_TOO_LARGE | 文件大小超出限制 |
| 415 | UNSUPPORTED_MEDIA_TYPE | 不支持的文件格式 |
| 422 | PROCESSING_ERROR | 文件处理失败 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

## 限制和配额

- **文件大小限制**: 2GB
- **并发上传**: 每用户最多5个并发上传
- **API请求频率**: 每分钟1000次
- **分析任务**: 每用户最多10个并发分析任务

## SDK和示例

### JavaScript/Node.js 示例

```javascript
// 文件上传示例
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('/api/v1/data_sources/upload?project_id=1', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const result = await response.json();
console.log('上传结果:', result);

// 视频分析示例
const analysisResponse = await fetch(`/api/v1/video-analysis/${dataSourceId}/analyze`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    analysis_type: 'comprehensive',
    options: {
      extract_audio: true,
      scene_detection: true,
      visual_analysis: true,
      multimodal_fusion: true
    }
  })
});

const analysisResult = await analysisResponse.json();
console.log('分析任务ID:', analysisResult.analysis_id);
```

### Python 示例

```python
import requests

# 登录
login_data = {
    "email": "user@example.com",
    "password": "password123"
}
response = requests.post("http://localhost:8008/api/v1/auth/login", json=login_data)
token = response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# 文件上传
with open("video.mp4", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:8008/api/v1/data_sources/upload?project_id=1",
        headers=headers,
        files=files
    )
    upload_result = response.json()
    print("上传结果:", upload_result)

# 触发视频分析
analysis_data = {
    "analysis_type": "comprehensive",
    "options": {
        "extract_audio": True,
        "scene_detection": True,
        "visual_analysis": True,
        "multimodal_fusion": True
    }
}
response = requests.post(
    f"http://localhost:8008/api/v1/video-analysis/{upload_result['id']}/analyze",
    headers=headers,
    json=analysis_data
)
analysis_result = response.json()
print("分析任务ID:", analysis_result["analysis_id"])
```

## 版本信息

- **API版本**: v1
- **文档版本**: 1.0.0
- **最后更新**: 2025-07-18
- **支持的功能**: 文本分析、图像分析、音频分析、视频深度分析、语义搜索

---

*如有问题或建议，请联系开发团队或查看项目GitHub仓库。* 