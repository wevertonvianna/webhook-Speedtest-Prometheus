# Webhook Speedtest + Prometheus + Docker

Este repositório contém um serviço Flask que recebe webhooks do MySpeedTest, processa métricas de ping, download, upload e duração do teste, e expõe tudo em formato Prometheus para uso com Grafana.

---
## 🔀 Versões do projeto

- 🐍 [Versão Python simples](https://github.com/wevertonvianna/webhook-Speedtest-Prometheus/tree/main)
- 🐳 [Ver versão com Docker](https://github.com/wevertonvianna/webhook-Speedtest-Prometheus/tree/Webhook%2Bdocker)
---
## 📌 Funcionalidades

* Recebe webhooks JSON via `/webhook`
* Processa eventos `TEST_FINISHED` e `TEST_ERROR`
* Exporta métricas para `/metrics`
* Cria métricas Prometheus:

  * `speedtest_ping_ms`
  * `speedtest_download_mbps`
  * `speedtest_upload_mbps`
  * `speedtest_duration_s`
  * `webhook_events_total`
  * `speedtest_errors_total`
  * `speedtest_time_hist_seconds`
  * `speedtest_summary_seconds`

---

# 📁 Estrutura do Projeto


```
├── app.py
├── requirements.txt
├── Dockerfile
├── dockercompose.yml
└── README.md
```

---


# 🐳 Rodando via Docker

## 1. Build da imagem

```
docker build -t speedtest-webhook .
```

## 3. Executar o container

```
docker run -d \
  --name speedtest-webhook \
  -p 8000:8000 \
  speedtest-webhook
```

---

# 🔧 docker-compose.yml (opcional)

```
version: '3.9'
services:
  webhook:
    build: .
    container_name: speedtest-webhook
    ports:
      - "8000:8000"
    restart: unless-stopped
```

Rodar com:

```
docker compose up -d
```

---

# 📡 Como enviar um webhook de teste

```
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
        "event": "TEST_FINISHED",
        "data": {
            "ping": 23,
            "download": 85.4,
            "upload": 12.7,
            "time": 14
        }
      }'
```

---

# 📊 Integrando com Prometheus

Adicione no `prometheus.yml`:

```
- job_name: 'webhook_flask'
  scrape_interval: 5s
  static_configs:
    - targets: ['IP_DO_SERVIDOR:8000']
```

---

# 📝 Licença

Projeto livre para uso pessoal.

---
