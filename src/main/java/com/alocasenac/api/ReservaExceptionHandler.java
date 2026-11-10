package com.alocasenac.api;

import java.util.Map;

import com.alocasenac.dominio.ConflitoReservaException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ReservaExceptionHandler {

    @ExceptionHandler(ConflitoReservaException.class)
    public ResponseEntity<Map<String, String>> tratarConflito(ConflitoReservaException erro) {
        return ResponseEntity.status(HttpStatus.CONFLICT).body(Map.of("detail", erro.getMessage()));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, String>> tratarValidacao(IllegalArgumentException erro) {
        return ResponseEntity.unprocessableEntity().body(Map.of("detail", erro.getMessage()));
    }
}