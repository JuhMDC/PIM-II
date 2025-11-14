// ============================================================
// userdb.c
// ------------------------------------------------------------
// Módulo em C para gerenciamento simples de usuários.
// Será usado como biblioteca chamada pelo Python via ctypes.
// ============================================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Nome do arquivo "banco de dados"
#define DBFILE "users.dat"

// Estrutura do usuário
typedef struct {
    char nome[50];
    char senha[50];
    char email[50];
    int idade;
} Usuario;

// Estrutura para notas
typedef struct {
    char nome[50]; // mesmo nome do usuário
    char disciplina[50];
    float nota;
} Nota;

// Estrutura para faltas
typedef struct {
    char nome[50]; // mesmo nome do usuário
    char disciplina[50];
    int faltas;
} Falta;

#define NOTASFILE "notas.dat"
#define FALTASFILE "faltas.dat"

// ------------------------------------------------------------
// Função: adiciona um usuário no arquivo
// ------------------------------------------------------------
void adicionar_usuario(const char *nome, const char *senha, const char *email, int idade) {
    FILE *f = fopen(DBFILE, "ab"); // abre ou cria o arquivo binário
    if (!f) {
        printf("Erro ao abrir o arquivo de banco.\n");
        return;
    }

    Usuario u;
    strncpy(u.nome, nome, sizeof(u.nome) - 1);
    u.nome[sizeof(u.nome) - 1] = '\0';
    strncpy(u.senha, senha, sizeof(u.senha) - 1);
    u.senha[sizeof(u.senha) - 1] = '\0';
    strncpy(u.email, email, sizeof(u.email) - 1);
    u.email[sizeof(u.email) - 1] = '\0';
    u.idade = idade;

    fwrite(&u, sizeof(Usuario), 1, f);
    fclose(f);
}

// ------------------------------------------------------------
// Função: lista todos os usuários cadastrados
// ------------------------------------------------------------
void listar_usuarios() {
    FILE *f = fopen(DBFILE, "rb");
    if (!f) {
        printf("Nenhum usuário encontrado (arquivo ausente).\n");
        return;
    }

    Usuario u;
    int count = 0;
    printf("=== Lista de Usuários ===\n");
    while (fread(&u, sizeof(Usuario), 1, f) == 1) {
        printf("Nome : %s\n", u.nome);
        printf("Senha: %s\n", u.senha);
        printf("Email: %s\n", u.email);
        printf("Idade: %d\n\n", u.idade);
        count++;
    }

    if (count == 0) {
        printf("Nenhum usuário cadastrado.\n");
    }

    fclose(f);
}

// ------------------------------------------------------------
// Função: adiciona uma nota
// ------------------------------------------------------------
void adicionar_nota(const char *nome, const char *disciplina, float nota) {
    FILE *f = fopen(NOTASFILE, "ab");
    if (!f) {
        printf("Erro ao abrir o arquivo de notas.\n");
        return;
    }
    Nota n;
    strncpy(n.nome, nome, sizeof(n.nome) - 1);
    n.nome[sizeof(n.nome) - 1] = '\0';
    strncpy(n.disciplina, disciplina, sizeof(n.disciplina) - 1);
    n.disciplina[sizeof(n.disciplina) - 1] = '\0';
    n.nota = nota;
    fwrite(&n, sizeof(Nota), 1, f);
    fclose(f);
}

// ------------------------------------------------------------
// Função: lista todas as notas
// ------------------------------------------------------------
void listar_notas() {
    FILE *f = fopen(NOTASFILE, "rb");
    if (!f) {
        printf("Nenhuma nota encontrada.\n");
        return;
    }
    Nota n;
    printf("=== Notas ===\n");
    while (fread(&n, sizeof(Nota), 1, f) == 1) {
        printf("Nome: %s\n", n.nome);
        printf("Disciplina: %s\n", n.disciplina);
        printf("Nota: %.2f\n\n", n.nota);
    }
    fclose(f);
}

// Lista notas de um usuário específico
void listar_notas_usuario(const char *nome) {
    FILE *f = fopen(NOTASFILE, "rb");
    if (!f) {
        printf("Nenhuma nota encontrada.\n");
        return;
    }
    Nota n;
    int encontrou = 0;
    printf("=== Notas de %s ===\n", nome);
    while (fread(&n, sizeof(Nota), 1, f) == 1) {
        if (strcmp(n.nome, nome) == 0) {
            printf("Disciplina: %s\n", n.disciplina);
            printf("Nota: %.2f\n\n", n.nota);
            encontrou = 1;
        }
    }
    if (!encontrou) {
        printf("Nenhuma nota para este usuário.\n");
    }
    fclose(f);
}

// ------------------------------------------------------------
// Função: adiciona uma falta
// ------------------------------------------------------------
void adicionar_falta(const char *nome, const char *disciplina, int faltas) {
    FILE *f = fopen(FALTASFILE, "ab");
    if (!f) {
        printf("Erro ao abrir o arquivo de faltas.\n");
        return;
    }
    Falta fta;
    strncpy(fta.nome, nome, sizeof(fta.nome) - 1);
    fta.nome[sizeof(fta.nome) - 1] = '\0';
    strncpy(fta.disciplina, disciplina, sizeof(fta.disciplina) - 1);
    fta.disciplina[sizeof(fta.disciplina) - 1] = '\0';
    fta.faltas = faltas;
    fwrite(&fta, sizeof(Falta), 1, f);
    fclose(f);
}

// ------------------------------------------------------------
// Função: lista todas as faltas
// ------------------------------------------------------------
void listar_faltas() {
    FILE *f = fopen(FALTASFILE, "rb");
    if (!f) {
        printf("Nenhuma falta encontrada.\n");
        return;
    }
    Falta fta;
    printf("=== Faltas ===\n");
    while (fread(&fta, sizeof(Falta), 1, f) == 1) {
        printf("Nome: %s\n", fta.nome);
        printf("Disciplina: %s\n", fta.disciplina);
        printf("Faltas: %d\n\n", fta.faltas);
    }
    fclose(f);
}

// Lista faltas de um usuário específico
void listar_faltas_usuario(const char *nome) {
    FILE *f = fopen(FALTASFILE, "rb");
    if (!f) {
        printf("Nenhuma falta encontrada.\n");
        return;
    }
    Falta fta;
    int encontrou = 0;
    printf("=== Faltas de %s ===\n", nome);
    while (fread(&fta, sizeof(Falta), 1, f) == 1) {
        if (strcmp(fta.nome, nome) == 0) {
            printf("Disciplina: %s\n", fta.disciplina);
            printf("Faltas: %d\n\n", fta.faltas);
            encontrou = 1;
        }
    }
    if (!encontrou) {
        printf("Nenhuma falta para este usuário.\n");
    }
    fclose(f);
}
