FROM nginxinc/nginx-unprivileged:1.31-alpine

# nginx-unprivileged listens on 8080 and runs as a non-root user, which is also what
# OpenShift requires (it assigns an arbitrary UID in group 0).
ENV BACKEND_URL=http://backend:8000 \
    PLATFORM_ENVIRONMENT=Local

COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY nginx/config.js.template /etc/nginx/config.js.template
COPY --chmod=755 docker-entrypoint.d/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh
COPY public /usr/share/nginx/html

EXPOSE 8080
