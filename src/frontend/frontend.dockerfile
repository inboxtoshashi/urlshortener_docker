FROM nginx:alpine

# Remove default files
RUN rm -rf /usr/share/nginx/html/*

# Copy application files
COPY ./static /usr/share/nginx/html/static
COPY ./templates /usr/share/nginx/html/templates
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]