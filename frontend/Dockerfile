FROM node:18-alpine

# 设置 npm 国内镜像源
RUN npm config set registry https://registry.npmmirror.com

WORKDIR /app

COPY package*.json ./

# 使用国内镜像源安装依赖
RUN npm install --registry https://registry.npmmirror.com

COPY . .

# 构建
RUN npm run build

# Nginx
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
