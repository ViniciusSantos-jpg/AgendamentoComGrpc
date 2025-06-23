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
        self.title("Sistema de Agendamento - Login")
        self.geometry("500x300")

        self.stub = agendamento_pb2_grpc.AgendamentoMedicoStub(channel)
        self.usuario_cpf_atual = ""
        self.usuario_nome_atual = ""

        self.login_frame = ttk.Frame(self, padding=(20, 10))
        self.main_app_frame = ttk.Frame(self, padding=(10, 10))

        self._criar_tela_login()

    def _criar_tela_login(self):
        """Cria e exibe os widgets da tela de login."""
        self.login_frame.pack(expand=True, fill=BOTH)
        
        header = ttk.Label(self.login_frame, text="Identificação do Paciente", font=("Helvetica", 16, "bold"))
        header.pack(pady=(10, 20))

        cpf_frame = ttk.Frame(self.login_frame)
        cpf_frame.pack(pady=5, padx=20, fill=X)
        cpf_label = ttk.Label(cpf_frame, text="CPF (11 números):", width=15)
        cpf_label.pack(side=LEFT)
        self.cpf_entry_login = ttk.Entry(cpf_frame)
        self.cpf_entry_login.pack(side=LEFT, expand=True, fill=X)
        
        nome_frame = ttk.Frame(self.login_frame)
        nome_frame.pack(pady=5, padx=20, fill=X)
        nome_label = ttk.Label(nome_frame, text="Nome Completo:", width=15)
        nome_label.pack(side=LEFT)
        self.nome_entry_login = ttk.Entry(nome_frame)
        self.nome_entry_login.pack(side=LEFT, expand=True, fill=X)
        # --- NOVO: BIND PARA FORMATAÇÃO DO NOME ---
        self.nome_entry_login.bind("<KeyRelease>", self._formatar_nome_para_titulo)

        entrar_btn = ttk.Button(self.login_frame, text="Entrar / Registrar", command=self.realizar_login, bootstyle="success")
        entrar_btn.pack(pady=20)

    def realizar_login(self):
        # ... (código da função realizar_login permanece igual)
        cpf = self.cpf_entry_login.get()
        nome = self.nome_entry_login.get()

        if not (cpf.isdigit() and len(cpf) == 11):
            messagebox.showerror("Erro de Validação", "CPF inválido. Por favor, digite 11 números.", parent=self)
            return
        if not nome.strip():
            messagebox.showerror("Erro de Validação", "O nome não pode estar em branco.", parent=self)
            return
        try:
            request = agendamento_pb2.LoginRequest(cpf=cpf, nome=nome)
            response = self.stub.Login(request)
            if response.sucesso:
                self.usuario_cpf_atual = cpf
                self.usuario_nome_atual = response.nome_correto
                messagebox.showinfo("Login", response.mensagem, parent=self)
                self.login_frame.pack_forget()
                self._criar_tela_principal()
                self.main_app_frame.pack(expand=True, fill=BOTH)
                self.geometry("900x750")
                self.title(f"Agendamento - Usuário: {self.usuario_nome_atual} (CPF: {self.usuario_cpf_atual[:3]}.***.***-**)")
                self.carregar_lista_inicial()
                threading.Thread(target=self.ouvir_atualizacoes, daemon=True).start()
            else:
                messagebox.showerror("Falha no Login", response.mensagem, parent=self)
        except grpc.RpcError as e:
            messagebox.showerror("Erro de Comunicação", f"Não foi possível conectar ao servidor: {e.details()}", parent=self)


    def _criar_tela_principal(self):
        vcmd = (self.register(self._validate_numeric_input), '%P')

        top_frame = ttk.Frame(self.main_app_frame)
        top_frame.pack(fill=X)
        form_frame = ttk.LabelFrame(top_frame, text="Agendar Consulta", padding=(20, 10))
        form_frame.pack(fill=X)
        
        ttk.Label(form_frame, text="Paciente:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.paciente_entry = ttk.Entry(form_frame, width=40)
        self.paciente_entry.grid(row=0, column=1, padx=5, pady=8)
        self.paciente_entry.insert(0, self.usuario_nome_atual)
        self.paciente_entry.config(state="readonly")
        
        ttk.Label(form_frame, text="Médico:").grid(row=1, column=0, padx=5, pady=8, sticky="w")
        self.medico_entry = ttk.Entry(form_frame, width=40)
        self.medico_entry.grid(row=1, column=1, padx=5, pady=8)
        
        ttk.Label(form_frame, text="Data:").grid(row=2, column=0, padx=5, pady=8, sticky="w")
        self.data_entry = ttk.Entry(form_frame, width=40, validate='key', validatecommand=vcmd)
        self.data_entry.grid(row=2, column=1, padx=5, pady=8)
        self.data_entry.bind("<KeyRelease>", self._formatar_data)
        
        ttk.Label(form_frame, text="Horário:").grid(row=3, column=0, padx=5, pady=8, sticky="w")
        self.horario_entry = ttk.Entry(form_frame, width=40, validate='key', validatecommand=vcmd)
        self.horario_entry.grid(row=3, column=1, padx=5, pady=8)
        self.horario_entry.bind("<KeyRelease>", self._formatar_horario)
        
        btn_frame = ttk.Frame(form_frame); btn_frame.grid(row=4, columnspan=2, pady=10)
        self.agendar_btn = ttk.Button(btn_frame, text="Agendar", command=self.agendar_consulta, bootstyle="success"); self.agendar_btn.pack(side=LEFT, padx=5)
        self.verificar_btn = ttk.Button(btn_frame, text="Verificar", command=self.verificar_disponibilidade, bootstyle="info"); self.verificar_btn.pack(side=LEFT, padx=5)

        notebook = ttk.Notebook(self.main_app_frame, bootstyle="primary"); notebook.pack(pady=10, expand=True, fill=BOTH)
        tab_todos = ttk.Frame(notebook, padding=10); notebook.add(tab_todos, text='Todos os Agendamentos')
        self.tree_todos = self._criar_tabela_consultas(tab_todos)
        tab_meus = ttk.Frame(notebook, padding=10); notebook.add(tab_meus, text='Meus Agendamentos')
        self.tree_meus = self._criar_tabela_consultas(tab_meus)
        self.cancelar_btn_meus = ttk.Button(tab_meus, text="Cancelar Meu Agendamento Selecionado", command=self.cancelar_consulta, bootstyle="danger"); self.cancelar_btn_meus.pack(pady=10)
    
    def _criar_tabela_consultas(self, parent_frame):
        frame = ttk.Frame(parent_frame); frame.pack(fill=BOTH, expand=True)
        columns = ('paciente', 'medico', 'data', 'horario'); tree = ttk.Treeview(frame, columns=columns, show='headings', bootstyle="primary")
        tree.heading('paciente', text='Paciente'); tree.column('paciente', width=200)
        tree.heading('medico', text='Médico(a)'); tree.column('medico', width=200)
        tree.heading('data', text='Data'); tree.column('data', width=100, anchor=CENTER)
        tree.heading('horario', text='Horário'); tree.column('horario', width=100, anchor=CENTER)
        scrollbar = ttk.Scrollbar(frame, orient=VERTICAL, command=tree.yview); tree.configure(yscrollcommand=scrollbar.set); tree.pack(side=LEFT, fill=BOTH, expand=True); scrollbar.pack(side=RIGHT, fill=Y)
        return tree

    # --- FUNÇÃO CORRIGIDA PARA O BUG DE APAGAR ---
    def _validate_numeric_input(self, P):
        """Permite a entrada apenas se o conteúdo for numérico, ignorando os formatadores."""
        if P == "":
            return True
        return P.replace('/', '').replace(':', '').isdigit()

    # --- NOVA FUNÇÃO PARA CAPITALIZAÇÃO AUTOMÁTICA ---
    def _formatar_nome_para_titulo(self, event):
        """Formata o nome do usuário para o modo Título a cada tecla pressionada."""
        entry = self.nome_entry_login
        texto_atual = entry.get()
        cursor_pos = entry.index(INSERT)
        texto_formatado = texto_atual.title()
        if texto_atual != texto_formatado:
            entry.delete(0, END)
            entry.insert(0, texto_formatado)
            entry.icursor(cursor_pos)

    def _validate_logical_datetime(self, date_str, time_str):
        try:
            dt_obj = datetime.strptime(f"{date_str} {time_str}", '%d/%m/%Y %H:%M')
            if dt_obj < datetime.now(): messagebox.showerror("Data Inválida", "Não é possível agendar em datas passadas."); return False
            if dt_obj > datetime.now() + timedelta(days=365*2): messagebox.showerror("Data Inválida", "Não é possível agendar com mais de 2 anos de antecedência."); return False
            return True
        except ValueError: messagebox.showerror("Data ou Horário Inválido", "A data ou o horário inserido não existe."); return False

    def ouvir_atualizacoes(self):
        try:
            request = agendamento_pb2.SubscribeRequest(cpf_do_requisitante=self.usuario_cpf_atual)
            for response in self.stub.InscreverParaAtualizacoes(request): self.after(0, self.atualizar_lista_gui, response.consultas)
        except grpc.RpcError as e: print(f"Conexão perdida: {e.details()}")

    def carregar_lista_inicial(self):
        try:
            request = agendamento_pb2.SubscribeRequest(cpf_do_requisitante=self.usuario_cpf_atual)
            response = self.stub.ListarConsultas(request); self.atualizar_lista_gui(response.consultas)
        except grpc.RpcError as e: messagebox.showerror("Erro de Comunicação", f"Não foi possível carregar a lista: {e.details()}")

    def atualizar_lista_gui(self, consultas):
        for tree in [self.tree_todos, self.tree_meus]:
            for item in tree.get_children(): tree.delete(item)
        consultas_ordenadas = sorted(consultas, key=self._get_sort_key)
        for c in consultas_ordenadas:
            self.tree_todos.insert('', END, values=(c.paciente, c.medico, c.data, c.horario))
            if c.cpf_paciente == self.usuario_cpf_atual: self.tree_meus.insert('', END, values=(c.paciente, c.medico, c.data, c.horario))

    def agendar_consulta(self):
        paciente, medico, data, horario = self.paciente_entry.get(), self.medico_entry.get(), self.data_entry.get(), self.horario_entry.get()
        if not all([medico, data, horario]): messagebox.showwarning("Campos Vazios", "Preencha Médico, Data e Horário."); return
        if not self._validate_logical_datetime(data, horario): return
        try:
            consulta = agendamento_pb2.Consulta(paciente=paciente, medico=medico, data=data, horario=horario, cpf_paciente=self.usuario_cpf_atual)
            request = agendamento_pb2.AgendarConsultaRequest(consulta=consulta)
            response = self.stub.AgendarConsulta(request)
            if response.sucesso: messagebox.showinfo("Agendamento", response.mensagem); self.medico_entry.delete(0, END); self.data_entry.delete(0, END); self.horario_entry.delete(0, END)
            else: messagebox.showerror("Agendamento Falhou", response.mensagem)
        except grpc.RpcError as e: messagebox.showerror("Erro de Comunicação", f"Não foi possível agendar: {e.details()}")

    def cancelar_consulta(self):
        selecionado = self.tree_meus.focus()
        if not selecionado: messagebox.showwarning("Ação Inválida", "Para cancelar, selecione um agendamento na aba 'Meus Agendamentos'."); return
        dados = self.tree_meus.item(selecionado, 'values')
        paciente, _, data, horario = dados
        if messagebox.askyesno("Confirmar Cancelamento", f"Deseja cancelar sua consulta em {data} às {horario}?"):
            try:
                request = agendamento_pb2.CancelarConsultaRequest(paciente=paciente, data=data, horario=horario, cpf_do_requisitante=self.usuario_cpf_atual)
                response = self.stub.CancelarConsulta(request)
                if response.sucesso: messagebox.showinfo("Cancelamento", response.mensagem)
                else: messagebox.showerror("Cancelamento Falhou", response.mensagem)
            except grpc.RpcError as e: messagebox.showerror("Erro de Comunicação", f"Erro ao cancelar: {e.details()}")

    def _get_sort_key(self, c):
        try: return (datetime.strptime(c.data, '%d/%m/%Y'), c.horario)
        except ValueError: return (datetime.max, c.horario)
    
    def _formatar_data(self, event):
        if event.keysym.lower() not in ('backspace','delete','left','right'):
            e=self.data_entry; t=e.get().replace("/","")[:8]; n=""
            if len(t)>4: n=f"{t[:2]}/{t[2:4]}/{t[4:]}"
            elif len(t)>2: n=f"{t[:2]}/{t[2:]}"
            else: n=t
            if e.get()!=n: e.delete(0,END); e.insert(0,n); e.icursor(END)

    def _formatar_horario(self, event):
        if event.keysym.lower() not in ('backspace','delete','left','right'):
            e=self.horario_entry; t=e.get().replace(":","")[:4]; n=""
            if len(t)>2: n=f"{t[:2]}:{t[2:]}"
            else: n=t
            if e.get()!=n: e.delete(0,END); e.insert(0,n); e.icursor(END)
            
    def verificar_disponibilidade(self):
        data, horario = self.data_entry.get(), self.horario_entry.get()
        if not all([data, horario]): messagebox.showwarning("Campos Vazios","Preencha Data e Horário."); return
        if not self._validate_logical_datetime(data, horario): return
        try:
            req = agendamento_pb2.VerificarDisponibilidadeRequest(data=data,horario=horario)
            res = self.stub.VerificarDisponibilidade(req)
            if res.disponivel: messagebox.showinfo("Disponibilidade",f"O horário {horario} do dia {data} está DISPONÍVEL.")
            else: messagebox.showwarning("Disponibilidade",f"O horário {horario} do dia {data} está OCUPADO.")
        except grpc.RpcError as e: messagebox.showerror("Erro",f"Erro ao verificar: {e.details()}")

if __name__ == '__main__':
    with grpc.insecure_channel('localhost:50051') as channel:
        app = AppCliente(channel)
        app.mainloop()