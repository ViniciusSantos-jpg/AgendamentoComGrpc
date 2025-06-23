# ... (imports iguais)
from concurrent import futures
import grpc
import time
import threading
from queue import Queue
from datetime import datetime, timedelta
import agendamento_pb2
import agendamento_pb2_grpc


# --- BANCOS DE DADOS EM MEMÓRIA ---
banco_de_dados_consultas = []
# NOVO: Dicionário para armazenar {cpf: nome_completo}
usuarios_cadastrados = {} 
db_lock = threading.Lock()
subscribers = {}

# ... (notificar_subscribers igual à versão anterior, com anonimização por CPF)
def notificar_subscribers():
    with db_lock:
        consultas_originais = list(banco_de_dados_consultas)
    for user_queue, cpf_requisitante in subscribers.items():
        consultas_sanitizadas = []
        for consulta in consultas_originais:
            cs = agendamento_pb2.Consulta(); cs.CopyFrom(consulta)
            if cs.cpf_paciente != cpf_requisitante: cs.paciente = cs.paciente.split(' ')[0]
            consultas_sanitizadas.append(cs)
        response = agendamento_pb2.ListarConsultasResponse(consultas=consultas_sanitizadas)
        user_queue.put(response)


class AgendamentoMedicoServicer(agendamento_pb2_grpc.AgendamentoMedicoServicer):
    
    # --- NOVA FUNÇÃO DE LOGIN ---
    def Login(self, request, context):
        cpf = request.cpf
        nome = request.nome
        print(f"Tentativa de login/registro para o CPF: {cpf}")

        with db_lock:
            # Usuário já existe?
            if cpf in usuarios_cadastrados:
                nome_cadastrado = usuarios_cadastrados[cpf]
                # Compara os nomes ignorando maiúsculas/minúsculas
                if nome_cadastrado.lower() == nome.lower():
                    print("Login bem-sucedido.")
                    return agendamento_pb2.LoginResponse(
                        sucesso=True, 
                        mensagem="Login bem-sucedido!",
                        nome_correto=nome_cadastrado # Devolve o nome com a formatação original
                    )
                else:
                    print("Falha no login: CPF já cadastrado com outro nome.")
                    return agendamento_pb2.LoginResponse(
                        sucesso=False,
                        mensagem=f"Erro: CPF já cadastrado",
                        nome_correto=""
                    )
            # Novo usuário
            else:
                # Padroniza o nome com a primeira letra de cada palavra maiúscula
                nome_padronizado = nome.title()
                usuarios_cadastrados[cpf] = nome_padronizado
                print(f"Novo usuário registrado: CPF {cpf} com nome '{nome_padronizado}'")
                return agendamento_pb2.LoginResponse(
                    sucesso=True,
                    mensagem="Bem-vindo! Usuário registrado e logado com sucesso!",
                    nome_correto=nome_padronizado
                )

    # ... (outras funções como AgendarConsulta, Listar, etc., permanecem iguais)
    def AgendarConsulta(self, request, context):
        try:
            data_agendamento = datetime.strptime(request.consulta.data, '%d/%m/%Y')
            data_limite = datetime.now() + timedelta(days=365*2)
            if data_agendamento > data_limite: return agendamento_pb2.AgendarConsultaResponse(mensagem="Erro: Não é possível agendar com mais de dois anos de antecedência.", sucesso=False)
        except ValueError: return agendamento_pb2.AgendarConsultaResponse(mensagem="Erro: Formato de data inválido.", sucesso=False)
        with db_lock:
            for c in banco_de_dados_consultas:
                if c.data == request.consulta.data and c.horario == request.consulta.horario:
                    return agendamento_pb2.AgendarConsultaResponse(mensagem="Erro: Horário já agendado.", sucesso=False)
            banco_de_dados_consultas.append(request.consulta)
        notificar_subscribers()
        return agendamento_pb2.AgendarConsultaResponse(mensagem="Consulta agendada com sucesso!", sucesso=True)
    def ListarConsultas(self, request, context):
        consultas_sanitizadas = []
        with db_lock:
            for c in banco_de_dados_consultas:
                cs = agendamento_pb2.Consulta(); cs.CopyFrom(c)
                if cs.cpf_paciente != request.cpf_do_requisitante: cs.paciente = cs.paciente.split(' ')[0]
                consultas_sanitizadas.append(cs)
        return agendamento_pb2.ListarConsultasResponse(consultas=consultas_sanitizadas)
    def InscreverParaAtualizacoes(self, request, context):
        cpf_requisitante = request.cpf_do_requisitante; q = Queue(); subscribers[q] = cpf_requisitante
        try:
            while context.is_active(): yield q.get()
        finally:
            if q in subscribers: del subscribers[q]
    def CancelarConsulta(self, request, context):
        removido=False; msg_erro="Consulta não encontrada."
        with db_lock:
            consulta_alvo = None
            for c in banco_de_dados_consultas:
                if c.data==request.data and c.horario==request.horario and c.paciente.lower()==request.paciente.lower():
                    consulta_alvo=c; break
            if consulta_alvo:
                if consulta_alvo.cpf_paciente == request.cpf_do_requisitante:
                    banco_de_dados_consultas.remove(consulta_alvo); removido=True; notificar_subscribers()
                else: msg_erro="Apenas o paciente que marcou a consulta pode cancelá-la."
        if removido: return agendamento_pb2.CancelarConsultaResponse(mensagem="Consulta cancelada com sucesso!", sucesso=True)
        else: return agendamento_pb2.CancelarConsultaResponse(mensagem=msg_erro, sucesso=False)
    def VerificarDisponibilidade(self, request, context):
        with db_lock:
            for c in banco_de_dados_consultas:
                if c.data == request.data and c.horario == request.horario: return agendamento_pb2.VerificarDisponibilidadeResponse(disponivel=False)
        return agendamento_pb2.VerificarDisponibilidadeResponse(disponivel=True)

def serve():
    # ... (código para iniciar o servidor igual)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    agendamento_pb2_grpc.add_AgendamentoMedicoServicer_to_server(AgendamentoMedicoServicer(), server)
    server.add_insecure_port('[::]:50051'); print("Iniciando servidor gRPC na porta 50051..."); server.start(); server.wait_for_termination()

if __name__ == '__main__':
    serve()