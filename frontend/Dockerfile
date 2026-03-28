FROM nginx:1.25-alpine

# Copiar archivos estáticos del frontend
COPY src/ /usr/share/nginx/html/

# Configuración de Nginx para servir archivos estáticos
RUN echo 'server { \
    listen 3000; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate"; \
    add_header Pragma "no-cache"; \
    add_header Expires "0"; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
