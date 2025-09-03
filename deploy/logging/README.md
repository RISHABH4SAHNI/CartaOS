# Logging Infrastructure

This directory contains the configuration for the CartaOS logging infrastructure using the ELK stack (Elasticsearch, Logstash, Kibana) with Filebeat for log collection.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. **Start the logging stack**:
   ```bash
   docker-compose up -d
   ```

2. **Access Kibana**:
   - Open http://localhost:5601 in your browser
   - The first time you access Kibana, it may take a few minutes to initialize

3. **Configure Kibana Index Pattern**:
   - Go to Stack Management > Index Patterns
   - Create index pattern: `cartaos-logs-*`
   - Select `@timestamp` as the time filter field

## Log Collection

Application logs are expected to be in JSON format in `/var/log/cartaos/`. Make sure your application has write permissions to this directory.

## Configuration

### Filebeat
- Config file: `filebeat/filebeat.yml`
- Collects logs from `/var/log/cartaos/*.log`
- Sends logs to Logstash on port 5044

### Logstash
- Pipeline config: `logstash/pipeline/logstash.conf`
- Processes logs and sends them to Elasticsearch

### Elasticsearch
- Single-node cluster
- Data is persisted in a Docker volume named `elasticsearch_data`

### Kibana
- Web interface for log visualization
- Accessible at http://localhost:5601

## Log Rotation

Log rotation is handled by the application. The recommended configuration is:

- Rotate when log file reaches 10MB
- Keep 5 backup files
- Compress rotated logs

## Security

For production use:
1. Enable security in Elasticsearch and Kibana
2. Set up proper authentication
3. Use TLS for communication between components
4. Restrict network access to the logging stack

## Monitoring

Monitor the health of your logging stack:

```bash
docker-compose ps
docker-compose logs -f
```

## Troubleshooting

### Logstash not starting
- Check the container logs: `docker-compose logs logstash`
- Verify the configuration: `docker-compose exec logstash logstash --config.test_and_exit -f /usr/share/logstash/pipeline/`

### No logs in Kibana
- Check if Filebeat is running: `docker-compose ps filebeat`
- Check Filebeat logs: `docker-compose logs filebeat`
- Verify log files exist in `/var/log/cartaos/`

### High resource usage
- Adjust JVM heap size in `docker-compose.yml`
- Consider adding more resources to Elasticsearch for production use
