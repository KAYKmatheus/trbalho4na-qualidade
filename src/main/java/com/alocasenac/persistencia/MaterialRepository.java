package com.alocasenac.persistencia;

import java.util.Optional;
import java.util.UUID;

import jakarta.persistence.LockModeType;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface MaterialRepository extends JpaRepository<Material, UUID> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select material from Material material where material.id = :id")
    Optional<Material> bloquearPorId(@Param("id") UUID id);
}