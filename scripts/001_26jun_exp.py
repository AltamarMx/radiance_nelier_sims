# %% 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# %%
cols_map = ['I1N', 'I2N', 'I3N', 'I4N', 'I1S', 'I2S', 'I3S', 'I4S', 'I5S']
f = "../data/experimental/005_26Junio/09h.csv"
nueve = pd.read_csv(f)
nueve = nueve[::-1].reset_index(drop=True)


f = '../data/experimental/005_26Junio/10h.csv'
diez = pd.read_csv(f)

f = '../data/experimental/005_26Junio/11h.csv'
once = pd.read_csv(f)
once = once[::-1].reset_index(drop=True)

f = '../data/experimental/005_26Junio/12h.csv'
doce = pd.read_csv(f)

f = '../data/experimental/005_26Junio/13h.csv'
trece = pd.read_csv(f)
trece = trece[::-1].reset_index(drop=True)

f = '../data/experimental/005_26Junio/14h.csv'
catorce = pd.read_csv(f)

f = '../data/experimental/005_26Junio/15h.csv'
quince = pd.read_csv(f)
quince = quince[::-1].reset_index(drop=True)

f = '../data/experimental/005_26Junio/16h.csv'
dieciseis = pd.read_csv(f)

f = '../data/experimental/005_26Junio/17h.csv'
diecisiete = pd.read_csv(f)
diecisiete = diecisiete[::-1].reset_index(drop=True)

dataframes_por_hora = [nueve[cols_map], 
                       diez[cols_map], 
                       once[cols_map], 
                       doce[cols_map], 
                       trece[cols_map], 
                       catorce[cols_map], 
                       quince[cols_map], 
                       dieciseis[cols_map], 
                       diecisiete[cols_map]]
horas = ["9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
dataframes_por_hora
# %%
niveles = [0, 299, 500, 1000, 1500, 2000, 3000,4000,5000,6000,7000,8000,10000]

# Definir las distancias dadas
distancia_muro_norte = 0.51  # Distancia del primer sensor al muro norte (m)
distancia_entre_sensores = 1.08  # Distancia entre sensores (m)
distancia_muro_sur = 0.51  # Distancia del noveno sensor al muro sur (m)
distancia_pizarron = 0.71  # Distancia de la primera línea al muro de pizarrón (m)
distancia_entre_lineas = 1.08  # Distancia entre líneas de sensores (m)
distancia_muro_fondo = 0.68  # Distancia de la última línea al muro de fondo del aula (m)

# Crear las posiciones en el eje Y para cada línea de sensores
y_positions = [distancia_pizarron + i * distancia_entre_lineas for i in range(7)]

# Crear las posiciones en el eje X para cada sensor
distancia_total_x = distancia_muro_norte + distancia_muro_sur + 8 * distancia_entre_sensores
x_positions = [distancia_muro_norte + i * distancia_entre_sensores for i in range(9)]

# Crear la figura y los subgráficos (3 filas x 3 columnas)
fig, axes = plt.subplots(3, 3, figsize=(18, 12),sharex=True,sharey=True)

for i, (df, hora) in enumerate(zip(dataframes_por_hora, horas)):
    ax = axes[i // 3, i % 3]  # Seleccionar el subgráfico correspondiente
    
    # Crear una malla de X e Y para el contorno
    X, Y = np.meshgrid(x_positions, y_positions)
    Z = df.values.astype(float) * 1000  # Convertir a tipo float y multiplicar por 1000 para ajustar unidades
    
    # Graficar el contorno con relleno
    contour_filled = ax.contourf(X, Y, Z, cmap='jet', alpha=0.7, levels=niveles)
    contour = ax.contour(X, Y, Z, colors='black', levels=niveles)
    ax.clabel(contour, inline=True, fontsize=8)
    
    # Configurar cada subgráfico
    ax.set_aspect(aspect='equal')
    # ax.set_xlabel('[m]')
    # ax.set_ylabel('[m]')
    ax.set_title(f'{hora}')
    ax.set_xticks(x_positions)
    ax.set_yticks(y_positions)
    # ax.grid(True, color='white')
    ax.invert_yaxis()  # Invertir el eje Y para que el origen esté en la esquina superior izquierda

# Ajustar el espacio entre los subgráficos
# plt.tight_layout(rect=[0, 0, 1, 0.95])

for i in range(3):
    axes[2,i].set_xlabel('[m]')
    axes[i,0].set_ylabel('[m]')
# Añadir la barra de color a la figura principal
cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])  # Definir la posición de la barra de color
fig.colorbar(contour_filled, cax=cbar_ax, label='Iluminancia [lx]')

plt.suptitle('Experimental Measurements - June 26', fontsize=14, fontweight='bold', y=0.98)
plt.savefig('../edificio/images/001_26jun_experimental.png', dpi=300, bbox_inches='tight')
plt.show()

# %%
