import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from datetime import datetime  # <-- NOVO: Importa a biblioteca datetime
import grpc
import threading

import agendamento_pb2
import agendamento_pb2_grpc

class AppCliente(ttk.Window):
    def __init__(self, channel):
        super().__init__(themename="superhero")
        self.title("Sistema de Agendamento Médico")
        self.geometry("850x700")

        self.stub = agendamento_pb2_grpc.AgendamentoMedicoStub(channel)
        vcmd = (self.register(self._validate_numeric_input), '%P')

        # --- Widgets da Interface ---
        form_frame = ttk.LabelFrame(self, text="Agendar / Cancelar Consulta", padding=(20, 10))
        form_frame.pack(padx=10, pady=10, fill="x")

        ttk.Label(form_frame, text="Paciente:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.paciente_entry = ttk.Entry(form_frame, width=40)
        self.paciente_entry.grid(row=0, column=1, padx=5, pady=8)

        ttk.Label(form_frame, text="Médico:").grid(row=1, column=0, padx=5, pady=8, sticky="w")
        self.medico_entry = ttk.Entry(form_frame, width=40)
        self.medico_entry.grid(row=1, column=1, padx=5, pady=8)

        ttk.Label(form_frame, text="Data (DD/MM/AAAA):").grid(row=2, column=0, padx=5, pady=8, sticky="w")
        self.data_entry = ttk.Entry(form_frame, width=40, validate='key', validatecommand=vcmd)
        self.data_entry.grid(row=2, column=1, padx=5, pady=8)
        self.data_entry.bind("<KeyRelease>", self._formatar_data)

        ttk.Label(form_frame, text="Horário (HH:MM):").grid(row=3, column=0, padx=5, pady=8, sticky="w")
        self.horario_entry = ttk.Entry(form_frame, width=40, validate='key', validatecommand=vcmd)
        self.horario_entry.grid(row=3, column=1, padx=5, pady=8)
        self.horario_entry.bind("<KeyRelease>", self._formatar_horario)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(padx=10, pady=10, fill="x", anchor="center")
        
        self.agendar_btn = ttk.Button(btn_frame, text="Agendar Consulta", command=self.agendar_consulta, bootstyle="success")
        self.agendar_btn.pack(side="left", padx=5, pady=5)
        self.cancelar_btn = ttk.Button(btn_frame, text="Cancelar Consulta", command=self.cancelar_consulta, bootstyle="danger")
        self.cancelar_btn.pack(side="left", padx=5, pady=5)
        self.verificar_btn = ttk.Button(btn_frame, text="Verificar Disponibilidade", command=self.verificar_disponibilidade, bootstyle="info")
        self.verificar_btn.pack(side="left", padx=5, pady=5)

        list_frame = ttk.LabelFrame(self, text="Consultas Agendadas", padding=(20, 10))
        list_frame.pack(padx=10, pady=10, fill="both", expand=True)

        columns = ('paciente', 'medico', 'data', 'horario')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', bootstyle="primary")

        self.tree.heading('paciente', text='Paciente')
        self.tree.column('paciente', width=200)
        self.tree.heading('medico', text='Médico(a)')
        self.tree.column('medico', width=200)
        self.tree.heading('data', text='Data')
        self.tree.column('data', width=100, anchor=CENTER)
        self.tree.heading('horario', text='Horário')
        self.tree.column('horario', width=100, anchor=CENTER)

        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.carregar_lista_inicial()
        thread = threading.Thread(target=self.ouvir_atualizacoes, daemon=True)
        thread.start()

    def _validate_numeric_input(self, P):
        if not P: return True
        return P.replace('/', '').replace(':', '').isdigit()

    # --- NOVA FUNÇÃO DE VALIDAÇÃO LÓGICA DE DATA E HORA ---
    def _validate_logical_datetime(self, date_str, time_str):
        """Verifica se a data/hora é válida e se não está no passado."""
        try:
            # Combina data e hora para uma validação completa
            full_datetime_str = f"{date_str} {time_str}"
            dt_obj = datetime.strptime(full_datetime_str, '%d/%m/%Y %H:%M')

            # Verifica se a data e hora do agendamento são no futuro
            if dt_obj < datetime.now():
                messagebox.showerror("Data Inválida", "Não é possível agendar consultas em datas ou horários passados.")
                return False
            
            return True
        except ValueError:
            # Ocorre se a data ou hora for impossível (ex: 31/02, 25:00)
            messagebox.showerror("Data ou Horário Inválido", "A data ou o horário inserido não existe. Por favor, verifique.")
            return False

    def ouvir_atualizacoes(self):
        try:
            request = agendamento_pb2.SubscribeRequest()
            for response in self.stub.InscreverParaAtualizacoes(request):
                print("Recebida atualização do servidor...")
                self.after(0, self.atualizar_lista_gui, response.consultas)
        except grpc.RpcError as e:
            print(f"Conexão com o stream perdida: {e.details()}")

    def carregar_lista_inicial(self):
        try:
            request = agendamento_pb2.SubscribeRequest()
            response = self.stub.ListarConsultas(request)
            self.atualizar_lista_gui(response.consultas)
        except grpc.RpcError as e:
            messagebox.showerror("Erro de Comunicação", f"Não foi possível carregar a lista: {e.details()}")

    def atualizar_lista_gui(self, consultas):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Converte a data para um formato comparável antes de ordenar
        consultas_ordenadas = sorted(consultas, key=lambda c: (datetime.strptime(c.data, '%d/%m/%Y'), c.horario))
        
        for c in consultas_ordenadas:
            self.tree.insert('', END, values=(c.paciente, c.medico, c.data, c.horario))

    def agendar_consulta(self):
        paciente, medico, data, horario = self.paciente_entry.get(), self.medico_entry.get(), self.data_entry.get(), self.horario_entry.get()
        if not all([paciente, medico, data, horario]):
            messagebox.showwarning("Campos Vazios", "Por favor, preencha todos os campos para agendar.")
            return
        if len(data) != 10 or len(horario) != 5:
            messagebox.showerror("Formato Incompleto", "A data ou o horário não foram preenchidos completamente.")
            return
        
        # --- MODIFICADO: Chama a nova validação lógica ---
        if not self._validate_logical_datetime(data, horario):
            return

        try:
            request = agendamento_pb2.AgendarConsultaRequest(consulta=agendamento_pb2.Consulta(paciente=paciente, medico=medico, data=data, horario=horario))
            response = self.stub.AgendarConsulta(request)
            messagebox.showinfo("Agendamento", response.mensagem)
            if response.sucesso:
                self._limpar_campos()
        except grpc.RpcError as e:
            messagebox.showerror("Erro de Comunicação", f"Não foi possível agendar: {e.details()}")

    def cancelar_consulta(self):
        selecionado = self.tree.focus()
        if not selecionado:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione uma consulta na tabela para cancelar.")
            return
        
        dados = self.tree.item(selecionado, 'values')
        paciente, data, horario = dados[0], dados[2], dados[3]
        confirmar = messagebox.askyesno("Confirmar Cancelamento", f"Deseja cancelar a consulta de {paciente} em {data} às {horario}?")
        if not confirmar:
            return
        
        try:
            request = agendamento_pb2.CancelarConsultaRequest(paciente=paciente, data=data, horario=horario)
            response = self.stub.CancelarConsulta(request)
            messagebox.showinfo("Cancelamento", response.mensagem)
            if response.sucesso:
                self._limpar_campos()
        except grpc.RpcError as e:
            messagebox.showerror("Erro de Comunicação", f"Erro ao cancelar: {e.details()}")

    def _limpar_campos(self):
        self.paciente_entry.delete(0, END); self.medico_entry.delete(0, END); self.data_entry.delete(0, END); self.horario_entry.delete(0, END)

    def _formatar_data(self, event):
        if event.keysym.lower() not in ('backspace', 'delete', 'left', 'right'):
            entry = self.data_entry; texto = entry.get().replace("/", "")[:8]; novo_texto = ""
            if len(texto) > 2: novo_texto += texto[:2] + "/"; texto = texto[2:]
            if len(texto) > 2: novo_texto += texto[:2] + "/"; texto = texto[2:]
            novo_texto += texto; entry.delete(0, END); entry.insert(0, novo_texto); entry.icursor(END)

    def _formatar_horario(self, event):
        if event.keysym.lower() not in ('backspace', 'delete', 'left', 'right'):
            entry = self.horario_entry; texto = entry.get().replace(":", "")[:4]; novo_texto = ""
            if len(texto) > 2: novo_texto += texto[:2] + ":"; texto = texto[2:]
            novo_texto += texto; entry.delete(0, END); entry.insert(0, novo_texto); entry.icursor(END)
            
    def verificar_disponibilidade(self):
        data, horario = self.data_entry.get(), self.horario_entry.get()
        if not all([data, horario]):
            messagebox.showwarning("Campos Vazios", "Preencha os campos 'Data' e 'Horário' para verificar."); return
        if len(data) != 10 or len(horario) != 5:
            messagebox.showerror("Formato Incompleto", "A data ou o horário não foram preenchidos completamente."); return
        
        # --- MODIFICADO: Chama a nova validação lógica ---
        if not self._validate_logical_datetime(data, horario):
            return

        try:
            request = agendamento_pb2.VerificarDisponibilidadeRequest(data=data, horario=horario)
            response = self.stub.VerificarDisponibilidade(request)
            if response.disponivel: messagebox.showinfo("Disponibilidade", f"O horário {horario} do dia {data} está DISPONÍVEL.")
            else: messagebox.showwarning("Disponibilidade", f"O horário {horario} do dia {data} está OCUPADO.")
        except grpc.RpcError as e:
            messagebox.showerror("Erro de Comunicação", f"Erro ao verificar: {e.details()}")

if __name__ == '__main__':
    with grpc.insecure_channel('localhost:50051') as channel:
        app = AppCliente(channel)
        app.mainloop()