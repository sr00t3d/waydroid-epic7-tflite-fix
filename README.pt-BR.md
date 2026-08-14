# Correção do Crash do TensorFlow Lite no Epic Seven no Waydroid

Um patch binário cirúrgico que resolve o encerramento inesperado do jogo (**SIGSEGV / Null Pointer Dereference**) no **Epic Seven** (`com.stove.epic7.google`) rodando via **Waydroid** com camada de tradução ARM64 (`libhoudini`).

<img width="900" height="auto" alt="image" src="https://github.com/user-attachments/assets/a65f9706-f510-47b1-901b-4a5abd7d3972" />

---

## 🔍 Causa Raiz do Problema

Ao abrir baús, fazer invocações ou processar tabelas de recompensas no jogo, o Epic Seven chama a biblioteca **TensorFlow Lite (`libtensorflowlite.so`)** através do seu motor interno de aceleração de matrizes (*Ruy*).

Em celulares físicos com chips ARM reais (Snapdragon, MediaTek), o *Ruy* lê registradores de hardware da CPU. No entanto, no **Waydroid x86_64** sob tradutores como o Intel **Houdini**, essa consulta retorna `NULL`.

Como a função não faz uma checagem de ponteiro nulo:
```arm64
0x2e92e4: bl  0x2e9e3c
0x2e92e8: ldr x9, [x0, #0x8]   <-- x0 é NULL -> Tenta ler a memória 0x8 -> SIGSEGV!
```
O kernel do Linux encerra o jogo instantaneamente com `SEGV_MAPERR`.

---

## ⚡ A Solução

Este script aplica um patch na rotina de detecção de hardware `tflite::CpuBackendContext::RuyHasAvxOrAbove` dentro da `libtensorflowlite.so` (`offset 0x2e9204`), inserindo uma instrução de retorno imediato (`ret` / `0xd65f03c0`).

Isso impede que o jogo acesse ponteiros nulos e permite que animações de baú e gacha rodem com 100% de estabilidade!

---

## 🚀 Como Usar

### 1. Clonar o repositório
```bash
git clone https://github.com/seu-usuario/waydroid-epic7-tflite-fix.git
cd waydroid-epic7-tflite-fix
```

### 2. Executar o Script
Com o Waydroid rodando (ou com o Epic Seven instalado):
```bash
python3 patch_epic7.py
```
*O script localiza automaticamente a pasta do jogo no seu usuário, faz um backup original `.orig`, aplica o patch e recompila o cache do app no Android.*

---

## 🔄 Como Desfazer (Restaurar Original)

Para restaurar o arquivo original sem o patch:
```bash
python3 patch_epic7.py --restore
```
