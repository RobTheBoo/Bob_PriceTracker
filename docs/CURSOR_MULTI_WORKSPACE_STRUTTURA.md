# Guida: Struttura Repo Multi-Progetto per Cursor

> Come organizzare un repository aziendale con agents, sub-agents, skills e rules, aperto come multi-workspace da sviluppatori che lavorano su prodotti diversi.

## 📚 Riferimenti Documentazione Cursor

- **Rules**: [cursor.com/docs/context/rules](https://cursor.com/docs/context/rules)
- **Skills**: [cursor.com/docs/context/skills](https://cursor.com/docs/context/skills)
- **Sub-agents**: [cursor.com/docs/context/subagents](https://cursor.com/docs/context/subagents)
- **Worktrees (parallel agents)**: [cursor.com/docs/configuration/worktrees](https://cursor.com/docs/configuration/worktrees)

---

## Strutture da **duplicare per ogni progetto/prodotto**

Per avere un repo efficiente in modalità multi-workspace, ogni prodotto deve avere **la propria copia** di queste cartelle/file:

### 1. `.cursor/rules/` (Project Rules)

```
prodotto-a/
├── .cursor/
│   └── rules/
│       ├── convenzioni-prodotto.mdc
│       ├── architettura.mdc
│       └── testing.mdc
```

**Perché duplicare:** Le rules sono valutate per contesto. Cursor può dare priorità alla prima cartella (alfabeticamente) in un multi-root. Avere `.cursor/rules/` in ogni prodotto garantisce che le convenzioni specifiche vengano applicate correttamente quando si lavora in quella cartella.

### 2. `.cursor/skills/` oppure `.agents/skills/`

```
prodotto-a/
├── .cursor/
│   └── skills/
│       └── skill-specifico-prodotto/
│           └── SKILL.md
```

**Perché duplicare:** Le skills sono scoperte da `.agents/skills/` e `.cursor/skills/`. Skills specifiche per prodotto (es. "deploy-microservizio-X") devono vivere nella root del progetto.

### 3. `AGENTS.md` (alternativa semplificata)

Se preferisci non usare `.cursor/rules/`, un singolo `AGENTS.md` nella root di ogni prodotto funziona come alternativa più semplice.

---

## Strutture **condivise** (root del repo)

Queste strutture vanno definite **una sola volta** a livello repository:

### 1. Team Rules (se disponibili)

Le Team Rules sono gestite dal dashboard Cursor e si applicano a tutta l'organizzazione. Non vanno duplicate.

### 2. Skills condivise (opzionale)

Puoi mettere skills riutilizzabili in **una cartella condivisa** e referenziarle:

```
repo-root/
├── .cursor/                    # Regole/skills condivise (workspace-level)
│   └── skills/
│       └── lint-aziendale/
│           └── SKILL.md
├── prodotti/
│   ├── prodotto-a/
│   │   └── .cursor/
│   │       ├── rules/
│   │       └── skills/         # Solo skill specifiche prodotto
│   └── prodotto-b/
│       └── .cursor/
│           ├── rules/
│           └── skills/
```

**Nota:** Le skills in `~/.cursor/skills/` sono globali per utente. Per il repo, conviene avere una cartella condivisa a livello root se tutti i prodotti le usano.

### 3. File workspace `.code-workspace`

Salva la configurazione multi-root in un file `.code-workspace` nella root:

```json
{
  "folders": [
    { "path": "prodotti/prodotto-a", "name": "Prodotto A" },
    { "path": "prodotti/prodotto-b", "name": "Prodotto B" }
  ],
  "settings": {}
}
```

---

## Gerarchia di applicazione (precedenza)

1. **Team Rules** (dashboard)
2. **Project Rules** (`.cursor/rules/` del progetto)
3. **User Rules** (impostazioni Cursor personali)
4. **Legacy** (`.cursorrules`, `AGENTS.md`)

---

## Best practice per multi-workspace

| Aspetto | Raccomandazione |
|---------|-----------------|
| **Glob patterns** | Usa glob espliciti nelle rules (es. `**/prodotto-a/**/*.ts`) per limitare l'applicazione |
| **Descrizioni** | Scrivi descrizioni chiare nel frontmatter delle rules: "Usa questa rule quando lavori su frontend React del Prodotto A" |
| **Base folder** | Mantieni tutti i prodotti sotto una cartella comune: l'indicizzazione del codebase funziona meglio se i file sono nello stesso albero |
| **Nomi cartelle** | Le cartelle vengono ordinate alfabeticamente; la prima può influenzare il comportamento. Usa prefissi se serve (es. `01-prodotto-a`) |
| **Indexing** | Esiste una limitazione: l'indicizzazione non funziona pienamente se i file non sono nella stessa base folder |

---

## Struttura raccomandata finale

```
repo-aziendale/
├── .code-workspace              # Config multi-root (aprire questo)
├── .cursor/                     # Opzionale: rules/skills condivise
│   ├── rules/
│   │   └── standard-aziendali.mdc
│   └── skills/
│       └── skill-condiviso/
├── prodotti/
│   ├── prodotto-a/
│   │   ├── .cursor/
│   │   │   ├── rules/           # ⬅️ DUPLICARE per ogni prodotto
│   │   │   │   ├── architettura.mdc
│   │   │   │   └── convenzioni.mdc
│   │   │   └── skills/         # ⬅️ DUPLICARE se skills specifiche
│   │   ├── src/
│   │   └── ...
│   ├── prodotto-b/
│   │   ├── .cursor/
│   │   │   ├── rules/
│   │   │   └── skills/
│   │   └── ...
│   └── prodotto-c/
│       └── ...
└── docs/
    └── CURSOR_MULTI_WORKSPACE_STRUTTURA.md  # Questa guida
```

---

## Checklist per ogni nuovo prodotto

- [ ] Creare `.cursor/rules/` con almeno un file `.mdc`
- [ ] Aggiungere glob/description appropriati per il prodotto
- [ ] (Opzionale) Creare `.cursor/skills/` per skill specifiche
- [ ] Aggiungere la cartella al file `.code-workspace`
- [ ] Verificare che le rules si applichino lavorando su file del prodotto

---

## Limitazioni note (da documentazione/forum)

- **Rules multi-folder:** Cursor può dare priorità alle rules della prima cartella; le description e i glob aiutano ma non sono una garanzia.
- **Indexing:** Se i progetti sono in percorsi molto disparati, l'indicizzazione cross-project può essere limitata.
- **Worktrees:** Per lavoro parallelo degli agenti, Cursor usa worktrees Git; utile per task distribuiti.

---

*Documento generato da documentazione Cursor ufficiale e best practices dalla community.*
