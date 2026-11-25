import { Injectable, inject, signal } from '@angular/core';
import { Api, Status, mensagemDeErro } from './api';

/**
 * Status do sistema compartilhado entre o topo e as telas.
 * É atualizado a cada poucos segundos enquanto o app está aberto.
 */
@Injectable({ providedIn: 'root' })
export class Estado {
  private api = inject(Api);

  readonly status = signal<Status | null>(null);
  readonly offline = signal(false);
  readonly erroMonitor = signal<string | null>(null);

  constructor() {
    this.atualizar();
    setInterval(() => this.atualizar(), 3000);
  }

  async atualizar() {
    try {
      this.status.set(await this.api.status());
      this.offline.set(false);
    } catch {
      this.offline.set(true);
    }
  }

  async alternarMonitor() {
    this.erroMonitor.set(null);
    try {
      const ativo = this.status()?.monitor.ativo;
      this.status.set(ativo ? await this.api.pararMonitor() : await this.api.iniciarMonitor());
    } catch (erro) {
      this.erroMonitor.set(mensagemDeErro(erro));
    }
  }
}
