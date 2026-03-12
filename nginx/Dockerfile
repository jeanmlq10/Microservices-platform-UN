FROM nginx:1.25-alpine

# Eliminar config por defecto
RUN rm /etc/nginx/conf.d/default.conf

# Copiar configuración personalizada
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf

# Crear directorio para configs dinámicas de microservicios
RUN mkdir -p /etc/nginx/dynamic

# Exponer puerto 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
