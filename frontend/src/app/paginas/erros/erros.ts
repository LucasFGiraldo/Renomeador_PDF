import { Component, computed, effect, inject, signal } from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';
import { Api, Configuracao, DadosPdf, PdfComErro, mensagemDeErro } from '../../api';
import { Estado } from '../../estado';

@Component({
  selector: 'app-erros',
  templateUrl: './erros.html',
  styleUrl: './erros.css',
})
export class Erros {
  private api = inject(Api);
  private estado = inject(Estado);
  private sanitizer = inject(DomSanitizer);

  protected lista = signal<PdfComErro[]>([]);
  protected carregou = signal(false);
  protected selecionado = signal<string | null>(null);
  protected dados = signal<DadosPdf>({});
  protected previa = signal<{ texto: string; ok: boolean }>({ texto: '', ok: false });
  protected aviso = signal<{ texto: string; erro: boolean } | null>(null);
  protected enviando = signal(false);
  private config = signal<Configuracao | null>(null);

  protected item = computed(() => this.lista().find((i) => i.arquivo === this.selecionado()) ?? null);
  protected urlPdf = computed(() => {
    const arquivo = this.selecionado();
    return arquivo ? this.api.urlPdf(arquivo) : null;
  });
  protected urlPdfSegura = computed(() => {
    const url = this.urlPdf();
    return url ? this.sanitizer.bypassSecurityTrustResourceUrl(url) : null;
  });
  /** Campos obrigatórios (marcados na configuração) que estão vazios */
  protected faltando = computed(() => {
    const c = this.config();
    const d = this.dados();
    return {
      cliente: !!c?.incluir_nome && !d.cliente?.trim(),
      data: !!c?.incluir_data && !d.data?.trim(),
      valor: !!c?.incluir_valor && !d.valor?.trim(),
    };
  });

  private ultimaContagem = -1;
  private espera?: ReturnType<typeof setTimeout>;

  constructor() {
    this.api.configuracao().then((c) => this.config.set(c), () => {});

    // Recarrega a lista quando a quantidade na pasta de erros mudar
    effect(() => {
      const n = this.estado.status()?.com_erro ?? 0;
      if (n !== this.ultimaContagem) {
        this.ultimaContagem = n;
        this.carregarLista();
      }
    });

    // Prévia do nome enquanto os campos são editados
    effect(() => {
      const dados = this.dados();
      if (!this.selecionado()) return;
      clearTimeout(this.espera);
      this.espera = setTimeout(() => this.atualizarPrevia(dados), 200);
    });
  }

  protected async selecionar(arquivo: string, limparAviso = true) {
    this.selecionado.set(arquivo);
    if (limparAviso) this.aviso.set(null);
    // Começa com o que foi lido no erro e depois relê o PDF
    this.dados.set({ ...(this.item()?.dados ?? {}) });
    try {
      const detalhe = await this.api.detalheErro(arquivo);
      if (this.selecionado() === arquivo) this.dados.set({ ...detalhe.dados });
    } catch (erro) {
      this.aviso.set({ texto: mensagemDeErro(erro), erro: true });
    }
  }

  protected alterar(campo: keyof DadosPdf, valor: string) {
    this.dados.update((d) => ({ ...d, [campo]: valor }));
  }

  protected async renomear() {
    const arquivo = this.selecionado();
    if (!arquivo) return;
    this.enviando.set(true);
    try {
      const r = await this.api.reprocessar(arquivo, this.dados());
      this.aviso.set({ texto: `Renomeado como ${r.novo_nome}`, erro: false });
      this.selecionado.set(null);
      await this.carregarLista();
      this.estado.atualizar();
    } catch (erro) {
      this.aviso.set({ texto: mensagemDeErro(erro), erro: true });
    } finally {
      this.enviando.set(false);
    }
  }

  private async carregarLista() {
    try {
      const lista = await this.api.erros();
      this.lista.set(lista);
      // Mantém a seleção; se não houver, abre o primeiro
      if (!lista.some((i) => i.arquivo === this.selecionado())) {
        if (lista.length) this.selecionar(lista[0].arquivo, false);
        else this.selecionado.set(null);
      }
    } catch {
      // O topo já mostra "API desconectada"
    } finally {
      this.carregou.set(true);
    }
  }

  private async atualizarPrevia(dados: DadosPdf) {
    try {
      this.previa.set({ texto: (await this.api.previa(dados)).nome, ok: true });
    } catch (erro) {
      this.previa.set({ texto: mensagemDeErro(erro), ok: false });
    }
  }
}
