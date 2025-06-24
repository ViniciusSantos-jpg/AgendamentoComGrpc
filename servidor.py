from concurrent import futures
import grpc
import os
import pickle
import threading
from datetime import datetime, timedelta
import uuid # Para gerar códigos únicos

import agendamento_pb2
import agendamento_pb2_grpc

CONSULTAS_DB_FILE = 'consultas_v2.pkl'
banco_de_dados_consultas = []
db_lock = threading.RLock()

def carregar_dados():
    global banco_de_dados_consultas
    with db_lock:
        if os.path.exists(CONSULTAS_DB_FILE):
            with open(CONSULTAS_DB_FILE, 'rb') as f:
                banco_de_dados_consultas = pickle.load(f)
                print(f"Carregadas {len(banco_de_dados_consultas)} consultas do arquivo.")

def salvar_dados():
    with db_lock:
        print("\nSalvando dados antes de encerrar...")
        with open(CONSULTAS_DB_FILE, 'wb') as f:
            pickle.dump(banco_de_dados_consultas, f)
            print(f"- {len(banco_de_dados_consultas)} consultas salvas em {CONSULTAS_DB_FILE}")

class AgendamentoMedicoServicer(agendamento_pb2_grpc.AgendamentoMedicoServicer):
    
    def AgendarConsulta(self, request, context):
        """Implementa a funcionalidade de 'Cadastrar uma consulta' e gera um código."""
        try:
            horario_agendamento = datetime.strptime(f"{request.data} {request.horario}", '%d/%m/%Y %H:%M')
            if horario_agendamento < datetime.now(): return agendamento_pb2.AgendarConsultaResponse(sucesso=False, mensagem="Erro: Não é possível agendar em datas ou horários passados.")
            if horario_agendamento > datetime.now() + timedelta(days=365*2): return agendamento_pb2.AgendarConsultaResponse(sucesso=False, mensagem="Erro: Não é possível agendar com mais de dois anos de antecedência.")
        except ValueError: return agendamento_pb2.AgendarConsultaResponse(sucesso=False, mensagem="Erro: Formato de data ou horário inválido.")

        with db_lock:
            for consulta_existente in banco_de_dados_consultas:
                if consulta_existente.data == request.data and consulta_existente.horario == request.horario:
                    return agendamento_pb2.AgendarConsultaResponse(sucesso=False, mensagem="Erro: Horário já agendado.")
            
            # --- MUDANÇA AQUI ---
            # Reduzido para 4 caracteres, conforme solicitado.
            novo_id = str(uuid.uuid4())[:4]
            
            nova_consulta = agendamento_pb2.Consulta(
                id_consulta=novo_id,
                paciente=request.paciente,
                medico=request.medico,
                data=request.data,
                horario=request.horario
            )
            banco_de_dados_consultas.append(nova_consulta)
        
        return agendamento_pb2.AgendarConsultaResponse(
            sucesso=True, 
            mensagem="Consulta agendada com sucesso! Guarde seu código.",
            id_consulta_gerado=novo_id
        )

    def BuscarConsulta(self, request, context):
        with db_lock:
            for consulta in banco_de_dados_consultas:
                if consulta.id_consulta == request.id_consulta:
                    return agendamento_pb2.GerenciarConsultaResponse(sucesso=True, consulta=consulta)
        return agendamento_pb2.GerenciarConsultaResponse(sucesso=False, mensagem="Consulta não encontrada.")

    def CancelarConsulta(self, request, context):
        """Implementa a funcionalidade de 'Cancelar um agendamento' usando o código."""
        consulta_para_remover = None
        with db_lock:
            for consulta in banco_de_dados_consultas:
                if consulta.id_consulta == request.id_consulta:
                    consulta_para_remover = consulta
                    break
            
            if consulta_para_remover:
                banco_de_dados_consultas.remove(consulta_para_remover)
                return agendamento_pb2.GerenciarConsultaResponse(sucesso=True, mensagem="Consulta cancelada com sucesso.")
        
        return agendamento_pb2.GerenciarConsultaResponse(sucesso=False, mensagem="Consulta não encontrada ou já cancelada.")


def serve():
    carregar_dados()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agendamento_pb2_grpc.add_AgendamentoMedicoServicer_to_server(AgendamentoMedicoServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Iniciando servidor gRPC na porta 50051...")
    server.start()
    try:
        server.wait_for_termination()
    finally:
        salvar_dados()

if __name__ == '__main__':
    serve()