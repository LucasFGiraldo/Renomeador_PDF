import { Component, computed, effect, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Api, Registro, dataHoraCurta, mensagemDeErro } from '../../api';
import { Estado } from '../../estado';

@Component({
  selector: 'app-painel',
  imports: [RouterLink],
  templateUrl: './painel.html',
  styleUrl: './painel.css',
})
export class Painel {
  private api = inject(Api);
  protected estado = inject(Estado);

  protected recentes = signal<Registro[]>([]);
  protected arrastando = signal(false);
  protected envio = signal<{ texto: string; erro: boolean } | null>(null);
  protected hora = (r: Registro) => dataHoraCurta(r.data_hora).split(' ')[1];

  protected pastas = computed(() => {
    const p = this.estado.status()?.pastas;
    if (!p) return [];
    return [
      { nome: 'Entrada', pasta: p.entrada },
      { nome: 'Saída', pasta: p.saida },
      { nome: 'Erros', pasta: p.erros },
    ];
  });

  private ultimoTotal = -1;

  constructor() {
    // Recarrega a lista sempre que o total de renomeados de hoje mudar
    effect(() => {
      const total = this.estado.status()?.hoje.sucessos ?? 0;
      if (total !== this.ultimoTotal) {
        this.ultimoTotal = total;
        this.carregarRecentes();
      }
    });
  }

  private async carregarRecentes() {
    try {
      this.recentes.set(await this.api.historico({ status: 'sucesso', limite: 6 }));
    } catch {
      // O topo já mostra "API desconectada"
    }
  }

  protected soltar(evento: DragEvent) {
    evento.preventDefault();
    this.arrastando.set(false);
    this.enviar(Array.from(evento.dataTransfer?.files ?? []));
  }

  protected escolher(entrada: HTMLInputElement) {
    this.enviar(Array.from(entrada.files ?? []));
    entrada.value = '';
  }

  private async enviar(arquivos: File[]) {
    if (!arquivos.length) return;
    this.envio.set({ texto: 'Enviando…', erro: false });
    try {
      const r = await this.api.enviarPdfs(arquivos);
      const partes = [];
      if (r.salvos.length) partes.push(`${r.salvos.length} enviado(s) para a pasta de entrada`);
      if (r.recusados.length) partes.push(`${r.recusados.length} recusado(s): não é PDF`);
      this.envio.set({ texto: partes.join(' · '), erro: r.recusados.length > 0 });
      this.estado.atualizar();
    } catch (erro) {
      this.envio.set({ texto: mensagemDeErro(erro), erro: true });
    }
  }
}
