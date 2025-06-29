from concurrent import futures
import grpc, os, pickle, threading, uuid
from queue import Queue
from datetime import datetime, timedelta
import agendamento_pb2
import agendamento_pb2_grpc

CONSULTAS_DB_FILE = 'consultas_v3.pkl'
banco_de_dados_consultas = []
db_lock = threading.RLock()
NOME_DO_MEDICO_PADRAO = "Dr. Gregory House"

# Lista de subscribers para a interface do médico
subscribers_medico = []

def carregar_dados():
    global banco_de_dados_consultas
    if os.path.exists(CONSULTAS_DB_FILE):
        with db_lock, open(CONSULTAS_DB_FILE, 'rb') as f:
            banco_de_dados_consultas = pickle.load(f)
            print(f"Carregadas {len(banco_de_dados_consultas)} consultas.")

def salvar_dados():
    with db_lock:
        with open(CONSULTAS_DB_FILE, 'wb') as f:
            pickle.dump(banco_de_dados_consultas, f)
            print(f"\nDados salvos: {len(banco_de_dados_consultas)} consultas.")

def notificar_medicos():
    """Envia a agenda completa e atualizada para todos os médicos conectados."""
    agenda_completa = []
    with db_lock:
        for consulta in banco_de_dados_consultas:
            if consulta.medico == NOME_DO_MEDICO_PADRAO:
                agenda_completa.append(consulta)
        
        # Copia a lista de subscribers para iterar
        subscribers_atuais = list(subscribers_medico)

    agenda_ordenada = sorted(agenda_completa, key=lambda c: (datetime.strptime(c.data, '%d/%m/%Y'), c.horario))
    response = agendamento_pb2.ListarConsultasResponse(consultas=agenda_ordenada)

    for q in subscribers_atuais:
        q.put(response)


class AgendamentoMedicoServicer(agendamento_pb2_grpc.AgendamentoMedicoServicer):
    
    def AgendarConsulta(self, request, context):
        with db_lock:
    
            # Adiciona a consulta
            nova_consulta = agendamento_pb2.Consulta(
                id_consulta=str(uuid.uuid4())[:4],
                paciente=request.paciente,
                cpf_paciente=request.cpf_paciente,
                medico=NOME_DO_MEDICO_PADRAO,
                data=request.data,
                horario=request.horario
            )
            banco_de_dados_consultas.append(nova_consulta)
            
            # Notifica os médicos sobre a nova consulta
            notificar_medicos()
        
        return agendamento_pb2.AgendarConsultaResponse(sucesso=True, mensagem="Consulta agendada com sucesso!", id_consulta_gerado=nova_consulta.id_consulta)

    def CancelarConsulta(self, request, context):
        alvo = None
        removido = False
        with db_lock:
            for c in banco_de_dados_consultas:
                if c.id_consulta == request.id_consulta:
                    alvo = c
                    break
            if alvo:
                banco_de_dados_consultas.remove(alvo)
                removido = True
                # Notifica os médicos sobre o cancelamento
                notificar_medicos()
        
        if removido:
            return agendamento_pb2.GerenciarConsultaResponse(sucesso=True, mensagem="Consulta cancelada com sucesso.")
        return agendamento_pb2.GerenciarConsultaResponse(sucesso=False, mensagem="Consulta não encontrada.")
    
    def InscreverParaAgendaMedico(self, request, context):
        """NOVO: Mantém o cliente do médico atualizado em tempo real."""
        q = Queue()
        with db_lock:
            subscribers_medico.append(q)
        
        print("Interface do médico conectada para atualizações.")

        # Envia a lista inicial assim que se conecta
        notificar_medicos()
        
        try:
            while context.is_active():
                yield q.get()
        finally:
            print("Interface do médico desconectada.")
            with db_lock:
                subscribers_medico.remove(q)

    def ListarAgendaMedico(self, request, context):
        agenda_do_medico = []
        with db_lock:
            for c in banco_de_dados_consultas:
                if c.medico == NOME_DO_MEDICO_PADRAO: agenda_do_medico.append(c)
        agenda_ordenada = sorted(agenda_do_medico, key=lambda c: (datetime.strptime(c.data, '%d/%m/%Y'), c.horario))
        return agendamento_pb2.ListarConsultasResponse(consultas=agenda_ordenada)
    def BuscarConsulta(self, request, context):
        with db_lock:
            for c in banco_de_dados_consultas:
                if c.id_consulta == request.id_consulta: return agendamento_pb2.GerenciarConsultaResponse(sucesso=True, consulta=c)
        return agendamento_pb2.GerenciarConsultaResponse(sucesso=False, mensagem="Consulta não encontrada.")

def serve():
    carregar_dados()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agendamento_pb2_grpc.add_AgendamentoMedicoServicer_to_server(AgendamentoMedicoServicer(), server)
    server.add_insecure_port('[::]:50051'); print("Iniciando servidor gRPC na porta 50051..."); server.start()
    try: server.wait_for_termination()
    finally: salvar_dados()

if __name__ == '__main__':
    serve()