package com.lapins.demo.invoiceapi;

import com.lapins.demo.invoiceapi.events.EventPublisher;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class DemoController {

  private final EventPublisher events;

  public DemoController(EventPublisher events) {
    this.events = events;
  }

  @GetMapping("/health")
  public Map<String, String> health() {
    return Map.of("status", "up", "service", "invoice-api");
  }

  /** Publishes on demand, so a publish can be driven from this service alone. */
  @PostMapping("/demo/ping")
  @ResponseStatus(HttpStatus.ACCEPTED)
  public Map<String, String> ping(
      @RequestParam(required = false) String correlationId) {
    events.publish("demo.ping", correlationId, Map.of());
    return Map.of("published", "demo.ping", "service", "invoice-api");
  }
}
