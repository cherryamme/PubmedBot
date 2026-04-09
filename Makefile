VENV = backend/.venv/bin
export PYTHONPATH := $(shell pwd)

# 安装所有依赖
install:
	python3 -m venv backend/.venv
	$(VENV)/pip install -r backend/requirements.txt
	cd frontend && npm install

# 启动后端开发服务器
backend:
	$(VENV)/uvicorn backend.app.main:app --reload --port 8894

# 启动前端开发服务器
frontend:
	cd frontend && npm run dev -- --port 8893 --host

# 同时启动前后端 (需要两个终端)
dev:
	@echo "请在两个终端分别运行:"
	@echo "  make backend"
	@echo "  make frontend"

# 构建前端生产版本
build:
	cd frontend && npm run build

# 生产模式启动 (前端已构建)
serve:
	$(VENV)/uvicorn backend.app.main:app --host 0.0.0.0 --port 8894

.PHONY: install backend frontend dev build serve
