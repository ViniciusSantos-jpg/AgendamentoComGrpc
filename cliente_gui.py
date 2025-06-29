import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import grpc
import agendamento_pb2
import agendamento_pb2_grpc

class AppCliente(ttk.Window):
    def __init__(self, channel):
        super().__init__(themename="superhero")
        self.title("Agendamento de Consultas - Paciente")
        self.geometry("700x650")

        self.stub = agendamento_pb2_grpc.AgendamentoMedicoStub(channel)
        
        # Validação e Formatação
        vcmd_numeric = (self.register(self._validate_numeric_input), '%P')

        # --- SEÇÃO DE AGENDAMENTO ---
        form_agendar = ttk.LabelFrame(self, text="1. Agendar Nova Consulta", padding=(20, 10))
        form_agendar.pack(padx=20, pady=10, fill=X)

        # Labels e Entradas
        ttk.Label(form_agendar, text="Nome Completo:", width=15).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.paciente_entry = ttk.Entry(form_agendar, width=40)
        self.paciente_entry.grid(row=0, column=1, padx=5, pady=5)
        self.paciente_entry.bind("<KeyRelease>", self._formatar_nome_para_titulo)
        
        ttk.Label(form_agendar, text="CPF (só números):", width=15).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cpf_entry = ttk.Entry(form_agendar, width=40, validate='key', validatecommand=vcmd_numeric)
        self.cpf_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form_agendar, text="Data (DD/MM/AAAA):", width=15).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.data_entry = ttk.Entry(form_agendar, width=40, validate='key', validatecommand=vcmd_numeric)
        self.data_entry.grid(row=2, column=1, padx=5, pady=5)
        self.data_entry.bind("<KeyRelease>", self._formatar_data)

        ttk.Label(form_agendar, text="Horário (HH:MM):", width=15).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.horario_entry = ttk.Entry(form_agendar, width=40, validate='key', validatecommand=vcmd_numeric)
        self.horario_entry.grid(row=3, column=1, padx=5, pady=5)
        self.horario_entry.bind("<KeyRelease>", self._formatar_horario)
        
        ttk.Button(form_agendar, text="Realizar Agendamento", command=self.agendar_consulta, bootstyle="success").grid(row=4, columnspan=2, pady=10)

        # --- SEÇÃO DE GERENCIAMENTO ---
        form_gerenciar = ttk.LabelFrame(self, text="2. Gerenciar Agendamento Existente", padding=(20, 10))
        form_gerenciar.pack(padx=20, pady=10, fill=X)
        
        ttk.Label(form_gerenciar, text="Código da Consulta:", width=15).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.codigo_entry = ttk.Entry(form_gerenciar, width=40)
        self.codigo_entry.grid(row=0, column=1, padx=5, pady=5)
        
        btn_frame_gerenciar = ttk.Frame(form_gerenciar)
        btn_frame_gerenciar.grid(row=1, columnspan=2, pady=10)
        ttk.Button(btn_frame_gerenciar, text="Buscar", command=self.buscar_consulta, bootstyle="info").pack(side=LEFT, padx=5)
        ttk.Button(btn_frame_gerenciar, text="Cancelar", command=self.cancelar_consulta, bootstyle="danger").pack(side=LEFT, padx=5)
        
        self.resultado_label = ttk.Label(self, text="Aguardando ação...", font=("Helvetica", 10, "italic"), wraplength=650)
        self.resultado_label.pack(padx=20, pady=20, fill=X)

    # --- FUNÇÃO DE VALIDAÇÃO ---
    def _validate_numeric_input(self, P):
        """Permite a entrada apenas se o conteúdo for numérico, ignorando os formatadores."""
        if P == "":
            return True
        return P.replace('/', '').replace(':', '').isdigit()

    def _formatar_nome_para_titulo(self, event):
        entry = event.widget
        texto_atual = entry.get()
        cursor_pos = entry.index(INSERT)
        texto_formatado = texto_atual.title()
        if texto_atual != texto_formatado:
            entry.delete(0, END)
            entry.insert(0, texto_formatado)
            entry.icursor(cursor_pos)

    def _formatar_data(self, event):
        entry = self.data_entry
        texto_atual = entry.get()
        texto_numerico = texto_atual.replace("/", "")[:8]
        novo_texto = texto_numerico
        
        if len(texto_numerico) > 4:
            novo_texto = f"{texto_numerico[:2]}/{texto_numerico[2:4]}/{texto_numerico[4:]}"
        elif len(texto_numerico) > 2:
            novo_texto = f"{texto_numerico[:2]}/{texto_numerico[2:]}"
        
        if texto_atual != novo_texto:
            cursor_pos = entry.index(INSERT)
            entry.delete(0, END)
            entry.insert(0, novo_texto)
            if cursor_pos == len(texto_atual) and len(novo_texto) > len(texto_atual):
                 entry.icursor(len(novo_texto))
            else:
                 entry.icursor(cursor_pos)

    def _formatar_horario(self, event):
        entry = self.horario_entry
        texto_atual = entry.get()
        texto_numerico = texto_atual.replace(":", "")[:4]
        novo_texto = texto_numerico

        if len(texto_numerico) > 2:
            novo_texto = f"{texto_numerico[:2]}:{texto_numerico[2:]}"
        
        if texto_atual != novo_texto:
            cursor_pos = entry.index(INSERT)
            entry.delete(0, END)
            entry.insert(0, novo_texto)
            if cursor_pos == len(texto_atual) and len(novo_texto) > len(texto_atual):
                 entry.icursor(len(novo_texto))
            else:
                 entry.icursor(cursor_pos)

    def agendar_consulta(self):
        paciente, cpf, data, horario = self.paciente_entry.get(), self.cpf_entry.get(), self.data_entry.get(), self.horario_entry.get()
        if not all([paciente, cpf, data, horario]):
            messagebox.showwarning("Campos Vazios", "Preencha todos os campos.")
            return
        if not (cpf.isdigit() and len(cpf) == 11):
            messagebox.showerror("CPF Inválido", "CPF deve ter 11 números.")
            return
        try:
            req = agendamento_pb2.AgendarConsultaRequest(paciente=paciente, cpf_paciente=cpf, data=data, horario=horario)
            res = self.stub.AgendarConsulta(req)
            if res.sucesso:
                self.resultado_label.config(text="")
                messagebox.showinfo("Sucesso", f"{res.mensagem}\n\nSeu código é: {res.id_consulta_gerado}")
                self.paciente_entry.delete(0,END); self.cpf_entry.delete(0,END); self.data_entry.delete(0,END); self.horario_entry.delete(0,END)
            else:
                messagebox.showerror("Falha", res.mensagem)
        except grpc.RpcError as e:
            messagebox.showerror("Erro de Comunicação", f"Falha ao conectar ao servidor: {e.details()}")

    def buscar_consulta(self):
        codigo = self.codigo_entry.get()
        if not codigo: messagebox.showwarning("Campo Vazio", "Insira o código da consulta."); return
        try:
            req=agendamento_pb2.GerenciarConsultaRequest(id_consulta=codigo)
            res=self.stub.BuscarConsulta(req)
            if res.sucesso:
                c=res.consulta
                info=f"Consulta Encontrada:\nPaciente: {c.paciente} (CPF: ...{c.cpf_paciente[-4:]})\nMédico: {c.medico}\nData: {c.data} às {c.horario}"
                self.resultado_label.config(text=info, bootstyle="success")
            else:
                self.resultado_label.config(text=res.mensagem, bootstyle="warning")
        except grpc.RpcError as e:
            messagebox.showerror("Erro de Comunicação", f"Falha ao conectar: {e.details()}")
    
    def cancelar_consulta(self):
        codigo = self.codigo_entry.get()
        if not codigo: messagebox.showwarning("Campo Vazio", "Insira o código para cancelar."); return
        if not messagebox.askyesno("Confirmar", "Tem certeza que deseja cancelar?"): return
        try:
            req=agendamento_pb2.GerenciarConsultaRequest(id_consulta=codigo)
            res=self.stub.CancelarConsulta(req)
            if res.sucesso:
                self.resultado_label.config(text="")
                messagebox.showinfo("Sucesso", res.mensagem)
                self.codigo_entry.delete(0, END)
            else:
                self.resultado_label.config(text=res.mensagem, bootstyle="danger")
        except grpc.RpcError as e:
            messagebox.showerror("Erro de Comunicação", f"Falha ao conectar: {e.details()}")

if __name__ == '__main__':
    with grpc.insecure_channel('localhost:50051') as channel:
        app = AppCliente(channel)
        app.mainloop()