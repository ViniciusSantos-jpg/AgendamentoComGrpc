# Sistema de Agendamento Médico Distribuído com gRPC

Este projeto é uma implementação de um sistema de agendamento médico distribuído, desenvolvido como parte do trabalho da disciplina de Sistemas Distribuídos. O sistema utiliza um modelo cliente-servidor, onde múltiplos clientes podem interagir com um servidor central para gerenciar consultas médicas.

A comunicação entre os componentes é realizada através do **gRPC (Google Remote Procedure Call)**, que garante uma comunicação leve, rápida e segura. O sistema é classificado como de **Objetos ou Componentes Distribuídos**, e abstrai detalhes de comunicação, localização e heterogeneidade para o desenvolvedor e usuário final.

## Funcionalidades

- **Arquitetura Cliente-Servidor:** Um servidor central gerencia os dados e múltiplos clientes com interface gráfica interagem com ele.
- **Comunicação Real-Time:** Clientes são notificados em tempo real sobre novos agendamentos ou cancelamentos através de *gRPC Streaming*, mantendo a lista de todos os clientes sempre sincronizada.
- **Interface Gráfica Moderna:** Interface desenvolvida com Python e a biblioteca `ttkbootstrap` para uma experiência de usuário agradável e intuitiva, sem a necessidade de um navegador web.
- **Gerenciamento de Consultas:**
    - Cadastrar uma nova consulta com dados de paciente, médico, data e horário.
    - Cancelar um agendamento existente através da seleção na lista.
    - Listar todas as consultas salvas em uma tabela organizada.
    - Verificar a disponibilidade de um horário específico.
- **Validação de Dados no Cliente:**
    - **Validação de Formato:** Formatação automática e restrição de entrada para campos de data (DD/MM/AAAA) e horário (HH:MM).
    - **Validação Lógica:** O sistema impede o agendamento de datas ou horários inválidos e de datas/horários que já passaram.

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
    python -m venv venv
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

No seu terminal, execute:
```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. agendamento.proto
```

### 2. Iniciar o Servidor

O servidor precisa estar rodando para que os clientes possam se conectar a ele.

Em um terminal, execute:
```bash
python servidor.py
```
Você verá uma mensagem `Iniciando servidor gRPC na porta 50051...`. **Deixe este terminal aberto.**

### 3. Iniciar o(s) Cliente(s)

Você pode iniciar quantas instâncias do cliente quiser para simular múltiplos usuários acessando o sistema simultaneamente.

Abra um **novo terminal** para cada cliente que desejar executar e, no diretório do projeto, rode o comando:
```bash
python cliente_gui.py
```
A interface gráfica do sistema será iniciada. Para testar a atualização em tempo real, abra pelo menos duas janelas de cliente e realize um agendamento em uma para ver a lista da outra ser atualizada automaticamente.
