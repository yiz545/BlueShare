import subprocess
import os
import sys
from datetime import datetime
import time
import threading
import tty
import termios

# 建立桌面錄音資料夾
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "BlueShare_錄音檔")
try:
    os.makedirs(DESKTOP_PATH, exist_ok=True)
except FileExistsError:
    DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop", "BlueShare_Records")
    os.makedirs(DESKTOP_PATH, exist_ok=True)

SWIFT_CODE = f"""
import Foundation
import CoreAudio
import AVFoundation

// 找出內建麥克風的 AudioDeviceID。Bluetooth 耳機在 A2DP 模式下的 :input 裝置雖然存在但不會送資料，
// 強迫用內建麥克風才能保證錄音與對講都收得到聲音。
func findBuiltInMic() -> AudioDeviceID? {{
    var addr = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDevices, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
    var size: UInt32 = 0
    AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject), &addr, 0, nil, &size)
    var ids = [AudioDeviceID](repeating: 0, count: Int(size)/MemoryLayout<AudioDeviceID>.size)
    AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &addr, 0, nil, &size, &ids)
    for id in ids {{
        var uidAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyDeviceUID, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
        var uid: CFString = "" as CFString
        var us = UInt32(MemoryLayout<CFString>.size)
        if AudioObjectGetPropertyData(id, &uidAddr, 0, nil, &us, &uid) == noErr {{
            if (uid as String) == "BuiltInMicrophoneDevice" {{ return id }}
        }}
    }}
    return nil
}}

func getDevices() {{
    var address = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDevices, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
    var propsize: UInt32 = 0
    AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject), &address, 0, nil, &propsize)
    let deviceCount = Int(propsize) / MemoryLayout<AudioDeviceID>.size
    var deviceIDs = [AudioDeviceID](repeating: 0, count: deviceCount)
    AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &address, 0, nil, &propsize, &deviceIDs)
    
    for id in deviceIDs {{
        var outAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyStreams, mScope: kAudioDevicePropertyScopeOutput, mElement: kAudioObjectPropertyElementMain)
        var inAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyStreams, mScope: kAudioDevicePropertyScopeInput, mElement: kAudioObjectPropertyElementMain)
        
        var outSize: UInt32 = 0
        var inSize: UInt32 = 0
        AudioObjectGetPropertyDataSize(id, &outAddr, 0, nil, &outSize)
        AudioObjectGetPropertyDataSize(id, &inAddr, 0, nil, &inSize)
        
        if outSize > 0 || inSize > 0 {{
            var nameAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyDeviceNameCFString, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
            var name: CFString = "" as CFString
            var nameSize = UInt32(MemoryLayout<CFString>.size)
            AudioObjectGetPropertyData(id, &nameAddr, 0, nil, &nameSize, &name)
            
            var uidAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyDeviceUID, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
            var uid: CFString = "" as CFString
            var uidSize = UInt32(MemoryLayout<CFString>.size)
            AudioObjectGetPropertyData(id, &uidAddr, 0, nil, &uidSize, &uid)
            
            var transportAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyTransportType, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
            var transport: UInt32 = 0
            var transportSize = UInt32(MemoryLayout<UInt32>.size)
            AudioObjectGetPropertyData(id, &transportAddr, 0, nil, &transportSize, &transport)
            
            var typeStr = ""
            if transport == kAudioDeviceTransportTypeBluetooth || transport == kAudioDeviceTransportTypeBluetoothLE {{
                typeStr = " (藍牙)"
            }} else if transport == kAudioDeviceTransportTypeBuiltIn {{
                typeStr = " (內建)"
            }}
            let micStr = (inSize > 0) ? " 🎤" : ""
            print("\\(id)|\\(name)\\(typeStr)\\(micStr)|\\(uid)")
        }}
    }}
}}

var sharedAggregateID: AudioDeviceID = 0

func destroyAggregatesByUID(_ targetUID: String) {{
    var addr = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDevices, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
    var size: UInt32 = 0
    AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject), &addr, 0, nil, &size)
    var ids = [AudioDeviceID](repeating: 0, count: Int(size)/MemoryLayout<AudioDeviceID>.size)
    AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &addr, 0, nil, &size, &ids)
    for id in ids {{
        var uidAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyDeviceUID, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
        var devUID: CFString = "" as CFString
        var us = UInt32(MemoryLayout<CFString>.size)
        if AudioObjectGetPropertyData(id, &uidAddr, 0, nil, &us, &devUID) == noErr {{
            if (devUID as String) == targetUID {{
                AudioHardwareDestroyAggregateDevice(id)
            }}
        }}
    }}
}}

class UltimateEngine {{
    var audioEngine: AVAudioEngine?
    var recorder: AVAudioFile?
    var isMuted = false

    func cleanup() {{
        if let engine = audioEngine, engine.isRunning {{
            engine.inputNode.removeTap(onBus: 0)
            engine.stop()
        }}
        recorder = nil
        if sharedAggregateID != 0 {{
            AudioHardwareDestroyAggregateDevice(sharedAggregateID)
            sharedAggregateID = 0
        }}
    }}

    func toggleMic() {{
        isMuted.toggle()
        audioEngine?.inputNode.volume = isMuted ? 0.0 : 1.0
        print(isMuted ? "MIC_MUTED" : "MIC_UNMUTED")
        fflush(stdout)
    }}
    
    func getDeviceID(for targetUID: String) -> AudioDeviceID? {{
        var address = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDevices, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
        var propsize: UInt32 = 0
        AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject), &address, 0, nil, &propsize)
        let deviceCount = Int(propsize) / MemoryLayout<AudioDeviceID>.size
        var deviceIDs = [AudioDeviceID](repeating: 0, count: deviceCount)
        AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &address, 0, nil, &propsize, &deviceIDs)
        
        for id in deviceIDs {{
            var uidAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyDeviceUID, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
            var uid: CFString = "" as CFString
            var uidSize = UInt32(MemoryLayout<CFString>.size)
            AudioObjectGetPropertyData(id, &uidAddr, 0, nil, &uidSize, &uid)
            
            if (uid as String) == targetUID {{
                return id
            }}
        }}
        return nil
    }}
    
    func setVolume(uid: String, direction: String) {{
        guard let id = getDeviceID(for: uid) else {{ return }}
        
        var volAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyVolumeScalar, mScope: kAudioDevicePropertyScopeOutput, mElement: kAudioObjectPropertyElementMain)
        var vol: Float32 = 0
        var volSize = UInt32(MemoryLayout<Float32>.size)
        var status = AudioObjectGetPropertyData(id, &volAddr, 0, nil, &volSize, &vol)
        
        if status != noErr {{
            volAddr.mElement = 1 // try channel 1
            status = AudioObjectGetPropertyData(id, &volAddr, 0, nil, &volSize, &vol)
        }}
        
        if status == noErr {{
            let step: Float32 = 0.05
            if direction == "up" {{ vol = min(1.0, vol + step) }}
            else if direction == "down" {{ vol = max(0.0, vol - step) }}
            
            AudioObjectSetPropertyData(id, &volAddr, 0, nil, volSize, &vol)
            if volAddr.mElement == 1 {{
                volAddr.mElement = 2
                AudioObjectSetPropertyData(id, &volAddr, 0, nil, volSize, &vol)
            }}
            print("VOL_CHANGED|\\(uid)|\\(vol)")
            fflush(stdout)
        }}
    }}

    func toggleDeviceMic(uid: String) {{
        guard let id = getDeviceID(for: uid) else {{ return }}
        
        var muteAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyMute, mScope: kAudioDevicePropertyScopeInput, mElement: kAudioObjectPropertyElementMain)
        var isMuted: UInt32 = 0
        var muteSize = UInt32(MemoryLayout<UInt32>.size)
        
        var status = AudioObjectGetPropertyData(id, &muteAddr, 0, nil, &muteSize, &isMuted)
        if status != noErr {{
            muteAddr.mElement = 1 // try channel 1
            status = AudioObjectGetPropertyData(id, &muteAddr, 0, nil, &muteSize, &isMuted)
        }}
        
        if status == noErr {{
            isMuted = (isMuted == 0) ? 1 : 0
            AudioObjectSetPropertyData(id, &muteAddr, 0, nil, muteSize, &isMuted)
            
            if muteAddr.mElement == 1 {{
                var muteAddr2 = muteAddr
                muteAddr2.mElement = 2
                AudioObjectSetPropertyData(id, &muteAddr2, 0, nil, muteSize, &isMuted)
            }}
            
            print("MIC_TOGGLED|\\(uid)|\\(isMuted)")
            fflush(stdout)
        }} else {{
            print("MIC_NOT_SUPPORTED|\\(uid)")
            fflush(stdout)
        }}
    }}
    
    func start(uids: [String], recordPath: String) {{
        // 啟動前先清掉任何同 UID 的殘留 aggregate（避免拿到上次的舊裝置）
        destroyAggregatesByUID("com.blueshare.ultimate")

        // 強制把預設輸入切到內建麥克風 —
        // 如果之前用過此工具或調過設定，預設輸入可能停在 Bluetooth :input 裝置，
        // 而 A2DP 模式下藍牙麥克風不會送出資料，會造成錄音和對講都收不到聲音。
        if let micID = findBuiltInMic() {{
            var inAddr = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDefaultInputDevice, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
            var id = micID
            AudioObjectSetPropertyData(AudioObjectID(kAudioObjectSystemObject), &inAddr, 0, nil, UInt32(MemoryLayout<AudioDeviceID>.size), &id)
        }}

        let subDevices = uids.map {{ [kAudioSubDeviceUIDKey: $0 as CFString, kAudioSubDeviceDriftCompensationKey: 1] }}
        let desc: [String: Any] = [
            kAudioAggregateDeviceNameKey: "BlueShare_Ultimate",
            kAudioAggregateDeviceUIDKey: "com.blueshare.ultimate",
            kAudioAggregateDeviceSubDeviceListKey: subDevices,
            kAudioAggregateDeviceIsStackedKey: 1,
            kAudioAggregateDeviceMasterSubDeviceKey: uids[0] as CFString
        ]

        var newID: AudioDeviceID = 0
        let createStatus = AudioHardwareCreateAggregateDevice(desc as CFDictionary, &newID)
        if createStatus != noErr || newID == 0 {{
            print("ERROR:CreateAggregate failed status=\\(createStatus)")
            fflush(stdout)
            return
        }}
        sharedAggregateID = newID

        var outAddr = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDefaultOutputDevice, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
        var devID = newID
        AudioObjectSetPropertyData(AudioObjectID(kAudioObjectSystemObject), &outAddr, 0, nil, UInt32(MemoryLayout<AudioDeviceID>.size), &devID)

        // 只有當 aggregate 真的有 input streams 時才把它設為預設輸入；否則保留系統原本的 mic
        var inStreamsAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyStreams, mScope: kAudioDevicePropertyScopeInput, mElement: kAudioObjectPropertyElementMain)
        var inStreamsSize: UInt32 = 0
        AudioObjectGetPropertyDataSize(newID, &inStreamsAddr, 0, nil, &inStreamsSize)
        if inStreamsSize > 0 {{
            var inAddr = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDefaultInputDevice, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
            AudioObjectSetPropertyData(AudioObjectID(kAudioObjectSystemObject), &inAddr, 0, nil, UInt32(MemoryLayout<AudioDeviceID>.size), &devID)
        }}

        Thread.sleep(forTimeInterval: 0.5)

        audioEngine = AVAudioEngine()
        guard let engine = audioEngine else {{ return }}

        let input = engine.inputNode
        // 不把 input 連到 mixer/output（不開對講迴路）—
        // 因為 macOS 把 aggregate 當預設輸出時，engine 的 output 鏈不一定能 pull，
        // 把 input 接進這條鏈會讓 inputNode 也卡住、tap 永遠不觸發。
        // 改成只在 inputNode 上 tap，獨立 pull，錄音可靠。
        // 副作用：無法把麥克風即時聲音送回兩支耳機（對講迴路無法在現有架構下與錄音同時運作）。

        let inFmt = input.inputFormat(forBus: 0)

        let url = URL(fileURLWithPath: recordPath)
        do {{
            // 在 inputNode 上 tap — 這是 AVAudioEngine 錄麥克風最可靠的點，
            // mixer/outputNode 的 tap 在某些 macOS 設定下會被優化掉而從不觸發
            let recFormat = inFmt
            let fileSettings: [String: Any] = [
                AVFormatIDKey: kAudioFormatLinearPCM,
                AVSampleRateKey: recFormat.sampleRate,
                AVNumberOfChannelsKey: recFormat.channelCount,
                AVLinearPCMBitDepthKey: 32,
                AVLinearPCMIsFloatKey: true,
                AVLinearPCMIsBigEndianKey: false,
                "AVLinearPCMIsNonInterleaved": false  // 在 script 模式下 AVLinearPCMIsNonInterleavedKey 不可見，用字面值
            ]
            recorder = try AVAudioFile(forWriting: url, settings: fileSettings, commonFormat: .pcmFormatFloat32, interleaved: true)

            input.installTap(onBus: 0, bufferSize: 1024, format: recFormat) {{ (buffer, _) in
                try? self.recorder?.write(from: buffer)
            }}

            try engine.start()

            // 再次強制把預設輸出設為 aggregate — engine.start() 過程中 macOS 的 Bluetooth manager
            // 可能會把預設輸出切到單一耳機，這裡覆寫回 aggregate 才能真的同步播出。
            Thread.sleep(forTimeInterval: 0.3)
            var outAddr2 = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDefaultOutputDevice, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
            var aggID = sharedAggregateID
            AudioObjectSetPropertyData(AudioObjectID(kAudioObjectSystemObject), &outAddr2, 0, nil, UInt32(MemoryLayout<AudioDeviceID>.size), &aggID)

            print("SUCCESS")
            fflush(stdout)
        }} catch {{
            print("ERROR:\\(error)")
            fflush(stdout)
        }}
    }}
}}

let args = CommandLine.arguments
if args.count > 1 && args[1] == "list" {{
    getDevices()
}} else if args.count > 3 && args[1] == "start" {{
    let uids = args[2].components(separatedBy: ",")
    let engine = UltimateEngine()

    // 訊號處理：被 kill / Ctrl+C 時要銷毀 aggregate，否則會在系統留下殭屍裝置
    signal(SIGINT) {{ _ in
        if sharedAggregateID != 0 {{
            AudioHardwareDestroyAggregateDevice(sharedAggregateID)
        }}
        exit(0)
    }}
    signal(SIGTERM) {{ _ in
        if sharedAggregateID != 0 {{
            AudioHardwareDestroyAggregateDevice(sharedAggregateID)
        }}
        exit(0)
    }}

    engine.start(uids: uids, recordPath: args[3])

    // 背景執行緒負責接收 Python 傳來的按鍵指令；stdin EOF 時做完整清理後結束
    // 協定：m=主靜音, v,UID,up|down=指定耳機調音量, mic,UID=指定耳機麥克風切換
    DispatchQueue.global().async {{
        while let line = readLine() {{
            let parts = line.components(separatedBy: ",")
            if parts[0] == "m" {{
                engine.toggleMic()
            }} else if parts[0] == "v" && parts.count == 3 {{
                engine.setVolume(uid: parts[1], direction: parts[2])
            }} else if parts[0] == "mic" && parts.count == 2 {{
                engine.toggleDeviceMic(uid: parts[1])
            }}
        }}
        // Python 關閉 stdin 時走這裡：把 aggregate 銷毀後正常結束
        engine.cleanup()
        exit(0)
    }}
    RunLoop.main.run()
}}
"""

def run_swift(cmd_args):
    with open("temp_ultimate.swift", "w") as f:
        f.write(SWIFT_CODE)
    process = subprocess.Popen(["swift", "temp_ultimate.swift"] + cmd_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    return process

def getch():
    # 捕捉單一按鍵，不需要按 Enter
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

if __name__ == "__main__":
    print("🎧 BlueShare Ultimate - 聽說共享 + 對講 + 錄音")
    print("------------------------------------------------")
    
    proc = run_swift(["list"])
    output, _ = proc.communicate()

    # 把同一支實體耳機的 :input / :output 兩個邏輯裝置合併成一筆顯示
    # 內部仍保留兩個 UID，建 aggregate 時兩個都加進去 → 同一裝置可同時播音樂與收音
    groups = {}
    order = []
    for line in output.split("\n"):
        if "|" not in line:
            continue
        parts = line.split("|")
        if len(parts) < 3:
            continue
        raw_name, uid = parts[1], parts[2]
        has_mic = "🎤" in raw_name
        clean_name = raw_name.replace(" 🎤", "")
        # 藍牙裝置 UID 形如 "XX-XX-...:input" / ":output"；非藍牙裝置直接用整個 UID 當 key
        if uid.endswith(":input") or uid.endswith(":output"):
            key = uid.rsplit(":", 1)[0]
        else:
            key = uid
        if key not in groups:
            groups[key] = {"name": clean_name, "uids": [], "has_mic": False}
            order.append(key)
        groups[key]["uids"].append(uid)
        if has_mic:
            groups[key]["has_mic"] = True

    devices = [groups[k] for k in order]
    if not devices:
        print("❌ 找不到可用的耳機，請確認耳機已連線藍牙。")
        sys.exit(1)

    print("📌 有標註 🎤 的代表該設備支援麥克風\n")
    for i, dev in enumerate(devices):
        mic_tag = " 🎤" if dev["has_mic"] else ""
        print(f"[{i}] {dev['name']}{mic_tag}")

    choice = input("\n請選擇要共享的耳機編號 (例如 0,1): ")
    try:
        indices = [int(x.strip()) for x in choice.split(",")]
        # Aggregate 只放 :output UID — 加入 :input 會強迫藍牙切換到 HFP 通話模式，
        # 不僅音質劣化，macOS 還會搶走預設輸出造成共享失敗。
        # 個別耳機的 :input UID 仍保留下來，按 5/6 鍵時直接用 CoreAudio 操作其麥克風屬性。
        selected_uids = []
        headphone_keys = []  # 每個被選耳機的 {"output": uid, "input": uid_or_None}，對應 1-6 按鍵
        for i in indices:
            out_uid = next((u for u in devices[i]["uids"] if u.endswith(":output")), None)
            in_uid = next((u for u in devices[i]["uids"] if u.endswith(":input")), None)
            # 非藍牙裝置（如內建喇叭）整個 UID 就是 output
            if out_uid is None and in_uid is None and devices[i]["uids"]:
                out_uid = devices[i]["uids"][0]
            if out_uid:
                selected_uids.append(out_uid)
            headphone_keys.append({"output": out_uid, "input": in_uid})
        
        filename = f"錄音_{datetime.now().strftime('%Y%m%d_%H%M%S')}.caf"
        record_path = os.path.join(DESKTOP_PATH, filename)
        
        print("\n🚀 正在整合耳機與麥克風...")
        time.sleep(1)
        
        proc = run_swift(["start", ",".join(selected_uids), record_path])
        
        def read_output(p):
            while True:
                line = p.stdout.readline()
                if not line: break
                if "SUCCESS" in line:
                    print(f"\r🎙️  對講模式：ON")
                    print(f"\r🔴 錄音模式：ON (儲存至 桌面/BlueShare_錄音檔/{filename})\n")
                    print("\r>>> 操作選單 <<<")
                    print("\r[按 1/2 鍵] 第一副耳機：調小/調大音量")
                    print("\r[按 3/4 鍵] 第二副耳機：調小/調大音量")
                    print("\r[按 5 鍵] 第一副耳機：獨立靜音切換")
                    print("\r[按 6 鍵] 第二副耳機：獨立靜音切換")
                    print("\r[按 M 鍵] 全部靜音總開關")
                    print("\r[按 Q 鍵] 結束共享並儲存錄音\n")
                    print(f"\r等待指令輸入...               ", end="", flush=True)
                elif "ERROR" in line:
                    print(f"\r❌ 發生錯誤: {line.strip()}          \n", flush=True)
                elif "MIC_MUTED" in line:
                    print(f"\r🔇 [總開關] 麥克風已靜音          ", end="", flush=True)
                elif "MIC_UNMUTED" in line:
                    print(f"\r🎙️  [總開關] 麥克風已開啟          ", end="", flush=True)
                elif "VOL_CHANGED" in line:
                    parts = line.strip().split("|")
                    vol_pct = int(float(parts[2]) * 100)
                    print(f"\r🔊 音量已調整至 {vol_pct}%          ", end="", flush=True)
                elif "MIC_TOGGLED" in line:
                    parts = line.strip().split("|")
                    state = "靜音" if parts[2] == "1" else "開啟"
                    print(f"\r🎙️  該耳機麥克風已 {state}          ", end="", flush=True)
                elif "MIC_NOT_SUPPORTED" in line:
                    print(f"\r⚠️ 此耳機不支援獨立麥克風開關      ", end="", flush=True)

        t = threading.Thread(target=read_output, args=(proc,))
        t.daemon = True
        t.start()
        
        def send_vol(headphone_idx, direction):
            if headphone_idx < len(headphone_keys):
                uid = headphone_keys[headphone_idx]["output"]
                if uid:
                    proc.stdin.write(f"v,{uid},{direction}\n")
                    proc.stdin.flush()

        def send_mic_toggle(headphone_idx):
            if headphone_idx < len(headphone_keys):
                uid = headphone_keys[headphone_idx]["input"]
                if uid:
                    proc.stdin.write(f"mic,{uid}\n")
                    proc.stdin.flush()
                else:
                    print(f"\r⚠️ 此耳機沒有可用的麥克風輸入裝置      ", end="", flush=True)

        # 監聽鍵盤輸入
        while True:
            ch = getch()
            if ch.lower() == 'm':
                proc.stdin.write("m\n")
                proc.stdin.flush()
            elif ch == '1': send_vol(0, "down")
            elif ch == '2': send_vol(0, "up")
            elif ch == '3': send_vol(1, "down")
            elif ch == '4': send_vol(1, "up")
            elif ch == '5': send_mic_toggle(0)
            elif ch == '6': send_mic_toggle(1)
            elif ch.lower() == 'q' or ch == '\x03': # Q 鍵或是 Ctrl+C
                break
                
        try:
            proc.stdin.close()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("\n\n⏹️  錄音已結束！檔案已儲存。")
        if os.path.exists("temp_ultimate.swift"): os.remove("temp_ultimate.swift")
        
    except Exception as e:
        print(f"\n\n發生錯誤: {e}")
        if os.path.exists("temp_ultimate.swift"): os.remove("temp_ultimate.swift")
