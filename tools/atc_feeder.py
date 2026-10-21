#!/usr/bin/env python3
"""そらメモ 受信の協力（PC・ラズパイ用）

受信機（ハンディ受信機のイヤホン端子、または SDR 受信機のソフトの音）をPCの音の入力につなぎ、
声のところだけを切り出して、このPCの中で英語の文字にし（faster-whisper）、そらメモに送ります。
音そのものは送りません。

使い方
  1. Python 3.10 以上を入れて、次を実行します
       pip install sounddevice numpy faster-whisper requests
  2. そらメモの「受信に協力する」→「受信機とPCで協力」で合言葉を作ります
  3. 受信機を聞きたい周波数に合わせて、次のように動かします（1つの周波数に1つずつ）
       python atc_feeder.py --token 合言葉 --iata HND --ch twr --freq 118.10
     音の入力を選ぶとき：python atc_feeder.py --list-devices で番号を調べ、--device 番号 を付けます
     GPU があれば --gpu を付けると速くなります。遅いPCでは --model tiny.en にします

ch（管制）は twr（タワー）・gnd（グランド）・app（アプローチ）・dep（ディパーチャー）・ramp・del のどれかです。
止めるときは Ctrl+C を押します。
"""
import argparse, json, queue, re, sys, threading, time

URL = "https://bygwdoypfrccgfjjrorc.supabase.co/functions/v1/atc-ingest"
RATE = 16000
BLOCK = 2048  # 約0.13秒


def main():
    ap = argparse.ArgumentParser(description="そらメモ 受信の協力（PC・ラズパイ用）")
    ap.add_argument("--token", help="そらメモで作った合言葉（64文字）")
    ap.add_argument("--iata", choices=["HND", "NRT"], default="HND")
    ap.add_argument("--ch", choices=["twr", "gnd", "app", "dep", "ramp", "del"], default="twr")
    ap.add_argument("--freq", default=None, help="受信機の周波数（例 118.10）")
    ap.add_argument("--device", type=int, default=None, help="音の入力の番号（--list-devices で調べる）")
    ap.add_argument("--model", default="base.en", help="音声認識のモデル（tiny.en・base.en・small.en）")
    ap.add_argument("--gpu", action="store_true", help="GPU で音声認識する")
    ap.add_argument("--threshold", type=float, default=3.0, help="声とみなす大きさ（雑音の何倍か）")
    ap.add_argument("--list-devices", action="store_true")
    a = ap.parse_args()

    import numpy as np
    import sounddevice as sd
    if a.list_devices:
        print(sd.query_devices()); return
    if not a.token or not re.fullmatch(r"[0-9a-f]{64}", a.token):
        sys.exit("合言葉（--token）を入れてください。そらメモの「受信に協力する」で作れます。")
    if a.freq and not re.fullmatch(r"1[1-3]\d\.\d{1,3}", a.freq):
        sys.exit("周波数は 118.10 のように入れてください。")

    import requests
    from faster_whisper import WhisperModel
    print("音声認識のモデルを読み込んでいます…")
    model = WhisperModel(a.model, device="cuda" if a.gpu else "cpu", compute_type="float16" if a.gpu else "int8")
    head = {"Content-Type": "application/json", "x-feeder-token": a.token}

    def post(body):
        try:
            r = requests.post(URL, headers=head, data=json.dumps(body), timeout=15)
            return r.json() if r.ok else {"error": r.status_code}
        except Exception as e:  # ネットが切れても止めない
            return {"error": str(e)}

    clips = queue.Queue(maxsize=20)
    state = {"buf": [], "speaking": False, "quiet": 0, "floor": 0.01}

    def on_audio(indata, frames, t, status):
        x = indata[:, 0].copy()
        rms = float(np.sqrt(np.mean(x * x)))
        if not state["speaking"]:
            state["floor"] = state["floor"] * 0.98 + rms * 0.02
        loud = rms > max(0.012, state["floor"] * a.threshold)
        if loud:
            state["speaking"], state["quiet"] = True, 0
            state["buf"].append(x)
        elif state["speaking"]:
            state["buf"].append(x); state["quiet"] += 1
            if state["quiet"] >= 6:
                flush()
        if len(state["buf"]) > 120:  # 15秒より長いものは区切る
            flush()

    def flush():
        buf, state["buf"], state["speaking"], state["quiet"] = state["buf"], [], False, 0
        n = sum(len(b) for b in buf)
        if n >= RATE * 0.6:
            try: clips.put_nowait((time.time() - n / RATE, np.concatenate(buf)))
            except queue.Full: pass

    def ping():
        while True:
            post({"ping": True, "iata": a.iata, "ch": a.ch, "freq": a.freq}); time.sleep(60)

    threading.Thread(target=ping, daemon=True).start()
    sent = shown = 0
    with sd.InputStream(samplerate=RATE, channels=1, dtype="float32", blocksize=BLOCK, device=a.device, callback=on_audio):
        print(f"受信中：{a.iata} {a.ch} {a.freq or ''}（Ctrl+C で止める）")
        try:
            while True:
                at, audio = clips.get()
                segs, info = model.transcribe(audio, language="en", beam_size=3, vad_filter=False,
                                              initial_prompt="Air traffic control. Japan Air, All Nippon, runway, taxi via, hold short, cleared to land, cleared for takeoff.")
                segs = list(segs)
                text = " ".join(s.text.strip() for s in segs).strip()
                if len(text) < 4: continue
                conf = float(np.exp(np.mean([s.avg_logprob for s in segs]))) if segs else None
                r = post({"iata": a.iata, "ch": a.ch, "freq": a.freq, "at": int(at * 1000), "text": text, "conf": conf})
                sent += 1; shown += 1 if r.get("shown") else 0
                print(time.strftime("%H:%M:%S", time.localtime(at)), text, "→", r.get("ja") or "（読み取れず）", "（画面に出ました）" if r.get("shown") else "", f"[{shown}/{sent}]")
        except KeyboardInterrupt:
            print("止めました。")


if __name__ == "__main__":
    main()
