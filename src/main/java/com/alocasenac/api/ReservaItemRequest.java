package com.alocasenac.api;

import java.time.Instant;
import java.util.UUID;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ReservaItemRequest(
        @JsonProperty("resource_type") String resourceType,
        @JsonProperty("resource_id") UUID resourceId,
        @JsonProperty("quantity") Integer quantity,
        @JsonProperty("start") Instant inicio,
        @JsonProperty("end") Instant fim) {
}