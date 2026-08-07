package com.lapins.demo.invoiceapi;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.net.InetSocketAddress;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Map;

/**
 * An Event Bus that only remembers.
 *
 * <p>The real bus is a separate service with its own tests; what the Invoice API owes it
 * is a publication of the right shape at the right moment, and that is all this records.
 * It answers over real HTTP so the publisher under test is the one the demo ships.
 */
final class StubEventBus {

  private static final ObjectMapper JSON = new ObjectMapper();

  private final HttpServer server;
  private final Deque<Map<String, Object>> published = new ArrayDeque<>();

  private StubEventBus(HttpServer server) {
    this.server = server;
  }

  static StubEventBus start() {
    try {
      HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
      StubEventBus bus = new StubEventBus(server);
      server.createContext(
          "/events",
          exchange -> {
            Map<String, Object> publication =
                JSON.readValue(exchange.getRequestBody().readAllBytes(), Map.class);
            synchronized (bus.published) {
              bus.published.add(publication);
            }
            exchange.sendResponseHeaders(202, -1);
            exchange.close();
          });
      server.start();
      return bus;
    } catch (IOException cannotListen) {
      throw new UncheckedIOException(cannotListen);
    }
  }

  String url() {
    return "http://127.0.0.1:" + server.getAddress().getPort();
  }

  /**
   * The one publication of this type, failing if the Invoice API never made it.
   *
   * <p>Publishing is synchronous inside the request that caused it, so anything the
   * server meant to say has already been said by the time a caller gets its response.
   */
  Map<String, Object> announcementOf(String type) {
    synchronized (published) {
      return published.stream()
          .filter(publication -> type.equals(publication.get("type")))
          .findFirst()
          .orElseThrow(
              () -> new AssertionError("no " + type + " was published; saw " + published));
    }
  }
}
