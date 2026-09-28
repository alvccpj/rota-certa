import { Component, type ErrorInfo, type ReactNode } from "react";

interface State {
  error: Error | null;
}

/** Mostra uma mensagem orientando o usuário quando uma tela falha ao ser exibida. */
export default class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Falha ao exibir a tela", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <section className="page state-page">
        <h1>Esta tela não pôde ser exibida</h1>
        <p className="muted">
          Recarregue a página para tentar de novo. Se o problema continuar, avise o administrador do sistema
          informando o que você estava fazendo.
        </p>
        <button type="button" className="button primary" onClick={() => window.location.reload()}>
          Recarregar a página
        </button>
      </section>
    );
  }
}
