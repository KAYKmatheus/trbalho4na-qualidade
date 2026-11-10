package com.alocasenac.servico;

import com.alocasenac.dominio.ConflitoReservaException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuditoriaService {

    private final JdbcTemplate jdbcTemplate;

    public AuditoriaService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void registrarConflito(ConflitoReservaException conflito) {
        String entidade = switch (conflito.getTipoRecurso()) {
            case "sala" -> "salas";
            case "professor" -> "professores";
            case "material" -> "materiais";
            default -> throw new IllegalArgumentException("Tipo de recurso inválido para auditoria.");
        };

        jdbcTemplate.update("""
                INSERT INTO auditoria (usuario_id, entidade, entidade_id, acao, valor_novo)
                VALUES (?, ?, ?, 'CONFLITO_EVITADO',
                    jsonb_build_object('inicio', ?, 'fim', ?, 'motivo', ?, 'quantidade', ?))
                """,
                conflito.getSolicitanteId(),
                entidade,
                conflito.getRecursoId(),
                conflito.getInicio().toString(),
                conflito.getFim().toString(),
                conflito.getMotivo(),
                conflito.getQuantidade());
    }
}