import Foundation
import CoreAudio

func getDevices() {
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
        
        print("Device \(id): \(name) | \(uid)")
        
        var inVolAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyVolumeScalar, mScope: kAudioDevicePropertyScopeInput, mElement: 1)
        var inVol: Float32 = 0
        var inVolSize = UInt32(MemoryLayout<Float32>.size)
        let inStatus = AudioObjectGetPropertyData(id, &inVolAddr, 0, nil, &inVolSize, &inVol)
        if inStatus == noErr {
            print("  Input Vol Ch1: \(inVol)")
        } else {
            // try master
            inVolAddr.mElement = kAudioObjectPropertyElementMain
            let inStatusMain = AudioObjectGetPropertyData(id, &inVolAddr, 0, nil, &inVolSize, &inVol)
            if inStatusMain == noErr {
                print("  Input Vol Main: \(inVol)")
            }
        }
        
        var outVolAddr = AudioObjectPropertyAddress(mSelector: kAudioDevicePropertyVolumeScalar, mScope: kAudioDevicePropertyScopeOutput, mElement: 1)
        var outVol: Float32 = 0
        var outVolSize = UInt32(MemoryLayout<Float32>.size)
        let outStatus = AudioObjectGetPropertyData(id, &outVolAddr, 0, nil, &outVolSize, &outVol)
        if outStatus == noErr {
            print("  Output Vol Ch1: \(outVol)")
        } else {
            outVolAddr.mElement = kAudioObjectPropertyElementMain
            let outStatusMain = AudioObjectGetPropertyData(id, &outVolAddr, 0, nil, &outVolSize, &outVol)
            if outStatusMain == noErr {
                print("  Output Vol Main: \(outVol)")
            }
        }
    }
}
getDevices()
