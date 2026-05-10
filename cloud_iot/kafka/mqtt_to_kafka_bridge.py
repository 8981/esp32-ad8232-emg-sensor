import json

import paho.mqtt.client as mqtt
from kafka import KafkaProducer


MQTT_TOPIC = "emg/prediction"

KAFKA_TOPIC = "emg_predictions"
KAFKA_SERVER = "localhost:9092"


producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)


def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker: rc={rc}")

    client.subscribe(MQTT_TOPIC)

    print(f"Subscribed to MQTT topic: {MQTT_TOPIC}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        print("MQTT received:", payload)

        producer.send(KAFKA_TOPIC, payload)

        producer.flush()

        print(f"Forwarded to Kafka topic: {KAFKA_TOPIC}")

    except Exception as e:
        print("Bridge error:", e)


client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

print("MQTT → Kafka bridge started.")

client.loop_forever()