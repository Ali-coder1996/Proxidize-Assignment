from flask import Flask, request, jsonify
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

# Set up the TracerProvider
trace.set_tracer_provider(
    TracerProvider(resource=Resource.create({"service.name": "length-service"}))
)
# Configure the OTLP exporter (e.g., sending traces to an OpenTelemetry Collector)
otlp_exporter = OTLPSpanExporter(
    endpoint="http://new-opentelemetry-collector:4317",  # OTLP gRPC endpoint
)
# Add the exporter to the TracerProvider
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

app = Flask(__name__)

# Auto-instrument the Flask app
FlaskInstrumentor().instrument_app(app)


# Prometheus Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total number of HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration in seconds', ['method', 'endpoint'])
ERROR_COUNT = Counter('http_errors_total', 'Total number of HTTP errors', ['method', 'endpoint', 'status_code'])

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/healthz')
def healthz():
    return '', 200

@app.route('/length', methods=['POST'])
def string_length():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("string_length_endpoint"):
        start_time = time.time()

        REQUEST_COUNT.labels(request.method, request.path).inc()
        data = request.json
        input_string = data.get('input', '')

        # Simulate processing
        time.sleep(0.1)

        duration = time.time() - start_time
        REQUEST_DURATION.labels(request.method, request.path).observe(duration)

        return jsonify(len(input_string))

@app.errorhandler(500)
def internal_error(error):
    ERROR_COUNT.labels(request.method, request.path, 500).inc()
    return jsonify(error="Internal Server Error"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)