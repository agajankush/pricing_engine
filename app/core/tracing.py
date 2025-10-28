# Singular file which initialize the tracer and the OTLP exported
# which sends the trace data to the Jaeger collector

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def configure_tracer(service_name: str):
    """
    Setup the OpenTelemetry Tracer Provider for the given service.
    """
    resource = Resource.create({"service.name": service_name})
    
    # Set the TracerProvider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://jaeger:4318/v1/traces",
    )
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
    
    return provider