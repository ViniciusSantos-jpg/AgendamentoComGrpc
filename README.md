# Sistema de Agendamento Médico Distribuído com gRPC

Este projeto é uma implementação de um sistema de agendamento médico distribuído, desenvolvido como parte do trabalho da disciplina de Sistemas Distribuídos. O sistema utiliza um modelo cliente-servidor, onde múltiplos clientes podem interagir com um servidor central para gerenciar consultas médicas de forma segura e em tempo real.

A comunicação entre os componentes é realizada através do **gRPC (Google Remote Procedure Call)**, que garante uma comunicação leve, rápida e segura. O sistema se enquadra na categoria de **Objetos ou Componentes Distribuídos** , abstraindo detalhes de comunicação, localização e heterogeneidade para o desenvolvedor e usuário final.

## Funcionalidades Principais

- **Arquitetura Cliente-Servidor:** Um servidor central em Python gerencia os dados e a lógica de negócio, enquanto múltiplos clientes com interface gráfica interagem com ele.

- **Comunicação Real-Time:** Clientes são notificados em tempo real sobre novos agendamentos ou cancelamentos através de *gRPC Streaming*, mantendo a lista de todos os clientes sempre sincronizada.

- **Identificação e Autorização:** Ao iniciar, o cliente solicita o nome do usuário. O sistema utiliza essa identidade para garantir que um usuário só possa cancelar os próprios agendamentos, implementando uma regra de negócio sobre a funcionalidade de 'Cancelar um agendamento'.

- **Privacidade e Visualização Aprimorada:** Para a funcionalidade de 'Listar todas as consultas salvas', a tela principal anonimiza o nome de outros pacientes para proteger a privacidade. A listagem é feita em uma tabela organizada e há uma aba dedicada "Meus Agendamentos" para uma visão focada do próprio usuário.

- **Validação Robusta:** O sistema valida o 'cadastro de consultas'  em múltiplas camadas:
    - Validação de formato e restrição de entrada nos campos de data e hora.
    - Validação lógica de datas/horários (ex: não permite 31/02).
    - Regras de negócio, como não permitir agendamentos no passado ou com mais de dois anos de antecedência.

- **Interface Gráfica Moderna:** Interface desenvolvida com Python, usando a biblioteca padrão Tkinter e o tema `ttkbootstrap` para uma experiência de usuário agradável, portátil e que não depende de navegador.

## Tecnologias Utilizadas

- **Linguagem:** Python 3
- **Comunicação:** gRPC (`grpcio`, `grpcio-tools`)
- **Serialização de Dados:** Protocol Buffers
- **Interface Gráfica:** Tkinter com `ttkbootstrap`

## Pré-requisitos

- Python 3.8 ou superior
- `pip` (gerenciador de pacotes do Python)

## Instalação

1.  Clone este repositório ou baixe e coloque todos os arquivos do projeto (`servidor.py`, `cliente_gui.py`, `agendamento.proto`, `requirements.txt`) em um mesmo diretório.

2.  Abra um terminal nesse diretório e crie um ambiente virtual (recomendado):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  Instale todas as bibliotecas necessárias usando o arquivo `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

## Como Executar

A execução do sistema é feita em 3 passos, nesta ordem:

### 1. Gerar o Código gRPC

Este passo compila o arquivo `.proto`, que define a comunicação, em código Python. **Ele só precisa ser executado uma vez**, ou sempre que o arquivo `agendamento.proto` for modificado.

No seu terminal (com o `venv` ativado), execute:
```bash
venv/bin/python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. agendamento.proto
```

### 2. Iniciar o Servidor

O servidor precisa estar rodando para que os clientes possam se conectar a ele.

No seu terminal (com o `venv` ativado), execute:
```bash
venv/bin/python servidor.py
```
Você verá uma mensagem `Iniciando servidor gRPC na porta 50051...`. **Deixe este terminal aberto.**

### 3. Iniciar o(s) Cliente(s)

Você pode iniciar quantas instâncias do cliente quiser para simular múltiplos usuários.

Abra um **novo terminal** para cada cliente, navegue até a pasta do projeto, ative o ambiente virtual (`source venv/bin/activate`) e rode o comando:
```bash
venv/bin/python cliente_gui.py
```
Ao ser executado, o cliente abrirá uma caixa de diálogo pedindo o seu nome completo. Este nome será usado como sua identidade para agendar e cancelar consultas. Para testar as funcionalidades de privacidade e atualização em tempo real, inicie pelo menos dois clientes com nomes diferentes.
