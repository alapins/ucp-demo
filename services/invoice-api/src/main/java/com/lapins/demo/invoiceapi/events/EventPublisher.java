package com.lapins.demo.invoiceapi.events;

import java.net.http.HttpClient;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.JdkClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

/** Announces this service's activity on the Event Bus. */
@Component
public class EventPublisher {

  private static final Logger log = LoggerFactory.getLogger(EventPublisher.class);
  private static final String SERVICE = "invoice-api";

  private final RestClient bus;

  public EventPublisher(@Value("${demo.event-bus-url}") String eventBusUrl) {
    // Pinned to HTTP/1.1. Left to itself the JDK client opens with an h2c upgrade
    // offer, and the Event Bus's HTTP/1.1-only server answers that request with an
    // empty body — so every publish failed while the JSON being sent was correct.
    HttpClient http1Only = HttpClient.newBuilder().version(HttpClient.Version.HTTP_1_1).build();
    this.bus =
        RestClient.builder()
            .requestFactory(new JdkClientHttpRequestFactory(http1Only))
            .baseUrl(eventBusUrl)
            .build();
  }

  public void publish(String type, String correlationId, Map<String, Object> payload) {
    try {
      bus.post()
          .uri("/events")
          .contentType(MediaType.APPLICATION_JSON)
          .body(
              Map.of(
                  "type", type,
                  "service", SERVICE,
                  "correlation_id", correlationId == null ? "" : correlationId,
                  "payload", payload == null ? Map.of() : payload))
          .retrieve()
          .toBodilessEntity();
    } catch (RuntimeException unreachable) {
      // The Event Bus is a window onto the demo, not a dependency of it. Work that
      // succeeded must not fail because nobody was watching.
      log.warn("could not publish {}: {}", type, unreachable.getMessage());
    }
  }
}
