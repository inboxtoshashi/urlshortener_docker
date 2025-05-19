FROM nginx:alpine

# Remove default files
RUN rm -rf /usr/share/nginx/html/*

COPY ./static /usr/share/nginx/html/static
COPY ./templates /usr/share/nginx/html/templates
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80