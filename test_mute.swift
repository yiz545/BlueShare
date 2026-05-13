import Foundation
import CoreAudio

func checkMute() {
    var address = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyDevices, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
    var propsize: UInt32 = 0
    AudioObjectGetPropertyDataSize(AudioObjectID(kAudioObjectSystemObject), &address, 0, nil, &propsize)
    let deviceCount = Int(propsize) / MemoryLayout<AudioDeviceID>.size
    var deviceIDs = [AudioDeviceID](repeating: 0, count: deviceCount)
    AudioObjectGetPropertyData(AudioObjectID(kAudioObjectSystemObject), &address, 0, nil, &propsize, &deviceIDs)
    
    for id in deviceIDs {
        var nameAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyDeviceNameCFString, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
        var name: CFString = "" as CFString
        var nameSize = UInt32(MemoryLayout<CFString>.size)
        AudioObjectGetPropertyData(id, &nameAddr, 0, nil, &nameSize, &name)
        
        var uidAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyDeviceUID, mScope: kAudioObjectPropertyScopeGlobal, mElement: kAudioObjectPropertyElementMain)
        var uid: CFString = "" as CFString
        var uidSize = UInt32(MemoryLayout<CFString>.size)
        AudioObjectGetPropertyData(id, &uidAddr, 0, nil, &uidSize, &uid)
        
        if (uid as String).contains("80-99-E7-7D-28-A6") {
            print("Device \(id): \(name) | \(uid)")
            
            var muteAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyMute, mScope: kAudioDevicePropertyScopeInput, mElement: kAudioObjectPropertyElementMain)
            var isMuted: UInt32 = 0
            var muteSize = UInt32(MemoryLayout<UInt32>.size)
            let inStatus = AudioObjectGetPropertyData(id, &muteAddr, 0, nil, &muteSize, &isMuted)
            if inStatus == noErr {
                print("  Input Mute Supported. Muted: \(isMuted)")
            } else {
                muteAddr.mElement = 1
                let inStatusCh1 = AudioObjectGetPropertyData(id, &muteAddr, 0, nil, &muteSize, &isMuted)
                if inStatusCh1 == noErr {
                    print("  Input Mute Ch1 Supported. Muted: \(isMuted)")
                } else {
                    print("  Input Mute NOT Supported.")
                }
            }
        }
    }
}
checkMute()
