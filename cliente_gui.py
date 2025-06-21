import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta
import grpc
import threading

import agendamento_pb2
import agendamento_pb2_grpc

class AppCliente(ttk.Window):
    def __init__(self, channel):
        super().__init__(themename="superhero")
        self.title("Sistema de Agendamento Médico")

        self.usuario_atual = simpledialog.askstring("Identificação", "Qual é o seu nome completo?", parent=self)
        if not self.usuario_atual: self.destroy(); return
        
        self.title(f"Sistema de Agendamento - Logado como: {self.usuario_atual}")
        self.geometry("900x750")

        self.stub = agendamento_pb2_grpc.AgendamentoMedicoStub(channel)
        vcmd = (self.register(self._validate_numeric_input), '%P')

        # Frame Principal e de Agendamento
        top_frame = ttk.Frame(self, padding=(10,10))
        top_frame.pack(fill=X)
        
        form_frame = ttk.LabelFrame(top_frame, text="Agendar Consulta", padding=(20, 10))
        form_frame.pack(fill=X)

        ttk.Label(form_frame, text="Paciente:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.paciente_entry = ttk.Entry(form_frame, width=40)
        self.paciente_entry.grid(row=0, column=1, padx=5, pady=8)
        self.paciente_entry.insert(0, self.usuario_atual); self.paciente_entry.config(state="readonly")
        
        ttk.Label(form_frame, text="Médico:").grid(row=1, column=0, padx=5, pady=8, sticky="w")
        self.medico_entry = ttk.Entry(form_frame, width=40)
        self.medico_entry.grid(row=1, column=1, padx=5, pady=8)
        
        ttk.Label(form_frame, text="Data (DD/MM/AAAA):").grid(row=2, column=0, padx=5, pady=8, sticky="w")
        self.data_entry = ttk.Entry(form_frame, width=40, validate='key', validatecommand=vcmd)
        self.data_entry.grid(row=2, column=1, padx=5, pady=8); self.data_entry.bind("<KeyRelease>", self._formatar_data)
        
        ttk.Label(form_frame, text="Horário (HH:MM):").grid(row=3, column=0, padx=5, pady=8, sticky="w")
        self.horario_entry = ttk.Entry(form_frame, width=40, validate='key', validatecommand=vcmd)
        self.horario_entry.grid(row=3, column=1, padx=5, pady=8); self.horario_entry.bind("<KeyRelease>", self._formatar_horario)
        
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, columnspan=2, pady=10)
        self.agendar_btn = ttk.Button(btn_frame, text="Agendar Consulta", command=self.agendar_consulta, bootstyle="success")
        self.agendar_btn.pack(side=LEFT, padx=5)
        self.verificar_btn = ttk.Button(btn_frame, text="Verificar Disponibilidade", command=self.verificar_disponibilidade, bootstyle="info")
        self.verificar_btn.pack(side=LEFT, padx=5)

        # Notebook para Abas
        notebook = ttk.Notebook(self, bootstyle="primary")
        notebook.pack(pady=10, padx=10, expand=True, fill=BOTH)

        # Aba 1: Todos os Agendamentos
        tab_todos = ttk.Frame(notebook, padding=10)
        notebook.add(tab_todos, text='Todos os Agendamentos')
        
        self.tree_todos = self._criar_tabela_consultas(tab_todos)
        self.cancelar_btn_todos = ttk.Button(tab_todos, text="Cancelar Consulta Selecionada", command=self.cancelar_consulta, bootstyle="danger")
        self.cancelar_btn_todos.pack(pady=10)

        # Aba 2: Meus Agendamentos
        tab_meus = ttk.Frame(notebook, padding=10)
        notebook.add(tab_meus, text='Meus Agendamentos')
        
        self.tree_meus = self._criar_tabela_consultas(tab_meus)
        self.cancelar_btn_meus = ttk.Button(tab_meus, text="Cancelar Meu Agendamento", command=self.cancelar_consulta, bootstyle="danger")
        self.cancelar_btn_meus.pack(pady=10)

        # Lógica de Inicialização
        self.carregar_lista_inicial()
        thread = threading.Thread(target=self.ouvir_atualizacoes, daemon=True)
        thread.start()

    def _criar_tabela_consultas(self, parent_frame):
        """Função auxiliar para criar uma tabela (Treeview) de consultas."""
        frame = ttk.Frame(parent_frame)
        frame.pack(fill=BOTH, expand=True)
        columns = ('paciente', 'medico', 'data', 'horario')
        tree = ttk.Treeview(frame, columns=columns, show='headings', bootstyle="primary")
        tree.heading('paciente', text='Paciente'); tree.column('paciente', width=200)
        tree.heading('medico', text='Médico(a)'); tree.column('medico', width=200)
        tree.heading('data', text='Data'); tree.column('data', width=100, anchor=CENTER)
        tree.heading('horario', text='Horário'); tree.column('horario', width=100, anchor=CENTER)
        scrollbar = ttk.Scrollbar(frame, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        return tree

    def _validate_numeric_input(self, P):
        if not P: return True
        return P.replace('/', '').replace(':', '').isdigit()

    def _validate_logical_datetime(self, date_str, time_str):
        try:
            dt_obj = datetime.strptime(f"{date_str} {time_str}", '%d/%m/%Y %H:%M')
            if dt_obj < datetime.now():
                messagebox.showerror("Data Inválida", "Não é possível agendar em datas ou horários passados.")
                return False
            data_limite = datetime.now() + timedelta(days=365 * 2)
            if dt_obj > data_limite:
                messagebox.showerror("Data Inválida", "Não é possível agendar com mais de dois anos de antecedência.")
                return False
            return True
        except ValueError:
            messagebox.showerror("Data ou Horário Inválido", "A data ou o horário inserido não existe. Verifique.")
            return False

    def ouvir_atualizacoes(self):
        try:
            request = agendamento_pb2.SubscribeRequest(nome_do_requisitante=self.usuario_atual)
            for response in self.stub.InscreverParaAtualizacoes(request):
                print("Recebida atualização do servidor...")
                self.after(0, self.atualizar_lista_gui, response.consultas)
        except grpc.RpcError as e:
            print(f"Conexão com o stream perdida: {e.details()}")

    def carregar_lista_inicial(self):
        try:
            request = agendamento_pb2.SubscribeRequest(nome_do_requisitante=self.usuario_atual)
            response = self.stub.ListarConsultas(request)
            self.atualizar_lista_gui(response.consultas)
        except grpc.RpcError as e:
            messagebox.showerror("Erro de Comunicação", f"Não foi possível carregar a lista: {e.details()}")

    def atualizar_lista_gui(self, consultas):
        """Atualiza AMBAS as tabelas (Todos e Meus Agendamentos)."""
        active_trees = [self.tree_todos, self.tree_meus]
        selections = {tree: tree.focus() for tree in active_trees}

        for tree in active_trees:
            for item in tree.get_children():
                tree.delete(item)
        
        consultas_ordenadas = sorted(consultas, key=self._get_sort_key)
        
        for c in consultas_ordenadas:
            self.tree_todos.insert('', END, values=(c.paciente, c.medico, c.data, c.horario))
            if c.paciente == self.usuario_atual:
                self.tree_meus.insert('', END, values=(c.paciente, c.medico, c.data, c.horario))
        
        for tree, selection in selections.items():
            if selection and tree.exists(selection):
                tree.focus(selection)
                tree.selection_set(selection)

    def agendar_consulta(self):
        paciente, medico, data, horario = self.paciente_entry.get(), self.medico_entry.get(), self.data_entry.get(), self.horario_entry.get()
        if not all([medico, data, horario]):
            messagebox.showwarning("Campos Vazios", "Preencha Médico, Data e Horário.")
            return
        if len(data) != 10 or len(horario) != 5:
            messagebox.showerror("Formato Incompleto", "Data ou horário incompletos.")
            return
        if not self._validate_logical_datetime(data, horario): return
        
        try:
            request = agendamento_pb2.AgendarConsultaRequest(consulta=agendamento_pb2.Consulta(paciente=paciente, medico=medico, data=data, horario=horario))
            response = self.stub.AgendarConsulta(request)
            if response.sucesso:
                messagebox.showinfo("Agendamento", response.mensagem)
                self._limpar_campos_agendamento()
            else:
                messagebox.showerror("Agendamento Falhou", response.mensagem)
        except grpc.RpcError as e:
            messagebox.showerror("Erro de Comunicação", f"Não foi possível agendar: {e.details()}")

    def cancelar_consulta(self):
        try:
            notebook = self.children['!notebook']
            active_tab_index = notebook.index(notebook.select())
            tree_ativa = self.tree_todos if active_tab_index == 0 else self.tree_meus
        except KeyError:
            return 

        selecionado = tree_ativa.focus()
        if not selecionado:
            messagebox.showwarning("Nenhuma Seleção", "Selecione uma consulta na tabela para cancelar.")
            return
        
        dados = tree_ativa.item(selecionado, 'values')
        paciente_na_linha, _, data, horario = dados

        # Para o request de cancelamento, sempre use o nome real do usuário logado
        # se ele estiver tentando cancelar a própria consulta.
        paciente_real_para_request = self.usuario_atual if paciente_na_linha == self.usuario_atual else paciente_na_linha
        
        confirmar = messagebox.askyesno("Confirmar Cancelamento", f"Tentar cancelar a consulta de '{paciente_na_linha}' em {data} às {horario}?")
        if not confirmar: return
        
        try:
            request = agendamento_pb2.CancelarConsultaRequest(paciente=paciente_real_para_request, data=data, horario=horario, nome_do_requisitante=self.usuario_atual)
            response = self.stub.CancelarConsulta(request)
            if response.sucesso:
                messagebox.showinfo("Cancelamento", response.mensagem)
            else:
                messagebox.showerror("Cancelamento Falhou", response.mensagem)
        except grpc.RpcError as e:
            messagebox.showerror("Erro de Comunicação", f"Erro ao cancelar: {e.details()}")

    def _get_sort_key(self, c):
        try: return (datetime.strptime(c.data, '%d/%m/%Y'), c.horario)
        except ValueError: return (datetime.max, c.horario)

    def _limpar_campos_agendamento(self):
        self.medico_entry.delete(0, END); self.data_entry.delete(0, END); self.horario_entry.delete(0, END)

    def _formatar_data(self, event):
        if event.keysym.lower() not in ('backspace','delete','left','right'):
            e=self.data_entry; t=e.get().replace("/","")[:8]; n="";
            if len(t)>2: n+=t[:2]+"/"; t=t[2:]
            if len(t)>2: n+=t[:2]+"/"; t=t[2:]
            n+=t; e.delete(0,END); e.insert(0,n); e.icursor(END)

    def _formatar_horario(self, event):
        if event.keysym.lower() not in ('backspace','delete','left','right'):
            e=self.horario_entry; t=e.get().replace(":","")[:4]; n="";
            if len(t)>2: n+=t[:2]+":"; t=t[2:]
            n+=t; e.delete(0,END); e.insert(0,n); e.icursor(END)
            
    def verificar_disponibilidade(self):
        d,h=self.data_entry.get(),self.horario_entry.get()
        if not all([d,h]): messagebox.showwarning("Campos Vazios","Preencha Data e Horário."); return
        if len(d)!=10 or len(h)!=5: messagebox.showerror("Formato Incompleto","Data ou horário incompletos."); return
        if not self._validate_logical_datetime(d,h): return
        try:
            req = agendamento_pb2.VerificarDisponibilidadeRequest(data=d,horario=h)
            res = self.stub.VerificarDisponibilidade(req)
            if res.disponivel: messagebox.showinfo("Disponibilidade",f"O horário {h} do dia {d} está DISPONÍVEL.")
            else: messagebox.showwarning("Disponibilidade",f"O horário {h} do dia {d} está OCUPADO.")
        except grpc.RpcError as e: messagebox.showerror("Erro",f"Erro ao verificar: {e.details()}")

if __name__ == '__main__':
    with grpc.insecure_channel('localhost:50051') as channel:
        app = AppCliente(channel)
        if hasattr(app, 'usuario_atual') and app.usuario_atual:
            app.mainloop()