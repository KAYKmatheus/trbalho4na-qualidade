package com.alocasenac.persistencia;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers
class MigracaoFlywayPostgresTest {

    @Container
    private static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine")
            .withDatabaseName("alocasenac")
            .withUsername("alocasenac")
            .withPassword("alocasenac");

    @BeforeAll
    static void aplicarMigracoes() {
        Flyway.configure()
                .dataSource(POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword())
                .locations("classpath:db/migration")
                .load()
                .migrate();
    }

    @Test
    void aplicaV1ComTabelasIntegridadeEExtensao() throws SQLException {
        try (Connection connection = abrirConexao(); Statement statement = connection.createStatement()) {
            Set<String> tabelas;
            try (ResultSet result = statement.executeQuery(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")) {
                tabelas = coletarPrimeiraColuna(result);
            }

            assertTrue(tabelas.containsAll(Set.of(
                    "usuarios", "salas", "recursos_tecnicos", "sala_recursos_tecnicos",
                    "professores", "competencias", "professor_competencias", "materiais",
                    "reservas", "reserva_itens", "aprovacoes", "bloqueios",
                    "retiradas_devolucoes", "auditoria", "notificacoes", "escopos_responsavel")));

            try (ResultSet result = statement.executeQuery(
                    "SELECT extname FROM pg_extension WHERE extname = 'btree_gist'")) {
                assertTrue(result.next());
            }
            try (ResultSet result = statement.executeQuery(
                    "SELECT conname FROM pg_constraint WHERE contype = 'x'")) {
                assertEquals(Set.of("ex_reserva_itens_sala_intervalo", "ex_reserva_itens_professor_intervalo"),
                        coletarPrimeiraColuna(result));
            }
            try (ResultSet result = statement.executeQuery(
                    "SELECT version FROM flyway_schema_history WHERE success AND version = '1'")) {
                assertTrue(result.next());
            }
        }
    }

    @Test
    void rejeitaSobreposicaoAtivaDeSalaMasAceitaIntervaloAdjacente() throws SQLException {
        try (Connection connection = abrirConexao(); Statement statement = connection.createStatement()) {
            String usuarioId = inserirUsuario(statement);
            String salaId = inserirSala(statement);
            connection.setAutoCommit(false);
            inserirReservaComItem(statement, usuarioId, salaId, "2030-01-01 09:00:00+00", "2030-01-01 10:00:00+00");
            connection.commit();

            SQLException conflito = assertThrows(SQLException.class,
                    () -> inserirReservaComItem(statement, usuarioId, salaId,
                            "2030-01-01 09:30:00+00", "2030-01-01 10:30:00+00"));
            assertEquals("23P01", conflito.getSQLState());
            connection.rollback();

            inserirReservaComItem(statement, usuarioId, salaId, "2030-01-01 10:00:00+00", "2030-01-01 11:00:00+00");
            connection.commit();
        }
    }

    @Test
    void impedeUpdateEDeleteEmAprovacoesEAuditoria() throws SQLException {
        try (Connection connection = abrirConexao(); Statement statement = connection.createStatement()) {
            String usuarioId = inserirUsuario(statement);
            String salaId = inserirSala(statement);
            connection.setAutoCommit(false);
            String itemId = inserirReservaComItem(statement, usuarioId, salaId,
                    "2030-02-01 09:00:00+00", "2030-02-01 10:00:00+00");
            connection.commit();
            connection.setAutoCommit(true);
            String aprovacaoId = inserirAprovacao(statement, itemId, usuarioId);
            String auditoriaId = inserirAuditoria(statement, usuarioId);

            assertAppendOnly(statement, "aprovacoes", aprovacaoId);
            assertAppendOnly(statement, "auditoria", auditoriaId);
        }
    }

    private static void assertAppendOnly(Statement statement, String table, String id) {
        for (String operation : new String[] {"UPDATE %s SET created_at = now() WHERE id = '%s'",
                "DELETE FROM %s WHERE id = '%s'"}) {
            SQLException error = assertThrows(SQLException.class,
                    () -> statement.executeUpdate(operation.formatted(table, id)));
            assertEquals("55000", error.getSQLState());
        }
    }

    private static Connection abrirConexao() throws SQLException {
        return DriverManager.getConnection(POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword());
    }

    private static String inserirUsuario(Statement statement) throws SQLException {
        return inserirEObterId(statement, "INSERT INTO usuarios (nome, email, senha_hash, perfil) "
                + "VALUES ('Solicitante', 'solicitante-" + UUID.randomUUID()
                + "@example.test', 'hash', 'SOLICITANTE') RETURNING id");
    }

    private static String inserirSala(Statement statement) throws SQLException {
        return inserirEObterId(statement, "INSERT INTO salas (nome, tipo, capacidade, localizacao) "
                + "VALUES ('Sala 1', 'AULA', 20, 'Bloco A') RETURNING id");
    }

    private static String inserirReservaComItem(Statement statement, String usuarioId, String salaId,
            String inicio, String fim) throws SQLException {
        String reservaId = inserirEObterId(statement, "INSERT INTO reservas "
                + "(solicitante_id, inicio, fim, status, finalidade) VALUES ('" + usuarioId + "', '"
                + inicio + "', '" + fim + "', 'PENDENTE', 'Aula') RETURNING id");
        return inserirEObterId(statement, "INSERT INTO reserva_itens "
                + "(reserva_id, sala_id, inicio, fim, status) VALUES ('" + reservaId + "', '" + salaId
                + "', '" + inicio + "', '" + fim + "', 'APROVADA') RETURNING id");
    }

    private static String inserirAprovacao(Statement statement, String itemId, String usuarioId) throws SQLException {
        return inserirEObterId(statement, "INSERT INTO aprovacoes "
                + "(reserva_item_id, responsavel_id, tipo, decisao, justificativa) VALUES ('" + itemId
                + "', '" + usuarioId + "', 'RECURSO_RESTRITO', 'APROVADA', 'Autorizado') RETURNING id");
    }

    private static String inserirAuditoria(Statement statement, String usuarioId) throws SQLException {
        return inserirEObterId(statement, "INSERT INTO auditoria "
                + "(usuario_id, entidade, entidade_id, acao) VALUES ('" + usuarioId
                + "', 'salas', gen_random_uuid(), 'CRIACAO') RETURNING id");
    }

    private static String inserirEObterId(Statement statement, String sql) throws SQLException {
        try (ResultSet result = statement.executeQuery(sql)) {
            assertTrue(result.next());
            return result.getString(1);
        }
    }

    private static Set<String> coletarPrimeiraColuna(ResultSet result) throws SQLException {
        Set<String> values = new HashSet<>();
        try (result) {
            while (result.next()) {
                values.add(result.getString(1));
            }
        }
        return values;
    }
}