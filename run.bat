:: init network turbo
@set http_proxy=http://127.0.0.1:52539
@set https_proxy=http://127.0.0.1:52539

:: init huggingface
@set HF_HOME=D:\PycharmProjects\Qwen-VL_API\huggingface_cache
:: @set TRANSFORMERS_OFFLINE=1

:: run OpenAI API server
@set WORK_DIR=D:\PycharmProjects\Qwen-VL_API

@cd %WORK_DIR%
@call %WORK_DIR%\venv\Scripts\activate.bat
uvicorn main:app --host 0.0.0.0 --port 6006 --reload

:: @call %WORK_DIR%\venv\Scripts\python.exe %WORK_DIR%\main.py --server-port 6006 --server-name '0.0.0.0'