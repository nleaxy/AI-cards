@echo off
echo Starting MinIO Server...
echo Access Console at: http://127.0.0.1:9001
echo User: minioadmin
echo Pass: minioadmin
echo.
.\minio\minio.exe server .\minio_data --console-address ":9001"
