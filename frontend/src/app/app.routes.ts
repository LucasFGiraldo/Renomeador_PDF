import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'painel' },
  { path: 'painel', title: 'Painel · Renomeador de PDFs', loadComponent: () => import('./paginas/painel/painel').then((m) => m.Painel) },
  {
    path: 'configuracao',
    title: 'Configuração · Renomeador de PDFs',
    loadComponent: () => import('./paginas/configuracao/configuracao').then((m) => m.Configuracao),
  },
  {
    path: 'historico',
    title: 'Histórico · Renomeador de PDFs',
    loadComponent: () => import('./paginas/historico/historico').then((m) => m.Historico),
  },
  { path: 'erros', title: 'Erros · Renomeador de PDFs', loadComponent: () => import('./paginas/erros/erros').then((m) => m.Erros) },
  { path: '**', redirectTo: 'painel' },
];
