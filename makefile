# Define o interpretador Python a ser usado, pegando o do ambiente virtual.
# O padrão é 'python3' se o venv ainda não existir.
PYTHON = venv/bin/python

# --- Alvos Principais ---

help:
	@echo "----------------------------------------------------------------"
	@echo "Makefile do Projeto de Agendamento Médico com gRPC"
	@echo "----------------------------------------------------------------"
	@echo "Comandos disponíveis:"
	@echo "  make setup          -> Cria o ambiente virtual e instala as dependências."
	@echo "  make proto          -> Gera o código Python a partir do arquivo .proto."
	@echo "  make run            -> (Apenas Linux com gnome-terminal) Inicia tudo em abas separadas."
	@echo "  make run-server     -> Inicia apenas o servidor."
	@echo "  make run-client     -> Inicia apenas o cliente do paciente."
	@echo "  make run-doctor     -> Inicia apenas o cliente do médico."
	@echo "  make clean          -> Apaga o ambiente virtual e arquivos gerados."
	@echo "----------------------------------------------------------------"


setup: venv/bin/pip
	@echo "Ambiente virtual pronto e dependências instaladas."


venv/bin/pip: requirements.txt
	python3 -m venv venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt


proto: agendamento_pb2.py agendamento_pb2_grpc.py
	@echo "Código gRPC gerado com sucesso."


agendamento_pb2.py agendamento_pb2_grpc.py: agendamento.proto
	@echo "Gerando código a partir do agendamento.proto..."
	$(PYTHON) -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. agendamento.proto


run-server: proto
	@echo "Iniciando o servidor gRPC..."
	$(PYTHON) servidor.py


run-client: proto
	@echo "Iniciando o cliente do paciente..."
	$(PYTHON) cliente_gui.py


run-doctor: proto
	@echo "Iniciando o cliente do médico..."
	$(PYTHON) medico_gui.py

# comando específico para o 'gnome-terminal'.
run: proto
	@echo "Iniciando servidor e clientes em abas separadas..."
	@echo "Aguarde alguns segundos para as janelas abrirem."
	gnome-terminal --tab --title="Servidor gRPC" -- bash -c "$(PYTHON) servidor.py; exec bash"
	@sleep 2 # Pequena pausa para o servidor iniciar antes dos clientes
	gnome-terminal --tab --title="Cliente Paciente" -- bash -c "$(PYTHON) cliente_gui.py; exec bash"
	gnome-terminal --tab --title="Cliente Médico" -- bash -c "$(PYTHON) medico_gui.py; exec bash"

clean:
	@echo "Limpando o diretório do projeto..."
	rm -rf venv __pycache__ *.pyc *.pkl *.pkl.bak
	rm -f agendamento_pb2.py agendamento_pb2_grpc.py agendamento_pb2.pyi
	@echo "Limpeza concluída."

.PHONY: help setup proto run run-server run-client run-doctor clean