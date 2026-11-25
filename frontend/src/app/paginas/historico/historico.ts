import { Component, computed, effect, inject, signal } from '@angular/core';
import { Api, Registro, dataHoraCurta, mensagemDeErro } from '../../api';
import { Estado } from '../../estado';

const POR_PAGINA = 20;

@Component({
  selector: 'app-historico',
  templateUrl: './historico.html',
  styleUrl: './historico.css',
})
export class Historico {
  private api = inject(Api);
  private estado = inject(Estado);

  protected busca = signal('');
  protected status = signal('');
  protected registros = signal<Registro[]>([]);
  protected pagina = signal(0);
  protected erro = signal<string | null>(null);
  protected dataHora = dataHoraCurta;

  protected total = computed(() => this.registros().length);
  protected ultimaPagina = computed(() => Math.max(0, Math.ceil(this.total() / POR_PAGINA) - 1));
  protected visiveis = computed(() =>
    this.registros().slice(this.pagina() * POR_PAGINA, (this.pagina() + 1) * POR_PAGINA),
  );
  protected faixa = computed(() => {
    if (!this.total()) return 'Nenhum registro';
    const inicio = this.pagina() * POR_PAGINA + 1;
    const fim = Math.min(this.total(), inicio + POR_PAGINA - 1);
    return `Mostrando ${inicio}–${fim} de ${this.total().toLocaleString('pt-BR')}`;
  });

  private espera?: ReturnType<typeof setTimeout>;

  constructor() {
    effect(() => {
      // Recarrega ao mudar os filtros ou quando algo novo for processado
      const filtros = { busca: this.busca(), status: this.status() };
      const hoje = this.estado.status()?.hoje;
      void (hoje && hoje.sucessos + hoje.erros);
      clearTimeout(this.espera);
      this.espera = setTimeout(() => this.carregar(filtros), 250);
    });
  }

  protected filtrar(campo: 'busca' | 'status', valor: string) {
    this[campo].set(valor);
    this.pagina.set(0);
  }

  private async carregar(filtros: { busca: string; status: string }) {
    try {
      this.registros.set(await this.api.historico({ ...filtros, limite: 10000 }));
      this.pagina.update((p) => Math.min(p, this.ultimaPagina()));
      this.erro.set(null);
    } catch (erro) {
      this.erro.set(mensagemDeErro(erro));
    }
  }
}
