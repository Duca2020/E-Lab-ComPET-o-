import customtkinter as ctk
from tkinter import Menu, Toplevel
from tkinter import filedialog, messagebox
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import threading
import requests
import time


def criar_janela_principal():
    root = ctk.CTk()
    root.title("Meu Lab Virtual")

    # Janela que ira conter todo o front end
    janela_principal = ctk.CTkFrame(root)
    janela_principal.pack(fill="both", expand=True, padx=10, pady=10)

    # Criar figura pelo matplotlib e canvas
    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    canvas = FigureCanvasTkAgg(fig, master=janela_principal)
    canvas.draw()
    canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    # Variaveis para guardar dados (limitada e nao limitada)
    x_data = []
    y_data = []
    x_full = []
    y_full = []

    # Variaveis para controle
    parar_pro = threading.Event()
    pausar_pro = threading.Event()

    # Variavel para medir tempo
    tempo_inicio = None

    # Variaveis para medicoes
    medidas_vars = {
        "Min": ctk.BooleanVar(),
        "Max": ctk.BooleanVar(),
        "Média": ctk.BooleanVar(),
        "Desvio padrão": ctk.BooleanVar()
    }

    # Funcao para obter dados via request de http do esp32
    def obter_dados():
        nonlocal x_data, y_data, x_full, y_full, tempo_inicio
        tempo_inicio = time.time()
        while not parar_pro.is_set():
            if not pausar_pro.is_set():
                try:
                    esp32_ip = 'http://192.168.4.1/'  # IP padrao do esp32 (precisa estar conectado na wlan dele)
                    response = requests.get(esp32_ip, timeout=1)
                    if response.status_code == 200:
                        # Obtem a string do http
                        distancia_str = response.text.strip()
                        try:
                            distancia = float(distancia_str)
                        except ValueError:
                            print(f"Received invalid data: {distancia_str}")
                            continue

                        tempo_atual = time.time() - tempo_inicio
                        x_data.append(tempo_atual)
                        y_data.append(distancia)
                        x_full.append(tempo_atual)
                        y_full.append(distancia)

                        # Limitar dados de plot a 100 pontos (porem o full mantem todo historico)
                        if len(x_data) > 100:
                            x_data = x_data[-100:]
                            y_data = y_data[-100:]

                        # Atualiza plot
                        ax.clear()
                        ax.plot(x_data, y_data, label="Distância (cm)", color='#1f77b4')
                        ax.set_xlabel("Tempo (s)")
                        ax.set_ylabel("Distância (cm)")
                        ax.legend()
                        canvas.draw()
                        root.update_idletasks()
                    else:
                        print(f"Código inesperado de status obtido {response.status_code}")
                except requests.RequestException as e:
                    print(f"Erro ao obter dados por http: {e}")
            time.sleep(0.2)  # delay ao fazer outro request
            update_medidas()

    # Função para inciar a obtenção de dados
    def iniciar_processo():
        x_data.clear()
        y_data.clear()
        ax.clear()
        parar_pro.clear()
        pausar_pro.clear()
        threading.Thread(target=obter_dados, daemon=True).start()
        messagebox.showinfo("Process Control", "Obtendo dados...")

    # Função para pausar a obtenção de dados
    def pausar_processo():
        pausar_pro.set()
        messagebox.showinfo("Process Control", "Processo pausado.")

    # Função para retornar a obtenção de dados
    def resume_process():
        pausar_pro.clear()
        messagebox.showinfo("Process Control", "Processo retornado.")

    # Função para parar a obtenção de dados
    def parar_processo():
        parar_pro.set()
        messagebox.showinfo("Process Control", "Processo interrompido.")

    # Função para limpar variaveis de dados e o plot
    def clear_data():
        nonlocal x_data, y_data
        x_data.clear()
        y_data.clear()
        ax.clear()
        canvas.draw()
        messagebox.showinfo("Data Control", "Dados limpos.")

    # Funcao para atualizar as medidas mostradas
    def update_medidas():
        medidas_selecionadas = []
        if medidas_vars["Min"].get():
            medidas_selecionadas.append(f"Min = {np.min(y_data):.2f}")
        if medidas_vars["Max"].get():
            medidas_selecionadas.append(f"Max = {np.max(y_data):.2f}")
        if medidas_vars["Média"].get():
            medidas_selecionadas.append(f"Média = {np.mean(y_data):.2f}")
        if medidas_vars["Desvio padrão"].get():
            medidas_selecionadas.append(f"Desvio padrão = {np.std(y_data):.2f}")

        # Unindo medidas selecionadas para display
        medidas_label.configure(
            text="\n".join(medidas_selecionadas) if medidas_selecionadas else "Nenhuma medida selecionada.")

    # Funcao para atualizar medidas apos mudanca de plot
    def atualizar_medidas():
        update_medidas()

        # Funcao para atualizar o plot dinamicamente

    def update_plot():
        parar_pro.clear()
        pausar_pro.clear()
        thread = threading.Thread(target=plot_thread)
        thread.start()

    def plot_thread():
        nonlocal x_data, y_data

        for i in range(len(x_data)):
            if parar_pro.is_set():
                break
            while pausar_pro.is_set():
                pass

            ax.clear()
            ax.plot(x_data[:i + 1], y_data[:i + 1], label=f"Dados lidos", color='#1f77b4')
            ax.set_xlabel("Tempo (s)")
            ax.set_ylabel("Distância (cm)")
            ax.legend()
            canvas.draw()
            root.update_idletasks()
            root.after(100)

        canvas.draw()
        update_medidas()

    # Permite ver a posição do cursor do mouse sobre o plot
    def on_hover(event):
        if event.inaxes == ax:
            x, y = event.xdata, event.ydata
            # Mostrar as coordenadas igual no matlab
            cursor_label.configure(text=f"x = {x:.2f}, y = {y:.2f}")

    # Função para abrir um arquivo de dados
    def abrir_arquivo():
        nonlocal x_data, y_data
        file_path = filedialog.askopenfilename(
            title="Abrir um arquivo de dados",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                data = pd.read_csv(file_path, delim_whitespace=True) if file_path.endswith('.txt') else pd.read_csv(
                    file_path)
                if data.shape[1] < 2:
                    messagebox.showerror("Erro", "O arquivo deve ter pelo menos duas colunas.")
                    return
                x_data = data.iloc[:, 0].to_numpy()
                y_data = data.iloc[:, 1].to_numpy()
                update_plot()  # Automaticamente atualiza o plot com os dados carregados
                update_medidas()  # Atualizar as medidas com os dados carregados
                messagebox.showinfo("Operação bem sucedida", "Arquivo carregado com sucesso.")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao carregar o arquivo:\n{e}")

    # Salvar arquivos em txt ou csv
    def save_file():
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                data = pd.DataFrame({"x": x_full, "y": y_full})
                if file_path.endswith('.txt'):
                    data.to_csv(file_path, sep='\t', index=False)
                else:
                    data.to_csv(file_path, index=False)
                messagebox.showinfo("Operação bem sucedida", f"Dados salvados em {file_path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar os dados:\n{e}")

    def open_preferences():
        pref_window = Toplevel(root)
        pref_window.title("Preferências")
        pref_window.geometry("300x200")

        theme_switch = ctk.CTkSwitch(pref_window, text="Dark Theme", command=toggle_theme)
        theme_switch.pack(pady=10)

        if ctk.get_appearance_mode() == "Dark":
            theme_switch.select()

    # Funcao para alternar entre tema claro e escuro
    def toggle_theme():
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Light":
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

        root.update()
        janela_principal.update()

    # Funcao para mostrar About
    def mostrar_sobre():
        messagebox.showinfo("Sobre", "Meu Lab Virtual \nVersão 1.0 @2024")

    # Funcao para mostrar Info
    def mostrar_info():
        messagebox.showinfo("Info", "Baseado em:\nPython/Custom TKinter\n/Pandas/Numpy/Matplotlib")

    # Criar as barras do menu
    menubar = Menu(root)

    # Menu Arquivo
    menu_arquivos = Menu(menubar, tearoff=0)
    menu_arquivos.add_command(label="Novo", command=criar_janela_principal)
    menu_arquivos.add_command(label="Abrir", command=abrir_arquivo)
    menu_arquivos.add_command(label="Salvar", command=save_file)
    menu_arquivos.add_separator()
    menu_arquivos.add_command(label="Sair", command=root.quit)
    menubar.add_cascade(label="Arquivo", menu=menu_arquivos)

    # Menu Processo
    menu_processos = Menu(menubar, tearoff=0)
    menu_processos.add_command(label="Iniciar", command=iniciar_processo)
    menu_processos.add_command(label="Pausar", command=pausar_processo)
    menu_processos.add_command(label="Resumir", command=resume_process)
    menu_processos.add_command(label="Parar", command=parar_processo)
    menu_processos.add_command(label="Limpar dados", command=clear_data)
    menubar.add_cascade(label="Processo", menu=menu_processos)

    # Menu Medidas
    menu_medidas = Menu(menubar, tearoff=0)
    for medida in medidas_vars.keys():
        menu_medidas.add_checkbutton(label=medida, variable=medidas_vars[medida])
    menu_medidas.add_command(label="Atualizar", command=atualizar_medidas)
    menubar.add_cascade(label="Medidas", menu=menu_medidas)

    # Menu Opcoes
    menu_opcoes = Menu(menubar, tearoff=0)
    menu_opcoes.add_command(label="Preferências", command=open_preferences)
    menubar.add_cascade(label="Opções", menu=menu_opcoes)

    # Menu Ajuda
    menu_ajuda = Menu(menubar, tearoff=0)
    menu_ajuda.add_command(label="Sobre", command=mostrar_sobre)
    menu_ajuda.add_command(label="Info", command=mostrar_info)
    menubar.add_cascade(label="Ajuda", menu=menu_ajuda)

    # Adiciona a barra de menu a janela principal
    root.config(menu=menubar)

    # Espaco de dados do cursor
    cursor = ctk.CTkFrame(janela_principal)
    cursor.pack(side="bottom", fill="x", padx=10, pady=5)
    cursor_label = ctk.CTkLabel(cursor, text="Posição do cursor: (x, y)")
    cursor_label.pack()

    # Espaco para medidas
    medidas = ctk.CTkFrame(janela_principal)
    medidas.pack(side="bottom", fill="x", padx=10, pady=5)
    medidas_label = ctk.CTkLabel(medidas, text="Nenhuma medida selecionada.")
    medidas_label.pack()

    fig.canvas.mpl_connect('motion_notify_event', on_hover)

    # Inicia o loop
    root.mainloop()


# Cria instancia da janela principal
criar_janela_principal()