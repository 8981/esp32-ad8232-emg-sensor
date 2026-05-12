import json
import time

from kafka import KafkaConsumer
from influxdb_client import InfluxDBClient, Point, WritePrecision


# Kafka settings
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "emg_predictions"

# InfluxDB settings
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "emg-token"
INFLUX_ORG = "emg-org"
INFLUX_BUCKET = "emg-bucket"


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def main():
    print("Starting Kafka → InfluxDB consumer...")
    print(f"Kafka bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Kafka topic: {KAFKA_TOPIC}")
    print(f"InfluxDB URL: {INFLUX_URL}")
    print(f"InfluxDB bucket: {INFLUX_BUCKET}")
    print()

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="emg-influxdb-writer",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    influx_client = InfluxDBClient(
        url=INFLUX_URL,
        token=INFLUX_TOKEN,
        org=INFLUX_ORG,
    )

    write_api = influx_client.write_api()

    print("Kafka → InfluxDB consumer started.")
    print("Waiting for Kafka messages...\n")

    try:
        for message in consumer:
            data = message.value

            prediction = str(data.get("prediction", "UNKNOWN"))
            label = safe_int(data.get("label", -1), -1)

            command_value = safe_float(data.get("command_value", 0.0))
            p_rest = safe_float(data.get("p_rest", 0.0))
            p_fist = safe_float(data.get("p_fist", 0.0))
            ema_fist = safe_float(data.get("ema_fist", 0.0))
            timestamp_source = safe_float(data.get("timestamp", time.time()))

            point = (
                Point("emg_prediction")
                .tag("prediction", prediction)
                .field("label", label)
                .field("command_value", command_value)
                .field("p_rest", p_rest)
                .field("p_fist", p_fist)
                .field("ema_fist", ema_fist)
                .field("timestamp_source", timestamp_source)
                .time(time.time_ns(), WritePrecision.NS)
            )

            write_api.write(
                bucket=INFLUX_BUCKET,
                org=INFLUX_ORG,
                record=point,
            )

            print(
                "Written to InfluxDB: "
                f"prediction={prediction}, "
                f"label={label}, "
                f"command_value={command_value:.3f}, "
                f"p_rest={p_rest:.3f}, "
                f"p_fist={p_fist:.3f}, "
                f"ema_fist={ema_fist:.3f}"
            )

    except KeyboardInterrupt:
        print("\nStopped by user.")

    finally:
        consumer.close()
        influx_client.close()


if __name__ == "__main__":
    main()
