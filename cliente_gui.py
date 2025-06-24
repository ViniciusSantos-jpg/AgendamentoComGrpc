import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from datetime import datetime, timedelta
import grpc

import agendamento_pb2
import agendamento_pb2_grpc

class AppCliente(ttk.Window):
    def __init__(self, channel):
        super().__init__(themename="superhero")
        self.title("Sistema de Agendamento Médico Simplificado")
        self.geometry("700x600")

        self.stub = agendamento_pb2_grpc.AgendamentoMedicoStub(channel)
        
        # --- Validação e Formatação ---
        vcmd_numeric = (self.register(self._validate_numeric_input), '%P')

        # --- SEÇÃO DE AGENDAMENTO ---
        form_agendar = ttk.LabelFrame(self, text="1. Agendar Nova Consulta", padding=(20, 10))
        form_agendar.pack(padx=20, pady=10, fill=X)

        # Labels e Entradas
        ttk.Label(form_agendar, text="Nome do Paciente:", width=15).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.paciente_entry = ttk.Entry(form_agendar, width=40)
        self.paciente_entry.grid(row=0, column=1, padx=5, pady=5)
        self.paciente_entry.bind("<KeyRelease>", self._formatar_nome_para_titulo) # <-- Formatação adicionada
        
        ttk.Label(form_agendar, text="Nome do Médico:", width=15).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.medico_entry = ttk.Entry(form_agendar, width=40)
        self.medico_entry.grid(row=1, column=1, padx=5, pady=5)
        self.medico_entry.bind("<KeyRelease>", self._formatar_nome_para_titulo) # <-- Formatação adicionada
        
        ttk.Label(form_agendar, text="Data (DD/MM/AAAA):", width=15).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.data_entry = ttk.Entry(form_agendar, width=40, validate='key', validatecommand=vcmd_numeric)
        self.data_entry.grid(row=2, column=1, padx=5, pady=5)
        self.data_entry.bind("<KeyRelease>", self._formatar_data) # <-- Formatação adicionada

        ttk.Label(form_agendar, text="Horário (HH:MM):", width=15).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.horario_entry = ttk.Entry(form_agendar, width=40, validate='key', validatecommand=vcmd_numeric)
        self.horario_entry.grid(row=3, column=1, padx=5, pady=5)
        self.horario_entry.bind("<KeyRelease>", self._formatar_horario) # <-- Formatação adicionada
        
        agendar_btn = ttk.Button(form_agendar, text="Realizar Agendamento", command=self.agendar_consulta, bootstyle="success")
        agendar_btn.grid(row=4, columnspan=2, pady=10)

        # --- SEÇÃO DE GERENCIAMENTO ---
        form_gerenciar = ttk.LabelFrame(self, text="2. Gerenciar Agendamento Existente", padding=(20, 10))
        form_gerenciar.pack(padx=20, pady=10, fill=X)
        
        ttk.Label(form_gerenciar, text="Código da Consulta:", width=15).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.codigo_entry = ttk.Entry(form_gerenciar, width=40)
        self.codigo_entry.grid(row=0, column=1, padx=5, pady=5)
        
        btn_frame_gerenciar = ttk.Frame(form_gerenciar)
        btn_frame_gerenciar.grid(row=1, columnspan=2, pady=10)
        buscar_btn = ttk.Button(btn_frame_gerenciar, text="Buscar", command=self.buscar_consulta, bootstyle="info"); buscar_btn.pack(side=LEFT, padx=5)
        cancelar_btn = ttk.Button(btn_frame_gerenciar, text="Cancelar", command=self.cancelar_consulta, bootstyle="danger"); cancelar_btn.pack(side=LEFT, padx=5)
        
        self.resultado_label = ttk.Label(self, text="Aguardando ação...", font=("Helvetica", 10, "italic"), wraplength=650)
        self.resultado_label.pack(padx=20, pady=20, fill=X)

    # --- FUNÇÕES DE FORMATAÇÃO E VALIDAÇÃO REINTRODUZIDAS ---
    def _validate_numeric_input(self, P):
        if P == "": return True
        return P.replace('/', '').replace(':', '').isdigit()

    def _formatar_nome_para_titulo(self, event):
        entry = event.widget
        texto_atual = entry.get(); cursor_pos = entry.index(INSERT)
        texto_formatado = texto_atual.title()
        if texto_atual != texto_formatado:
            entry.delete(0, END); entry.insert(0, texto_formatado); entry.icursor(cursor_pos)

    def _formatar_data(self, event):
        if event.keysym.lower() not in ('backspace','delete','left','right'):
            e=self.data_entry; t=e.get().replace("/","")[:8]; n=t
            if len(t)>4: n=f"{t[:2]}/{t[2:4]}/{t[4:]}"
            elif len(t)>2: n=f"{t[:2]}/{t[2:]}"
            if e.get()!=n: e.delete(0,END); e.insert(0,n); e.icursor(END)

    def _formatar_horario(self, event):
        if event.keysym.lower() not in ('backspace','delete','left','right'):
            e=self.horario_entry; t=e.get().replace(":","")[:4]; n=t
            if len(t)>2: n=f"{t[:2]}:{t[2:]}"
            if e.get()!=n: e.delete(0,END); e.insert(0,n); e.icursor(END)

    def agendar_consulta(self):
        paciente = self.paciente_entry.get()
        medico = self.medico_entry.get()
        data = self.data_entry.get()
        horario = self.horario_entry.get()

        if not all([paciente, medico, data, horario]):
            messagebox.showwarning("Campos Vazios", "Por favor, preencha todos os campos para agendar.")
            return

        try:
            # --- CORREÇÃO DA CRIAÇÃO DO REQUEST ---
            request = agendamento_pb2.AgendarConsultaRequest(
                paciente=paciente, 
                medico=medico, 
                data=data, 
                horario=horario
            )
            response = self.stub.AgendarConsulta(request)
            
            if response.sucesso:
                self.resultado_label.config(text="")
                codigo = response.id_consulta_gerado
                messagebox.showinfo("Agendamento Realizado", f"{response.mensagem}\n\nSeu código é: {codigo}\n\nGuarde-o para futuras consultas ou cancelamentos.")
                self.paciente_entry.delete(0, END); self.medico_entry.delete(0, END)
                self.data_entry.delete(0, END); self.horario_entry.delete(0, END)
            else:
                messagebox.showerror("Agendamento Falhou", response.mensagem)
        except grpc.RpcError as e:
            messagebox.showerror("Erro de Comunicação", f"Não foi possível conectar ao servidor: {e.details()}")

    def buscar_consulta(self):
        codigo = self.codigo_entry.get()
        if not codigo: messagebox.showwarning("Campo Vazio", "Por favor, insira o código da consulta para buscar."); return
        try:
            request = agendamento_pb2.GerenciarConsultaRequest(id_consulta=codigo)
            response = self.stub.BuscarConsulta(request)
            if response.sucesso:
                c = response.consulta
                info = f"Consulta Encontrada:\nPaciente: {c.paciente}\nMédico: {c.medico}\nData: {c.data} às {c.horario}"
                self.resultado_label.config(text=info, bootstyle="success")
            else:
                self.resultado_label.config(text=response.mensagem, bootstyle="warning")
        except grpc.RpcError as e: messagebox.showerror("Erro de Comunicação", f"Não foi possível conectar ao servidor: {e.details()}")

    def cancelar_consulta(self):
        codigo = self.codigo_entry.get()
        if not codigo: messagebox.showwarning("Campo Vazio", "Por favor, insira o código da consulta para cancelar."); return
        if not messagebox.askyesno("Confirmar Cancelamento", "Você tem certeza que deseja cancelar esta consulta? Esta ação não pode ser desfeita."): return
        try:
            request = agendamento_pb2.GerenciarConsultaRequest(id_consulta=codigo)
            response = self.stub.CancelarConsulta(request)
            if response.sucesso:
                self.resultado_label.config(text="")
                messagebox.showinfo("Sucesso", response.mensagem)
                self.codigo_entry.delete(0, END)
            else:
                self.resultado_label.config(text=response.mensagem, bootstyle="danger")
        except grpc.RpcError as e:
            messagebox.showerror("Erro de Comunicação", f"Não foi possível conectar ao servidor: {e.details()}")

if __name__ == '__main__':
    with grpc.insecure_channel('localhost:50051') as channel:
        app = AppCliente(channel)
        app.mainloop()