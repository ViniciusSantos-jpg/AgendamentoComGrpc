from concurrent import futures
import grpc
import time
import threading
from queue import Queue

import agendamento_pb2
import agendamento_pb2_grpc

# Lista em memória para armazenar as consultas
banco_de_dados_consultas = []
# Lock para garantir que o acesso à lista seja seguro entre múltiplas threads
db_lock = threading.Lock()
# Lista para manter as filas de atualização de cada cliente inscrito
subscribers = []

def notificar_subscribers():
    """Envia a lista de consultas atualizada para todos os clientes inscritos."""
    with db_lock:
        response = agendamento_pb2.ListarConsultasResponse(consultas=banco_de_dados_consultas)
    
    for q in subscribers:
        q.put(response)

class AgendamentoMedicoServicer(agendamento_pb2_grpc.AgendamentoMedicoServicer):
    def AgendarConsulta(self, request, context):
        print(f"Requisição para agendar consulta recebida: {request.consulta}")
        
        with db_lock:
            for consulta in banco_de_dados_consultas:
                if consulta.data == request.consulta.data and consulta.horario == request.consulta.horario:
                    print("Falha: Horário indisponível.")
                    return agendamento_pb2.AgendarConsultaResponse(
                        mensagem="Erro: Horário já agendado.",
                        sucesso=False
                    )

            banco_de_dados_consultas.append(request.consulta)
        
        print("Sucesso: Consulta agendada. Notificando subscribers...")
        notificar_subscribers() # NOVO: Notifica todos sobre a mudança
        return agendamento_pb2.AgendarConsultaResponse(
            mensagem="Consulta agendada com sucesso!",
            sucesso=True
        )

    def ListarConsultas(self, request, context):
        print("Requisição para listar consultas (carga inicial) recebida.")
        with db_lock:
            return agendamento_pb2.ListarConsultasResponse(consultas=banco_de_dados_consultas)

    def CancelarConsulta(self, request, context):
        print(f"Requisição de cancelamento para {request.paciente} em {request.data} às {request.horario}.")
        
        removido = False
        with db_lock:
            consulta_para_remover = None
            for consulta in banco_de_dados_consultas:
                if (consulta.paciente == request.paciente and
                    consulta.data == request.data and
                    consulta.horario == request.horario):
                    consulta_para_remover = consulta
                    break
            
            if consulta_para_remover:
                banco_de_dados_consultas.remove(consulta_para_remover)
                removido = True
        
        if removido:
            print("Sucesso: Consulta cancelada. Notificando subscribers...")
            notificar_subscribers() # NOVO: Notifica todos sobre a mudança
            return agendamento_pb2.CancelarConsultaResponse(
                mensagem="Consulta cancelada com sucesso!",
                sucesso=True
            )
        else:
            print("Falha: Consulta não encontrada.")
            return agendamento_pb2.CancelarConsultaResponse(
                mensagem="Erro: Consulta não encontrada para cancelamento.",
                sucesso=False
            )
            
    def InscreverParaAtualizacoes(self, request, context):
        """Função de streaming que mantém o cliente atualizado."""
        print("Novo cliente se inscreveu para atualizações.")
        q = Queue()
        subscribers.append(q)

        try:
            while context.is_active():
                # Espera por uma nova atualização na fila
                response = q.get()
                yield response
        except grpc.RpcError:
            print("Cliente desconectado.")
        finally:
            # Garante que a fila do cliente seja removida da lista ao desconectar
            print("Removendo cliente da lista de subscribers.")
            subscribers.remove(q)

    # Função VerificarDisponibilidade não precisa de mudanças
    def VerificarDisponibilidade(self, request, context):
        # ... (código igual ao anterior)
        print(f"Requisição para verificar disponibilidade em {request.data} às {request.horario}.")
        disponivel = True
        with db_lock:
            for consulta in banco_de_dados_consultas:
                if consulta.data == request.data and consulta.horario == request.horario:
                    disponivel = False
                    break
        
        if disponivel:
            print("Resultado: Disponível.")
        else:
            print("Resultado: Indisponível.")
        return agendamento_pb2.VerificarDisponibilidadeResponse(disponivel=disponivel)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agendamento_pb2_grpc.add_AgendamentoMedicoServicer_to_server(
        AgendamentoMedicoServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    print("Iniciando servidor gRPC na porta 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()