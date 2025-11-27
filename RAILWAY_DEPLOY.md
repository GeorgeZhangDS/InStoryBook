# Railway 快速部署指南

## 第一步：连接 GitHub 仓库

1. 登录 Railway: https://railway.app
2. 点击 "New Project"
3. 选择 "Deploy from GitHub repo"
4. 授权 Railway 访问你的 GitHub 仓库
5. 选择 `Instorybook` 仓库

## 第二步：配置服务

Railway 会自动检测到 `backend/Dockerfile`，如果没有：

1. 进入项目设置
2. 设置 Root Directory: `backend`
3. 确保使用 Dockerfile 构建

## 第三步：配置环境变量

在 Railway Dashboard → 你的服务 → Variables，添加以下环境变量：

### 必需的环境变量

```bash
# Redis 配置（从 Upstash 获取）
REDIS_URL=redis://default:password@host:port

# AWS / Nova 配置
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_KEY=your_aws_secret_key
AWS_REGION=us-east-1
NOVA_MODEL=us.amazon.nova-lite-v1:0

# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# Runware 配置
RUNWARE_API_KEY=your_runware_api_key
RUNWARE_IMAGE_MODEL=runware:101@1
RUNWARE_API_BASE_URL=https://api.runware.ai/v1

# AI 提供商配置
AI_PROVIDER=nova
AI_FALLBACK_PROVIDER=openai

# CORS 配置（先使用占位符，前端部署后更新）
CORS_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:5173

# 调试模式
DEBUG=false
```

## 第四步：获取后端 URL

1. 部署完成后，Railway 会分配一个域名
2. 在服务设置中查看生成的域名
3. 记录此 URL，格式：`https://xxx.railway.app`
4. API 地址：`https://xxx.railway.app/api/v1`
5. WebSocket 地址：`wss://xxx.railway.app/api/v1/ws`

## 第五步：测试后端

访问健康检查端点：
```
https://xxx.railway.app/health
```

应该返回：
```json
{
  "status": "healthy",
  "service": "InStoryBook"
}
```

## 常见问题

### 构建失败

- 检查 `backend/Dockerfile` 是否存在
- 确认 `requirements.txt` 文件完整
- 查看 Railway 构建日志

### 服务无法启动

- 检查环境变量是否全部配置
- 确认 Redis URL 格式正确
- 查看 Railway 日志

### WebSocket 连接失败

- 确认使用 `wss://` 协议（生产环境）
- 检查 CORS 配置
- 确认服务正在运行

