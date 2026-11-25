import { HttpErrorResponse } from '@angular/common/http';
import { Component, effect, inject, signal } from '@angular/core';
import { Api, Configuracao as Config, mensagemDeErro } from '../../api';
import { Estado } from '../../estado';

// Comprovante de exemplo usado na prévia
const EXEMPLO = {
  cliente: 'EMPRESA EXEMPLO SERVICOS LTDA',
  data: '02-02-2026',
  valor: '2.898,00',
};

const PADRAO: Config = { sufixo: 'COMP', incluir_data: true, incluir_nome: true, incluir_valor: true };

@Component({
  selector: 'app-configuracao',
  templateUrl: './configuracao.html',
  styleUrl: './configuracao.css',
})
export class Configuracao {
  private api = inject(Api);
  private estado = inject(Estado);

  protected config = signal<Config>({ ...PADRAO });
  protected previa = signal('');
  protected aviso = signal<{ texto: string; erro: boolean } | null>(null);
  protected salvando = signal(false);

  private espera?: ReturnType<typeof setTimeout>;

  constructor() {
    this.carregar();
    // Atualiza a prévia (com um pequeno atraso enquanto a pessoa digita)
    effect(() => {
      const config = this.config();
      clearTimeout(this.espera);
      this.espera = setTimeout(() => this.atualizarPrevia(config), 200);
    });
  }

  protected alterar<K extends keyof Config>(campo: K, valor: Config[K]) {
    this.config.update((c) => ({ ...c, [campo]: valor }));
    this.aviso.set(null);
  }

  protected async carregar() {
    this.aviso.set(null);
    try {
      this.config.set(await this.api.configuracao());
    } catch (erro) {
      if (erro instanceof HttpErrorResponse && erro.status === 404) {
        this.config.set({ ...PADRAO });
        this.aviso.set({ texto: 'Ainda não há configuração salva.', erro: false });
      } else {
        this.aviso.set({ texto: mensagemDeErro(erro), erro: true });
      }
    }
  }

  protected async salvar() {
    this.salvando.set(true);
    try {
      this.config.set(await this.api.salvarConfiguracao(this.config()));
      this.aviso.set({ texto: 'Configuração salva.', erro: false });
      this.estado.atualizar();
    } catch (erro) {
      this.aviso.set({ texto: mensagemDeErro(erro), erro: true });
    } finally {
      this.salvando.set(false);
    }
  }

  private async atualizarPrevia(config: Config) {
    if (!config.sufixo.trim()) {
      this.previa.set('');
      return;
    }
    try {
      this.previa.set((await this.api.previa(EXEMPLO, config)).nome);
    } catch {
      this.previa.set('');
    }
  }
}
