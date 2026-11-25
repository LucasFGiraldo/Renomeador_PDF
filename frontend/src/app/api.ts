import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom } from 'rxjs';

// Formatos devolvidos pela API (api.py)

export interface Pasta {
  caminho: string;
  acessivel: boolean;
}

export interface Status {
  monitor: { ativo: boolean; parando: boolean; iniciado_em: string | null; erro: string | null };
  configurado: boolean;
  pastas: { entrada: Pasta; saida: Pasta; erros: Pasta };
  fila: number;
  com_erro: number;
  hoje: { sucessos: number; erros: number };
}

export interface Configuracao {
  sufixo: string;
  incluir_data: boolean;
  incluir_valor: boolean;
  incluir_nome: boolean;
}

export interface DadosPdf {
  cliente?: string | null;
  data?: string | null;
  valor?: string | null;
}

export interface Registro {
  data_hora: string;
  status: 'sucesso' | 'erro';
  arquivo_original: string;
  novo_nome?: string;
  erro?: string;
  dados: DadosPdf;
}

export interface PdfComErro {
  arquivo: string;
  tamanho: number;
  modificado_em: string;
  erro: string | null;
  dados: DadosPdf;
}

export interface DetalheErro {
  arquivo: string;
  dados: DadosPdf;
  erro_leitura: string | null;
}

@Injectable({ providedIn: 'root' })
export class Api {
  private http = inject(HttpClient);

  status() {
    return firstValueFrom(this.http.get<Status>('/api/status'));
  }

  iniciarMonitor() {
    return firstValueFrom(this.http.post<Status>('/api/monitor/iniciar', null));
  }

  pararMonitor() {
    return firstValueFrom(this.http.post<Status>('/api/monitor/parar', null));
  }

  configuracao() {
    return firstValueFrom(this.http.get<Configuracao>('/api/configuracao'));
  }

  salvarConfiguracao(configuracao: Configuracao) {
    return firstValueFrom(this.http.put<Configuracao>('/api/configuracao', configuracao));
  }

  previa(dados: DadosPdf, configuracao?: Configuracao) {
    return firstValueFrom(
      this.http.post<{ nome: string }>('/api/configuracao/previa', { dados, configuracao }),
    );
  }

  historico(filtros: { status?: string; busca?: string; limite?: number }) {
    let params = new HttpParams();
    for (const [chave, valor] of Object.entries(filtros)) {
      if (valor) params = params.set(chave, valor);
    }
    return firstValueFrom(this.http.get<Registro[]>('/api/historico', { params }));
  }

  erros() {
    return firstValueFrom(this.http.get<PdfComErro[]>('/api/erros'));
  }

  detalheErro(arquivo: string) {
    return firstValueFrom(this.http.get<DetalheErro>(`/api/erros/${encodeURIComponent(arquivo)}`));
  }

  urlPdf(arquivo: string) {
    return `/api/erros/${encodeURIComponent(arquivo)}/pdf`;
  }

  reprocessar(arquivo: string, dados: DadosPdf) {
    return firstValueFrom(
      this.http.post<{ novo_nome: string }>(
        `/api/erros/${encodeURIComponent(arquivo)}/reprocessar`,
        dados,
      ),
    );
  }

  enviarPdfs(arquivos: File[]) {
    const form = new FormData();
    for (const arquivo of arquivos) form.append('arquivos', arquivo);
    return firstValueFrom(
      this.http.post<{ salvos: string[]; recusados: { arquivo: string; motivo: string }[] }>(
        '/api/pdfs',
        form,
      ),
    );
  }
}

/** Transforma o erro da API numa frase para mostrar na tela. */
export function mensagemDeErro(erro: unknown): string {
  if (erro instanceof HttpErrorResponse) {
    if (erro.status === 0) return 'Não foi possível falar com a API. Ela está rodando?';
    const detalhe = erro.error?.detail;
    if (typeof detalhe === 'string') return detalhe;
    // Erro de validação do FastAPI: lista de campos
    if (Array.isArray(detalhe)) {
      return detalhe.map((d) => `${d.loc?.at(-1)}: ${d.msg.replace('Value error, ', '')}`).join('; ');
    }
  }
  return 'Erro inesperado.';
}

/** "2026-11-25T13:23:38" → "25/11 13:23" */
export function dataHoraCurta(iso: string): string {
  const [data, hora] = iso.split('T');
  const [, mes, dia] = data.split('-');
  return `${dia}/${mes} ${hora.slice(0, 5)}`;
}
