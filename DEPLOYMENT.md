# InStoryBook 部署指南

## 部署架构

- **后端**: Railway（自动构建和部署）
- **前端**: Vercel（自动构建和部署）
- **Redis**: Upstash（托管 Redis 服务）

## 第一步：配置 Upstash Redis

1. 访问 https://upstash.com 并注册账号
2. 创建新的 Redis 数据库
3. 选择免费层（10K 请求/天）
4. 复制 Redis 连接 URL（格式：`redis://default:password@host:port`）
5. 保存此 URL，后续在 Railway 中配置

**注意**：如果使用 Upstash，连接 URL 格式可能是：
- `redis://default:password@host:port`（标准格式）
- 或者 Upstash 提供的 REST URL（需要转换为标准格式）

## 第二步：部署后端到 Railway

### 2.1 连接 GitHub 仓库

1. 登录 Railway: https://railway.app
2. 点击 "New Project"
3. 选择 "Deploy from GitHub repo"
4. 授权 Railway 访问你的 GitHub 仓库
5. 选择 `Instorybook` 仓库

### 2.2 配置服务

1. Railway 会自动检测到 `backend/Dockerfile`
2. 如果没有自动检测，手动设置：
   - Root Directory: `backend`
   - Build Command: （留空，使用 Dockerfile）
   - Start Command: （留空，使用 Dockerfile）

### 2.3 配置环境变量

在 Railway Dashboard 中，进入你的服务 → Settings → Variables，添加以下环境变量：

#### 必需的环境变量

```bash
# Redis 配置
REDIS_URL=redis://default:your_password@your_host:port

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

### 2.4 获取后端 URL

1. 部署完成后，Railway 会分配一个域名（如：`xxx.railway.app`）
2. 在服务设置中，可以查看生成的域名
3. 记录此 URL，格式：`https://xxx.railway.app`
4. API 地址：`https://xxx.railway.app/api/v1`
5. WebSocket 地址：`wss://xxx.railway.app/api/v1/ws`

## 第三步：部署前端到 Vercel

### 3.1 连接 GitHub 仓库

1. 访问 https://vercel.com 并登录
2. 点击 "Add New Project"
3. 导入你的 GitHub 仓库 `Instorybook`
4. 配置项目设置：
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm ci`

### 3.2 配置环境变量

在 Vercel 项目设置 → Environment Variables 中添加：

```bash
# 后端 API 地址（使用第二步获取的 Railway URL）
VITE_API_URL=https://xxx.railway.app/api/v1

# WebSocket 地址
VITE_WS_URL=wss://xxx.railway.app/api/v1/ws
```

### 3.3 部署

1. 点击 "Deploy"
2. 等待构建完成
3. Vercel 会分配一个域名（如：`xxx.vercel.app`）
4. 记录前端 URL

### 3.4 更新后端 CORS 配置

1. 回到 Railway Dashboard
2. 更新 `CORS_ORIGINS` 环境变量：
   ```
   https://xxx.vercel.app,http://localhost:5173
   ```
3. 重新部署后端服务（Railway 会自动检测环境变量变化）

## 第四步：测试部署

1. 访问前端 URL（Vercel 分配的域名）
2. 打开浏览器开发者工具 → Network 标签
3. 测试功能：
   - 输入故事主题
   - 检查 WebSocket 连接是否成功
   - 验证故事生成功能
   - 检查图片生成功能

## 常见问题

### 问题 1: Railway 构建失败

**解决方案**:
- 检查 `backend/Dockerfile` 是否存在
- 确认 `requirements.txt` 文件完整
- 查看 Railway 构建日志

### 问题 2: WebSocket 连接失败

**解决方案**:
- 确认使用 `wss://` 协议（生产环境）
- 检查后端 CORS 配置
- 确认 Railway 服务正在运行

### 问题 3: 前端无法连接后端

**解决方案**:
- 检查 `VITE_API_URL` 和 `VITE_WS_URL` 环境变量
- 确认后端 URL 正确
- 检查后端健康检查端点：`https://xxx.railway.app/health`

### 问题 4: Redis 连接失败

**解决方案**:
- 检查 `REDIS_URL` 格式是否正确
- 确认 Upstash Redis 实例正在运行
- 检查网络连接

## 部署检查清单

- [ ] Upstash Redis 实例创建并获取连接 URL
- [ ] Railway 账号创建并连接 GitHub
- [ ] 后端 Dockerfile 创建完成
- [ ] Railway 环境变量配置完成
- [ ] 后端部署成功并获取 URL
- [ ] Vercel 账号创建并连接 GitHub
- [ ] Vercel 环境变量配置完成
- [ ] 前端部署成功并获取 URL
- [ ] 更新后端 CORS 配置
- [ ] 端到端功能测试通过

## 下一步：自定义域名（可选）

1. 在 Namecheap 购买域名
2. 在 Cloudflare 配置 DNS
3. 在 Railway 中配置自定义域名
4. 在 Vercel 中配置自定义域名

## 监控和维护

### Railway 监控

- 在 Railway Dashboard 查看服务状态
- 查看日志和指标
- 设置告警（可选）

### Vercel 监控

- 在 Vercel Dashboard 查看部署状态
- 查看访问分析
- 设置性能监控

### Redis 监控

- 在 Upstash Dashboard 查看使用情况
- 监控请求数量（免费层限制：10K/天）

