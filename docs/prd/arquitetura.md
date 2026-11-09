# Arquitetura — Sistema acadêmico de reservas

**Status:** Proposta

## 1. Drivers arquiteturais

Os principales drivers de arquitetura do sistema são:

- Segurança e autorização por perfil e por escopo
- Integridade de reserva e concorrência em operações simultâneas
- Auditoria imutável e rastreabilidade das decisões
- Disponibilidade e resiliência de materiais, salas e professores
- Desempenho de leitura e consulta de disponibilidade
- Manutenibilidade da documentação e das regras de negócio
- Acessibilidade e clareza das mensagens para as personas
- Implantabilidade em ambientes institucionais com pouca dependência de infraestrutura específica

## 2. Estilo arquitetural

O sistema adota um estilo arquitetural em camadas com separação explícita entre:

- Apresentação: interface do usuário e fluxos de interação
- API: contratos de entrada e saída, autenticação e validação de perfil
- Aplicação: regras de negócio, orquestração, validação de disponibilidade e autorização
- Dados: persistência, auditoria, índices, regras de integridade e consultas

Além disso, o desenho mantém uma orientação de domínio por caso de uso: reservas, aprovações, bloqueios, movimentações de materiais, auditoria e relatórios. A camada de aplicação centraliza decisões de negócio relevantes e reduz dispersão de regras no frontend ou no banco.

## 3. Visão de execução

A execução principal é organizada em três ciclos:

1. Solicitação e validação
   - autenticado por perfil e escopo
   - validação de campos e disponibilidade
   - rejeição por conflito ou autorização insuficiente

2. Decisão e confirmação
   - aprovação de recursos restritos
   - validação de docente para itens com professor
   - persistência da reserva ou item pendente

3. Execução operacional e rastreio
   - movimentação de materiais
   - bloqueios e manutenção
   - auditoria e notificações
   - geração de relatórios

## 4. Visão de implantação

O ambiente de implantação é organizado em quatro blocos:

- Frontend: interface web responsiva e mensagens claras
- API: camada de aplicação e orquestração de regras
- Banco de dados: armazenamento relacional com regras de integridade, auditoria append-only e índices para consulta de disponibilidade
- Observabilidade e operação: logs, auditoria, métricas e relatórios

Em termos de implantação, o sistema deve operar em um ambiente institucional com:

- banco relacional suporte PostgreSQL
- execução em ambiente de homologação e produção com configuração documentada
- separação entre dados operacionais e histórico auditável
- backup e restauração gerenciados por política institucional

## 5. Táticas por atributo de qualidade

### 5.1 Segurança

- autenticação por perfil
- checagem de autorização no servidor
- escopo do Responsável em tabela de domínio
- regras de acesso por recurso e por pessoa

### 5.2 Integridade e concorrência

- transações para criação e aprovação de reservas
- validação de conflitos em sala, professor e material
- lock de linha ou transação para estoque e disponibilidade
- auditoria de conflito evitado

### 5.3 Desempenho

- índices por intervalo de reservas, recursos e status
- consultas agregadas para disponibilidade e relatórios
- desacoplamento entre visualização e regras de negócio pesadas

### 5.4 Usabilidade

- mensagens claras e consistentes por código de erro
- feedback de estados pendentes, aprovados, rejeitados e bloqueados
- interface adaptativa para desktop e mobile

### 5.5 Confiabilidade

- consistência de transações e registro em auditoria
- definições de disponibilidade com RPO/RTO propostos
- tratamento de falhas sem deixar estado parcial

### 5.6 Manutenibilidade

- documentação persistente dos requisitos e fluxos
- separação por módulos e regras de negócio explícitas
- modelagem de domínio alinhada ao DBML

### 5.7 Portabilidade

- implantação com variáveis e configuração documentadas
- ausência de dependência de host local específico
- compatibilidade com ambientes suportados pela instituição

## 6. Trade-offs e riscos

### Trade-offs

- Consistência forte e concorrência rigorosa aumentam complexidade operacional, mas reduzem risco de alocação indevida.
- Auditoria imutável exige mais armazenamento e disciplina de escrita, mas aumenta rastreabilidade.
- Escopo do Responsável torna a regra mais segura, mas exige manutenção do mapeamento por recurso.
- Interface responsiva e mensagens claras reduzem ambiguidade, mas demandam mais esforço de UX e ciclos de validação.

### Riscos

- Escopo do Responsável mal definido gera negação indevida de deciões.
- Conflito de reservas concorrentes sem transação correta pode causar sobreposição em produção.
- Falta de política de manutenção do bloqueio gera recursos indisponíveis sem mecanismo claro.
- Alterações em regras sem atualização documental podem tornar requisitos inconsistentes.

## 7. Derivação de requisitos para arquitetura

A arquitetura foi desenhada para suportar diretamente:

- FR-01 a FR-16
- RN01 a RN10
- NFR-01 a NFR-12

Os principais vínculos de arquitetura passam por:

- validação de disponibilidade e conflitos: FR-03, FR-04, FR-06, FR-07, FR-09, FR-10
- autorização e escopo: FR-01, FR-08, FR-16
- auditoria e rastreabilidade: FR-11, FR-12, FR-13
- documentação e interface: FR-14, FR-15

## 8. ADRs vinculadas

- [ADR-01: Integridade e concorrência em reservas](./adr-01-integridade-concorrencia.md)
- [ADR-02: Escopo do Responsável](./adr-02-escopo-responsavel.md)
- [ADR-03: Auditoria imutável e conflito evitado](./adr-03-auditoria-imutavel.md)
- [ADR-04: Controle de disponibilidade de materiais e recursos](./adr-04-disponibilidade-material.md)
- [ADR-05: API e separação de camadas](./adr-05-api-e-separacao-de-camadas.md)
