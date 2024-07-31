# Esteira Seletora de Peças

Este projeto consiste em uma esteira seletora de peças que identifica inconformidades usando Arduino, um servo motor, uma câmera para captura de imagens e uma IA em Python com TensorFlow/Keras para categorização das peças. O sistema utiliza um servidor Flask para comunicação e controle entre os componentes.

## Funcionalidades

- **Captura de Imagens**: A câmera captura imagens das peças conforme passam pela esteira.
- **Identificação de Categorias**: A IA categoriza as peças em diferentes classes, incluindo categorias para peças com inconformidades.
- **Controle de Servos**: O Arduino recebe sinais do servidor via porta serial para controlar servo motores que movem aletas para separar as peças.
- **Interface Web**: Um site usando Vite.js exibe a imagem da câmera em tempo real e mostra a contagem de cada categoria de peças, assim como a porcentagem de peças em cada categoria.

## Componentes Utilizados

- Arduino
- Servo motor
- Câmera para captura de imagens
- TensorFlow/Keras para IA em Python
- Flask para o servidor de controle
- Vite.js para a interface web

## Dataset

O dataset utilizado consiste em cubos de Lego com diferenças de cores e padrões, totalizando 3000 imagens.

## Participantes do Projeto

- [Vinícius Lima](https://github.com/ViniMSLima)
- [Luiz Rosa](https://github.com/luizblank)

## Relatórios

Os relatórios gerados incluem:
- Data e hora da identificação da inconformidade.
- Imagem da peça com inconformidade.
- Descrição da peça.
- Outras informações relevantes ainda a serem definidas.

## Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).
