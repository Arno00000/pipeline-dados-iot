# Roteiro do vídeo pitch (até 4 minutos)

> Dica: deixe abertos antes de gravar o VS Code com o projeto, o terminal e o dashboard em http://localhost:8501.

## 0:00–0:30 — O problema
**Tela:** você na câmera ou o título do dashboard.

"Oi, eu sou o [seu nome] e este é o meu projeto de Disruptive Architectures. Sensores IoT geram leitura o tempo todo, mas um arquivo cheio de números não diz muita coisa. Não dá pra ver tendência, nem se o sensor parou de mandar dado. A ideia aqui foi montar um pipeline que pega dados reais de um sensor de temperatura e transforma isso num dashboard que qualquer pessoa entende."

## 0:30–1:10 — Arquitetura e tecnologias
**Tela:** README, na seção Arquitetura.

"O fluxo é esse: o dataset vem do Kaggle em CSV, o Python com Pandas faz a limpeza, os dados vão para um PostgreSQL rodando no Docker, eu crio três views SQL em cima da tabela e o Streamlit com Plotly lê essas views e monta o dashboard. O banco sobe com um único comando, `docker compose up -d`, e a senha fica num arquivo `.env`, fora do GitHub. A conexão do Python com o banco é feita com SQLAlchemy."

## 1:10–2:00 — Processamento dos dados
**Tela:** terminal rodando `python src/load_data.py` e depois o `views.sql`.

"Antes de escrever código eu olhei o CSV de verdade, e ainda bem: ele não tem a coluna device_id do exemplo. São 97.606 leituras de uma sala só, com um sensor interno e um externo, de julho a dezembro de 2018. A data vem no formato dia-mês-ano, então eu converti com o formato explícito pra não trocar dia por mês. Não tinha nulo, mas tinha uma linha duplicada, que o script removeu. Ficaram 97.605 registros no banco. E o script pode rodar várias vezes sem duplicar nada, porque ele recarrega a tabela numa transação só. Em cima disso eu criei três views: temperatura por ambiente, leituras por hora e temperatura por dia."

## 2:00–3:10 — Demonstração do dashboard
**Tela:** dashboard, interagindo.

"Esse é o dashboard. Em cima ficam os indicadores: total de leituras, média, máxima e mínima. No primeiro gráfico dá pra ver que o lado de fora é mais quente e varia muito mais, olha o tamanho dessa barrinha de desvio. O segundo mostra quantas leituras chegam em cada hora, e se eu passar o mouse aparece a temperatura média daquela hora. No terceiro eu acompanho máxima, média e mínima de cada dia, e posso trocar entre interno e externo [clicar]. Repara nesses saltos: são dias em que o sensor simplesmente não mandou nada. Na lateral eu filtro por período e por faixa de temperatura [mudar o período para outubro], e os indicadores e o histograma se atualizam na hora."

## 3:10–3:40 — Principais insights
**Tela:** gráfico 3 (externo) ou a seção Insights do README.

"O que os dados mostraram: o ambiente externo teve média de 36,3 graus contra 30,4 dentro da sala. Do fim de setembro em diante a temperatura externa subiu uns 9 graus de média. E o mais interessante pra IoT: só teve leitura em 86 dos 134 dias, e um único dia concentrou 21% de todos os dados. Isso é sinal de falha de conexão ou de envio em lote, que é justamente o tipo de coisa que um pipeline desses ajuda a enxergar."

## 3:40–4:00 — Conclusão
**Tela:** repositório no GitHub.

"No fim, o projeto junta ingestão, armazenamento, consulta e visualização, tudo reproduzível com Docker e um README passo a passo. O código está no GitHub, o link está na descrição. Obrigado!"
