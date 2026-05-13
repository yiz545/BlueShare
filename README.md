<div align="center">

# 🎧 BlueShare

**Mac 雙耳機音訊共享 · 雙人對講 · 即時錄音**

把同一份聲音同時送到兩支不同品牌的藍牙耳機，並讓兩人透過內建麥克風即時對話、全程錄音。

![macOS](https://img.shields.io/badge/macOS-12%2B-blue?logo=apple&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8%2B-yellow?logo=python&logoColor=white)
![Swift](https://img.shields.io/badge/Swift-5-orange?logo=swift&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## 📖 為什麼有這個專案

當你跟朋友想用兩支不同品牌的藍牙耳機一起聽音樂、看影片，會撞到三件事：

1. macOS 內建「多重輸出裝置」設定繁瑣，且系統音量鍵會失效
2. 跨品牌耳機（如 AirPods + Sony）容易延遲、聲音不同步
3. 想邊聽邊聊天，卻沒有現成的「對講機」模式

**BlueShare** 一次解決，並提供兩種使用方式：

| 版本 | 檔案 | 適用情境 |
|------|------|---------|
| 🖥️ macOS 原生版 | [`blueshare.py`](blueshare.py) | 系統級整合、低延遲對講、長時間錄音 |
| 🌐 Web 版 | [`index.html`](index.html) | 跨平台、無需安裝、即開即用 |

---

## 📸 介面預覽

<!-- TODO: 補上實際截圖 -->

**Web 版 UI**

> _截圖位置（請執行 `open index.html` 後截圖，命名為 `docs/web-ui.png` 並取消下行註解）_

<!-- ![Web UI](docs/web-ui.png) -->

**macOS 原生版控制台**

> _截圖位置（執行 `./Start_BlueShare.command` 後截圖，命名為 `docs/cli-ui.png`）_

<!-- ![CLI UI](docs/cli-ui.png) -->

---

## ✨ 功能

### 🎯 共通核心
- 同時播放音訊到兩支不同藍牙耳機（**支援跨品牌混搭**）
- 雙人對講：兩支耳機的麥克風即時互聽
- 即時錄音（音樂 + 對話混音）
- 每支耳機**獨立音量**控制
- 每支耳機麥克風**獨立靜音**
- 全部靜音總開關

### 🖥️ macOS 原生版獨家
- 系統級 Aggregate Device — 所有 App（Spotify、Zoom、YouTube…）都自動受惠
- 高品質 `.caf` 格式錄音
- 漂移補償 (Drift Compensation) 跨品牌耳機自動同步
- 終端機快捷鍵控制（無需切換視窗）

### 🌐 Web 版獨家
- 淺色系毛玻璃 UI
- 即時雙麥克風音量表（視覺化）
- 音量可調至 **150%**（軟體增益）
- 內建錄音播放器與下載清單
- 零安裝，全程於本機處理（不上傳任何音訊）

---

## 🚀 快速開始

### 方式一：macOS 原生版

```bash
# 1. 先確認兩支藍牙耳機都已配對並連線
# 2. 雙擊執行
./Start_BlueShare.command

# 或直接從終端執行
python3 blueshare.py
```

**控制鍵**：

| 鍵位 | 動作 |
|------|------|
| `1` / `2` | 第一副耳機 音量－ / ＋ |
| `3` / `4` | 第二副耳機 音量－ / ＋ |
| `5` / `6` | 第一 / 第二副耳機 麥克風獨立開關 |
| `M` | 全部靜音切換（總開關） |
| `Q` | 結束並儲存錄音 |

錄音自動儲存於 `~/Desktop/BlueShare_錄音檔/錄音_YYYYMMDD_HHMMSS.caf`

### 方式二：Web 版

```bash
# 直接以瀏覽器開啟（建議 Chrome / Edge / Opera）
open index.html
```

或啟動本地伺服器（部分瀏覽器需 HTTPS / localhost 才允許麥克風授權）：

```bash
python3 -m http.server 8000
# 瀏覽器開啟 http://localhost:8000
```

**四步流程**：
1. 點「🔓 授權並掃描裝置」（瀏覽器規範，僅一次）
2. 選一至兩支麥克風（對講用）
3. 選兩支耳機（A 與 B），可獨立調音量
4. 按「▶️ 開始共享」

**快捷鍵**：`Space` 開始/停止 · `M` 全部靜音 · `R` 開始/停止錄音

---

## 🛠 技術原理

### macOS 原生版

- **核心**：Core Audio 的 `AudioHardwareCreateAggregateDevice` 建立堆疊式 (`kAudioAggregateDeviceIsStackedKey`) 多重輸出
- **同步**：每個 sub-device 開啟 `kAudioSubDeviceDriftCompensationKey` 防止時鐘漂移
- **混音**：`AVAudioEngine` 把 `inputNode` 連到 `mainMixerNode` 達成即時對講
- **錄音**：在 mixer 上 `installTap` 取出音訊緩衝，寫入 `AVAudioFile`
- **快捷鍵**：Python 攔截單鍵（`tty.setraw`）→ stdin 傳指令給 Swift 子行程

### Web 版

- **多裝置輸出**：兩個 `MediaStreamAudioDestinationNode` + 兩個 `<audio>` 元素，各自呼叫 `setSinkId(deviceId)`
- **混音**：所有來源（mic 1、mic 2、檔案）→ master `GainNode` → 分接給兩個輸出
- **錄音**：另一個 destination 接 `MediaRecorder`，輸出 WebM Opus
- **音量表**：`AnalyserNode` + `requestAnimationFrame` 即時頻譜平均值

**Web 版完整訊號路由**：

```
mic1 ─→ micGain1 ─┐                ┌─→ outGainA → destA → <audio sinkId=A>
mic2 ─→ micGain2 ─┼─→ masterGain ──┼─→ outGainB → destB → <audio sinkId=B>
file ─→ fileGain ─┘                └─→ recDest  → MediaRecorder
```

---

## ⚠️ 已知限制

- **🎙️ 藍牙麥克風物理限制**：同時啟用多支耳機的麥克風時，macOS 會強制切換到 HFP (Hands-Free Profile) 通話模式，音質會降為單聲道低位元率。**這是藍牙硬體層級限制，無法用軟體破解**。若只需共享聽音樂，請不要開麥克風。
- **🌐 Web 版瀏覽器**：`setSinkId()` 僅支援 Chromium 系（Chrome / Edge / Opera）。Safari / Firefox 會自動回退到系統預設裝置（網頁會顯示警告）。
- **🔓 首次需授權**：Web 版按瀏覽器規範，要先取得麥克風權限才能讀取真實裝置名稱。
- **⏱️ 跨品牌延遲**：雖有漂移補償，極端情況（例如同時混用很舊與很新的型號）仍可能有微小不同步。

---

## 📁 專案結構

```
BlueShare/
├── README.md                       # 本檔案
├── blueshare.py                    # macOS 原生版主程式（Python 外殼 + 內嵌 Swift）
├── Start_BlueShare.command         # macOS 一鍵啟動腳本
├── index.html                      # Web 版單檔應用（含所有 CSS/JS）
│
├── dev/                            # 開發歷程探路腳本（不參與運行）
│   ├── README.md
│   ├── get_list.swift              # 探索：列出音訊裝置
│   ├── test_vol.swift              # 探索：音量讀寫測試
│   ├── test_mute.swift             # 探索：麥克風靜音屬性
│   └── temp_pro.swift              # 早期 Pro 版草稿
│
├── Sharing Audio Across Bluetooth Devices.md   # 完整開發脈絡記錄
└── Managing Multi-Headphone Audio Settings.md  # 音量／麥克風功能討論記錄
```

> 💡 **執行檔只有兩個**：`blueshare.py`（macOS 原生版）與 `index.html`（Web 版）。所有 Swift 程式碼皆以字串內嵌於 `blueshare.py`，執行時動態產生 `temp_ultimate.swift` 並於結束時刪除。`dev/` 內的獨立 `.swift` 檔僅供學習與獨立測試。

---

## 🧪 開發歷程

兩份 `.md` 對話記錄完整保留了專案從零開始的迭代過程：

1. **方案調研** — 比較 macOS 內建 MIDI 設定、PairPods、macos-audio-devices CLI
2. **核心實作** — Swift 直接呼叫 Core Audio 建立 Aggregate Device
3. **Python 包裝** — 避免 `pyobjc` 安裝問題，改為 Python 外殼 + 動態編譯 Swift
4. **跨品牌支援** — 加入 drift compensation 與 master clock
5. **對講功能** — 用 `AVAudioEngine` 接通 inputNode 到 mixer
6. **錄音功能** — `installTap` + 桌面自動建立資料夾
7. **獨立控制** — 加入逐耳機音量／麥克風快捷鍵
8. **Web 版** — Web Audio API + `setSinkId()` 重新實作所有功能

---

## 📜 授權

MIT License

---

## 🤝 貢獻

歡迎開 Issue 或 PR：

- 加入 Windows 版（Web 版理論上可用，待測）
- 多軌錄音（每支耳機獨立軌道）
- 支援藍牙喇叭混合輸出
- 加入錄音檔即時上傳雲端的選項
- i18n（多國語系）

---

<div align="center">
Made with ☕ on macOS · Built for sharing moments together
</div>
