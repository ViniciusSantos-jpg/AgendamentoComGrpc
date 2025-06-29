# Sistema de Agendamento Médico Distribuído com gRPC

Este projeto é uma implementação de um sistema distribuído para agendamento de consultas médicas, utilizando uma arquitetura cliente-servidor e a tecnologia gRPC para comunicação.  O sistema foi projetado para ser robusto e demonstrar conceitos-chave de sistemas distribuídos, como chamadas de procedimento remotas, concorrência e diferentes visões de dados para diferentes tipos de usuários.

## Funcionalidades Principais

O ecossistema é composto por um servidor central e duas aplicações cliente distintas: uma para pacientes e outra para o médico.

### Cliente do Paciente (`cliente_gui.py`)
- **Agendamento Anônimo:** Não requer login ou criação de conta. O usuário simplesmente preenche seus dados para 'Cadastrar uma consulta'. 
- **Gerenciamento por Código Único:** Ao agendar, o sistema gera um código único de 4 caracteres. O paciente utiliza este código para 'Cancelar um agendamento' ou buscar os detalhes da sua consulta, garantindo a privacidade e a segurança do acesso. 
- **Interface Intuitiva:** Desenvolvida com `ttkbootstrap`, a 'interface com campos de entrada e botões para interação'  possui formatação automática de nomes, datas e horários, além de validação para evitar a entrada de dados incorretos.

### Cliente do Médico (`medico_gui.py`)
- **Visão da Agenda em Tempo Real:** A principal funcionalidade é uma tela de visualização que lista todas as consultas do médico, ordenadas por data e hora. 
- **Atualização Automática (Streaming):** Utilizando o 'suporte nativo a streaming de dados' do gRPC, a agenda do médico é atualizada instantaneamente sempre que um paciente agenda ou cancela uma consulta, sem a necessidade de atualização manual.
- **Acesso Direto:** A interface não requer login. Ela abre e exibe diretamente a agenda do médico padrão configurado no servidor, focando na simplicidade de uso.

### Servidor (`servidor.py`)
- **Lógica de Negócio Centralizada:** O servidor impõe todas as regras do sistema, como:
    - Impedir agendamentos em horários já ocupados.
    - Garantir um intervalo mínimo de 15 minutos entre as consultas.
    - Não permitir agendamentos no passado ou com mais de 2 anos de antecedência.
- **Persistência de Dados:** Embora utilize uma lista em memória para alta velocidade durante a execução,  o servidor salva todos os agendamentos em um arquivo (`consultas_v3.pkl`) ao ser encerrado, e os carrega na inicialização. Isso garante que os dados não sejam perdidos entre as sessões.
- **Geração de Código:** Responsável por criar o código único para cada novo agendamento.

### Automação (`Makefile`)
- **Fluxo de Trabalho Simplificado:** Um `Makefile` foi criado para automatizar todo o processo de instalação de dependências, compilação do `.proto` e execução dos clientes e do servidor com comandos simples.

## Tecnologias Utilizadas

- **Linguagem:** Python 3
- **Comunicação:** gRPC (`grpcio`, `grpcio-tools`)
- **Serialização de Dados:** Protocol Buffers 
- **Interface Gráfica:** Tkinter com `ttkbootstrap` 

## Pré-requisitos

- Python 3.8 ou superior
- `pip` (gerenciador de pacotes do Python)

## Instalação

1.  Clone este repositório ou baixe todos os arquivos do projeto em um mesmo diretório.

2.  Abra um terminal nesse diretório e execute o comando de setup do `Makefile`. Ele criará o ambiente virtual e instalará todas as dependências automaticamente.
    ```bash
    make setup
    ```
    *(Se o comando `make` não for encontrado, certifique-se de que ele está instalado no seu sistema. Em sistemas Debian/Ubuntu: `sudo apt install build-essential`)*

## Como Executar

Com o `Makefile`, a execução do projeto é muito simples.

### Opção 1: Rodar Tudo Automaticamente (Recomendado para Testes)

Este comando compila os arquivos necessários e abre três novas abas no seu terminal: uma para o servidor, uma para o cliente do paciente e uma para o cliente do médico.

```bash
make run
```
**Atenção:** Este comando é otimizado para o `gnome-terminal`, o padrão do Ubuntu. Se você usa outro emulador de terminal, talvez precise ajustar o comando dentro do `Makefile`.

### Opção 2: Rodar as Partes Separadamente

Você também pode controlar cada parte individualmente em terminais diferentes.

1.  **Terminal 1 - Servidor:**
    ```bash
    make run-server
    ```
    Deixe este terminal aberto.

2.  **Terminal 2 - Cliente do Paciente:**
    ```bash
    make run-client
    ```

3.  **Terminal 3 - Cliente do Médico:**
    ```bash
    make run-doctor
    ```

### Outros Comandos Úteis

-   `make proto`: Força a recompilação do arquivo `.proto` (útil se você fizer alterações manuais nele).
-   `make clean`: Apaga o ambiente virtual, os arquivos de cache e os arquivos gerados pelo gRPC. Útil para começar uma instalação do zero.
