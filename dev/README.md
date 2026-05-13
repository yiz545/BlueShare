# dev/ — 開發歷程資料

⚠️ **這個資料夾的檔案不參與運行時行為**。BlueShare 主程式 (`blueshare.py`) 將所有 Swift 程式碼以字串 `SWIFT_CODE` 內嵌，執行時動態寫入 `temp_ultimate.swift` 並編譯。本資料夾僅作為**開發歷程記錄與學習參考**。

## 🛠 探路用 Swift 腳本

這些獨立 `.swift` 檔是專案迭代過程中的探路腳本，驗證 Core Audio API 行為後，邏輯才被整合進主程式。

| 檔案 | 對應 `blueshare.py` 內的最終實作 |
|------|--------------------------------|
| [`get_list.swift`](get_list.swift) | `SWIFT_CODE` 中的 `getDevices()` — 列出音訊裝置 |
| [`test_vol.swift`](test_vol.swift) | `SWIFT_CODE` 中的 `setVolume()` — 讀寫 `kAudioDevicePropertyVolumeScalar` |
| [`test_mute.swift`](test_mute.swift) | `SWIFT_CODE` 中的 `toggleDeviceMic()` — 讀寫 `kAudioDevicePropertyMute` |
| [`temp_pro.swift`](temp_pro.swift) | 早期 Pro 版完整草稿（已被淘汰） |

想自己單獨跑這些腳本：

```bash
cd dev
swift get_list.swift      # 列出所有音訊裝置 (id|name|uid)
swift test_vol.swift      # 列出裝置與輸入/輸出音量
swift test_mute.swift     # 檢查特定裝置的 mic mute 支援度
```

## 📝 開發對話記錄

兩份 `.md` 完整保留了專案從零開始的迭代脈絡，含當時的研究、決策、踩雷與解法：

| 檔案 | 內容 |
|------|------|
| [`Sharing Audio Across Bluetooth Devices.md`](Sharing%20Audio%20Across%20Bluetooth%20Devices.md) | 主軸：方案調研 → Swift/Python 實作 → 跨品牌支援 → 對講 → 錄音 → 獨立控制 |
| [`Managing Multi-Headphone Audio Settings.md`](Managing%20Multi-Headphone%20Audio%20Settings.md) | 子題：每副耳機音量／麥克風獨立控制的功能討論 |

保留這些檔案是為了：
- 給想理解 Core Audio API 的讀者一個逐步學習的路徑
- 將來除錯時可獨立測試單一功能，不必整支主程式跑起來
- 記錄為什麼做出某些設計選擇（避免將來重複踩同樣的雷）
