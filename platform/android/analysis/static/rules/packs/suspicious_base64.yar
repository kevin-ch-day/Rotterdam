rule ANDROID_SuspiciousBase64 {
    meta:
        description = "Detects long Base64 strings in files"
    strings:
        $b64 = /[A-Za-z0-9+\/]{20,}={0,2}/
    condition:
        $b64
}
