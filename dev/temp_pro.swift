
import Foundation
import CoreAudio
import AVFoundation

class BlueShareEngine {
    var audioEngine = AVAudioEngine()
    var inputNode: AVAudioInputNode?
    var outputNode: AVAudioOutputNode?
    var recorder: AVAudioFile?
    
    // 獲取裝置清單
    func listDevices() {
        var address = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDevices, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
        var propsize: UInt32 = 0
        AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject), &address, 0, nil, &propsize)
        let deviceCount = Int(propsize) / MemoryLayout<AudioDeviceID>.size
        var deviceIDs = [AudioDeviceID](repeating: 0, count: deviceCount)
        AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &address, 0, nil, &propsize, &deviceIDs)
        
        for id in deviceIDs {
            var name: CFString = "" as CFString
            var nameSize = UInt32(MemoryLayout<CFString>.size)
            var nameAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyDeviceNameCFString, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
            AudioObjectGetPropertyData(id, &nameAddr, 0, nil, &nameSize, &name)
            
            var uid: CFString = "" as CFString
            var uidSize = UInt32(MemoryLayout<CFString>.size)
            var uidAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyDeviceUID, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
            AudioObjectGetPropertyData(id, &uidAddr, 0, nil, &uidSize, &uid)
            
            print("\(id)|\(name)|\(uid)")
        }
    }

    func startSharing(uids: [String], recordPath: String) {
        // 1. 建立多重輸出裝置
        let subDevices = uids.map { [kAudioSubDeviceUIDKey: $0 as CFString, kAudioSubDeviceDriftCompensationKey: 1] }
        let desc: [String: Any] = [
            kAudioAggregateDeviceNameKey: "BlueShare_Pro",
            kAudioAggregateDeviceUIDKey: "com.blueshare.pro",
            kAudioAggregateDeviceSubDeviceListKey: subDevices,
            kAudioAggregateDeviceIsStackedKey: 1,
            kAudioAggregateDeviceMasterSubDeviceKey: uids[0] as CFString
        ]
        
        var aggregateID: AudioDeviceID = 0
        AudioHardwareCreateAggregateDevice(desc as CFDictionary, &aggregateID)
        
        // 2. 將系統輸出設為此裝置
        var addr = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDefaultOutputDevice, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
        var devID = aggregateID
        AudioObjectSetPropertyData(AudioObjectID(kAudioObjectSystemObject), &addr, 0, nil, UInt32(MemoryLayout<AudioDeviceID>.size), &devID)
        
        // 3. 啟動對講監聽與錄音 (使用 AVAudioEngine)
        let mainMixer = audioEngine.mainMixerNode
        let input = audioEngine.inputNode // 預設麥克風
        
        // 將麥克風聲音導向耳機 (監聽)
        audioEngine.connect(input, to: mainMixer, format: input.inputFormat(forBus: 0))
        
        // 設定錄音
        let url = URL(fileURLWithPath: recordPath)
        do {
            let settings = mainMixer.outputFormat(forBus: 0).settings
            recorder = try AVAudioFile(forWriting: url, settings: settings)
            
            mainMixer.installTap(onBus: 0, bufferSize: 1024, format: mainMixer.outputFormat(forBus: 0)) { (buffer, _) in
                try? self.recorder?.write(from: buffer)
            }
            
            try audioEngine.start()
            print("SUCCESS")
        } catch {
            print("ERROR:\(error.localizedDescription)")
        }
    }
}

let engine = BlueShareEngine()
let args = CommandLine.arguments
if args.count > 1 && args[1] == "list" {
    engine.listDevices()
} else if args.count > 3 && args[1] == "start" {
    let uids = args[2].components(separatedBy: ",")
    engine.startSharing(uids: uids, recordPath: args[3])
    RunLoop.main.run() // 保持運行以進行錄音與監聽
}
