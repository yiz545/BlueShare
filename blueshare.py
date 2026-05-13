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

class UltimateEngine {{
    var audioEngine: AVAudioEngine?
    var recorder: AVAudioFile?
    var isMuted = false
    
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
        let subDevices = uids.map {{ [kAudioSubDeviceUIDKey: $0 as CFString, kAudioSubDeviceDriftCompensationKey: 1] }}
        let desc: [String: Any] = [
            kAudioAggregateDeviceNameKey: "BlueShare_Ultimate",
            kAudioAggregateDeviceUIDKey: "com.blueshare.ultimate",
            kAudioAggregateDeviceSubDeviceListKey: subDevices,
            kAudioAggregateDeviceIsStackedKey: 1,
            kAudioAggregateDeviceMasterSubDeviceKey: uids[0] as CFString
        ]
        
        var newID: AudioDeviceID = 0
        AudioHardwareCreateAggregateDevice(desc as CFDictionary, &newID)
        
        var outAddr = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDefaultOutputDevice, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
        var inAddr = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDefaultInputDevice, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
        var devID = newID
        AudioObjectSetPropertyData(AudioObjectID(kAudioObjectSystemObject), &outAddr, 0, nil, UInt32(MemoryLayout<AudioDeviceID>.size), &devID)
        AudioObjectSetPropertyData(AudioObjectID(kAudioObjectSystemObject), &inAddr, 0, nil, UInt32(MemoryLayout<AudioDeviceID>.size), &devID)
        
        Thread.sleep(forTimeInterval: 0.5)
        
        audioEngine = AVAudioEngine()
        guard let engine = audioEngine else {{ return }}
        
        let mixer = engine.mainMixerNode
        let input = engine.inputNode
        
        engine.connect(input, to: mixer, format: input.inputFormat(forBus: 0))
        
        let url = URL(fileURLWithPath: recordPath)
        do {{
            let format = mixer.outputFormat(forBus: 0)
            recorder = try AVAudioFile(forWriting: url, settings: format.settings)
            
            mixer.installTap(onBus: 0, bufferSize: 1024, format: format) {{ (buffer, _) in
                try? self.recorder?.write(from: buffer)
            }}
            
            try engine.start()
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
    engine.start(uids: uids, recordPath: args[3])
    
    // 背景執行緒負責接收 Python 傳來的按鍵指令
    DispatchQueue.global().async {{
        while let line = readLine() {{
            let parts = line.components(separatedBy: ",")
            if parts[0] == "m" {{
                engine.toggleMic()
            }} else if parts[0] == "v" && parts.count == 3 {{
                if let idx = Int(parts[1]), idx < uids.count {{
                    engine.setVolume(uid: uids[idx], direction: parts[2])
                }}
            }} else if parts[0] == "mic" && parts.count == 2 {{
                if let idx = Int(parts[1]), idx < uids.count {{
                    engine.toggleDeviceMic(uid: uids[idx])
                }}
            }}
        }}
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
    devices = []
    
    for line in output.split("\n"):
        if "|" in line:
            parts = line.split("|")
            devices.append({"name": parts[1], "uid": parts[2]})
            
    if not devices:
        print("❌ 找不到可用的耳機，請確認耳機已連線藍牙。")
        sys.exit(1)
        
    print("📌 有標註 🎤 的代表該設備支援麥克風\n")
    for i, dev in enumerate(devices):
        print(f"[{i}] {dev['name']}")
        
    choice = input("\n請選擇要共享的耳機編號 (例如 1,2): ")
    try:
        indices = [int(x.strip()) for x in choice.split(",")]
        selected_uids = [devices[i]["uid"] for i in indices]
        
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
        
        # 監聽鍵盤輸入
        while True:
            ch = getch()
            if ch.lower() == 'm':
                proc.stdin.write("m\n")
                proc.stdin.flush()
            elif ch == '1':
                proc.stdin.write("v,0,down\n")
                proc.stdin.flush()
            elif ch == '2':
                proc.stdin.write("v,0,up\n")
                proc.stdin.flush()
            elif ch == '3':
                proc.stdin.write("v,1,down\n")
                proc.stdin.flush()
            elif ch == '4':
                proc.stdin.write("v,1,up\n")
                proc.stdin.flush()
            elif ch == '5':
                proc.stdin.write("mic,0\n")
                proc.stdin.flush()
            elif ch == '6':
                proc.stdin.write("mic,1\n")
                proc.stdin.flush()
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
