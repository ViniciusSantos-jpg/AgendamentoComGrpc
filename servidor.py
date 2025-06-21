from concurrent import futures
import grpc
import time
import threading
from queue import Queue
from datetime import datetime, timedelta

import agendamento_pb2
import agendamento_pb2_grpc

banco_de_dados_consultas = []
db_lock = threading.Lock()
subscribers = {} # Dicionário para guardar a fila e o nome do usuário

def notificar_subscribers():
    """Envia a lista de consultas atualizada para cada cliente, com a devida anonimização."""
    with db_lock:
        consultas_originais = list(banco_de_dados_consultas)
    
    for user_queue, requisitante in subscribers.items():
        consultas_sanitizadas = []
        for consulta in consultas_originais:
            # Cria uma cópia da consulta para não alterar o original
            consulta_sanitizada = agendamento_pb2.Consulta()
            consulta_sanitizada.CopyFrom(consulta)
            
            # Anonimiza o nome do paciente se não for o próprio requisitante
            if consulta.paciente != requisitante:
                primeiro_nome = consulta.paciente.split(' ')[0]
                consulta_sanitizada.paciente = primeiro_nome
            
            consultas_sanitizadas.append(consulta_sanitizada)
        
        response = agendamento_pb2.ListarConsultasResponse(consultas=consultas_sanitizadas)
        user_queue.put(response)

class AgendamentoMedicoServicer(agendamento_pb2_grpc.AgendamentoMedicoServicer):
    
    def AgendarConsulta(self, request, context):
        """Implementa a funcionalidade de 'Cadastrar uma consulta' com validação de data."""
        print(f"Requisição para agendar consulta recebida: {request.consulta}")
        
        # Validação de data de 2 anos (LADO DO SERVIDOR)
        try:
            data_agendamento = datetime.strptime(request.consulta.data, '%d/%m/%Y')
            data_limite = datetime.now() + timedelta(days=365*2)
            if data_agendamento > data_limite:
                msg = "Erro: Não é possível agendar com mais de dois anos de antecedência."
                print(msg)
                return agendamento_pb2.AgendarConsultaResponse(mensagem=msg, sucesso=False)
        except ValueError:
            return agendamento_pb2.AgendarConsultaResponse(mensagem="Erro: Formato de data inválido.", sucesso=False)

        with db_lock:
            for consulta in banco_de_dados_consultas:
                if consulta.data == request.consulta.data and consulta.horario == request.consulta.horario:
                    return agendamento_pb2.AgendarConsultaResponse(mensagem="Erro: Horário já agendado.", sucesso=False)
            banco_de_dados_consultas.append(request.consulta)
        
        print("Sucesso: Consulta agendada. Notificando subscribers...")
        notificar_subscribers()
        return agendamento_pb2.AgendarConsultaResponse(mensagem="Consulta agendada com sucesso!", sucesso=True)

    def ListarConsultas(self, request, context):
        """Implementa a funcionalidade de 'Listar todas as consultas salvas'."""
        print(f"Requisição para listar (carga inicial) de {request.nome_do_requisitante} recebida.")
        consultas_sanitizadas = []
        with db_lock:
            for consulta in banco_de_dados_consultas:
                consulta_sanitizada = agendamento_pb2.Consulta()
                consulta_sanitizada.CopyFrom(consulta)
                if consulta.paciente != request.nome_do_requisitante:
                    primeiro_nome = consulta.paciente.split(' ')[0]
                    consulta_sanitizada.paciente = primeiro_nome
                consultas_sanitizadas.append(consulta_sanitizada)
        return agendamento_pb2.ListarConsultasResponse(consultas=consultas_sanitizadas)

    def InscreverParaAtualizacoes(self, request, context):
        requisitante = request.nome_do_requisitante
        print(f"Cliente '{requisitante}' se inscreveu para atualizações.")
        q = Queue()
        subscribers[q] = requisitante
        try:
            while context.is_active():
                response = q.get()
                yield response
        except grpc.RpcError:
            print(f"Cliente '{requisitante}' desconectado.")
        finally:
            print(f"Removendo '{requisitante}' da lista de subscribers.")
            if q in subscribers:
                del subscribers[q]
                
    def CancelarConsulta(self, request, context):
        """Implementa a funcionalidade de 'Cancelar um agendamento'."""
        print(f"Requisição de cancelamento de {request.nome_do_requisitante} para a consulta de {request.paciente} em {request.data} às {request.horario}.")
        removido_com_sucesso = False; mensagem_erro = "Erro: Consulta não encontrada."
        with db_lock:
            consulta_encontrada = None
            for c in banco_de_dados_consultas:
                if c.data == request.data and c.horario == request.horario and c.paciente == request.paciente:
                    consulta_encontrada = c; break
            if consulta_encontrada:
                if consulta_encontrada.paciente == request.nome_do_requisitante:
                    banco_de_dados_consultas.remove(consulta_encontrada); removido_com_sucesso = True
                    print(f"Sucesso: Consulta de {request.paciente} cancelada por {request.nome_do_requisitante}.")
                    notificar_subscribers()
                else:
                    mensagem_erro = "Apenas o paciente que marcou a consulta pode cancelá-la."
                    print(f"Falha na autorização: {request.nome_do_requisitante} tentou cancelar consulta de {consulta_encontrada.paciente}.")
        if removido_com_sucesso: return agendamento_pb2.CancelarConsultaResponse(mensagem="Consulta cancelada com sucesso!", sucesso=True)
        else: return agendamento_pb2.CancelarConsultaResponse(mensagem=mensagem_erro, sucesso=False)

    def VerificarDisponibilidade(self, request, context):
        """Implementa a funcionalidade de 'Ver se um horário está disponível'."""
        print(f"Requisição para verificar disponibilidade em {request.data} às {request.horario}.")
        disponivel = True
        with db_lock:
            for c in banco_de_dados_consultas:
                if c.data == request.data and c.horario == request.horario:
                    disponivel = False; break
        if disponivel: print("Resultado: Disponível.")
        else: print("Resultado: Indisponível.")
        return agendamento_pb2.VerificarDisponibilidadeResponse(disponivel=disponivel)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agendamento_pb2_grpc.add_AgendamentoMedicoServicer_to_server(AgendamentoMedicoServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Iniciando servidor gRPC na porta 50051...")
    server.start(); server.wait_for_termination()

if __name__ == '__main__':
    serve()