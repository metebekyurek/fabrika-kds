import paho.mqtt.client as mqtt
import json
import time
import random

BROKER = "test.mosquitto.org"
PORT = 1883
KONU = "fabrikakds/olcum"

client = mqtt.Client()
client.connect(BROKER, PORT, 60)

print("🔌 Sahte sensör başladı. Broker'a veri gönderiyor... (durdurmak için Ctrl+C)")
print(f"   Broker: {BROKER} · Kanal: {KONU}\n")

# İki makine için gerçekçi değerler üretir, ara sıra sınırı aşar
while True:
    for makine in ["PRES-01", "CNC-01"]:
        # Yağ sıcaklığı: normalde 60-68, ara sıra 72-76 (alarm)
        yag = round(random.choice([62, 64, 66, 68, 73, 75]) + random.uniform(-1, 1), 1)
        # Titreşim: normalde 2-4, ara sıra 5-6 (alarm)
        titresim = round(random.choice([2.5, 3.0, 3.5, 4.0, 5.2, 5.8]) + random.uniform(-0.3, 0.3), 1)

        for param, deger, birim in [("yag_sicakligi", yag, "°C"), ("titresim", titresim, "mm/s")]:
            veri = {
                "makine_id": makine,
                "zaman": time.strftime("%Y-%m-%d %H:%M:%S"),
                "parametre": param,
                "deger": deger,
                "birim": birim
            }
            client.publish(KONU, json.dumps(veri))
            print(f"📤 {makine} · {param}: {deger} {birim}")

    print("---")
    time.sleep(3)  # 3 saniyede bir yeni ölçüm gönder