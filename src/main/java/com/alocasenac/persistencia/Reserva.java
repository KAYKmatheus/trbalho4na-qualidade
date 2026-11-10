package com.alocasenac.persistencia;

import java.time.Instant;
import java.util.UUID;

import org.hibernate.annotations.ColumnDefault;
import org.hibernate.annotations.Generated;
import org.hibernate.generator.EventType;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.Version;

@Entity
@Table(name = "reservas")
public class Reserva {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "solicitante_id", nullable = false)
    private UUID solicitanteId;

    @Column(name = "inicio", nullable = false)
    private Instant inicio;

    @Column(name = "fim", nullable = false)
    private Instant fim;

    @Enumerated(EnumType.STRING)
    @JdbcTypeCode(SqlTypes.NAMED_ENUM)
    @Column(name = "status", nullable = false, columnDefinition = "status_reserva")
    private StatusReserva status;

    @Version
    @Generated(event = {EventType.INSERT, EventType.UPDATE})
    @ColumnDefault("1")
    @Column(name = "versao", nullable = false)
    private Integer versao;

    @Column(name = "finalidade", nullable = false)
    private String finalidade;

    protected Reserva() {
    }

    public Reserva(UUID solicitanteId, Instant inicio, Instant fim, StatusReserva status, String finalidade) {
        this.solicitanteId = solicitanteId;
        this.inicio = inicio;
        this.fim = fim;
        this.status = status;
        this.finalidade = finalidade;
    }

    public UUID getId() {
        return id;
    }

    public UUID getSolicitanteId() {
        return solicitanteId;
    }

    public StatusReserva getStatus() {
        return status;
    }
}