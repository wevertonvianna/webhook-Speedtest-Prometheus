from flask import Flask, request, jsonify
import time, json
from prometheus_client import Counter, Gauge, Histogram, Summary, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# ========================
# MÉTRICAS PROMETHEUS
# ========================
webhook_events_total = Counter('webhook_events_total','Total de webhooks recebidos',['event_type'])
speedtest_ping = Gauge('speedtest_ping_ms', 'Último valor de ping (ms)')
speedtest_download = Gauge('speedtest_download_mbps', 'Última velocidade de download (Mbps)')
speedtest_upload = Gauge('speedtest_upload_mbps', 'Última velocidade de upload (Mbps)')
speedtest_duration = Gauge('speedtest_duration_s', 'Duração total do teste (segundos)')
webhook_last_timestamp = Gauge('webhook_last_timestamp', 'Timestamp do último webhook recebido (epoch)')
speedtest_time_hist = Histogram('speedtest_time_hist_seconds','Distribuição dos tempos de teste (segundos)',buckets=[1, 5, 10, 15, 20, 30, 60])
speedtest_summary = Summary('speedtest_summary_seconds','Tempo de teste com quantis',['event_type'])
speedtest_errors_total = Counter('speedtest_errors_total','Total de erros em testes speedtest',['error_type'])

# ========================
# FUNÇÃO WEBHOOK
# ========================
@app.route('/webhook', methods=['POST'])
def receive_webhook():
    start_time = time.time()  # início do processamento
    
    try:
        # Captura o corpo bruto da requisição
        raw_data = request.get_data(as_text=True)
        print(f"[✔] Webhook recebido às {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(raw_data)

        # --- Leitura segura do JSON com fallback ---
        try:
            data = request.get_json(force=True)
        except Exception:
            try:
                data = json.loads(raw_data)
            except Exception:
                print("[!] JSON inválido recebido.")
                speedtest_errors_total.labels(error_type="invalid_json").inc()
                return jsonify({"status": "error", "message": "JSON inválido"}), 400

        # Extrai campos
        event = data.get("event", "UNKNOWN")
        payload = data.get("data", {})

        # Contador de webhooks
        webhook_events_total.labels(event_type=event).inc()
        webhook_last_timestamp.set(time.time())

        # Processamento de eventos
        if event == "TEST_FINISHED":
            ping = payload.get("ping", 0)
            download = payload.get("download", 0)
            upload = payload.get("upload", 0)
            duration = payload.get("time", 0)

            # Atualiza métricas
            speedtest_ping.set(ping)
            speedtest_download.set(download)
            speedtest_upload.set(upload)
            speedtest_duration.set(duration)

            # Histogram e Summary
            speedtest_time_hist.observe(duration)
            speedtest_summary.labels(event_type=event).observe(duration)

        elif event == "TEST_ERROR":
            error_type = payload.get("error", "unknown_error")
            speedtest_errors_total.labels(error_type=error_type).inc()

        # Mede tempo total de processamento do webhook
        processing_duration = time.time() - start_time
        speedtest_summary.labels(event_type="webhook_process").observe(processing_duration)

        return jsonify({"status": "success"}), 200

    except KeyError as ke:
        print(f"[!] Campo ausente: {ke}")
        speedtest_errors_total.labels(error_type=f"missing_key_{ke.args[0]}").inc()
        return jsonify({"status": "error", "message": f"Campo ausente: {ke}"}), 400

    except json.JSONDecodeError as je:
        print(f"[!] Erro ao decodificar JSON: {je}")
        speedtest_errors_total.labels(error_type="json_decode_error").inc()
        return jsonify({"status": "error", "message": "JSON inválido"}), 400

    except Exception as e:
        print(f"[!] Erro inesperado: {e}")
        speedtest_errors_total.labels(error_type="unexpected_exception").inc()
        return jsonify({"status": "error", "message": str(e)}), 500

# ========================
# ROTA METRICS
# ========================
@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# ========================
# RUN
# ========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
