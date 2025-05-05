FROM mysql:5.7

ENV MYSQL_ROOT_PASSWORD=root
ENV MYSQL_DATABASE=urlshortener
ENV MYSQL_USER=appuser
ENV MYSQL_PASSWORD=appsecret

COPY init.sql /docker-entrypoint-initdb.d/


