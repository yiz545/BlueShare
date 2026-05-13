# dev/ — 開發歷程探路腳本

⚠️ **這個資料夾的 Swift 檔案不參與運行時行為**。BlueShare 主程式 (`blueshare.py`) 將所有 Swift 程式碼以字串 `SWIFT_CODE` 內嵌，執行時動態寫入 `temp_ultimate.swift` 並編譯。

這些獨立 `.swift` 檔是專案迭代過程中的探路腳本，驗證 Core Audio API 行為後，邏輯才被整合進主程式。

| 檔案 | 對應 `blueshare.py` 內的最終實作 |
|------|--------------------------------|
| [`get_list.swift`](get_list.swift) | `SWIFT_CODE` 中的 `getDevices()` — 列出音訊裝置 |
| [`test_vol.swift`](test_vol.swift) | `SWIFT_CODE` 中的 `setVolume()` — 讀寫 `kAudioDevicePropertyVolumeScalar` |
| [`test_mute.swift`](test_mute.swift) | `SWIFT_CODE` 中的 `toggleDeviceMic()` — 讀寫 `kAudioDevicePropertyMute` |
| [`temp_pro.swift`](temp_pro.swift) | 早期 Pro 版完整草稿（已被淘汰） |

## 想自己跑這些腳本？

```bash
cd dev
swift get_list.swift      # 列出所有音訊裝置 (id|name|uid)
swift test_vol.swift      # 列出裝置與輸入/輸出音量
swift test_mute.swift     # 檢查特定裝置的 mic mute 支援度
```

保留這些檔案是為了：
- 給想理解 Core Audio API 的讀者一個逐步學習的路徑
- 將來除錯時可獨立測試單一功能，不必整支主程式跑起來
