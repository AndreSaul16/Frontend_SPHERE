import { Component, type ReactNode, type ErrorInfo } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Log error to console in production
    console.error("ErrorBoundary caught an error:", error);
    console.error("Component stack:", info.componentStack);
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Allow custom fallback or use default
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          role="alert"
          className="flex flex-col items-center justify-center min-h-[300px] p-8 text-center"
        >
          <div className="mb-6 h-16 w-16 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
            <svg
              className="h-8 w-8 text-red-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">
            Algo salió mal
          </h2>
          <p className="text-sm text-gray-400 max-w-md mb-6 leading-relaxed">
            Ocurrió un error inesperado. Por favor, intentá nuevamente. Si el
            problema persiste, recargá la página.
          </p>
          <button
            onClick={this.handleRetry}
            className="px-6 py-2.5 rounded-xl bg-electric-cyan/10 border border-electric-cyan/30 text-electric-cyan font-medium text-sm hover:bg-electric-cyan/20 transition-colors"
          >
            Reintentar
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
