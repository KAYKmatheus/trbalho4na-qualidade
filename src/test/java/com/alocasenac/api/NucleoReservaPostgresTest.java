package com.alocasenac.api;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import org.junit.jupiter.api.Test;
import com.alocasenac.config.AlocaSenacApplication;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@SpringBootTest(classes = AlocaSenacApplication.class,
    webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
class NucleoReservaPostgresTest {

    private static final HttpClient HTTP = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
    private static final int REQUESTS = 12;

    @Container
    private static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine")
            .withDatabaseName("alocasenac_core")
            .withUsername("alocasenac")
            .withPassword("alocasenac");

    @DynamicPropertySource
    static void configurePostgres(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
    }

    @LocalServerPort
    private int port;

    @Autowired
    private JdbcTemplate jdbc;

    @Test
    void ct15RecusaSobreposicaoDaMesmaSala() throws Exception {
        UUID userId = criarSolicitante();
        UUID salaId = criarSala();

        assertEquals(201, reservar(userId, item("sala", salaId, 1, "2031-01-01T09:00:00Z", "2031-01-01T10:00:00Z")));
        assertEquals(409, reservar(userId, item("sala", salaId, 1, "2031-01-01T09:30:00Z", "2031-01-01T10:30:00Z")));
        assertEquals(1, jdbc.queryForObject(
            "SELECT count(*) FROM reserva_itens WHERE sala_id = ?", Integer.class, salaId));
        assertEquals(1, contarConflitos("salas", salaId));
    }

    @Test
    void ct16RecusaSobreposicaoDoMesmoProfessorEmSalasDiferentes() throws Exception {
        UUID userId = criarSolicitante();
        UUID professorId = criarProfessor();
        UUID primeiraSala = criarSala();
        UUID segundaSala = criarSala();
        String inicio = "2031-01-02T09:00:00Z";
        String fim = "2031-01-02T10:00:00Z";

        assertEquals(201, reservar(userId,
                item("sala", primeiraSala, 1, inicio, fim),
                item("professor", professorId, 1, inicio, fim)));
        jdbc.update("UPDATE reserva_itens SET status = 'APROVADA' WHERE professor_id = ?", professorId);

        assertEquals(409, reservar(userId,
                item("sala", segundaSala, 1, inicio, fim),
                item("professor", professorId, 1, inicio, fim)));
        assertEquals(1, jdbc.queryForObject(
            "SELECT count(*) FROM reserva_itens WHERE professor_id = ?", Integer.class, professorId));
        assertEquals(1, jdbc.queryForObject(
            "SELECT count(*) FROM reserva_itens WHERE sala_id IN (?, ?)",
            Integer.class, primeiraSala, segundaSala));
        assertEquals(1, contarConflitos("professores", professorId));
    }

    @Test
    void ct17PermiteReservaAdjacente() throws Exception {
        UUID userId = criarSolicitante();
        UUID salaId = criarSala();

        assertEquals(201, reservar(userId, item("sala", salaId, 1, "2031-01-03T09:00:00Z", "2031-01-03T10:00:00Z")));
        assertEquals(201, reservar(userId, item("sala", salaId, 1, "2031-01-03T10:00:00Z", "2031-01-03T11:00:00Z")));
        assertEquals(2, jdbc.queryForObject(
            "SELECT count(*) FROM reserva_itens WHERE sala_id = ?", Integer.class, salaId));
        assertEquals(0, contarConflitos("salas", salaId));
    }

    @Test
    void ct18RecusaQuantidadeDeMaterialAcimaDoEstoque() throws Exception {
        UUID userId = criarSolicitante();
        UUID materialId = criarMaterial(3);

        assertEquals(201, reservar(userId,
                item("material", materialId, 2, "2031-01-04T09:00:00Z", "2031-01-04T10:00:00Z")));
        assertEquals(409, reservar(userId,
                item("material", materialId, 2, "2031-01-04T09:00:00Z", "2031-01-04T10:00:00Z")));
        assertEquals(2, jdbc.queryForObject(
            "SELECT COALESCE(SUM(quantidade), 0) FROM reserva_itens WHERE material_id = ?",
            Integer.class, materialId));
        assertEquals(1, contarConflitos("materiais", materialId));
    }

    @Test
    void ct19ApenasUmaRequisicaoConcorrenteConfirmaASala() throws Exception {
        UUID userId = criarSolicitante();
        UUID salaId = criarSala();

        List<Integer> statuses = executarConcorrentes(REQUESTS,
                () -> reservar(userId,
                        item("sala", salaId, 1, "2031-01-05T09:00:00Z", "2031-01-05T10:00:00Z")));
        long confirmadas = statuses.stream().filter(status -> status == 201).count();
        long conflitos = statuses.stream().filter(status -> status == 409).count();

        System.out.printf("CT-19 requests=%d confirmed=%d conflicts=%d%n", REQUESTS, confirmadas, conflitos);
        assertEquals(1, confirmadas);
        assertEquals(REQUESTS - 1, conflitos);
        assertEquals(1, jdbc.queryForObject(
            "SELECT count(*) FROM reserva_itens WHERE sala_id = ?", Integer.class, salaId));
        assertEquals(REQUESTS - 1, contarConflitos("salas", salaId));
    }

    @Test
    void ct20RequisicoesConcorrentesNaoExcedemOEstoqueDeMaterial() throws Exception {
        UUID userId = criarSolicitante();
        int estoque = 3;
        UUID materialId = criarMaterial(estoque);

        List<Integer> statuses = executarConcorrentes(REQUESTS,
                () -> reservar(userId,
                        item("material", materialId, 1, "2031-01-06T09:00:00Z", "2031-01-06T10:00:00Z")));
        long confirmadas = statuses.stream().filter(status -> status == 201).count();
        long conflitos = statuses.stream().filter(status -> status == 409).count();

        System.out.printf("CT-20 requests=%d stock=%d confirmed=%d conflicts=%d%n",
                REQUESTS, estoque, confirmadas, conflitos);
        assertEquals(estoque, confirmadas);
        assertEquals(REQUESTS - estoque, conflitos);
        assertEquals(estoque, jdbc.queryForObject(
            "SELECT COALESCE(SUM(quantidade), 0) FROM reserva_itens WHERE material_id = ?",
            Integer.class, materialId));
        assertEquals(REQUESTS - estoque, contarConflitos("materiais", materialId));
    }

    private List<Integer> executarConcorrentes(int quantidade, RequestCall request) throws Exception {
        ExecutorService executor = Executors.newFixedThreadPool(quantidade);
        CountDownLatch prontos = new CountDownLatch(quantidade);
        CountDownLatch inicio = new CountDownLatch(1);
        List<Future<Integer>> futures = new ArrayList<>();

        try {
            for (int indice = 0; indice < quantidade; indice++) {
                futures.add(executor.submit(() -> {
                    prontos.countDown();
                    if (!inicio.await(30, TimeUnit.SECONDS)) {
                        throw new IllegalStateException("Timeout aguardando início concorrente");
                    }
                    return request.invoke();
                }));
            }
            assertTrue(prontos.await(30, TimeUnit.SECONDS), "Todas as requisições devem estar prontas");
            inicio.countDown();

            List<Integer> statuses = new ArrayList<>(quantidade);
            for (Future<Integer> future : futures) {
                statuses.add(future.get(60, TimeUnit.SECONDS));
            }
            return statuses;
        } finally {
            inicio.countDown();
            executor.shutdownNow();
            assertTrue(executor.awaitTermination(10, TimeUnit.SECONDS), "Pool concorrente deve encerrar");
        }
    }

    private int reservar(UUID solicitanteId, String... itens) throws Exception {
        String corpo = "{\"solicitante_id\":\"" + solicitanteId
                + "\",\"reason\":\"Reserva CT\",\"items\":[" + String.join(",", itens) + "]}";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("http://localhost:" + port + "/v1/reservations"))
                .timeout(Duration.ofSeconds(30))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(corpo))
                .build();
        HttpResponse<String> response = HTTP.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() == 201 && !corpo.contains("\"resource_type\":\"professor\"")) {
            assertTrue(response.body().contains("\"status\":\"CONFIRMADA\""),
                "Reserva sem professor aceita deve estar confirmada");
        }
        return response.statusCode();
    }

    private static String item(String tipo, UUID recursoId, int quantidade, String inicio, String fim) {
        return "{\"resource_type\":\"" + tipo + "\",\"resource_id\":\"" + recursoId
                + "\",\"quantity\":" + quantidade + ",\"start\":\"" + inicio
                + "\",\"end\":\"" + fim + "\"}";
    }

    private UUID criarSolicitante() {
        return jdbc.queryForObject(
                "INSERT INTO usuarios (nome, email, senha_hash, perfil) VALUES (?, ?, ?, 'SOLICITANTE') RETURNING id",
                UUID.class,
                "Solicitante CT",
                "ct-" + UUID.randomUUID() + "@example.test",
                "hash");
    }

    private UUID criarSala() {
        return jdbc.queryForObject(
                "INSERT INTO salas (nome, tipo, capacidade, localizacao) VALUES (?, 'AULA', 20, 'Bloco A') RETURNING id",
                UUID.class,
                "Sala CT " + UUID.randomUUID());
    }

    private UUID criarProfessor() {
        return jdbc.queryForObject(
                "INSERT INTO professores (nome) VALUES (?) RETURNING id",
                UUID.class,
                "Professor CT " + UUID.randomUUID());
    }

    private UUID criarMaterial(int quantidade) {
        return jdbc.queryForObject(
                "INSERT INTO materiais (nome, tipo, quantidade_total) VALUES (?, 'EQUIPAMENTO', ?) RETURNING id",
                UUID.class,
                "Material CT " + UUID.randomUUID(),
                quantidade);
    }

    private int contarConflitos(String entidade, UUID recursoId) {
        Integer total = jdbc.queryForObject(
                "SELECT count(*) FROM auditoria WHERE acao = 'CONFLITO_EVITADO' AND entidade = ? AND entidade_id = ?",
                Integer.class,
                entidade,
                recursoId);
        return total == null ? 0 : total;
    }

    @FunctionalInterface
    private interface RequestCall {
        int invoke() throws Exception;
    }
}