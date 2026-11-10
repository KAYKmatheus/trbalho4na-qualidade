package com.alocasenac.persistencia;

import java.util.UUID;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "materiais")
public class Material {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "nome", nullable = false)
    private String nome;

    @Column(name = "tipo", nullable = false)
    private String tipo;

    @Column(name = "quantidade_total", nullable = false)
    private int quantidadeTotal;

    @Column(name = "restrito", nullable = false)
    private boolean restrita;

    @Column(name = "ativo", nullable = false)
    private boolean ativo;

    protected Material() {
    }

    public UUID getId() {
        return id;
    }

    public int getQuantidadeTotal() {
        return quantidadeTotal;
    }

    public boolean isRestrita() {
        return restrita;
    }

    public boolean isAtivo() {
        return ativo;
    }
}