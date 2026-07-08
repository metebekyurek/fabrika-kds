import paho.mqtt.client as mqtt
import json
import threading
import time

# Ücretsiz genel test broker'ı (kayıt gerektirmez, deneme için)
BROKER = "test.mosquitto.org"
PORT = 1883
KONU = "fabrikakds/olcum"  # bu "kanala" gelen verileri dinleyeceğiz

# Gelen son ölçümler burada birikir (bellekte)
son_olcumler = []
_kilit = threading.Lock()


def _mesaj_geldi(client, userdata, msg):
    """Broker'dan bir ölçüm gelince çalışır."""
    try:
        veri = json.loads(msg.payload.decode())
        with _kilit:
            son_olcumler.append(veri)
            # Son 50 ölçümü tut, fazlasını at
            if len(son_olcumler) > 50:
                son_olcumler.pop(0)
    except Exception:
        pass


def dinlemeye_basla():
    """Arka planda broker'ı dinlemeye başlar."""
    def calis():
        client = mqtt.Client()
        client.on_message = _mesaj_geldi
        try:
            client.connect(BROKER, PORT, 60)
            client.subscribe(KONU)
            client.loop_forever()
        except Exception as e:
            print(f"MQTT bağlantı hatası: {e}")

    t = threading.Thread(target=calis, daemon=True)
    t.start()


def olcumleri_al():
    """Şu ana kadar biriken ölçümleri döndürür."""
    with _kilit:
        return list(son_olcumler)