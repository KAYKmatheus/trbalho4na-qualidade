package com.alocasenac.api;

import java.util.List;
import java.util.UUID;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ReservaRequest(
        @JsonProperty("solicitante_id") UUID solicitanteId,
        @JsonProperty("reason") String finalidade,
        @JsonProperty("items") List<ReservaItemRequest> itens) {
}