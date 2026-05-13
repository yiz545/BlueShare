#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 正在啟動 BlueShare 音訊共享工具..."
echo "-----------------------------------"

# 檢查並安裝套件
python3 -m pip install pyobjc-framework-CoreAudio pyobjc-framework-Cocoa --quiet

# 執行程式
python3 blueshare.py

echo "-----------------------------------"
echo "程式執行完畢，按任意鍵關閉視窗。"
read -n 1
