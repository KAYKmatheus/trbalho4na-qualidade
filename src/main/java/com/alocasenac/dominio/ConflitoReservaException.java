package com.alocasenac.dominio;

import java.time.Instant;
import java.util.UUID;

public class ConflitoReservaException extends RuntimeException {

    private final UUID solicitanteId;
    private final String tipoRecurso;
    private final UUID recursoId;
    private final Instant inicio;
    private final Instant fim;
    private final int quantidade;
    private final String motivo;

    public ConflitoReservaException(
            UUID solicitanteId,
            String tipoRecurso,
            UUID recursoId,
            Instant inicio,
            Instant fim,
            int quantidade,
            String motivo) {
        super("Conflito detectado para " + tipoRecurso + " " + recursoId + ".");
        this.solicitanteId = solicitanteId;
        this.tipoRecurso = tipoRecurso;
        this.recursoId = recursoId;
        this.inicio = inicio;
        this.fim = fim;
        this.quantidade = quantidade;
        this.motivo = motivo;
    }

    public UUID getSolicitanteId() {
        return solicitanteId;
    }

    public String getTipoRecurso() {
        return tipoRecurso;
    }

    public UUID getRecursoId() {
        return recursoId;
    }

    public Instant getInicio() {
        return inicio;
    }

    public Instant getFim() {
        return fim;
    }

    public int getQuantidade() {
        return quantidade;
    }

    public String getMotivo() {
        return motivo;
    }
}