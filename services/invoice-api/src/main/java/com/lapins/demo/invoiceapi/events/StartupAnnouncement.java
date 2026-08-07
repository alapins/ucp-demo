package com.lapins.demo.invoiceapi.events;

import java.util.Map;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

/** Publishes once, when this service is ready, so the windows see it join the system. */
@Component
public class StartupAnnouncement {

  private final EventPublisher events;

  public StartupAnnouncement(EventPublisher events) {
    this.events = events;
  }

  @EventListener(ApplicationReadyEvent.class)
  public void announce() {
    events.publish("service.started", null, Map.of("service", "invoice-api"));
  }
}
