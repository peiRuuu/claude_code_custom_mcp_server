# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 這是什麼

HiSKIO Claude Code 課程的作業：一個用 Python MCP SDK 2.x（`mcp.server.mcpserver.MCPServer`）寫的 stdio MCP server，提供三個圖片工具：`fetch_toy_image`（DuckDuckGo 搜圖下載）、`resize_image`（Pillow）、`remove_background_as_png`（rembg）。全部程式碼都在 `server.py`。

## 架構重點

- mcp 2.x 把 1.x 的 `FastMCP` 改名為 `MCPServer`；課程原始碼是 1.x 寫法，`requirements.txt` 的 `mcp>=1.0.0` 會裝到 2.x，所以 import 已改成 2.x。
- 工具用 `@mcp.tool()` 裝飾 async 函式註冊；工具的 schema 由函式簽名與型別標註自動產生，description 取自 docstring。新增工具＝在 `server.py` 加一個帶 `@mcp.tool()` 的函式。
- README「Adding New Tools」寫的 `handle_list_tools()` / `handle_call_tool()` 是舊的低階 Server API 寫法，**和目前程式碼不符**，以 `server.py` 為準。README 提到的 `--log-level DEBUG` / `LOG_LEVEL` 程式碼也沒有實作（logging 寫死 INFO）。
- 工具回傳字串；錯誤以 `"Error: ..."` 字串回傳而不是丟例外。
- 檔案路徑是 server 端的路徑：Docker 執行時只有掛載的 `/app/images`、`/app/input`、`/app/output` 對應到主機的 `images/`、`input/`、`output/`。
- stdio 傳輸：stdout 是 MCP 協定通道，不要在 server 裡 `print()` 到 stdout（用 `logger`）。

## 常用指令

```bash
# 本機跑（需 Python 3.11+）
pip install -r requirements.txt
python server.py

# Docker（.mcp.json 用的是這個 image 名稱）
docker build -t mcp-toy-image-tools-server .
```

改了 `server.py` 之後要重建 image 才會生效：用專案指令 `/rebuild_restart_image_tools_server`（檢查 docker → `docker build` → 提醒到 `/mcp` 重連 `image-tools-server-docker`）。

沒有測試或 lint 設定。

## 已知的環境問題

- `.mcp.json` 的掛載路徑寫死成這台 Windows 的絕對路徑（原本講師版用 `${PWD}` 和 Mac 的 `cwd`，在 Windows 上連不上）；換電腦或搬資料夾要跟著改。
- server 啟動約 66 秒：`import rembg` 時 pymatting 每次都用 numba 重新編譯（約 60 秒），超過 Claude Code 預設 30 秒的 MCP 連線 timeout。所以 `.claude/settings.local.json` 設了 `MCP_TIMEOUT=120000`。
- 第一次去背會下載 rembg 模型（約 100MB+），會比較久。
