# B3 Value investing

Desenvolvimento de um Dashboard para tomada de decisão relativas a
ações da B3 (Bovespa).

O trabalho foi uma adaptação da idéia do [Vicent Tatan](https://github.com/VincentTatan/ValueInvesting) utilizando as técnicas do livro [Gone Fishing with (Warren Buffett) - Sean Seah](http://valueinvesting-sg.com/ebook/GoneFishingWithBuffett.pdf)

## Link do deploy no HerokuApp
[https://b3valueinvesting.herokuapp.com/]

## Principais Bibliotecas Utilizadas:
* Dash
* BeautifulSoup
* UrlLib3
* Selenium
* Pandas
* Numpy


## Scrapping das informações das ações
Lista das ações e nomes das empresas
* Obtendo os dados do Yahoo Finanças

## Valor das ações ao longo do tempo
* Utilização do Pandas DataReader para obter os dados

## Dados de Balanço Fiscal e Financeiros utilizando Selenium
* EPS
* ROE
* ROA
* Dívida de Longo Prazo
* Lucro Líquido
* Patrimônio Líquido
* EBIT

## Lista de alertas baseados na proposta de Sean Seah
* Avaliar a viabilidade do investimento de uma companhia:
    * Estar no mercado há mais de 10 anos
    * Ter alta eficiência (ROE > 15%)
    * Ter bom retorno sobre ativos (ROA > 7%)
    * Ter pequena dívida de longo prazo

## Máquina de Decisão baseada em Preço Marginal do EPS
* Tomada de decisão de cada empresa em termos de taxa de retorno, dada a metodologia de Sean Seah
    * Encontrar a taxa anual de crescimento composta por EPS
    * Estimatimar o EPS daqui a 5 anos
    * Estimativa do preço das ações daqui a 5 anos (Valor EPS da ação * P/E médio)
    * Determine a meta por preço hoje com base nos retornos (taxa de desconto de 15% / 20%)
    * Adicione margem de segurança (rede de segurança 15%)
    * Compre se o preço de mercado for menor que o preço marginal
    * Venda se o preço de mercado for superior ao preço marginal

#### Aviso Legal: O autor não se responsabiliza por erros, omissões ou pelos resultados obtidos com o uso dessas informações.
