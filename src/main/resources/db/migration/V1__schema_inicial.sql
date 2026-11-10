CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TYPE perfil_usuario AS ENUM ('ADMIN', 'RESPONSAVEL', 'SOLICITANTE');
CREATE TYPE status_reserva AS ENUM ('PENDENTE', 'APROVADA', 'CONFIRMADA', 'CANCELADA', 'REJEITADA');
CREATE TYPE status_reserva_item AS ENUM ('PENDENTE', 'APROVADA', 'CONFIRMADA', 'CANCELADA', 'REJEITADA');
CREATE TYPE tipo_decisao AS ENUM ('RECURSO_RESTRITO', 'VALIDACAO_DOCENTE');
CREATE TYPE decisao_aprovacao AS ENUM ('APROVADA', 'REJEITADA');
CREATE TYPE tipo_bloqueio AS ENUM ('BLOQUEIO', 'MANUTENCAO');
CREATE TYPE status_bloqueio AS ENUM ('ATIVO', 'CANCELADO', 'CONCLUIDO');
CREATE TYPE tipo_movimentacao_material AS ENUM ('RETIRADA', 'DEVOLUCAO');
CREATE TYPE status_notificacao AS ENUM ('PENDENTE', 'ENVIADA', 'LIDA', 'FALHOU');

CREATE TABLE usuarios (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nome varchar(200) NOT NULL,
    email varchar(320) NOT NULL UNIQUE,
    senha_hash text NOT NULL,
    perfil perfil_usuario NOT NULL,
    ativo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE salas (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nome varchar(160) NOT NULL,
    tipo varchar(80) NOT NULL,
    capacidade integer NOT NULL CHECK (capacidade > 0),
    localizacao varchar(240) NOT NULL,
    restrita boolean NOT NULL DEFAULT false,
    ativa boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE recursos_tecnicos (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nome varchar(120) NOT NULL UNIQUE,
    descricao text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE professores (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id uuid UNIQUE REFERENCES usuarios(id) ON DELETE RESTRICT,
    nome varchar(200) NOT NULL,
    email varchar(320) UNIQUE,
    ativo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE competencias (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nome varchar(160) NOT NULL UNIQUE,
    descricao text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE materiais (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nome varchar(200) NOT NULL,
    tipo varchar(100) NOT NULL,
    quantidade_total integer NOT NULL CHECK (quantidade_total >= 0),
    restrito boolean NOT NULL DEFAULT false,
    ativo boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sala_recursos_tecnicos (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sala_id uuid NOT NULL REFERENCES salas(id) ON DELETE CASCADE,
    recurso_tecnico_id uuid NOT NULL REFERENCES recursos_tecnicos(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_sala_recurso_tecnico UNIQUE (sala_id, recurso_tecnico_id)
);

CREATE TABLE professor_competencias (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    professor_id uuid NOT NULL REFERENCES professores(id) ON DELETE CASCADE,
    competencia_id uuid NOT NULL REFERENCES competencias(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_professor_competencia UNIQUE (professor_id, competencia_id)
);

CREATE TABLE reservas (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    solicitante_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    inicio timestamptz NOT NULL,
    fim timestamptz NOT NULL,
    status status_reserva NOT NULL DEFAULT 'PENDENTE',
    versao integer NOT NULL DEFAULT 1,
    finalidade text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_reservas_intervalo CHECK (inicio < fim),
    CONSTRAINT ck_reservas_versao CHECK (versao > 0)
);

CREATE FUNCTION manter_versao_reserva() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        NEW.versao := COALESCE(NEW.versao, 1);
    ELSIF NEW.versao = OLD.versao THEN
        NEW.versao := OLD.versao + 1;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_manter_versao_reserva
    BEFORE INSERT OR UPDATE ON reservas
    FOR EACH ROW EXECUTE FUNCTION manter_versao_reserva();

CREATE TABLE reserva_itens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    reserva_id uuid NOT NULL REFERENCES reservas(id) ON DELETE RESTRICT,
    sala_id uuid REFERENCES salas(id) ON DELETE RESTRICT,
    professor_id uuid REFERENCES professores(id) ON DELETE RESTRICT,
    material_id uuid REFERENCES materiais(id) ON DELETE RESTRICT,
    inicio timestamptz NOT NULL,
    fim timestamptz NOT NULL,
    quantidade integer NOT NULL DEFAULT 1,
    status status_reserva_item NOT NULL DEFAULT 'PENDENTE',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_reserva_itens_intervalo CHECK (inicio < fim),
    CONSTRAINT ck_reserva_itens_recurso CHECK (num_nonnulls(sala_id, professor_id, material_id) = 1),
    CONSTRAINT ck_reserva_itens_quantidade CHECK (
        (material_id IS NOT NULL AND quantidade > 0)
        OR (material_id IS NULL AND quantidade = 1)
    )
);

CREATE TABLE aprovacoes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    reserva_item_id uuid NOT NULL REFERENCES reserva_itens(id) ON DELETE RESTRICT,
    responsavel_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    tipo tipo_decisao NOT NULL,
    decisao decisao_aprovacao NOT NULL,
    justificativa text NOT NULL,
    decidido_em timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_aprovacoes_justificativa CHECK (length(trim(justificativa)) > 0)
);

CREATE TABLE bloqueios (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sala_id uuid REFERENCES salas(id) ON DELETE RESTRICT,
    professor_id uuid REFERENCES professores(id) ON DELETE RESTRICT,
    material_id uuid REFERENCES materiais(id) ON DELETE RESTRICT,
    tipo tipo_bloqueio NOT NULL,
    inicio timestamptz NOT NULL,
    fim timestamptz NOT NULL,
    motivo text NOT NULL,
    status status_bloqueio NOT NULL DEFAULT 'ATIVO',
    criado_por uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_bloqueios_intervalo CHECK (inicio < fim),
    CONSTRAINT ck_bloqueios_recurso CHECK (num_nonnulls(sala_id, professor_id, material_id) = 1)
);

CREATE TABLE retiradas_devolucoes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    reserva_item_id uuid NOT NULL REFERENCES reserva_itens(id) ON DELETE RESTRICT,
    responsavel_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    tipo tipo_movimentacao_material NOT NULL,
    quantidade integer NOT NULL CHECK (quantidade > 0),
    ocorrido_em timestamptz NOT NULL DEFAULT now(),
    observacao text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE auditoria (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id uuid REFERENCES usuarios(id) ON DELETE RESTRICT,
    origem varchar(20) NOT NULL DEFAULT 'USUARIO',
    entidade varchar(100) NOT NULL,
    entidade_id uuid NOT NULL,
    acao varchar(40) NOT NULL,
    valor_anterior jsonb,
    valor_novo jsonb,
    ocorrido_em timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE notificacoes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    reserva_id uuid REFERENCES reservas(id) ON DELETE RESTRICT,
    assunto varchar(200) NOT NULL,
    mensagem text NOT NULL,
    status status_notificacao NOT NULL DEFAULT 'PENDENTE',
    data timestamptz NOT NULL DEFAULT now(),
    enviada_em timestamptz,
    lida_em timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE escopos_responsavel (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    responsavel_id uuid NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    sala_id uuid REFERENCES salas(id) ON DELETE RESTRICT,
    professor_id uuid REFERENCES professores(id) ON DELETE RESTRICT,
    material_id uuid REFERENCES materiais(id) ON DELETE RESTRICT,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_escopos_responsavel_recurso CHECK (
        num_nonnulls(sala_id, professor_id, material_id) = 1
    ),
    CONSTRAINT uq_escopo_responsavel_sala UNIQUE (responsavel_id, sala_id),
    CONSTRAINT uq_escopo_responsavel_professor UNIQUE (responsavel_id, professor_id),
    CONSTRAINT uq_escopo_responsavel_material UNIQUE (responsavel_id, material_id)
);

CREATE FUNCTION validar_intervalo_item_reserva() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM reservas r
        WHERE r.id = NEW.reserva_id
          AND r.inicio <= NEW.inicio
          AND NEW.fim <= r.fim
    ) THEN
        RAISE EXCEPTION 'Intervalo do item deve estar contido no intervalo da reserva'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validar_intervalo_item_reserva
    BEFORE INSERT OR UPDATE OF reserva_id, inicio, fim ON reserva_itens
    FOR EACH ROW EXECUTE FUNCTION validar_intervalo_item_reserva();

CREATE FUNCTION validar_intervalo_itens_reserva() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM reserva_itens i
        WHERE i.reserva_id = NEW.id
          AND (i.inicio < NEW.inicio OR NEW.fim < i.fim)
    ) THEN
        RAISE EXCEPTION 'Intervalo da reserva deve conter os intervalos dos itens'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validar_intervalo_itens_reserva
    BEFORE UPDATE OF inicio, fim ON reservas
    FOR EACH ROW EXECUTE FUNCTION validar_intervalo_itens_reserva();

CREATE FUNCTION validar_reserva_com_item() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    target_reserva_id uuid;
BEGIN
    target_reserva_id := COALESCE(NEW.id, OLD.id);
    IF EXISTS (SELECT 1 FROM reservas r WHERE r.id = target_reserva_id)
       AND NOT EXISTS (
           SELECT 1 FROM reserva_itens i WHERE i.reserva_id = target_reserva_id
       ) THEN
        RAISE EXCEPTION 'Reserva deve possuir ao menos um item'
            USING ERRCODE = '23514';
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_reserva_deve_possuir_item
    AFTER INSERT ON reservas DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION validar_reserva_com_item();

CREATE CONSTRAINT TRIGGER trg_reserva_nao_pode_ficar_sem_item
    AFTER DELETE ON reserva_itens DEFERRABLE INITIALLY DEFERRED
    FOR EACH ROW EXECUTE FUNCTION validar_reserva_com_item();

CREATE INDEX idx_salas_tipo_capacidade ON salas (tipo, capacidade);
CREATE INDEX idx_salas_localizacao ON salas (localizacao);
CREATE INDEX idx_salas_ativa_restrita ON salas (ativa, restrita);
CREATE INDEX idx_sala_recursos_tecnicos_recurso ON sala_recursos_tecnicos (recurso_tecnico_id);
CREATE INDEX idx_professores_ativo_nome ON professores (ativo, nome);
CREATE INDEX idx_professor_competencias_competencia ON professor_competencias (competencia_id);
CREATE INDEX idx_materiais_tipo_ativo ON materiais (tipo, ativo);
CREATE INDEX idx_materiais_nome ON materiais (nome);
CREATE INDEX idx_reservas_solicitante_created ON reservas (solicitante_id, created_at);
CREATE INDEX idx_reservas_status_intervalo ON reservas (status, inicio, fim);
CREATE INDEX idx_reserva_itens_reserva ON reserva_itens (reserva_id);
CREATE INDEX idx_reserva_itens_sala_status_intervalo ON reserva_itens (sala_id, status, inicio, fim);
CREATE INDEX idx_reserva_itens_professor_status_intervalo ON reserva_itens (professor_id, status, inicio, fim);
CREATE INDEX idx_reserva_itens_material_status_intervalo ON reserva_itens (material_id, status, inicio, fim);
CREATE INDEX idx_aprovacoes_item_tipo_decidido ON aprovacoes (reserva_item_id, tipo, decidido_em);
CREATE INDEX idx_aprovacoes_responsavel_decidido ON aprovacoes (responsavel_id, decidido_em);
CREATE INDEX idx_bloqueios_sala_status_intervalo ON bloqueios (sala_id, status, inicio, fim);
CREATE INDEX idx_bloqueios_professor_status_intervalo ON bloqueios (professor_id, status, inicio, fim);
CREATE INDEX idx_bloqueios_material_status_intervalo ON bloqueios (material_id, status, inicio, fim);
CREATE INDEX idx_movimentacoes_item_ocorrido ON retiradas_devolucoes (reserva_item_id, ocorrido_em);
CREATE INDEX idx_movimentacoes_responsavel_ocorrido ON retiradas_devolucoes (responsavel_id, ocorrido_em);
CREATE INDEX idx_auditoria_entidade_ocorrido ON auditoria (entidade, entidade_id, ocorrido_em);
CREATE INDEX idx_auditoria_usuario_ocorrido ON auditoria (usuario_id, ocorrido_em);
CREATE INDEX idx_notificacoes_usuario_status_data ON notificacoes (usuario_id, status, data);
CREATE INDEX idx_notificacoes_reserva_data ON notificacoes (reserva_id, data);

ALTER TABLE reserva_itens
    ADD CONSTRAINT ex_reserva_itens_sala_intervalo
    EXCLUDE USING gist (sala_id WITH =, tstzrange(inicio, fim, '[)') WITH &&)
    WHERE (status IN ('APROVADA', 'CONFIRMADA'));

ALTER TABLE reserva_itens
    ADD CONSTRAINT ex_reserva_itens_professor_intervalo
    EXCLUDE USING gist (professor_id WITH =, tstzrange(inicio, fim, '[)') WITH &&)
    WHERE (status IN ('APROVADA', 'CONFIRMADA'));

CREATE FUNCTION impedir_alteracao_append_only() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Tabela % e append-only', TG_TABLE_NAME
        USING ERRCODE = '55000';
END;
$$;

CREATE TRIGGER trg_aprovacoes_append_only
    BEFORE UPDATE OR DELETE ON aprovacoes
    FOR EACH ROW EXECUTE FUNCTION impedir_alteracao_append_only();

CREATE TRIGGER trg_auditoria_append_only
    BEFORE UPDATE OR DELETE ON auditoria
    FOR EACH ROW EXECUTE FUNCTION impedir_alteracao_append_only();