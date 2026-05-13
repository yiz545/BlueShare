#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 正在啟動 BlueShare 音訊共享工具..."
echo "-----------------------------------"

# 執行程式（本工具透過動態編譯 Swift 呼叫 Core Audio，無需安裝 pyobjc）
python3 blueshare.py

echo "-----------------------------------"
echo "程式執行完畢，按任意鍵關閉視窗。"
read -n 1
