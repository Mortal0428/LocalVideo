# -------------------------------------------------------------
# 阶段 1: 构建阶段 (Node.js 编译)
# -------------------------------------------------------------
FROM node:20-alpine AS build-stage

WORKDIR /app

# 利用 Docker 缓存层加速依赖构建
COPY package.json package-lock.json ./
RUN npm install --registry=https://registry.npmmirror.com

# 拷贝前端全部源码并执行生产打包
COPY . .
RUN npm run build

# -------------------------------------------------------------
# 阶段 2: 生产运行阶段 (Nginx 静态托管)
# -------------------------------------------------------------
FROM nginx:1.25-alpine AS production-stage

# 拷贝静态资源与自定义 Nginx 配置文件
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
