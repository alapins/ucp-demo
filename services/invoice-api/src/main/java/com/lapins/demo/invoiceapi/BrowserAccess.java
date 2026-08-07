package com.lapins.demo.invoiceapi;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * The merchant window is served from a different origin than the server it reads, the
 * same way the Event Bus is. Wide open, as befits a demo with no credentials in it.
 */
@Configuration
class BrowserAccess implements WebMvcConfigurer {

  @Override
  public void addCorsMappings(CorsRegistry registry) {
    registry.addMapping("/**").allowedOrigins("*").allowedMethods("*").allowedHeaders("*");
  }
}
