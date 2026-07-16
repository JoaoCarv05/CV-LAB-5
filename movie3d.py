"""
Gravacao de video 3D anaglifo (~10-20 s) — versao com DEBUG.
Setup: camera ESQUERDA = 1, camera DIREITA = 0, parametros em data/params_py.xml.
Salva em data/movie3d/.
"""
import os
import time

import cv2

# ===================== CONFIG =====================
CamL_id = 1                          # ESQUERDA
CamR_id = 0                          # DIREITA
PARAMS_FILE = "data/params_py.xml"
OUT_DIR = "data/movie3d"
VIDEO_FILE = os.path.join(OUT_DIR, "video3d_joao.avi")
DURACAO_S = 15
FPS = 20
TAMANHO = (700, 700)
# =================================================

print("[DEBUG] Iniciando script...")
print("[DEBUG] Diretorio de trabalho atual:", os.getcwd())

os.makedirs(OUT_DIR, exist_ok=True)
print("[DEBUG] Pasta de saida garantida:", os.path.abspath(OUT_DIR))

print("[DEBUG] Verificando arquivo de parametros:", os.path.abspath(PARAMS_FILE))
if not os.path.exists(PARAMS_FILE):
    print("[ERRO] Arquivo de parametros NAO encontrado:", PARAMS_FILE)
    raise SystemExit(-1)
print("[DEBUG] Arquivo de parametros encontrado. OK")

# ---- Abertura das cameras ----
# No Windows, se nao abrir, troque para: cv2.VideoCapture(id, cv2.CAP_DSHOW)
print("[DEBUG] Abrindo camera ESQUERDA (id=%d)..." % CamL_id)
CamL = cv2.VideoCapture(CamL_id)
print("[DEBUG] CamL.isOpened() =", CamL.isOpened())

print("[DEBUG] Abrindo camera DIREITA (id=%d)..." % CamR_id)
CamR = cv2.VideoCapture(CamR_id)
print("[DEBUG] CamR.isOpened() =", CamR.isOpened())

if not CamL.isOpened() or not CamR.isOpened():
    print("[ERRO] Uma das cameras nao abriu. Verifique os IDs (0/1) ou use CAP_DSHOW.")
    CamL.release(); CamR.release()
    raise SystemExit(-1)

# ---- Leitura dos parametros ----
print("[DEBUG] Lendo parametros de:", PARAMS_FILE)
cv_file = cv2.FileStorage(PARAMS_FILE, cv2.FILE_STORAGE_READ)
Left_Stereo_Map_x = cv_file.getNode("Left_Stereo_Map_x").mat()
Left_Stereo_Map_y = cv_file.getNode("Left_Stereo_Map_y").mat()
Right_Stereo_Map_x = cv_file.getNode("Right_Stereo_Map_x").mat()
Right_Stereo_Map_y = cv_file.getNode("Right_Stereo_Map_y").mat()
cv_file.release()
if Left_Stereo_Map_x is None or Right_Stereo_Map_x is None:
    print("[ERRO] Mapas de retificacao vazios. O XML nao tem as chaves esperadas "
          "(Left_Stereo_Map_x/y, Right_Stereo_Map_x/y).")
    raise SystemExit(-1)
print("[DEBUG] Parametros carregados. shape mapaL_x =", Left_Stereo_Map_x.shape)

# ---- Gravador de video ----
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
writer = cv2.VideoWriter(VIDEO_FILE, fourcc, FPS, TAMANHO)
print("[DEBUG] VideoWriter aberto? ->", writer.isOpened(), "| arquivo:", os.path.abspath(VIDEO_FILE))
if not writer.isOpened():
    print("[ERRO] VideoWriter nao abriu. Tente outro codec, ex: *'XVID'.")
    raise SystemExit(-1)

print("[DEBUG] Comecando a gravar ~%d s ..." % DURACAO_S)
start = time.time()
frames_gravados = 0

while True:
    retR, imgR = CamR.read()
    retL, imgL = CamL.read()
    print("[DEBUG] retL=%s retR=%s | t=%.1fs | frames=%d"
          % (retL, retR, time.time() - start, frames_gravados))

    if retL and retR:
        Left_nice = cv2.remap(imgL, Left_Stereo_Map_x, Left_Stereo_Map_y,
                              cv2.INTER_LANCZOS4, cv2.BORDER_CONSTANT, 0)
        Right_nice = cv2.remap(imgR, Right_Stereo_Map_x, Right_Stereo_Map_y,
                               cv2.INTER_LANCZOS4, cv2.BORDER_CONSTANT, 0)

        # Anaglifo: B e G da direita; R (vermelho) da esquerda.
        output = Right_nice.copy()
        output[:, :, 2] = Left_nice[:, :, 2]
        output = cv2.resize(output, TAMANHO)

        writer.write(output)
        frames_gravados += 1

        cv2.namedWindow("3D movie", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("3D movie", TAMANHO[0], TAMANHO[1])
        cv2.imshow("3D movie", output)

        if (time.time() - start) >= DURACAO_S:
            print("[DEBUG] Duracao atingida. Encerrando.")
            break
        if cv2.waitKey(1) & 0xFF == 27:
            print("[DEBUG] ESC pressionado. Encerrando.")
            break
    else:
        print("[ERRO] Falha ao capturar frame (ret=False). Encerrando.")
        break

writer.release()
CamR.release()
CamL.release()
cv2.destroyAllWindows()
print("[DEBUG] Finalizado. Frames gravados:", frames_gravados)
print("[DEBUG] Video salvo em:", os.path.abspath(VIDEO_FILE))