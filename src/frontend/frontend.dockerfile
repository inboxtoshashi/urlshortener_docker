FROM nginx:alpine

# Remove default files
RUN rm -rf /usr/share/nginx/html/*

COPY static/ /usr/share/nginx/html/static/
COPY templates/index.html /usr/share/nginx/html/index.html

EXPOSE 80
