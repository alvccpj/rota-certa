# Módulo de otimização

Este pacote implementa a primeira evolução prática do componente de Tópicos
Avançados. A proposta usa otimização de processamento e paralelização; não
depende de uma funcionalidade superficial de inteligência artificial.

Implementações disponíveis:

- linha de base sequencial com vizinho mais próximo;
- refinamento de rota com 2-opt;
- distribuição do cálculo de múltiplos entregadores com processos independentes;
- coleta de tempo de execução, distância total, quantidade de pedidos e número de workers;
- comparação reproduzível entre as versões sequencial e paralela.

A API expõe `POST /optimizer/compare`. O endpoint recebe o depósito e as paradas
previamente atribuídas a cada entregador, executa a mesma heurística nos dois
modos e retorna rotas, distâncias, tempos, número de workers, speedup e uma
verificação de equivalência.

Os testes podem ser executados na raiz do repositório:

```bash
python -m unittest discover backend/tests -v
```
