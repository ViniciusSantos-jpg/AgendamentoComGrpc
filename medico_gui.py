import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import grpc
import threading # Importa threading
import agendamento_pb2
import agendamento_pb2_grpc

class AppMedico(ttk.Window):
    def __init__(self, channel):
        super().__init__(themename="cyborg")
        self.title("Agenda do Consultório")
        self.geometry("800x600")

        self.stub = agendamento_pb2_grpc.AgendamentoMedicoStub(channel)
        
        # --- LOGIN REMOVIDO ---
        # Define o nome do médico aqui, poderia vir de um login mais complexo
        self.nome_medico = "Dr. Gregory House"
        self.title(f"Agenda de {self.nome_medico}")

        # Frame da Tabela
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=BOTH, expand=True)

        # --- BOTÃO DE ATUALIZAR REMOVIDO ---

        # Tabela (Treeview)
        columns = ('data', 'horario', 'paciente', 'cpf')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings')
        self.tree.heading('data', text='Data'); self.tree.column('data', width=100, anchor=CENTER)
        self.tree.heading('horario', text='Horário'); self.tree.column('horario', width=100, anchor=CENTER)
        self.tree.heading('paciente', text='Paciente'); self.tree.column('paciente', width=300)
        self.tree.heading('cpf', text='CPF do Paciente'); self.tree.column('cpf', width=150, anchor=CENTER)
        
        self.tree.pack(fill=BOTH, expand=True)
        
        # NOVO: Inicia a thread que ouve as atualizações do servidor
        threading.Thread(target=self.ouvir_atualizacoes_agenda, daemon=True).start()

    def ouvir_atualizacoes_agenda(self):
        """Ouve o stream de atualizações do servidor em segundo plano."""
        try:
            # A requisição agora é vazia
            request = agendamento_pb2.AgendaMedicoRequest()
            for response in self.stub.InscreverParaAgendaMedico(request):
                # Agenda a atualização da UI na thread principal
                self.after(0, self.atualizar_tabela, response.consultas)
        except grpc.RpcError as e:
            # Se a conexão falhar, mostra um erro e fecha
            print(f"Erro no stream do médico: {e.details()}")
            if "failed to connect" in e.details():
                self.after(0, self.mostrar_erro_conexao)
    
    def mostrar_erro_conexao(self):
        messagebox.showerror("Erro de Conexão", "Não foi possível conectar ao servidor. Verifique se ele está em execução e tente novamente.")
        self.destroy()

    def atualizar_tabela(self, consultas):
        """Limpa a tabela e insere os novos dados da agenda."""
        # Limpa a tabela antes de carregar
        for item in self.tree.get_children():
            self.tree.delete(item)

        if consultas:
            for c in consultas:
                self.tree.insert('', END, values=(c.data, c.horario, c.paciente, c.cpf_paciente))
        else:
            self.tree.insert('', END, values=("", "", "Nenhuma consulta agendada", ""))

if __name__ == '__main__':
    with grpc.insecure_channel('localhost:50051') as channel:
        app = AppMedico(channel)
        app.mainloop()