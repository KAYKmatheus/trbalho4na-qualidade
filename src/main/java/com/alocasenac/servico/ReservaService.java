package com.alocasenac.servico;

import java.sql.Timestamp;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.alocasenac.api.ReservaItemRequest;
import com.alocasenac.api.ReservaRequest;
import com.alocasenac.dominio.ConflitoReservaException;
import com.alocasenac.persistencia.Material;
import com.alocasenac.persistencia.MaterialRepository;
import com.alocasenac.persistencia.Reserva;
import com.alocasenac.persistencia.ReservaRepository;
import com.alocasenac.persistencia.StatusReserva;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

@Service
public class ReservaService {

    private final JdbcTemplate jdbcTemplate;
    private final NamedParameterJdbcTemplate namedJdbc;
    private final MaterialRepository materialRepository;
    private final ReservaRepository reservaRepository;
    private final AuditoriaService auditoriaService;
    private final TransactionTemplate transactionTemplate;

    public ReservaService(
            JdbcTemplate jdbcTemplate,
            NamedParameterJdbcTemplate namedJdbc,
            MaterialRepository materialRepository,
            ReservaRepository reservaRepository,
            AuditoriaService auditoriaService,
            PlatformTransactionManager transactionManager) {
        this.jdbcTemplate = jdbcTemplate;
        this.namedJdbc = namedJdbc;
        this.materialRepository = materialRepository;
        this.reservaRepository = reservaRepository;
        this.auditoriaService = auditoriaService;
        this.transactionTemplate = new TransactionTemplate(transactionManager);
    }

    public Map<String, Object> criar(ReservaRequest request) {
        List<ItemNormalizado> itens = normalizar(request);
        try {
            return transactionTemplate.execute(status -> criarNaTransacao(request, itens));
        } catch (ConflitoReservaException conflito) {
            auditoriaService.registrarConflito(conflito);
            throw conflito;
        } catch (DataIntegrityViolationException erro) {
            ConflitoReservaException conflito = conflitoExclusao(request, itens, erro);
            if (conflito == null) {
                throw erro;
            }
            auditoriaService.registrarConflito(conflito);
            throw conflito;
        }
    }

    private Map<String, Object> criarNaTransacao(ReservaRequest request, List<ItemNormalizado> itens) {
        Instant inicioReserva = itens.stream().map(ItemNormalizado::inicio).min(Instant::compareTo).orElseThrow();
        Instant fimReserva = itens.stream().map(ItemNormalizado::fim).max(Instant::compareTo).orElseThrow();
        boolean pendente = itens.stream().anyMatch(this::exigeAprovacao);
        StatusReserva statusReserva = pendente ? StatusReserva.PENDENTE : StatusReserva.CONFIRMADA;

        Reserva reserva = reservaRepository.saveAndFlush(new Reserva(
                request.solicitanteId(), inicioReserva, fimReserva, statusReserva, request.finalidade()));

        List<Map<String, Object>> itensResposta = new ArrayList<>();
        for (ItemNormalizado item : itens) {
            StatusReserva statusItem = exigeAprovacao(item) ? StatusReserva.PENDENTE : StatusReserva.CONFIRMADA;
            validarDisponibilidade(request.solicitanteId(), item);
            inserirItem(request.solicitanteId(), reserva.getId(), item, statusItem);
            itensResposta.add(Map.of(
                    "resource_type", item.tipoRecurso(),
                    "resource_id", item.recursoId().toString(),
                    "quantity", item.quantidade(),
                    "start", item.inicio().toString(),
                    "end", item.fim().toString(),
                    "status", statusItem.name()));
        }

        namedJdbc.update("""
                INSERT INTO auditoria (usuario_id, entidade, entidade_id, acao, valor_novo)
                VALUES (:usuario, 'reservas', :reserva, 'CRIACAO',
                    jsonb_build_object('status', :status, 'itens', :quantidade))
                """,
                new MapSqlParameterSource()
                        .addValue("usuario", request.solicitanteId())
                        .addValue("reserva", reserva.getId())
                        .addValue("status", statusReserva.name())
                        .addValue("quantidade", itens.size()));

        Map<String, Object> resposta = new LinkedHashMap<>();
        resposta.put("id", reserva.getId().toString());
        resposta.put("solicitante_id", reserva.getSolicitanteId().toString());
        resposta.put("status", statusReserva.name());
        resposta.put("items", itensResposta);
        return resposta;
    }

    private List<ItemNormalizado> normalizar(ReservaRequest request) {
        if (request == null || request.solicitanteId() == null
                || request.finalidade() == null || request.finalidade().isBlank()) {
            throw new IllegalArgumentException("Solicitante e motivo são obrigatórios.");
        }
        if (request.itens() == null || request.itens().isEmpty()) {
            throw new IllegalArgumentException("A reserva deve conter ao menos um item.");
        }

        List<ItemNormalizado> itens = new ArrayList<>();
        for (ReservaItemRequest item : request.itens()) {
            if (item == null || item.resourceType() == null || item.resourceId() == null
                    || item.inicio() == null || item.fim() == null) {
                throw new IllegalArgumentException("Cada item precisa de tipo, recurso e intervalo.");
            }
            if (!item.inicio().isBefore(item.fim())) {
                throw new IllegalArgumentException("O início deve ser anterior ao fim.");
            }
            String tipo = item.resourceType().toLowerCase();
            if (!List.of("sala", "professor", "material").contains(tipo)) {
                throw new IllegalArgumentException("Tipo de recurso inválido.");
            }
            int quantidade = item.quantity() == null ? 1 : item.quantity();
            if (quantidade < 1 || (!tipo.equals("material") && quantidade != 1)) {
                throw new IllegalArgumentException("Quantidade inválida para o tipo de recurso.");
            }
            itens.add(new ItemNormalizado(tipo, item.resourceId(), item.inicio(), item.fim(), quantidade));
        }
        return itens;
    }

    private boolean exigeAprovacao(ItemNormalizado item) {
        if (item.tipoRecurso().equals("professor")) {
            return true;
        }
        if (item.tipoRecurso().equals("material")) {
            Material material = bloquearMaterial(item.recursoId());
            return material.isRestrita();
        }
        Boolean restrita = jdbcTemplate.queryForObject(
                "SELECT restrita FROM salas WHERE id = ? AND ativa = true",
                Boolean.class,
                item.recursoId());
        if (restrita == null) {
            throw new IllegalArgumentException("Sala não encontrada ou inativa.");
        }
        return restrita;
    }

    private void validarDisponibilidade(UUID solicitanteId, ItemNormalizado item) {
        if (item.tipoRecurso().equals("material")) {
            Material material = bloquearMaterial(item.recursoId());
            if (bloqueado(item)) {
                throw conflito(solicitanteId, item, "BLOQUEIO");
            }
            if (material.isRestrita()) {
                return;
            }
            Integer reservado = jdbcTemplate.queryForObject("""
                    SELECT
                        COALESCE((
                            SELECT SUM(quantidade)
                            FROM reserva_itens
                            WHERE material_id = ? AND status IN ('APROVADA', 'CONFIRMADA')
                              AND inicio < ? AND fim > ?
                        ), 0)
                        + COALESCE((
                            SELECT SUM(CASE WHEN movimentacao.tipo = 'RETIRADA'
                                            THEN movimentacao.quantidade
                                            ELSE -movimentacao.quantidade END)
                            FROM retiradas_devolucoes movimentacao
                            JOIN reserva_itens item ON item.id = movimentacao.reserva_item_id
                            WHERE item.material_id = ? AND item.fim <= ?
                        ), 0)
                    """,
                    Integer.class,
                    item.recursoId(), Timestamp.from(item.fim()), Timestamp.from(item.inicio()),
                    item.recursoId(), Timestamp.from(item.inicio()));
            if (item.quantidade() > material.getQuantidadeTotal() - (reservado == null ? 0 : reservado)) {
                throw conflito(solicitanteId, item, "ESTOQUE");
            }
            return;
        }

        if (!recursoAtivo(item)) {
            throw new IllegalArgumentException("Recurso não encontrado ou inativo.");
        }
        if (bloqueado(item)) {
            throw conflito(solicitanteId, item, "BLOQUEIO");
        }
        if (sobreposto(item)) {
            throw conflito(solicitanteId, item, "SOBREPOSICAO");
        }
    }

    private Material bloquearMaterial(UUID id) {
        Material material = materialRepository.bloquearPorId(id)
                .orElseThrow(() -> new IllegalArgumentException("Material não encontrado."));
        if (!material.isAtivo()) {
            throw new IllegalArgumentException("Material inativo.");
        }
        return material;
    }

    private boolean recursoAtivo(ItemNormalizado item) {
        String query = item.tipoRecurso().equals("sala")
                ? "SELECT EXISTS (SELECT 1 FROM salas WHERE id = ? AND ativa = true)"
                : "SELECT EXISTS (SELECT 1 FROM professores WHERE id = ? AND ativo = true)";
        Boolean exists = jdbcTemplate.queryForObject(query, Boolean.class, item.recursoId());
        return Boolean.TRUE.equals(exists);
    }

    private boolean bloqueado(ItemNormalizado item) {
        String coluna = switch (item.tipoRecurso()) {
            case "sala" -> "sala_id";
            case "professor" -> "professor_id";
            case "material" -> "material_id";
            default -> throw new IllegalArgumentException("Tipo de recurso inválido.");
        };
        Boolean exists = jdbcTemplate.queryForObject(
                "SELECT EXISTS (SELECT 1 FROM bloqueios WHERE " + coluna
                        + " = ? AND status = 'ATIVO' AND inicio < ? AND fim > ?)",
                Boolean.class,
                item.recursoId(),
                Timestamp.from(item.fim()),
                Timestamp.from(item.inicio()));
        return Boolean.TRUE.equals(exists);
    }

    private boolean sobreposto(ItemNormalizado item) {
        String coluna = switch (item.tipoRecurso()) {
            case "sala" -> "sala_id";
            case "professor" -> "professor_id";
            default -> throw new IllegalArgumentException("Tipo de recurso não exclusivo.");
        };
        Boolean exists = jdbcTemplate.queryForObject(
                "SELECT EXISTS (SELECT 1 FROM reserva_itens WHERE " + coluna
                        + " = ? AND status IN ('APROVADA', 'CONFIRMADA') AND inicio < ? AND fim > ?)",
                Boolean.class,
                item.recursoId(),
                Timestamp.from(item.fim()),
                Timestamp.from(item.inicio()));
        return Boolean.TRUE.equals(exists);
    }

    private void inserirItem(
            UUID solicitanteId,
            UUID reservaId,
            ItemNormalizado item,
            StatusReserva status) {
        UUID salaId = item.tipoRecurso().equals("sala") ? item.recursoId() : null;
        UUID professorId = item.tipoRecurso().equals("professor") ? item.recursoId() : null;
        UUID materialId = item.tipoRecurso().equals("material") ? item.recursoId() : null;
        try {
            namedJdbc.update("""
                    INSERT INTO reserva_itens
                        (reserva_id, sala_id, professor_id, material_id, inicio, fim, quantidade, status)
                    VALUES
                        (:reserva, :sala, :professor, :material, :inicio, :fim, :quantidade,
                         CAST(:status AS status_reserva_item))
                    """,
                    new MapSqlParameterSource()
                            .addValue("reserva", reservaId)
                            .addValue("sala", salaId)
                            .addValue("professor", professorId)
                            .addValue("material", materialId)
                            .addValue("inicio", Timestamp.from(item.inicio()))
                            .addValue("fim", Timestamp.from(item.fim()))
                            .addValue("quantidade", item.quantidade())
                            .addValue("status", status.name()));
        } catch (DataIntegrityViolationException erro) {
            if (sqlState(erro, "23P01")) {
                throw conflito(solicitanteId, item, "CONCORRENCIA");
            }
            throw erro;
        }
    }

    private ConflitoReservaException conflito(UUID solicitanteId, ItemNormalizado item, String motivo) {
        return new ConflitoReservaException(solicitanteId, item.tipoRecurso(), item.recursoId(),
                item.inicio(), item.fim(), item.quantidade(), motivo);
    }

    private ConflitoReservaException conflitoExclusao(
            ReservaRequest request, List<ItemNormalizado> itens, DataIntegrityViolationException erro) {
        if (!sqlState(erro, "23P01")) {
            return null;
        }
        return conflito(request.solicitanteId(), itens.get(0), "CONCORRENCIA");
    }

    private boolean sqlState(Throwable erro, String esperado) {
        for (Throwable causa = erro; causa != null; causa = causa.getCause()) {
            if (causa instanceof java.sql.SQLException sqlException && esperado.equals(sqlException.getSQLState())) {
                return true;
            }
        }
        return false;
    }

    private record ItemNormalizado(String tipoRecurso, UUID recursoId, Instant inicio, Instant fim, int quantidade) {
    }
}