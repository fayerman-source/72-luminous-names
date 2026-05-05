import os
import subprocess
import json

def get_audio_info(file_path):
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)

def get_volume_info(file_path):
    cmd = [
        "ffmpeg", "-i", file_path, "-af", "volumedetect", "-f", "null", "/dev/null"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr
    
    info = {}
    for line in output.split('\n'):
        if "max_volume" in line:
            info["max_volume"] = line.split(":")[-1].strip()
        if "mean_volume" in line:
            info["mean_volume"] = line.split(":")[-1].strip()
    return info

def run_qc():
    audio_dir = "static/audio"
    report = []
    
    print(f"{'ID':<4} | {'Duration':<10} | {'Max Vol':<12} | {'Mean Vol':<12} | {'Size':<10} | {'Status'}")
    print("-" * 75)
    
    for i in range(1, 73):
        file_path = os.path.join(audio_dir, f"{i}.mp3")
        if not os.path.exists(file_path):
            print(f"{i:<4} | MISSING")
            continue
            
        size_kb = os.path.getsize(file_path) / 1024
        info = get_audio_info(file_path)
        vol = get_volume_info(file_path)
        
        duration = float(info['format']['duration']) if info else 0
        max_vol = vol.get('max_volume', 'N/A')
        mean_vol = vol.get('mean_volume', 'N/A')
        
        # QC Logic
        status = "✅ OK"
        if duration < 5: status = "⚠️ SHORT"
        if size_kb < 50: status = "❌ SMALL"
        if max_vol == "-inf dB": status = "🔇 SILENT"
        
        print(f"{i:<4} | {duration:>8.2f}s | {max_vol:<12} | {mean_vol:<12} | {size_kb:>8.1f}K | {status}")
        
if __name__ == "__main__":
    run_qc()
