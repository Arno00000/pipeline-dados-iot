-- =====================================================================
-- Views SQL do Pipeline IoT
-- Tabela base: temperature_readings
--   reading_id  TEXT       id único da leitura (coluna "id" do CSV)
--   room_id     TEXT       sala do sensor ("room_id/id" do CSV)
--   noted_at    TIMESTAMP  data/hora da leitura ("noted_date", DD-MM-YYYY HH:MM)
--   temperature SMALLINT   temperatura em °C ("temp")
--   location    TEXT       'In' (interno) ou 'Out' (externo) ("out/in")
-- O script src/load_data.py executa este arquivo automaticamente.
-- =====================================================================


-- ---------------------------------------------------------------------
-- VIEW 1: temperatura_media_ambiente
-- O que faz: resume as leituras por ambiente (In = interno, Out = externo):
--            quantidade, média, mínima, máxima e desvio padrão.
-- Dados:     location e temperature de todas as leituras.
-- Relevância: compara o comportamento térmico dentro e fora da sala,
--            mostrando o quanto o ambiente interno é mais estável.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW temperatura_media_ambiente AS
SELECT
    location                              AS ambiente,
    COUNT(*)                              AS quantidade_leituras,
    ROUND(AVG(temperature)::numeric, 2)   AS temperatura_media,
    MIN(temperature)                      AS temperatura_minima,
    MAX(temperature)                      AS temperatura_maxima,
    ROUND(STDDEV(temperature)::numeric, 2) AS desvio_padrao
FROM temperature_readings
GROUP BY location;


-- ---------------------------------------------------------------------
-- VIEW 2: leituras_por_hora
-- O que faz: conta as leituras e calcula a temperatura média em cada
--            hora do dia (0 a 23), separadas por ambiente.
-- Dados:     noted_at (hora extraída), location e temperature.
-- Relevância: mostra em que horários os sensores mais enviam dados e
--            como a temperatura varia ao longo do dia.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW leituras_por_hora AS
SELECT
    EXTRACT(HOUR FROM noted_at)::int      AS hora,
    location                              AS ambiente,
    COUNT(*)                              AS quantidade_leituras,
    ROUND(AVG(temperature)::numeric, 2)   AS temperatura_media
FROM temperature_readings
GROUP BY EXTRACT(HOUR FROM noted_at), location
ORDER BY hora, ambiente;


-- ---------------------------------------------------------------------
-- VIEW 3: temperatura_por_dia
-- O que faz: para cada dia e ambiente, traz mínima, máxima, média e
--            quantidade de leituras.
-- Dados:     noted_at (data), location e temperature.
-- Relevância: permite acompanhar a evolução da temperatura no tempo e
--            identificar dias atípicos ou sem coleta de dados.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW temperatura_por_dia AS
SELECT
    DATE(noted_at)                        AS data,
    location                              AS ambiente,
    MIN(temperature)                      AS temperatura_minima,
    MAX(temperature)                      AS temperatura_maxima,
    ROUND(AVG(temperature)::numeric, 2)   AS temperatura_media,
    COUNT(*)                              AS quantidade_leituras
FROM temperature_readings
GROUP BY DATE(noted_at), location
ORDER BY data, ambiente;
