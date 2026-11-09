Cada parâmetro do treino, agrupado por onde aparece.

## Dados

| Parâmetro | Valor | O que é | Efeito de mudar |
|---|---|---|---|
| `d.data / 16.0` | divide por 16 | Os pixels do dataset vão de 0 a 16. Dividir normaliza para 0 a 1. | Sem isso, entradas grandes saturam a sigmoide e o treino quase não anda. |
| `np.eye(10)[d.target]` | one-hot | Transforma o rótulo (ex: `3`) em vetor `[0,0,0,1,0,0,0,0,0,0]`. | É o formato que a saída da rede (10 neurônios) espera comparar. |
| `test_size` | `0.2` | 20% das imagens ficam reservadas só para testar (360 de 1797). | Mais teste dá uma medida mais confiável, mas deixa menos dados para treinar. |
| `random_state` | `0` | Semente do sorteio que separa treino e teste. | Fixa a divisão, então todo mundo testa nas mesmas imagens. Mudar o número muda quais imagens caem no teste. |

## Arquitetura

| Parâmetro | Valor | O que é | Efeito de mudar |
|---|---|---|---|
| `layer_sizes` | `[64, 32, 10]` | 64 entradas (8x8 pixels), uma camada oculta de 32 neurônios, 10 saídas (dígitos 0 a 9). | Entrada e saída são fixas pelo problema. Só a camada oculta é livre: mais neurônios dão mais capacidade, mas treino mais lento e risco de decorar os dados. |
| Inicialização | `randn * sqrt(1/n_entradas)` | Os pesos começam aleatórios, com escala proporcional ao número de entradas da camada. | Com `* 0.01` o treino fica muito mais lento. Os vieses começam em zero. |
| Ativação | sigmoide | Aplicada em todas as camadas, inclusive na saída. | Cada saída vira um valor independente entre 0 e 1 (por isso as 10 não somam 1). |

## Treinamento

| Parâmetro | Valor | O que é | Efeito de mudar |
|---|---|---|---|
| `epochs` | `3000` | Número de passos de aprendizado. Como o treino usa todos os exemplos de uma vez, cada época é um `forward` + `backward` completo. | Poucas épocas deixam a rede sem aprender (underfitting). Muitas só melhoram até certo ponto, e a perda para de cair. |
| `lr` (taxa de aprendizado) | `0.5` | O tamanho de cada ajuste nos pesos: `W -= lr * dW`. | Muito alto: a perda oscila ou explode. Muito baixo: aprende devagar. Com sigmoide, valores entre 0,1 e 1 costumam funcionar. |
| `verbose` | `True` | Imprime a perda a cada 500 épocas. | Só afeta a exibição. |

## Parâmetros que existem de forma implícita

- **Tamanho do lote (batch):** é o conjunto de treino inteiro (1437 imagens) em cada passo, o chamado *batch gradient descent*. Alternativas como mini-batch podem aprender mais rápido, mas exigem alterar o `train`.
- **Função de perda:** o `train` imprime o **MSE** (`mean((A - y)²)`), mas o gradiente usado no `backward` (`A - y`) é o da **entropia cruzada**. Os dois caem juntos, então o número impresso serve para acompanhar, mas não é exatamente o que está sendo otimizado.
- **Semente dos pesos:** `np.random.randn` **não tem semente fixa**. É por isso que suas duas execuções deram acurácias diferentes (0,969 e 0,975) com o mesmo `random_state`. A divisão treino/teste era a mesma, mas os pesos iniciais mudaram.

Para resultados reproduzíveis, coloque no início do `cv.py`:

```python
np.random.seed(0)
```

## Como interpretar seus resultados

A perda caiu de 0,25 para 0,0025 e ainda descia ao final, e a acurácia no teste ficou em 97%. Isso indica que a rede aprendeu bem. Para ver se vale ajustar algo, compare também a acurácia **no treino** com a do teste: se o treino estiver em 100% e o teste bem abaixo, a rede está decorando, e convém reduzir a camada oculta ou parar antes. Se os dois estiverem parecidos, mais épocas ou mais neurônios ainda podem ajudar.

Posso colocar essa documentação como docstrings dentro do `train` e da classe, no seu `ml.py`, ou montar um pequeno experimento que varie `lr` e `layer_sizes` e mostre o efeito na acurácia.