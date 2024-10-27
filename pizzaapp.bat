@ECHO off
start /min daphne -b 0.0.0.0 -p 8000 pizza_manage.asgi:application