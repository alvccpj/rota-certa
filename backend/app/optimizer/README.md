# Módulo de otimização

Este pacote concentrará o componente de Tópicos Avançados.

Implementações previstas:

- linha de base sequencial com vizinho mais próximo;
- refinamento de rota com 2-opt;
- distribuição do cálculo de múltiplos entregadores com processos independentes;
- coleta de tempo de execução, distância total, quantidade de pedidos e número de workers;
- comparação reproduzível entre as versões sequencial e paralela.

A interface do módulo deverá receber entregadores, pedidos e uma matriz de distâncias e retornar rotas ordenadas acompanhadas das métricas da execução.
